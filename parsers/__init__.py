"""
Parsers module for web scraping, source discovery, and entity extraction.
"""

from .web_scraper import WebScraper, ScrapedContent
from .source_discovery import SourceDiscovery, CTISource
from .entity_extractor import EntityExtractor, CTIEntities

__all__ = [
    "WebScraper",
    "ScrapedContent",
    "SourceDiscovery",
    "CTISource",
    "EntityExtractor",
    "CTIEntities",
]
