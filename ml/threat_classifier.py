"""
ML-based threat classification for CTI content.
Uses hybrid approach: rule-based scoring + LLM analysis.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ThreatType(str, Enum):
    """Threat classification types."""
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    PHISHING = "phishing"
    APT = "apt"
    VULNERABILITY = "vulnerability"
    DATA_BREACH = "data_breach"
    DDoS = "ddos"
    FRAUD = "fraud"
    SCAM = "scam"
    BOTNET = "botnet"
    SUPPLY_CHAIN = "supply_chain"
    INSIDER_THREAT = "insider_threat"
    UNKNOWN = "unknown"


@dataclass
class ThreatClassification:
    """Result of threat classification."""
    threat_type: ThreatType
    threat_level: ThreatLevel
    confidence: float  # 0.0 to 1.0
    indicators: List[str]  # Reasons for classification
    risk_score: float  # 0 to 100
    recommended_actions: List[str]
    metadata: Optional[Dict] = None


class ThreatClassifier:
    """
    Advanced ML-based threat classifier.

    Uses multiple techniques:
    - Rule-based pattern matching
    - Entity-based scoring
    - Keyword analysis
    - LLM-based classification (optional)
    """

    # Threat keywords and patterns
    THREAT_PATTERNS = {
        ThreatType.RANSOMWARE: [
            r'\b(ransomware|cryptolocker|wannacry|locky|ryuk|revil|conti)\b',
            r'\b(encrypt|ransom|bitcoin|payment|decrypt)\b',
            r'\b(files?\s+encrypted|restore\s+files)\b'
        ],
        ThreatType.PHISHING: [
            r'\b(phishing|spear-?phishing|credential\s+harvest)\b',
            r'\b(fake\s+login|spoofed\s+email|malicious\s+link)\b',
            r'\b(business\s+email\s+compromise|bec)\b'
        ],
        ThreatType.APT: [
            r'\b(apt\d+|advanced\s+persistent\s+threat)\b',
            r'\b(nation[- ]state|state[- ]sponsored)\b',
            r'\b(lazarus|fancy\s+bear|cozy\s+bear|apt\s+group)\b'
        ],
        ThreatType.MALWARE: [
            r'\b(malware|trojan|virus|worm|backdoor)\b',
            r'\b(payload|dropper|loader|rat|remote\s+access)\b',
            r'\b(emotet|trickbot|qakbot|icedid)\b'
        ],
        ThreatType.VULNERABILITY: [
            r'\bCVE-\d{4}-\d{4,7}\b',
            r'\b(zero[- ]day|0day|vulnerability|exploit)\b',
            r'\b(rce|remote\s+code\s+execution|sql\s+injection)\b',
            r'\b(critical\s+vulnerability|security\s+flaw)\b'
        ],
        ThreatType.DATA_BREACH: [
            r'\b(data\s+breach|breach|leaked|exposed\s+data)\b',
            r'\b(stolen\s+data|compromised\s+data|exfiltrat)\b',
            r'\b(personal\s+information|pii|credentials\s+leaked)\b'
        ],
        ThreatType.DDoS: [
            r'\b(ddos|denial[- ]of[- ]service|dos\s+attack)\b',
            r'\b(botnet|amplification\s+attack)\b',
            r'\b(mirai|traffic\s+flood)\b'
        ],
        ThreatType.FRAUD: [
            r'\b(fraud|scam|fraudulent)\b',
            r'\b(financial\s+fraud|payment\s+fraud|wire\s+fraud)\b',
            r'\b(identity\s+theft|account\s+takeover)\b'
        ],
        ThreatType.SUPPLY_CHAIN: [
            r'\b(supply\s+chain|third[- ]party|vendor\s+compromise)\b',
            r'\b(software\s+supply\s+chain|dependency\s+attack)\b',
            r'\b(solarwinds|codecov|npm\s+package)\b'
        ]
    }

    # Severity keywords
    SEVERITY_KEYWORDS = {
        ThreatLevel.CRITICAL: [
            'critical', 'emergency', 'severe', 'widespread', 'actively exploited',
            'zero-day', '0day', 'worm', 'ransomware', 'apt'
        ],
        ThreatLevel.HIGH: [
            'high', 'serious', 'significant', 'remote code execution', 'rce',
            'data breach', 'malware', 'backdoor'
        ],
        ThreatLevel.MEDIUM: [
            'medium', 'moderate', 'elevated', 'vulnerability', 'exposure',
            'phishing', 'suspicious'
        ],
        ThreatLevel.LOW: [
            'low', 'minor', 'limited', 'informational', 'advisory'
        ]
    }

    def __init__(self, llm_provider=None):
        """
        Initialize threat classifier.

        Args:
            llm_provider: Optional LLM provider for advanced classification
        """
        self.llm_provider = llm_provider
        logger.info("ThreatClassifier initialized")

    def classify(
        self,
        content: str,
        entities: Optional[Dict[str, List[str]]] = None,
        title: Optional[str] = None
    ) -> ThreatClassification:
        """
        Classify threat based on content and entities.

        Args:
            content: Text content to classify
            entities: Extracted entities (CVEs, IPs, malware, etc.)
            title: Article/content title

        Returns:
            ThreatClassification with threat type, level, and details
        """
        # Combine title and content for analysis
        full_text = f"{title or ''} {content}".lower()

        # Step 1: Pattern-based threat type detection
        threat_scores = self._score_threat_types(full_text)

        # Step 2: Entity-based scoring
        entity_scores = self._score_entities(entities or {})

        # Step 3: Combine scores
        combined_scores = self._combine_scores(threat_scores, entity_scores)

        # Step 4: Determine threat type
        threat_type, confidence = self._determine_threat_type(combined_scores)

        # Step 5: Determine threat level
        threat_level = self._determine_threat_level(full_text, entities or {})

        # Step 6: Calculate risk score
        risk_score = self._calculate_risk_score(
            threat_type, threat_level, entities or {}, confidence
        )

        # Step 7: Identify indicators
        indicators = self._identify_indicators(
            full_text, threat_type, entities or {}
        )

        # Step 8: Generate recommendations
        recommendations = self._generate_recommendations(threat_type, threat_level)

        # Step 9: Optional LLM enhancement
        if self.llm_provider and confidence < 0.7:
            try:
                llm_result = self._llm_classify(content, title)
                if llm_result:
                    threat_type = llm_result.get('threat_type', threat_type)
                    confidence = max(confidence, llm_result.get('confidence', 0))
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}")

        return ThreatClassification(
            threat_type=threat_type,
            threat_level=threat_level,
            confidence=confidence,
            indicators=indicators,
            risk_score=risk_score,
            recommended_actions=recommendations,
            metadata={
                'entities_count': sum(len(v) for v in (entities or {}).values()),
                'content_length': len(content),
                'has_cve': bool(entities and entities.get('cves')),
                'has_ioc': bool(entities and (entities.get('ips') or entities.get('domains')))
            }
        )

    def _score_threat_types(self, text: str) -> Dict[ThreatType, float]:
        """Score each threat type based on pattern matching."""
        scores = {}

        for threat_type, patterns in self.THREAT_PATTERNS.items():
            score = 0.0
            matches = 0

            for pattern in patterns:
                found = re.findall(pattern, text, re.IGNORECASE)
                if found:
                    matches += len(found)
                    score += 1.0

            # Normalize score
            if matches > 0:
                scores[threat_type] = min(score / len(patterns), 1.0)

        return scores

    def _score_entities(self, entities: Dict[str, List[str]]) -> Dict[ThreatType, float]:
        """Score threat types based on extracted entities."""
        scores = {}

        # CVEs indicate vulnerabilities
        if entities.get('cves'):
            scores[ThreatType.VULNERABILITY] = min(len(entities['cves']) * 0.3, 1.0)

        # IOCs indicate active threats
        ioc_count = (
            len(entities.get('ips', [])) +
            len(entities.get('domains', [])) +
            len(entities.get('urls', [])) +
            len(entities.get('hashes', []))
        )
        if ioc_count > 0:
            scores[ThreatType.MALWARE] = min(ioc_count * 0.2, 1.0)

        # Malware names
        if entities.get('malware'):
            scores[ThreatType.MALWARE] = min(len(entities['malware']) * 0.4, 1.0)

        # Threat actors indicate APT
        if entities.get('threat_actors'):
            scores[ThreatType.APT] = min(len(entities['threat_actors']) * 0.5, 1.0)

        return scores

    def _combine_scores(
        self,
        pattern_scores: Dict[ThreatType, float],
        entity_scores: Dict[ThreatType, float]
    ) -> Dict[ThreatType, float]:
        """Combine pattern and entity scores."""
        combined = {}
        all_types = set(pattern_scores.keys()) | set(entity_scores.keys())

        for threat_type in all_types:
            pattern_score = pattern_scores.get(threat_type, 0.0)
            entity_score = entity_scores.get(threat_type, 0.0)

            # Weighted combination (70% patterns, 30% entities)
            combined[threat_type] = (pattern_score * 0.7) + (entity_score * 0.3)

        return combined

    def _determine_threat_type(
        self,
        scores: Dict[ThreatType, float]
    ) -> Tuple[ThreatType, float]:
        """Determine threat type and confidence from scores."""
        if not scores:
            return ThreatType.UNKNOWN, 0.0

        # Get top threat type
        threat_type = max(scores.items(), key=lambda x: x[1])

        # If score is too low, mark as unknown
        if threat_type[1] < 0.2:
            return ThreatType.UNKNOWN, threat_type[1]

        return threat_type[0], min(threat_type[1], 1.0)

    def _determine_threat_level(
        self,
        text: str,
        entities: Dict[str, List[str]]
    ) -> ThreatLevel:
        """Determine threat severity level."""
        # Count severity keywords
        level_scores = {}

        for level, keywords in self.SEVERITY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            level_scores[level] = score

        # Factor in entity counts
        cve_count = len(entities.get('cves', []))
        ioc_count = (
            len(entities.get('ips', [])) +
            len(entities.get('domains', [])) +
            len(entities.get('hashes', []))
        )

        # Critical if CVEs or many IOCs
        if cve_count > 2 or ioc_count > 10:
            level_scores[ThreatLevel.CRITICAL] = level_scores.get(ThreatLevel.CRITICAL, 0) + 2

        # Get highest scoring level
        if level_scores:
            return max(level_scores.items(), key=lambda x: x[1])[0]

        return ThreatLevel.INFO

    def _calculate_risk_score(
        self,
        threat_type: ThreatType,
        threat_level: ThreatLevel,
        entities: Dict[str, List[str]],
        confidence: float
    ) -> float:
        """Calculate overall risk score (0-100)."""
        # Base scores by threat type
        type_scores = {
            ThreatType.RANSOMWARE: 90,
            ThreatType.APT: 85,
            ThreatType.DATA_BREACH: 80,
            ThreatType.MALWARE: 70,
            ThreatType.VULNERABILITY: 65,
            ThreatType.SUPPLY_CHAIN: 75,
            ThreatType.PHISHING: 60,
            ThreatType.DDoS: 55,
            ThreatType.FRAUD: 50,
            ThreatType.UNKNOWN: 30
        }

        # Level multipliers
        level_multipliers = {
            ThreatLevel.CRITICAL: 1.0,
            ThreatLevel.HIGH: 0.8,
            ThreatLevel.MEDIUM: 0.6,
            ThreatLevel.LOW: 0.4,
            ThreatLevel.INFO: 0.2
        }

        base_score = type_scores.get(threat_type, 50)
        level_mult = level_multipliers.get(threat_level, 0.5)

        # Entity bonus
        entity_bonus = min(sum(len(v) for v in entities.values()) * 2, 15)

        # Calculate final score
        risk_score = (base_score * level_mult) + entity_bonus
        risk_score *= confidence  # Adjust by confidence

        return min(risk_score, 100.0)

    def _identify_indicators(
        self,
        text: str,
        threat_type: ThreatType,
        entities: Dict[str, List[str]]
    ) -> List[str]:
        """Identify specific indicators for the classification."""
        indicators = []

        # Add threat type specific indicators
        if threat_type in self.THREAT_PATTERNS:
            for pattern in self.THREAT_PATTERNS[threat_type]:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    indicators.append(f"Pattern match: {matches[0]}")

        # Add entity indicators
        if entities.get('cves'):
            indicators.append(f"CVEs detected: {len(entities['cves'])}")

        if entities.get('malware'):
            indicators.append(f"Malware families: {', '.join(entities['malware'][:3])}")

        if entities.get('threat_actors'):
            indicators.append(f"Threat actors: {', '.join(entities['threat_actors'][:3])}")

        ioc_count = sum(len(entities.get(k, [])) for k in ['ips', 'domains', 'urls', 'hashes'])
        if ioc_count > 0:
            indicators.append(f"IOCs detected: {ioc_count}")

        return indicators[:10]  # Limit to top 10

    def _generate_recommendations(
        self,
        threat_type: ThreatType,
        threat_level: ThreatLevel
    ) -> List[str]:
        """Generate recommended actions based on threat classification."""
        recommendations = []

        # Threat type specific recommendations
        type_recommendations = {
            ThreatType.RANSOMWARE: [
                "Ensure backups are up-to-date and offline",
                "Block identified IOCs at network perimeter",
                "Review and test incident response plan",
                "Monitor for lateral movement"
            ],
            ThreatType.PHISHING: [
                "Alert users about phishing campaign",
                "Block sender domains/IPs",
                "Review email security policies",
                "Conduct phishing awareness training"
            ],
            ThreatType.VULNERABILITY: [
                "Patch affected systems immediately",
                "Scan infrastructure for vulnerable versions",
                "Implement temporary mitigations if patch unavailable",
                "Monitor for exploitation attempts"
            ],
            ThreatType.MALWARE: [
                "Update anti-malware signatures",
                "Block malicious IOCs",
                "Hunt for indicators in environment",
                "Isolate infected systems"
            ],
            ThreatType.APT: [
                "Initiate threat hunt operations",
                "Review logs for historical compromise",
                "Engage threat intelligence team",
                "Consider external IR assistance"
            ],
            ThreatType.DATA_BREACH: [
                "Identify affected data and systems",
                "Notify affected parties per regulations",
                "Investigate breach scope and timeline",
                "Reset compromised credentials"
            ]
        }

        recommendations.extend(type_recommendations.get(threat_type, [
            "Review and assess threat relevance",
            "Update threat intelligence feeds",
            "Monitor for related indicators"
        ]))

        # Level-specific recommendations
        if threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
            recommendations.insert(0, "⚠️  URGENT: Escalate to security team immediately")

        return recommendations[:5]  # Top 5 recommendations

    def _llm_classify(self, content: str, title: Optional[str]) -> Optional[Dict]:
        """Optional LLM-based classification for complex cases."""
        if not self.llm_provider:
            return None

        try:
            prompt = f"""Analyze this cybersecurity threat and classify it.

Title: {title or 'N/A'}
Content: {content[:2000]}

Classify the threat type (ransomware, phishing, apt, malware, vulnerability, etc.) and provide a confidence score (0-1).

Respond in JSON format:
{{"threat_type": "...", "confidence": 0.0}}"""

            response = self.llm_provider.generate(prompt, temperature=0.1, max_tokens=100)

            # Parse JSON response
            import json
            return json.loads(response)

        except Exception as e:
            logger.error(f"LLM classification error: {e}")
            return None
