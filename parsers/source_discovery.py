"""
CTI source discovery module.
Autonomously discovers and validates new CTI sources.
"""

import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
import yaml
from pathlib import Path

from llm import LLMFactory, LLMMessage, BaseLLM

logger = logging.getLogger(__name__)


@dataclass
class CTISource:
    """Represents a CTI source."""
    name: str
    url: str
    type: str  # 'rss', 'web', 'api'
    category: str  # 'government', 'news', 'blog', 'database'
    priority: str  # 'high', 'medium', 'low'
    enabled: bool = True
    confidence_score: float = 0.0


class SourceDiscovery:
    """Discovers and validates CTI sources autonomously."""

    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        sources_config_path: str = "./config/cti_sources.yaml"
    ):
        """
        Initialize source discovery.

        Args:
            llm: LLM instance for analysis (creates default if None)
            sources_config_path: Path to sources configuration file
        """
        self.llm = llm or LLMFactory.get_default_llm()
        self.sources_config_path = Path(sources_config_path)
        self.known_sources: List[CTISource] = []
        self.discovered_sources: List[CTISource] = []

        # Load existing sources
        self._load_sources()

        logger.info(f"SourceDiscovery initialized with {len(self.known_sources)} known sources")

    def _load_sources(self) -> None:
        """Load sources from configuration file."""
        try:
            if self.sources_config_path.exists():
                with open(self.sources_config_path, 'r') as f:
                    config = yaml.safe_load(f)

                sources_data = config.get('sources', [])
                for source_data in sources_data:
                    source = CTISource(**source_data)
                    self.known_sources.append(source)

                logger.info(f"Loaded {len(self.known_sources)} sources from config")
            else:
                logger.warning(f"Sources config not found: {self.sources_config_path}")

        except Exception as e:
            logger.error(f"Error loading sources config: {e}")

    def get_enabled_sources(self) -> List[CTISource]:
        """
        Get list of enabled sources.

        Returns:
            List of enabled CTISource objects
        """
        return [s for s in self.known_sources if s.enabled]

    def discover_sources(
        self,
        keywords: List[str],
        max_sources: int = 5
    ) -> List[CTISource]:
        """
        Discover new CTI sources using LLM.

        Args:
            keywords: Keywords to guide discovery
            max_sources: Maximum sources to discover

        Returns:
            List of discovered CTISource objects
        """
        logger.info(f"Discovering new sources with keywords: {keywords}")

        system_prompt = """You are a cybersecurity intelligence expert. Your task is to identify
reliable and authoritative sources for cyber threat intelligence (CTI).

Focus on:
- Government agencies (CISA, CERT, NCSC, etc.)
- Security vendors and researchers
- Industry news sites
- Open-source threat intelligence platforms
- Security blogs from recognized experts

Provide sources that are:
1. Regularly updated
2. Authoritative and credible
3. Focused on actionable threat intelligence
4. Publicly accessible

For each source, provide: name, URL, type (rss/web/api), category, and a brief description."""

        user_prompt = f"""Suggest {max_sources} high-quality CTI sources related to these topics:
{', '.join(keywords)}

Known sources to avoid duplicating:
{', '.join([s.name for s in self.known_sources])}

Provide your response in this format for each source:
NAME: [Source Name]
URL: [Full URL]
TYPE: [rss/web/api]
CATEGORY: [government/news/blog/vendor/database]
DESCRIPTION: [Brief description]
---"""

        try:
            response = self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            if not self.llm.validate_response(response):
                logger.error("Invalid LLM response for source discovery")
                return []

            # Parse response
            discovered = self._parse_discovery_response(response.content)
            self.discovered_sources.extend(discovered)

            logger.info(f"Discovered {len(discovered)} new sources")
            return discovered

        except Exception as e:
            logger.error(f"Error in source discovery: {e}")
            return []

    def _parse_discovery_response(self, response: str) -> List[CTISource]:
        """Parse LLM response to extract sources."""
        sources = []

        # Split by separator
        source_blocks = response.split('---')

        for block in source_blocks:
            try:
                lines = [l.strip() for l in block.strip().split('\n') if l.strip()]

                name = None
                url = None
                source_type = 'web'
                category = 'news'

                for line in lines:
                    if line.startswith('NAME:'):
                        name = line.replace('NAME:', '').strip()
                    elif line.startswith('URL:'):
                        url = line.replace('URL:', '').strip()
                    elif line.startswith('TYPE:'):
                        source_type = line.replace('TYPE:', '').strip().lower()
                    elif line.startswith('CATEGORY:'):
                        category = line.replace('CATEGORY:', '').strip().lower()

                if name and url:
                    # Validate URL format
                    if url.startswith(('http://', 'https://')):
                        source = CTISource(
                            name=name,
                            url=url,
                            type=source_type,
                            category=category,
                            priority='medium',
                            enabled=False,  # Require manual verification
                            confidence_score=0.5
                        )
                        sources.append(source)
                        logger.debug(f"Parsed source: {name} - {url}")

            except Exception as e:
                logger.warning(f"Error parsing source block: {e}")
                continue

        return sources

    def validate_source(self, source: CTISource) -> bool:
        """
        Validate a CTI source using LLM.

        Args:
            source: Source to validate

        Returns:
            True if valid, False otherwise
        """
        logger.info(f"Validating source: {source.name}")

        system_prompt = """You are a cybersecurity expert validating threat intelligence sources.
Assess whether the given source is reliable, authoritative, and suitable for CTI gathering.

Consider:
1. Domain reputation and authority
2. Content relevance to cybersecurity
3. Update frequency
4. Source credibility

Respond with: VALID or INVALID, followed by a confidence score (0-100) and brief reasoning."""

        user_prompt = f"""Validate this CTI source:
Name: {source.name}
URL: {source.url}
Type: {source.type}
Category: {source.category}

Is this a reliable and appropriate CTI source?"""

        try:
            response = self.llm.generate_with_system(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            content = response.content.upper()

            if 'VALID' in content and 'INVALID' not in content:
                # Extract confidence score
                import re
                score_match = re.search(r'(\d+)%?', content)
                if score_match:
                    source.confidence_score = int(score_match.group(1)) / 100.0

                logger.info(f"Source validated: {source.name} (confidence: {source.confidence_score:.2f})")
                return True
            else:
                logger.info(f"Source rejected: {source.name}")
                return False

        except Exception as e:
            logger.error(f"Error validating source {source.name}: {e}")
            return False

    def add_source(self, source: CTISource, save: bool = True) -> bool:
        """
        Add a new source to the known sources.

        Args:
            source: Source to add
            save: Whether to save to config file

        Returns:
            True if added, False otherwise
        """
        # Check for duplicates
        for existing in self.known_sources:
            if existing.url == source.url:
                logger.warning(f"Source already exists: {source.url}")
                return False

        self.known_sources.append(source)
        logger.info(f"Added new source: {source.name}")

        if save:
            self.save_sources()

        return True

    def save_sources(self) -> bool:
        """
        Save sources to configuration file.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert sources to dict
            sources_data = []
            for source in self.known_sources:
                sources_data.append({
                    'name': source.name,
                    'url': source.url,
                    'type': source.type,
                    'category': source.category,
                    'priority': source.priority,
                    'enabled': source.enabled
                })

            config = {
                'sources': sources_data,
                'discovery': {
                    'enabled': True,
                    'search_engines': ['google'],
                    'max_new_sources': 5,
                    'verification_required': True,
                    'blacklist': ['*.ads.*', '*.marketing.*', '*.promo.*']
                }
            }

            # Ensure directory exists
            self.sources_config_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(self.sources_config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Saved {len(self.known_sources)} sources to {self.sources_config_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving sources: {e}")
            return False

    def get_source_statistics(self) -> Dict:
        """
        Get statistics about known sources.

        Returns:
            Dictionary with source statistics
        """
        total = len(self.known_sources)
        enabled = len([s for s in self.known_sources if s.enabled])
        by_category = {}
        by_priority = {}

        for source in self.known_sources:
            by_category[source.category] = by_category.get(source.category, 0) + 1
            by_priority[source.priority] = by_priority.get(source.priority, 0) + 1

        return {
            'total_sources': total,
            'enabled_sources': enabled,
            'disabled_sources': total - enabled,
            'by_category': by_category,
            'by_priority': by_priority,
            'discovered_sources': len(self.discovered_sources)
        }
