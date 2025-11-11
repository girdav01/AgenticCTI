"""
Crawl4ai-based web scraping module for CTI content extraction.
Provides advanced scraping capabilities including JavaScript rendering and multi-page crawling.
"""

import logging
import os
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from parsers.web_scraper import ScrapedContent

logger = logging.getLogger(__name__)


class Crawl4AIScraper:
    """
    Advanced web scraper using Crawl4ai for JavaScript rendering and complex crawling.

    Features:
    - JavaScript rendering support
    - Multi-page crawling
    - Link extraction
    - Schema extraction
    - Screenshot capture
    """

    def __init__(
        self,
        base_url: str = None,
        api_token: str = None,
        timeout: int = 60,
        max_retries: int = 3,
        user_agent: str = "AgenticCTI/1.0 (Security Research Bot)"
    ):
        """
        Initialize Crawl4ai scraper.

        Args:
            base_url: Crawl4ai API base URL (e.g., http://crawl4ai:11235)
            api_token: Optional API token for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            user_agent: User agent string
        """
        self.base_url = base_url or os.getenv("CRAWL4AI_BASE_URL", "http://localhost:11235")
        self.api_token = api_token or os.getenv("CRAWL4AI_API_TOKEN")
        self.timeout = timeout
        self.user_agent = user_agent

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        headers = {"User-Agent": user_agent}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        self.session.headers.update(headers)

        logger.info(f"Crawl4AIScraper initialized with base URL: {self.base_url}")

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc

    def scrape_url(
        self,
        url: str,
        wait_for: Optional[str] = None,
        screenshot: bool = False,
        extract_links: bool = False,
        css_selector: Optional[str] = None,
        word_count_threshold: int = 100
    ) -> Optional[ScrapedContent]:
        """
        Scrape content from a URL using Crawl4ai.

        Args:
            url: URL to scrape
            wait_for: CSS selector to wait for before extracting content
            screenshot: Whether to capture a screenshot
            extract_links: Whether to extract links from the page
            css_selector: CSS selector for content extraction
            word_count_threshold: Minimum word count for valid content

        Returns:
            ScrapedContent object or None if failed

        Raises:
            ValueError: If URL is invalid
        """
        # Validate URL
        if not url or not url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {url}")

        logger.info(f"Scraping URL with Crawl4ai: {url}")

        try:
            # Prepare crawl request
            crawl_request = {
                "urls": [url],
                "priority": 8,
                "crawler_params": {
                    "headless": True,
                    "page_timeout": self.timeout * 1000,  # Convert to milliseconds
                    "verbose": False,
                    "user_agent": self.user_agent
                },
                "extra": {
                    "word_count_threshold": word_count_threshold
                }
            }

            # Add optional parameters
            if wait_for:
                crawl_request["crawler_params"]["wait_for"] = wait_for

            if screenshot:
                crawl_request["extra"]["screenshot"] = True

            if extract_links:
                crawl_request["extra"]["only_text"] = False

            if css_selector:
                crawl_request["css_selector"] = css_selector

            # Call Crawl4ai API
            response = self.session.post(
                f"{self.base_url}/crawl",
                json=crawl_request,
                timeout=self.timeout + 10  # Add buffer to API timeout
            )
            response.raise_for_status()

            # Parse response
            result = response.json()

            if not result.get("success") or not result.get("results"):
                logger.error(f"Crawl4ai failed for {url}: {result.get('error', 'Unknown error')}")
                return None

            # Extract first result
            crawl_result = result["results"][0]

            if not crawl_result.get("success"):
                logger.error(f"Failed to crawl {url}: {crawl_result.get('error', 'Unknown error')}")
                return None

            # Extract content
            markdown_content = crawl_result.get("markdown", "")
            html_content = crawl_result.get("cleaned_html", "")

            # Prefer markdown, fallback to HTML
            content = markdown_content if markdown_content else html_content

            if len(content.split()) < word_count_threshold:
                logger.warning(f"Content too short for {url}: {len(content.split())} words")
                return None

            # Extract metadata
            metadata = crawl_result.get("metadata", {})

            # Extract links if requested
            links = None
            if extract_links:
                links_data = crawl_result.get("links", {})
                links = {
                    "internal": links_data.get("internal", []),
                    "external": links_data.get("external", [])
                }

            return ScrapedContent(
                url=url,
                title=metadata.get("title", "No Title"),
                content=content,
                publish_date=metadata.get("published_date") or metadata.get("modified_date"),
                author=metadata.get("author"),
                tags=metadata.get("keywords", []),
                metadata={
                    "description": metadata.get("description"),
                    "language": metadata.get("language"),
                    "links": links,
                    "screenshot": crawl_result.get("screenshot"),
                    "content_length": len(content),
                    "word_count": len(content.split()),
                    "scraper": "crawl4ai"
                }
            )

        except requests.exceptions.Timeout:
            logger.error(f"Timeout scraping {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}", exc_info=True)
            return None

    def scrape_multiple(
        self,
        urls: List[str],
        **kwargs
    ) -> List[ScrapedContent]:
        """
        Scrape multiple URLs.

        Args:
            urls: List of URLs to scrape
            **kwargs: Additional arguments passed to scrape_url

        Returns:
            List of successfully scraped content
        """
        results = []
        for url in urls:
            try:
                content = self.scrape_url(url, **kwargs)
                if content:
                    results.append(content)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")

        logger.info(f"Successfully scraped {len(results)}/{len(urls)} URLs using Crawl4ai")
        return results

    def health_check(self) -> bool:
        """
        Check if Crawl4ai service is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Crawl4ai health check failed: {e}")
            return False
