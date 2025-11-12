"""
YARA rule generation from CTI entities and IOCs.
Automatically generates detection rules from threat intelligence.
"""

import logging
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RuleType(str, Enum):
    """Types of YARA rules."""
    MALWARE = "malware"
    APT = "apt"
    EXPLOIT = "exploit"
    PHISHING = "phishing"
    GENERIC_THREAT = "generic_threat"


@dataclass
class YARARule:
    """Generated YARA rule."""
    name: str
    rule_type: RuleType
    description: str
    rule_content: str
    iocs: List[str]
    metadata: Dict
    created_at: str


class YARAGenerator:
    """
    Generate YARA rules from CTI findings.

    Features:
    - String-based rules from content patterns
    - Hash-based rules from file hashes
    - Network IOC rules (domains, IPs)
    - Metadata enrichment
    - Rule validation
    """

    def __init__(self):
        """Initialize YARA generator."""
        self.generated_rules: List[YARARule] = []
        logger.info("YARAGenerator initialized")

    def generate_from_entities(
        self,
        entities: Dict[str, List[str]],
        title: str,
        description: str,
        threat_type: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> List[YARARule]:
        """
        Generate YARA rules from extracted entities.

        Args:
            entities: Dictionary of extracted entities
            title: Threat title
            description: Threat description
            threat_type: Type of threat
            source_url: Source URL

        Returns:
            List of generated YARA rules
        """
        rules = []

        # Sanitize name for YARA
        rule_name = self._sanitize_rule_name(title or "unknown_threat")

        # Generate hash-based rule if hashes present
        if entities.get('hashes'):
            hash_rule = self._generate_hash_rule(
                rule_name=f"{rule_name}_hashes",
                hashes=entities['hashes'],
                description=description,
                metadata={
                    'source': source_url,
                    'threat_type': threat_type,
                    'created': datetime.utcnow().isoformat()
                }
            )
            if hash_rule:
                rules.append(hash_rule)

        # Generate network IOC rule
        network_iocs = []
        network_iocs.extend(entities.get('domains', []))
        network_iocs.extend(entities.get('ips', []))
        network_iocs.extend(entities.get('urls', []))

        if network_iocs:
            network_rule = self._generate_network_rule(
                rule_name=f"{rule_name}_network",
                iocs=network_iocs,
                description=description,
                metadata={
                    'source': source_url,
                    'threat_type': threat_type,
                    'created': datetime.utcnow().isoformat()
                }
            )
            if network_rule:
                rules.append(network_rule)

        # Generate malware family rule
        if entities.get('malware'):
            malware_rule = self._generate_malware_family_rule(
                rule_name=f"{rule_name}_malware",
                malware_families=entities['malware'],
                description=description,
                additional_strings=self._extract_malware_strings(entities),
                metadata={
                    'source': source_url,
                    'threat_type': threat_type,
                    'created': datetime.utcnow().isoformat()
                }
            )
            if malware_rule:
                rules.append(malware_rule)

        # Generate CVE-based rule
        if entities.get('cves'):
            cve_rule = self._generate_cve_rule(
                rule_name=f"{rule_name}_exploit",
                cves=entities['cves'],
                description=description,
                metadata={
                    'source': source_url,
                    'threat_type': threat_type,
                    'created': datetime.utcnow().isoformat()
                }
            )
            if cve_rule:
                rules.append(cve_rule)

        self.generated_rules.extend(rules)
        logger.info(f"Generated {len(rules)} YARA rules from entities")

        return rules

    def _sanitize_rule_name(self, name: str) -> str:
        """Sanitize name for use in YARA rule."""
        # Remove special characters, keep only alphanumeric and underscore
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)
        # Ensure it starts with a letter
        if name and not name[0].isalpha():
            name = 'rule_' + name
        # Limit length
        name = name[:64]
        # Ensure not empty
        if not name:
            name = 'generated_rule'

        return name.lower()

    def _generate_hash_rule(
        self,
        rule_name: str,
        hashes: List[str],
        description: str,
        metadata: Dict
    ) -> Optional[YARARule]:
        """Generate YARA rule based on file hashes."""
        if not hashes:
            return None

        # Categorize hashes by type
        md5_hashes = []
        sha1_hashes = []
        sha256_hashes = []

        for hash_val in hashes:
            hash_val = hash_val.lower().strip()
            if len(hash_val) == 32:
                md5_hashes.append(hash_val)
            elif len(hash_val) == 40:
                sha1_hashes.append(hash_val)
            elif len(hash_val) == 64:
                sha256_hashes.append(hash_val)

        if not (md5_hashes or sha1_hashes or sha256_hashes):
            return None

        # Build rule
        rule_lines = [
            f'rule {rule_name} {{',
            '    meta:',
            f'        description = "{self._escape_string(description[:200])}"',
            f'        author = "AgenticCTI"',
            f'        date = "{metadata.get("created", "")}"',
        ]

        if metadata.get('source'):
            rule_lines.append(f'        reference = "{metadata["source"]}"')

        if metadata.get('threat_type'):
            rule_lines.append(f'        threat_type = "{metadata["threat_type"]}"')

        rule_lines.append('        hash_based = "true"')
        rule_lines.append('')
        rule_lines.append('    condition:')

        # Add hash conditions
        conditions = []

        for i, hash_val in enumerate(md5_hashes[:10]):  # Limit to 10
            conditions.append(f'hash.md5(0, filesize) == "{hash_val}"')

        for i, hash_val in enumerate(sha1_hashes[:10]):
            conditions.append(f'hash.sha1(0, filesize) == "{hash_val}"')

        for i, hash_val in enumerate(sha256_hashes[:10]):
            conditions.append(f'hash.sha256(0, filesize) == "{hash_val}"')

        if conditions:
            # Join with OR
            condition_str = ' or\n        '.join(conditions)
            rule_lines.append(f'        {condition_str}')

        rule_lines.append('}')

        rule_content = '\n'.join(rule_lines)

        return YARARule(
            name=rule_name,
            rule_type=RuleType.MALWARE,
            description=description,
            rule_content=rule_content,
            iocs=hashes,
            metadata=metadata,
            created_at=metadata.get('created', datetime.utcnow().isoformat())
        )

    def _generate_network_rule(
        self,
        rule_name: str,
        iocs: List[str],
        description: str,
        metadata: Dict
    ) -> Optional[YARARule]:
        """Generate YARA rule for network IOCs."""
        if not iocs:
            return None

        # Build rule
        rule_lines = [
            f'rule {rule_name} {{',
            '    meta:',
            f'        description = "{self._escape_string(description[:200])}"',
            f'        author = "AgenticCTI"',
            f'        date = "{metadata.get("created", "")}"',
        ]

        if metadata.get('source'):
            rule_lines.append(f'        reference = "{metadata["source"]}"')

        if metadata.get('threat_type'):
            rule_lines.append(f'        threat_type = "{metadata["threat_type"]}"')

        rule_lines.append('        ioc_type = "network"')
        rule_lines.append('')
        rule_lines.append('    strings:')

        # Add IOC strings
        for i, ioc in enumerate(iocs[:50], 1):  # Limit to 50
            escaped_ioc = self._escape_string(ioc)
            rule_lines.append(f'        $ioc{i} = "{escaped_ioc}" nocase wide ascii')

        rule_lines.append('')
        rule_lines.append('    condition:')
        rule_lines.append('        any of ($ioc*)')
        rule_lines.append('}')

        rule_content = '\n'.join(rule_lines)

        return YARARule(
            name=rule_name,
            rule_type=RuleType.GENERIC_THREAT,
            description=description,
            rule_content=rule_content,
            iocs=iocs,
            metadata=metadata,
            created_at=metadata.get('created', datetime.utcnow().isoformat())
        )

    def _generate_malware_family_rule(
        self,
        rule_name: str,
        malware_families: List[str],
        description: str,
        additional_strings: List[str],
        metadata: Dict
    ) -> Optional[YARARule]:
        """Generate YARA rule for malware families."""
        if not malware_families:
            return None

        # Build rule
        rule_lines = [
            f'rule {rule_name} {{',
            '    meta:',
            f'        description = "{self._escape_string(description[:200])}"',
            f'        author = "AgenticCTI"',
            f'        date = "{metadata.get("created", "")}"',
        ]

        if metadata.get('source'):
            rule_lines.append(f'        reference = "{metadata["source"]}"')

        malware_str = ', '.join(malware_families[:5])
        rule_lines.append(f'        malware_families = "{malware_str}"')
        rule_lines.append('')
        rule_lines.append('    strings:')

        # Add malware family names
        for i, family in enumerate(malware_families[:20], 1):
            escaped = self._escape_string(family)
            rule_lines.append(f'        $family{i} = "{escaped}" nocase wide ascii')

        # Add additional strings
        for i, string in enumerate(additional_strings[:30], 1):
            if len(string) >= 4:  # Minimum string length
                escaped = self._escape_string(string)
                rule_lines.append(f'        $str{i} = "{escaped}" nocase wide ascii')

        rule_lines.append('')
        rule_lines.append('    condition:')
        rule_lines.append('        any of ($family*) or 2 of ($str*)')
        rule_lines.append('}')

        rule_content = '\n'.join(rule_lines)

        return YARARule(
            name=rule_name,
            rule_type=RuleType.MALWARE,
            description=description,
            rule_content=rule_content,
            iocs=malware_families,
            metadata=metadata,
            created_at=metadata.get('created', datetime.utcnow().isoformat())
        )

    def _generate_cve_rule(
        self,
        rule_name: str,
        cves: List[str],
        description: str,
        metadata: Dict
    ) -> Optional[YARARule]:
        """Generate YARA rule for CVE exploits."""
        if not cves:
            return None

        # Build rule
        rule_lines = [
            f'rule {rule_name} {{',
            '    meta:',
            f'        description = "{self._escape_string(description[:200])}"',
            f'        author = "AgenticCTI"',
            f'        date = "{metadata.get("created", "")}"',
        ]

        if metadata.get('source'):
            rule_lines.append(f'        reference = "{metadata["source"]}"')

        cve_str = ', '.join(cves[:10])
        rule_lines.append(f'        cves = "{cve_str}"')
        rule_lines.append('        rule_type = "exploit"')
        rule_lines.append('')
        rule_lines.append('    strings:')

        # Add CVE strings
        for i, cve in enumerate(cves[:20], 1):
            rule_lines.append(f'        $cve{i} = "{cve}" nocase wide ascii')

        # Add common exploit strings
        exploit_strings = [
            'exploit',
            'vulnerability',
            'poc',
            'proof of concept',
            'shellcode',
            'payload'
        ]

        for i, string in enumerate(exploit_strings, 1):
            rule_lines.append(f'        $exploit{i} = "{string}" nocase wide ascii')

        rule_lines.append('')
        rule_lines.append('    condition:')
        rule_lines.append('        any of ($cve*) and any of ($exploit*)')
        rule_lines.append('}')

        rule_content = '\n'.join(rule_lines)

        return YARARule(
            name=rule_name,
            rule_type=RuleType.EXPLOIT,
            description=description,
            rule_content=rule_content,
            iocs=cves,
            metadata=metadata,
            created_at=metadata.get('created', datetime.utcnow().isoformat())
        )

    def _extract_malware_strings(self, entities: Dict[str, List[str]]) -> List[str]:
        """Extract potential malware-related strings from entities."""
        strings = []

        # Add TTPs
        if entities.get('ttps'):
            strings.extend(entities['ttps'])

        # Add threat actor names
        if entities.get('threat_actors'):
            strings.extend(entities['threat_actors'])

        # Add campaigns
        if entities.get('campaigns'):
            strings.extend(entities['campaigns'])

        return list(set(strings))[:30]  # Deduplicate and limit

    def _escape_string(self, s: str) -> str:
        """Escape string for YARA rule."""
        # Escape special characters
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        return s

    def export_rules(self, output_path: str) -> bool:
        """
        Export all generated rules to a file.

        Args:
            output_path: Path to output .yar file

        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w') as f:
                f.write('/*\n')
                f.write(' * YARA Rules Generated by AgenticCTI\n')
                f.write(f' * Generated: {datetime.utcnow().isoformat()}Z\n')
                f.write(f' * Total Rules: {len(self.generated_rules)}\n')
                f.write(' */\n\n')

                # Add import statements
                f.write('import "hash"\n\n')

                for rule in self.generated_rules:
                    f.write(rule.rule_content)
                    f.write('\n\n')

            logger.info(f"Exported {len(self.generated_rules)} rules to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export rules: {e}")
            return False

    def validate_rule(self, rule: YARARule) -> bool:
        """
        Validate a YARA rule (basic syntax check).

        Args:
            rule: YARA rule to validate

        Returns:
            True if valid
        """
        try:
            content = rule.rule_content

            # Basic validation checks
            if not content.startswith('rule '):
                return False

            if '{' not in content or '}' not in content:
                return False

            if 'condition:' not in content:
                return False

            # Check balanced braces
            if content.count('{') != content.count('}'):
                return False

            return True

        except Exception as e:
            logger.error(f"Rule validation error: {e}")
            return False

    def get_rules_by_type(self, rule_type: RuleType) -> List[YARARule]:
        """Get all rules of a specific type."""
        return [r for r in self.generated_rules if r.rule_type == rule_type]

    def clear_rules(self):
        """Clear all generated rules."""
        self.generated_rules.clear()
        logger.info("Cleared all generated rules")

    def get_stats(self) -> Dict:
        """Get statistics about generated rules."""
        type_counts = {}
        for rule in self.generated_rules:
            type_counts[rule.rule_type.value] = type_counts.get(rule.rule_type.value, 0) + 1

        return {
            'total_rules': len(self.generated_rules),
            'rules_by_type': type_counts,
            'total_iocs': sum(len(r.iocs) for r in self.generated_rules)
        }
