"""
Webhook management system for real-time threat alerts.
Supports multiple webhook destinations with retry logic and batching.
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(str, Enum):
    """Types of alerts."""
    THREAT_DETECTED = "threat_detected"
    VULNERABILITY_FOUND = "vulnerability_found"
    IOC_DISCOVERED = "ioc_discovered"
    SCRAPE_COMPLETED = "scrape_completed"
    SCRAPE_FAILED = "scrape_failed"
    HIGH_RISK_CONTENT = "high_risk_content"
    NEW_MALWARE = "new_malware"
    NEW_THREAT_ACTOR = "new_threat_actor"


@dataclass
class WebhookAlert:
    """Webhook alert payload."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    timestamp: str
    title: str
    description: str
    source_url: Optional[str] = None
    entities: Optional[Dict[str, List[str]]] = None
    threat_classification: Optional[Dict] = None
    iocs: Optional[List[Dict]] = None
    recommendations: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert enums to strings
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class WebhookConfig:
    """Webhook destination configuration."""
    url: str
    name: str
    enabled: bool = True
    headers: Optional[Dict[str, str]] = None
    timeout: int = 10
    retry_count: int = 3
    secret: Optional[str] = None  # For HMAC signatures
    filter_severity: Optional[List[AlertSeverity]] = None  # Only send certain severities


class WebhookManager:
    """
    Manages webhook notifications with retry logic and batching.

    Features:
    - Multiple webhook destinations
    - Automatic retries with exponential backoff
    - Signature verification (HMAC)
    - Severity filtering per webhook
    - Batching support
    - Rate limiting
    """

    def __init__(self, webhooks: Optional[List[WebhookConfig]] = None):
        """
        Initialize webhook manager.

        Args:
            webhooks: List of webhook configurations
        """
        self.webhooks = webhooks or []
        self.session = self._create_session()
        self._sent_count = 0
        self._failed_count = 0

        logger.info(f"WebhookManager initialized with {len(self.webhooks)} webhooks")

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def add_webhook(self, webhook: WebhookConfig):
        """Add a webhook destination."""
        self.webhooks.append(webhook)
        logger.info(f"Added webhook: {webhook.name} -> {webhook.url}")

    def remove_webhook(self, name: str) -> bool:
        """Remove a webhook by name."""
        original_count = len(self.webhooks)
        self.webhooks = [w for w in self.webhooks if w.name != name]

        if len(self.webhooks) < original_count:
            logger.info(f"Removed webhook: {name}")
            return True

        return False

    def send_alert(
        self,
        alert: WebhookAlert,
        webhook_names: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Send alert to webhooks.

        Args:
            alert: Alert to send
            webhook_names: Optional list of specific webhook names to send to.
                          If None, sends to all webhooks.

        Returns:
            Dictionary mapping webhook names to success status
        """
        results = {}

        # Filter webhooks
        target_webhooks = self.webhooks
        if webhook_names:
            target_webhooks = [w for w in self.webhooks if w.name in webhook_names]

        for webhook in target_webhooks:
            if not webhook.enabled:
                logger.debug(f"Skipping disabled webhook: {webhook.name}")
                continue

            # Check severity filter
            if webhook.filter_severity and alert.severity not in webhook.filter_severity:
                logger.debug(f"Alert severity {alert.severity} filtered out for {webhook.name}")
                continue

            try:
                success = self._send_to_webhook(alert, webhook)
                results[webhook.name] = success

                if success:
                    self._sent_count += 1
                else:
                    self._failed_count += 1

            except Exception as e:
                logger.error(f"Error sending to webhook {webhook.name}: {e}")
                results[webhook.name] = False
                self._failed_count += 1

        return results

    def _send_to_webhook(self, alert: WebhookAlert, webhook: WebhookConfig) -> bool:
        """Send alert to a specific webhook."""
        try:
            payload = alert.to_dict()

            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AgenticCTI-Webhook/1.0'
            }

            if webhook.headers:
                headers.update(webhook.headers)

            # Add signature if secret is provided
            if webhook.secret:
                import hmac
                import hashlib

                payload_str = json.dumps(payload)
                signature = hmac.new(
                    webhook.secret.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers['X-Webhook-Signature'] = f"sha256={signature}"

            # Send request
            logger.info(f"Sending {alert.alert_type} alert to {webhook.name}")

            response = self.session.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=webhook.timeout
            )

            response.raise_for_status()

            logger.info(f"Successfully sent alert to {webhook.name} (status: {response.status_code})")
            return True

        except requests.exceptions.Timeout:
            logger.error(f"Timeout sending to {webhook.name}")
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send to {webhook.name}: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error sending to {webhook.name}: {e}")
            return False

    def send_batch(
        self,
        alerts: List[WebhookAlert],
        webhook_names: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Send multiple alerts in batch.

        Args:
            alerts: List of alerts to send
            webhook_names: Optional webhook names to target

        Returns:
            Dictionary mapping webhook names to successful send counts
        """
        results = {}

        for alert in alerts:
            send_results = self.send_alert(alert, webhook_names)

            for webhook_name, success in send_results.items():
                if webhook_name not in results:
                    results[webhook_name] = 0
                if success:
                    results[webhook_name] += 1

        return results

    def create_threat_alert(
        self,
        title: str,
        description: str,
        severity: AlertSeverity,
        source_url: Optional[str] = None,
        entities: Optional[Dict[str, List[str]]] = None,
        threat_classification: Optional[Dict] = None,
        recommendations: Optional[List[str]] = None
    ) -> WebhookAlert:
        """
        Create a threat detection alert.

        Args:
            title: Alert title
            description: Alert description
            severity: Alert severity
            source_url: Source URL
            entities: Extracted entities
            threat_classification: ML classification results
            recommendations: Recommended actions

        Returns:
            WebhookAlert ready to send
        """
        import uuid

        # Extract IOCs from entities
        iocs = []
        if entities:
            for ip in entities.get('ips', []):
                iocs.append({'type': 'ipv4', 'value': ip})
            for domain in entities.get('domains', []):
                iocs.append({'type': 'domain', 'value': domain})
            for hash_val in entities.get('hashes', []):
                iocs.append({'type': 'hash', 'value': hash_val})

        return WebhookAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=AlertType.THREAT_DETECTED,
            severity=severity,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            title=title,
            description=description,
            source_url=source_url,
            entities=entities,
            threat_classification=threat_classification,
            iocs=iocs if iocs else None,
            recommendations=recommendations
        )

    def create_vulnerability_alert(
        self,
        title: str,
        cves: List[str],
        severity: AlertSeverity,
        description: str,
        source_url: Optional[str] = None,
        affected_products: Optional[List[str]] = None
    ) -> WebhookAlert:
        """Create a vulnerability alert."""
        import uuid

        return WebhookAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=AlertType.VULNERABILITY_FOUND,
            severity=severity,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            title=title,
            description=description,
            source_url=source_url,
            entities={'cves': cves},
            metadata={
                'affected_products': affected_products,
                'cve_count': len(cves)
            }
        )

    def create_scrape_alert(
        self,
        url: str,
        success: bool,
        error_message: Optional[str] = None,
        entity_count: Optional[int] = None
    ) -> WebhookAlert:
        """Create a scraping completion/failure alert."""
        import uuid

        alert_type = AlertType.SCRAPE_COMPLETED if success else AlertType.SCRAPE_FAILED
        severity = AlertSeverity.INFO if success else AlertSeverity.MEDIUM

        title = f"Scrape {'completed' if success else 'failed'}: {url}"
        description = error_message if error_message else f"Successfully scraped {url}"

        if entity_count:
            description += f" ({entity_count} entities extracted)"

        return WebhookAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            title=title,
            description=description,
            source_url=url,
            metadata={'entity_count': entity_count} if entity_count else None
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get webhook statistics."""
        return {
            'webhooks_configured': len(self.webhooks),
            'webhooks_enabled': sum(1 for w in self.webhooks if w.enabled),
            'alerts_sent': self._sent_count,
            'alerts_failed': self._failed_count,
            'success_rate': (
                self._sent_count / (self._sent_count + self._failed_count)
                if (self._sent_count + self._failed_count) > 0
                else 0.0
            )
        }


# Slack-specific webhook formatter
class SlackWebhookFormatter:
    """Format alerts for Slack webhooks."""

    @staticmethod
    def format_alert(alert: WebhookAlert) -> Dict:
        """Format alert as Slack message."""
        # Severity colors
        colors = {
            AlertSeverity.CRITICAL: "#ff0000",
            AlertSeverity.HIGH: "#ff6600",
            AlertSeverity.MEDIUM: "#ffcc00",
            AlertSeverity.LOW: "#00cc00",
            AlertSeverity.INFO: "#0099ff"
        }

        # Severity emojis
        emojis = {
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.HIGH: "⚠️",
            AlertSeverity.MEDIUM: "⚡",
            AlertSeverity.LOW: "ℹ️",
            AlertSeverity.INFO: "📊"
        }

        fields = []

        # Add entities
        if alert.entities:
            entity_summary = []
            for entity_type, values in alert.entities.items():
                if values:
                    entity_summary.append(f"*{entity_type.upper()}:* {len(values)}")

            if entity_summary:
                fields.append({
                    "title": "Entities Detected",
                    "value": "\n".join(entity_summary),
                    "short": True
                })

        # Add threat classification
        if alert.threat_classification:
            fields.append({
                "title": "Threat Classification",
                "value": f"*Type:* {alert.threat_classification.get('threat_type', 'Unknown')}\n"
                        f"*Risk Score:* {alert.threat_classification.get('risk_score', 0):.1f}/100",
                "short": True
            })

        # Add IOC count
        if alert.iocs:
            fields.append({
                "title": "IOCs",
                "value": f"{len(alert.iocs)} indicators",
                "short": True
            })

        attachment = {
            "fallback": f"{emojis.get(alert.severity, '')} {alert.title}",
            "color": colors.get(alert.severity, "#cccccc"),
            "title": f"{emojis.get(alert.severity, '')} {alert.title}",
            "text": alert.description,
            "fields": fields,
            "footer": "AgenticCTI",
            "ts": int(datetime.fromisoformat(alert.timestamp.rstrip('Z')).timestamp())
        }

        if alert.source_url:
            attachment["title_link"] = alert.source_url

        if alert.recommendations:
            attachment["fields"].append({
                "title": "Recommended Actions",
                "value": "\n".join(f"• {rec}" for rec in alert.recommendations[:3]),
                "short": False
            })

        return {
            "text": f"New {alert.alert_type.value} alert",
            "attachments": [attachment]
        }
