"""
Autonomous CTI Agent.
Orchestrates the entire CTI workflow: discovery, scraping, analysis, export, and notification.
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
from pathlib import Path

from llm import BaseLLM, LLMFactory
from parsers import WebScraper, SourceDiscovery, EntityExtractor, CTISource, ScrapedContent, CTIEntities

logger = logging.getLogger(__name__)


@dataclass
class AgentRunResult:
    """Result of an agent run."""
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    sources_discovered: int = 0
    articles_scraped: int = 0
    entities_extracted: int = 0
    stix_objects_created: int = 0
    reports_generated: int = 0
    notifications_sent: int = 0
    errors: List[str] = None
    success: bool = False

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CTIAgent:
    """Autonomous Cyber Threat Intelligence Agent."""

    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize CTI Agent.

        Args:
            llm: LLM instance (creates default if None)
            config: Configuration dictionary
        """
        self.llm = llm or LLMFactory.get_default_llm()
        self.config = config or {}

        # Initialize components
        self.scraper = WebScraper(
            user_agent=self.config.get('user_agent', 'AgenticCTI/1.0'),
            timeout=self.config.get('timeout', 30),
            max_retries=self.config.get('max_retries', 3),
            rate_limit=self.config.get('rate_limit', 0.5)
        )

        self.source_discovery = SourceDiscovery(
            llm=self.llm,
            sources_config_path=self.config.get('sources_config_path', './config/cti_sources.yaml')
        )

        self.entity_extractor = EntityExtractor(llm=self.llm)

        # State
        self.current_run: Optional[AgentRunResult] = None
        self.last_run_time: Optional[datetime] = None
        self.collected_intelligence: List[Dict] = []

        logger.info("CTIAgent initialized")

    def run(
        self,
        discover_new_sources: bool = True,
        max_sources: int = 20,
        max_articles_per_source: int = 10
    ) -> AgentRunResult:
        """
        Execute a complete CTI collection and analysis run.

        Args:
            discover_new_sources: Whether to discover new sources
            max_sources: Maximum sources to process
            max_articles_per_source: Maximum articles per source

        Returns:
            AgentRunResult with run statistics
        """
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Starting CTI agent run: {run_id}")

        self.current_run = AgentRunResult(
            run_id=run_id,
            start_time=datetime.now()
        )

        try:
            # Step 1: Source Discovery (if enabled)
            if discover_new_sources:
                self._discover_sources()

            # Step 2: Get active sources
            sources = self.source_discovery.get_enabled_sources()[:max_sources]
            logger.info(f"Processing {len(sources)} CTI sources")

            # Step 3: Scrape content from sources
            all_scraped = self._scrape_sources(sources, max_articles_per_source)

            # Step 4: Extract entities from scraped content
            all_entities = self._extract_entities(all_scraped)

            # Step 5: Store collected intelligence
            self._store_intelligence(all_scraped, all_entities)

            # Mark run as successful
            self.current_run.success = True
            self.current_run.end_time = datetime.now()
            self.last_run_time = self.current_run.end_time

            duration = (self.current_run.end_time - self.current_run.start_time).total_seconds()
            logger.info(f"CTI agent run completed successfully in {duration:.2f}s")
            logger.info(f"Scraped: {self.current_run.articles_scraped} articles, "
                       f"Extracted: {self.current_run.entities_extracted} entity sets")

            return self.current_run

        except Exception as e:
            logger.error(f"Error in agent run: {e}", exc_info=True)
            self.current_run.errors.append(str(e))
            self.current_run.success = False
            self.current_run.end_time = datetime.now()
            return self.current_run

    def _discover_sources(self) -> None:
        """Discover new CTI sources."""
        logger.info("Discovering new CTI sources...")

        try:
            keywords = self.config.get('discovery_keywords', [
                'cyber threat intelligence',
                'cybersecurity news',
                'vulnerability reports'
            ])

            discovered = self.source_discovery.discover_sources(
                keywords=keywords,
                max_sources=5
            )

            # Validate discovered sources
            for source in discovered:
                if self.source_discovery.validate_source(source):
                    self.source_discovery.add_source(source, save=False)
                    self.current_run.sources_discovered += 1

            # Save updated sources
            if self.current_run.sources_discovered > 0:
                self.source_discovery.save_sources()
                logger.info(f"Discovered and validated {self.current_run.sources_discovered} new sources")

        except Exception as e:
            logger.error(f"Error in source discovery: {e}")
            self.current_run.errors.append(f"Source discovery error: {e}")

    def _scrape_sources(
        self,
        sources: List[CTISource],
        max_articles_per_source: int
    ) -> List[ScrapedContent]:
        """
        Scrape content from CTI sources.

        Args:
            sources: List of sources to scrape
            max_articles_per_source: Maximum articles per source

        Returns:
            List of scraped content
        """
        logger.info(f"Scraping {len(sources)} sources...")

        all_scraped = []

        for source in sources:
            try:
                logger.info(f"Scraping source: {source.name}")

                # For now, scrape the main page
                # In production, would parse RSS feeds, paginate, etc.
                content = self.scraper.scrape_url(source.url)

                if content:
                    all_scraped.append(content)
                    self.current_run.articles_scraped += 1

                    # In a real implementation, would discover and scrape article links
                    # For demo purposes, limiting to main page

            except Exception as e:
                logger.error(f"Error scraping {source.name}: {e}")
                self.current_run.errors.append(f"Scraping error ({source.name}): {e}")

        logger.info(f"Successfully scraped {len(all_scraped)} articles")
        return all_scraped

    def _extract_entities(
        self,
        scraped_content: List[ScrapedContent]
    ) -> List[CTIEntities]:
        """
        Extract entities from scraped content.

        Args:
            scraped_content: List of scraped content

        Returns:
            List of extracted entities
        """
        logger.info(f"Extracting entities from {len(scraped_content)} articles...")

        all_entities = []

        for content in scraped_content:
            try:
                logger.info(f"Extracting entities from: {content.title}")

                entities = self.entity_extractor.extract_entities(
                    text=content.content,
                    title=content.title
                )

                # Generate summary if not present
                if not entities.summary:
                    entities.summary = self.entity_extractor.generate_summary(
                        entities=entities,
                        content=content.content
                    )

                all_entities.append(entities)
                self.current_run.entities_extracted += 1

            except Exception as e:
                logger.error(f"Error extracting entities from {content.url}: {e}")
                self.current_run.errors.append(f"Entity extraction error ({content.url}): {e}")

        logger.info(f"Successfully extracted entities from {len(all_entities)} articles")
        return all_entities

    def _store_intelligence(
        self,
        scraped_content: List[ScrapedContent],
        entities: List[CTIEntities]
    ) -> None:
        """
        Store collected intelligence.

        Args:
            scraped_content: Scraped content
            entities: Extracted entities
        """
        logger.info("Storing collected intelligence...")

        try:
            # Combine content and entities
            for content, entity_set in zip(scraped_content, entities):
                intelligence_item = {
                    'timestamp': datetime.now().isoformat(),
                    'url': content.url,
                    'title': content.title,
                    'publish_date': content.publish_date,
                    'author': content.author,
                    'entities': {
                        'ttps': entity_set.ttps,
                        'cves': entity_set.cves,
                        'iocs': entity_set.iocs,
                        'threat_actors': entity_set.threat_actors,
                        'malware': entity_set.malware,
                        'campaigns': entity_set.campaigns,
                        'industries': entity_set.industries,
                        'countries': entity_set.countries,
                    },
                    'summary': entity_set.summary,
                    'severity': entity_set.severity,
                    'confidence': entity_set.confidence
                }

                self.collected_intelligence.append(intelligence_item)

            # Save to file
            self._save_intelligence()

        except Exception as e:
            logger.error(f"Error storing intelligence: {e}")
            self.current_run.errors.append(f"Storage error: {e}")

    def _save_intelligence(self) -> None:
        """Save collected intelligence to JSON file."""
        try:
            data_dir = Path('./data')
            data_dir.mkdir(exist_ok=True)

            filename = f"cti_intelligence_{datetime.now().strftime('%Y%m%d')}.json"
            filepath = data_dir / filename

            # Load existing data if file exists
            existing_data = []
            if filepath.exists():
                with open(filepath, 'r') as f:
                    existing_data = json.load(f)

            # Append new intelligence
            existing_data.extend(self.collected_intelligence)

            # Save
            with open(filepath, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)

            logger.info(f"Saved intelligence to {filepath}")

        except Exception as e:
            logger.error(f"Error saving intelligence file: {e}")

    def get_daily_summary(self) -> Dict[str, Any]:
        """
        Generate daily summary of collected intelligence.

        Returns:
            Dictionary with summary statistics and highlights
        """
        logger.info("Generating daily summary...")

        summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_articles': len(self.collected_intelligence),
            'total_cves': 0,
            'total_threat_actors': 0,
            'total_malware': 0,
            'critical_findings': [],
            'top_industries_targeted': {},
            'severity_distribution': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        }

        # Aggregate statistics
        all_cves = set()
        all_threat_actors = set()
        all_malware = set()
        all_industries = []

        for item in self.collected_intelligence:
            entities = item.get('entities', {})

            # Collect unique items
            all_cves.update(entities.get('cves', []))
            all_threat_actors.update(entities.get('threat_actors', []))
            all_malware.update(entities.get('malware', []))
            all_industries.extend(entities.get('industries', []))

            # Count severity
            severity = item.get('severity', 'medium')
            if severity in summary['severity_distribution']:
                summary['severity_distribution'][severity] += 1

            # Collect critical findings
            if severity in ['critical', 'high']:
                summary['critical_findings'].append({
                    'title': item.get('title'),
                    'url': item.get('url'),
                    'severity': severity,
                    'summary': item.get('summary', '')
                })

        summary['total_cves'] = len(all_cves)
        summary['total_threat_actors'] = len(all_threat_actors)
        summary['total_malware'] = len(all_malware)

        # Top industries
        from collections import Counter
        industry_counts = Counter(all_industries)
        summary['top_industries_targeted'] = dict(industry_counts.most_common(5))

        # Limit critical findings
        summary['critical_findings'] = summary['critical_findings'][:10]

        return summary

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.

        Returns:
            Dictionary with agent status
        """
        return {
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'current_run': asdict(self.current_run) if self.current_run else None,
            'total_intelligence_items': len(self.collected_intelligence),
            'source_statistics': self.source_discovery.get_source_statistics()
        }

    def clear_intelligence(self) -> None:
        """Clear collected intelligence (for new day)."""
        self.collected_intelligence = []
        logger.info("Cleared collected intelligence")
