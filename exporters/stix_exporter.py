"""
STIX 2.1 exporter for CTI data.
Converts extracted entities to STIX 2.1 objects.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid

try:
    from stix2 import (
        Indicator, Malware, ThreatActor, AttackPattern, Vulnerability,
        Campaign, Identity, Relationship, Bundle, Sighting, ObservedData,
        MarkingDefinition, TLP_WHITE, TLP_GREEN, TLP_AMBER, TLP_RED
    )
    STIX2_AVAILABLE = True
except ImportError:
    STIX2_AVAILABLE = False

from parsers import CTIEntities

logger = logging.getLogger(__name__)


class STIXExporter:
    """Exports CTI entities to STIX 2.1 format."""

    def __init__(
        self,
        identity_name: str = "AgenticCTI",
        identity_class: str = "system",
        default_marking: str = "TLP:WHITE",
        export_path: str = "./data/stix_exports"
    ):
        """
        Initialize STIX exporter.

        Args:
            identity_name: Name of the identity creating STIX objects
            identity_class: Class of identity (system, organization, individual)
            default_marking: Default TLP marking
            export_path: Directory to export STIX bundles

        Raises:
            ImportError: If stix2 package not installed
        """
        if not STIX2_AVAILABLE:
            raise ImportError("stix2 package is required. Install with: pip install stix2")

        self.identity = Identity(
            name=identity_name,
            identity_class=identity_class
        )

        # Set marking definition
        marking_map = {
            "TLP:WHITE": TLP_WHITE,
            "TLP:GREEN": TLP_GREEN,
            "TLP:AMBER": TLP_AMBER,
            "TLP:RED": TLP_RED
        }
        self.default_marking = marking_map.get(default_marking.upper(), TLP_WHITE)

        self.export_path = Path(export_path)
        self.export_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"STIXExporter initialized with identity: {identity_name}")

    def export_entities(
        self,
        entities: CTIEntities,
        source_url: str,
        title: str,
        **metadata
    ) -> Optional[Bundle]:
        """
        Export CTI entities to STIX 2.1 bundle.

        Args:
            entities: Extracted CTI entities
            source_url: Source URL
            title: Content title
            **metadata: Additional metadata

        Returns:
            STIX Bundle or None if failed
        """
        logger.info(f"Exporting entities to STIX 2.1 for: {title}")

        try:
            stix_objects = [self.identity]

            # Create indicators from IOCs
            for ioc_type, ioc_values in entities.iocs.items():
                for ioc_value in ioc_values[:50]:  # Limit to 50 per type
                    indicator = self._create_indicator(
                        ioc_type=ioc_type,
                        ioc_value=ioc_value,
                        name=f"{ioc_type.upper()}: {ioc_value}",
                        description=f"IOC extracted from {title}",
                        source_url=source_url,
                        confidence=int(entities.confidence * 100)
                    )
                    if indicator:
                        stix_objects.append(indicator)

            # Create vulnerability objects from CVEs
            for cve in entities.cves:
                vuln = self._create_vulnerability(
                    cve_id=cve,
                    name=f"Vulnerability {cve}",
                    description=f"CVE mentioned in {title}",
                    source_url=source_url
                )
                if vuln:
                    stix_objects.append(vuln)

            # Create threat actor objects
            for actor_name in entities.threat_actors:
                actor = self._create_threat_actor(
                    name=actor_name,
                    description=f"Threat actor mentioned in {title}",
                    source_url=source_url
                )
                if actor:
                    stix_objects.append(actor)

            # Create malware objects
            for malware_name in entities.malware:
                malware = self._create_malware(
                    name=malware_name,
                    description=f"Malware mentioned in {title}",
                    source_url=source_url
                )
                if malware:
                    stix_objects.append(malware)

            # Create campaign objects
            for campaign_name in entities.campaigns:
                campaign = self._create_campaign(
                    name=campaign_name,
                    description=f"Campaign mentioned in {title}",
                    source_url=source_url
                )
                if campaign:
                    stix_objects.append(campaign)

            # Create attack patterns from TTPs
            for ttp in entities.ttps:
                attack_pattern = self._create_attack_pattern(
                    name=ttp,
                    description=f"TTP mentioned in {title}",
                    source_url=source_url
                )
                if attack_pattern:
                    stix_objects.append(attack_pattern)

            # Create bundle
            bundle = Bundle(objects=stix_objects)

            logger.info(f"Created STIX bundle with {len(stix_objects)} objects")
            return bundle

        except Exception as e:
            logger.error(f"Error exporting to STIX: {e}", exc_info=True)
            return None

    def _create_indicator(
        self,
        ioc_type: str,
        ioc_value: str,
        name: str,
        description: str,
        source_url: str,
        confidence: int
    ) -> Optional[Indicator]:
        """Create STIX Indicator object."""
        try:
            # Map IOC type to STIX pattern
            pattern_map = {
                'ipv4': f"[ipv4-addr:value = '{ioc_value}']",
                'domain': f"[domain-name:value = '{ioc_value}']",
                'url': f"[url:value = '{ioc_value}']",
                'md5': f"[file:hashes.MD5 = '{ioc_value}']",
                'sha1': f"[file:hashes.'SHA-1' = '{ioc_value}']",
                'sha256': f"[file:hashes.'SHA-256' = '{ioc_value}']",
                'email': f"[email-addr:value = '{ioc_value}']",
            }

            pattern = pattern_map.get(ioc_type)
            if not pattern:
                logger.warning(f"Unknown IOC type: {ioc_type}")
                return None

            indicator = Indicator(
                name=name,
                description=description,
                pattern=pattern,
                pattern_type="stix",
                valid_from=datetime.now(timezone.utc),
                created_by_ref=self.identity.id,
                confidence=confidence,
                external_references=[{
                    "source_name": "AgenticCTI",
                    "url": source_url
                }],
                object_marking_refs=[self.default_marking],
                labels=["malicious-activity"]
            )

            return indicator

        except Exception as e:
            logger.error(f"Error creating indicator for {ioc_value}: {e}")
            return None

    def _create_vulnerability(
        self,
        cve_id: str,
        name: str,
        description: str,
        source_url: str
    ) -> Optional[Vulnerability]:
        """Create STIX Vulnerability object."""
        try:
            vuln = Vulnerability(
                name=name,
                description=description,
                created_by_ref=self.identity.id,
                external_references=[
                    {
                        "source_name": "cve",
                        "external_id": cve_id,
                        "url": f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve_id}"
                    },
                    {
                        "source_name": "AgenticCTI",
                        "url": source_url
                    }
                ],
                object_marking_refs=[self.default_marking]
            )

            return vuln

        except Exception as e:
            logger.error(f"Error creating vulnerability for {cve_id}: {e}")
            return None

    def _create_threat_actor(
        self,
        name: str,
        description: str,
        source_url: str
    ) -> Optional[ThreatActor]:
        """Create STIX ThreatActor object."""
        try:
            actor = ThreatActor(
                name=name,
                description=description,
                created_by_ref=self.identity.id,
                threat_actor_types=["unknown"],
                external_references=[{
                    "source_name": "AgenticCTI",
                    "url": source_url
                }],
                object_marking_refs=[self.default_marking]
            )

            return actor

        except Exception as e:
            logger.error(f"Error creating threat actor for {name}: {e}")
            return None

    def _create_malware(
        self,
        name: str,
        description: str,
        source_url: str
    ) -> Optional[Malware]:
        """Create STIX Malware object."""
        try:
            malware = Malware(
                name=name,
                description=description,
                created_by_ref=self.identity.id,
                is_family=False,
                malware_types=["unknown"],
                external_references=[{
                    "source_name": "AgenticCTI",
                    "url": source_url
                }],
                object_marking_refs=[self.default_marking]
            )

            return malware

        except Exception as e:
            logger.error(f"Error creating malware for {name}: {e}")
            return None

    def _create_campaign(
        self,
        name: str,
        description: str,
        source_url: str
    ) -> Optional[Campaign]:
        """Create STIX Campaign object."""
        try:
            campaign = Campaign(
                name=name,
                description=description,
                created_by_ref=self.identity.id,
                external_references=[{
                    "source_name": "AgenticCTI",
                    "url": source_url
                }],
                object_marking_refs=[self.default_marking]
            )

            return campaign

        except Exception as e:
            logger.error(f"Error creating campaign for {name}: {e}")
            return None

    def _create_attack_pattern(
        self,
        name: str,
        description: str,
        source_url: str
    ) -> Optional[AttackPattern]:
        """Create STIX AttackPattern object."""
        try:
            attack_pattern = AttackPattern(
                name=name,
                description=description,
                created_by_ref=self.identity.id,
                external_references=[{
                    "source_name": "AgenticCTI",
                    "url": source_url
                }],
                object_marking_refs=[self.default_marking]
            )

            return attack_pattern

        except Exception as e:
            logger.error(f"Error creating attack pattern for {name}: {e}")
            return None

    def save_bundle(
        self,
        bundle: Bundle,
        filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Save STIX bundle to file.

        Args:
            bundle: STIX Bundle to save
            filename: Optional filename (generates if None)

        Returns:
            Path to saved file or None if failed
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"stix_bundle_{timestamp}.json"

            filepath = self.export_path / filename

            with open(filepath, 'w') as f:
                f.write(bundle.serialize(indent=2, ensure_ascii=False))

            logger.info(f"Saved STIX bundle to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving STIX bundle: {e}")
            return None

    def load_bundle(self, filepath: Path) -> Optional[Bundle]:
        """
        Load STIX bundle from file.

        Args:
            filepath: Path to bundle file

        Returns:
            STIX Bundle or None if failed
        """
        try:
            with open(filepath, 'r') as f:
                return Bundle(**json.load(f))

        except Exception as e:
            logger.error(f"Error loading STIX bundle from {filepath}: {e}")
            return None

    def get_bundle_summary(self, bundle: Bundle) -> Dict[str, Any]:
        """
        Get summary of STIX bundle.

        Args:
            bundle: STIX Bundle

        Returns:
            Dictionary with bundle summary
        """
        summary = {
            'total_objects': len(bundle.objects),
            'object_types': {},
            'created_at': bundle.objects[0].created if bundle.objects else None
        }

        for obj in bundle.objects:
            obj_type = obj.type
            summary['object_types'][obj_type] = summary['object_types'].get(obj_type, 0) + 1

        return summary
