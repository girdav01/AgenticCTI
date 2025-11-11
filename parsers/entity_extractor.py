"""
Entity extraction module for CTI analysis.
Extracts TTPs, CVEs, IOCs, threat actors, and other entities using LLM.
"""

import re
import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
import json

from llm import BaseLLM, LLMFactory

logger = logging.getLogger(__name__)


@dataclass
class CTIEntities:
    """Container for extracted CTI entities."""
    ttps: List[str] = field(default_factory=list)  # Tactics, Techniques, Procedures
    cves: List[str] = field(default_factory=list)  # CVEs
    iocs: Dict[str, List[str]] = field(default_factory=dict)  # IOCs by type
    threat_actors: List[str] = field(default_factory=list)
    malware: List[str] = field(default_factory=list)
    campaigns: List[str] = field(default_factory=list)
    industries: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=list)
    summary: str = ""
    severity: str = "medium"  # low, medium, high, critical
    confidence: float = 0.5


class EntityExtractor:
    """Extracts CTI entities from text using LLM and regex patterns."""

    # Regex patterns for common IOCs
    PATTERNS = {
        'ipv4': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        'domain': r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b',
        'url': r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)',
        'md5': r'\b[a-fA-F0-9]{32}\b',
        'sha1': r'\b[a-fA-F0-9]{40}\b',
        'sha256': r'\b[a-fA-F0-9]{64}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'cve': r'CVE-\d{4}-\d{4,7}',
    }

    def __init__(self, llm: Optional[BaseLLM] = None):
        """
        Initialize entity extractor.

        Args:
            llm: LLM instance (creates default if None)
        """
        self.llm = llm or LLMFactory.get_default_llm()
        logger.info("EntityExtractor initialized")

    def extract_entities(self, text: str, title: str = "") -> CTIEntities:
        """
        Extract CTI entities from text.

        Args:
            text: Content to analyze
            title: Optional title for context

        Returns:
            CTIEntities object with extracted entities
        """
        logger.info("Extracting entities from content")

        entities = CTIEntities()

        try:
            # Extract using regex patterns
            regex_entities = self._extract_with_regex(text)

            # Extract using LLM
            llm_entities = self._extract_with_llm(text, title)

            # Merge results
            entities = self._merge_entities(regex_entities, llm_entities)

            logger.info(f"Extracted: {len(entities.cves)} CVEs, {len(entities.threat_actors)} threat actors, "
                       f"{sum(len(v) for v in entities.iocs.values())} IOCs")

            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return entities

    def _extract_with_regex(self, text: str) -> CTIEntities:
        """Extract entities using regex patterns."""
        entities = CTIEntities()

        # Extract CVEs
        cves = re.findall(self.PATTERNS['cve'], text, re.IGNORECASE)
        entities.cves = list(set(cves))

        # Extract IOCs
        entities.iocs = {
            'ipv4': list(set(re.findall(self.PATTERNS['ipv4'], text))),
            'domain': self._filter_domains(re.findall(self.PATTERNS['domain'], text.lower())),
            'url': list(set(re.findall(self.PATTERNS['url'], text))),
            'md5': list(set(re.findall(self.PATTERNS['md5'], text))),
            'sha1': list(set(re.findall(self.PATTERNS['sha1'], text))),
            'sha256': list(set(re.findall(self.PATTERNS['sha256'], text))),
            'email': list(set(re.findall(self.PATTERNS['email'], text))),
        }

        # Remove empty lists
        entities.iocs = {k: v for k, v in entities.iocs.items() if v}

        return entities

    def _filter_domains(self, domains: List[str]) -> List[str]:
        """Filter out common/benign domains."""
        # Common domains to exclude
        exclude = {
            'example.com', 'test.com', 'localhost', 'gmail.com', 'yahoo.com',
            'outlook.com', 'microsoft.com', 'google.com', 'twitter.com',
            'facebook.com', 'linkedin.com', 'github.com'
        }

        filtered = []
        for domain in set(domains):
            # Skip very short domains
            if len(domain) < 4:
                continue
            # Skip if in exclude list
            if domain in exclude:
                continue
            # Skip common extensions without subdomain
            if domain.count('.') == 1 and domain.split('.')[1] in ['com', 'org', 'net']:
                continue

            filtered.append(domain)

        return filtered[:50]  # Limit to 50 domains

    def _extract_with_llm(self, text: str, title: str) -> CTIEntities:
        """Extract entities using LLM."""
        entities = CTIEntities()

        # Truncate text if too long
        max_length = 4000
        if len(text) > max_length:
            text = text[:max_length] + "..."

        system_prompt = """You are a cybersecurity threat intelligence analyst. Extract structured information from threat reports.

Extract and categorize:
1. TTPs (Tactics, Techniques, Procedures) - specific attack methods
2. Threat actors - named groups or individuals
3. Malware - malware families, tools, variants
4. Campaigns - named attack campaigns
5. Targeted industries/sectors
6. Targeted countries/regions
7. Severity assessment (critical/high/medium/low)

Return response in JSON format:
{
  "ttps": ["technique1", "technique2"],
  "threat_actors": ["actor1", "actor2"],
  "malware": ["malware1", "malware2"],
  "campaigns": ["campaign1"],
  "industries": ["industry1"],
  "countries": ["country1"],
  "severity": "high",
  "summary": "Brief 1-2 sentence summary of the threat",
  "confidence": 0.8
}"""

        user_prompt = f"""Analyze this threat intelligence content:

Title: {title}

Content:
{text}

Extract all relevant CTI entities and provide a structured analysis."""

        try:
            response = self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2  # Lower temperature for more consistent extraction
            )

            if not self.llm.validate_response(response):
                logger.warning("Invalid LLM response for entity extraction")
                return entities

            # Parse JSON response
            parsed = self._parse_llm_response(response.content)

            entities.ttps = parsed.get('ttps', [])
            entities.threat_actors = parsed.get('threat_actors', [])
            entities.malware = parsed.get('malware', [])
            entities.campaigns = parsed.get('campaigns', [])
            entities.industries = parsed.get('industries', [])
            entities.countries = parsed.get('countries', [])
            entities.severity = parsed.get('severity', 'medium')
            entities.summary = parsed.get('summary', '')
            entities.confidence = parsed.get('confidence', 0.5)

            return entities

        except Exception as e:
            logger.error(f"Error in LLM entity extraction: {e}")
            return entities

    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response to extract JSON."""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

            # Try direct parse
            return json.loads(response)

        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON")
            # Fallback: try to extract fields manually
            return self._fallback_parse(response)

    def _fallback_parse(self, response: str) -> Dict:
        """Fallback parser for non-JSON responses."""
        result = {
            'ttps': [],
            'threat_actors': [],
            'malware': [],
            'campaigns': [],
            'industries': [],
            'countries': [],
            'severity': 'medium',
            'summary': '',
            'confidence': 0.5
        }

        # Simple line-based extraction
        lines = response.split('\n')
        current_key = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers
            lower = line.lower()
            if 'ttp' in lower or 'technique' in lower:
                current_key = 'ttps'
            elif 'threat actor' in lower or 'actor' in lower:
                current_key = 'threat_actors'
            elif 'malware' in lower:
                current_key = 'malware'
            elif 'campaign' in lower:
                current_key = 'campaigns'
            elif 'industry' in lower or 'sector' in lower:
                current_key = 'industries'
            elif 'country' in lower or 'region' in lower:
                current_key = 'countries'
            elif 'severity' in lower:
                current_key = 'severity'
            elif 'summary' in lower:
                current_key = 'summary'
            elif current_key and line.startswith(('-', '*', '•')):
                # List item
                item = line.lstrip('-*•').strip()
                if current_key in ['ttps', 'threat_actors', 'malware', 'campaigns', 'industries', 'countries']:
                    result[current_key].append(item)

        return result

    def _merge_entities(self, regex_entities: CTIEntities, llm_entities: CTIEntities) -> CTIEntities:
        """Merge entities from regex and LLM extraction."""
        merged = CTIEntities()

        # Combine CVEs (from regex)
        merged.cves = regex_entities.cves

        # Combine IOCs (from regex)
        merged.iocs = regex_entities.iocs

        # Use LLM results for semantic entities
        merged.ttps = llm_entities.ttps
        merged.threat_actors = llm_entities.threat_actors
        merged.malware = llm_entities.malware
        merged.campaigns = llm_entities.campaigns
        merged.industries = llm_entities.industries
        merged.countries = llm_entities.countries
        merged.severity = llm_entities.severity
        merged.summary = llm_entities.summary
        merged.confidence = llm_entities.confidence

        return merged

    def generate_summary(self, entities: CTIEntities, content: str) -> str:
        """
        Generate actionable summary from entities.

        Args:
            entities: Extracted entities
            content: Original content

        Returns:
            Actionable summary string
        """
        if entities.summary:
            return entities.summary

        logger.info("Generating summary from entities")

        system_prompt = """You are a cybersecurity analyst creating actionable threat summaries.
Create a concise, actionable summary (2-3 sentences) that highlights:
- What the threat is
- Who it targets
- What actions should be taken

Focus on actionable intelligence for security teams."""

        # Create context from entities
        context_parts = []
        if entities.threat_actors:
            context_parts.append(f"Threat Actors: {', '.join(entities.threat_actors[:3])}")
        if entities.malware:
            context_parts.append(f"Malware: {', '.join(entities.malware[:3])}")
        if entities.cves:
            context_parts.append(f"CVEs: {', '.join(entities.cves[:5])}")
        if entities.industries:
            context_parts.append(f"Targets: {', '.join(entities.industries[:3])}")

        context = "\n".join(context_parts)

        # Truncate content
        content_snippet = content[:1000] if len(content) > 1000 else content

        user_prompt = f"""Create an actionable summary for this threat intelligence:

Extracted Entities:
{context}

Content Snippet:
{content_snippet}

Provide a 2-3 sentence actionable summary."""

        try:
            response = self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3
            )

            summary = response.content.strip()
            entities.summary = summary
            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Error generating summary"
