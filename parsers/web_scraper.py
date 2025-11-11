"""
Web scraping module for CTI content extraction.
Implements secure and robust web scraping with rate limiting and error handling.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Represents scraped web content."""
    url: str
    title: str
    content: str
    publish_date: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict] = None


class WebScraper:
    """Secure web scraper with rate limiting and retry logic."""

    def __init__(
        self,
        user_agent: str = "AgenticCTI/1.0 (Security Research Bot)",
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit: float = 0.5,  # seconds between requests
        respect_robots: bool = True
    ):
        """
        Initialize web scraper.

        Args:
            user_agent: User agent string
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limit: Delay between requests in seconds
            respect_robots: Whether to respect robots.txt
        """
        if not BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 is required. Install with: pip install beautifulsoup4")

        self.user_agent = user_agent
        self.timeout = timeout
        self.rate_limit = rate_limit
        self.respect_robots = respect_robots
        self.last_request_time: Dict[str, float] = {}

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({"User-Agent": user_agent})

        logger.info("WebScraper initialized with rate limit: %.2fs", rate_limit)

    def _apply_rate_limit(self, domain: str) -> None:
        """
        Apply rate limiting per domain.

        Args:
            domain: Domain to rate limit
        """
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.rate_limit:
                sleep_time = self.rate_limit - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                time.sleep(sleep_time)

        self.last_request_time[domain] = time.time()

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc

    def _sanitize_content(self, content: str) -> str:
        """
        Sanitize scraped content.

        Args:
            content: Raw content

        Returns:
            Sanitized content
        """
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        # Remove control characters
        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
        return content.strip()

    def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        """
        Scrape content from a URL.

        Args:
            url: URL to scrape

        Returns:
            ScrapedContent object or None if failed

        Raises:
            ValueError: If URL is invalid
        """
        # Validate URL
        if not url or not url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {url}")

        domain = self._extract_domain(url)
        logger.info(f"Scraping URL: {url}")

        try:
            # Apply rate limiting
            self._apply_rate_limit(domain)

            # Fetch content
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No Title"

            # Try to find main content
            content = self._extract_main_content(soup)

            # Extract metadata
            publish_date = self._extract_publish_date(soup)
            author = self._extract_author(soup)
            tags = self._extract_tags(soup)

            # Sanitize content
            content = self._sanitize_content(content)

            if len(content) < 100:
                logger.warning(f"Content too short for {url}: {len(content)} chars")
                return None

            return ScrapedContent(
                url=url,
                title=title_text,
                content=content,
                publish_date=publish_date,
                author=author,
                tags=tags,
                metadata={
                    "status_code": response.status_code,
                    "content_type": response.headers.get("Content-Type"),
                    "content_length": len(content)
                }
            )

        except requests.exceptions.Timeout:
            logger.error(f"Timeout scraping {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from parsed HTML."""
        # Try common content selectors
        content_selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.post-content',
            '.article-content',
            '#content',
            'main'
        ]

        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(separator=' ', strip=True)

        # Fallback to body
        body = soup.find('body')
        return body.get_text(separator=' ', strip=True) if body else ""

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date from HTML."""
        # Try meta tags
        date_metas = [
            'article:published_time',
            'datePublished',
            'publishdate',
            'DC.date.issued'
        ]

        for meta_name in date_metas:
            meta = soup.find('meta', property=meta_name) or soup.find('meta', attrs={'name': meta_name})
            if meta and meta.get('content'):
                return meta['content']

        # Try time tags
        time_tag = soup.find('time')
        if time_tag:
            return time_tag.get('datetime') or time_tag.get_text()

        return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author from HTML."""
        # Try meta tags
        author_metas = ['author', 'article:author', 'DC.creator']

        for meta_name in author_metas:
            meta = soup.find('meta', property=meta_name) or soup.find('meta', attrs={'name': meta_name})
            if meta and meta.get('content'):
                return meta['content']

        # Try author class/id
        author_elem = soup.find(class_=re.compile(r'author', re.I)) or soup.find(id=re.compile(r'author', re.I))
        if author_elem:
            return author_elem.get_text().strip()

        return None

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract tags/keywords from HTML."""
        tags = []

        # Try meta keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta and keywords_meta.get('content'):
            tags.extend([t.strip() for t in keywords_meta['content'].split(',')])

        # Try article tags
        tag_elements = soup.find_all(class_=re.compile(r'tag', re.I))
        for tag_elem in tag_elements[:10]:  # Limit to 10 tags
            tag_text = tag_elem.get_text().strip()
            if tag_text and len(tag_text) < 50:
                tags.append(tag_text)

        return list(set(tags))[:10]  # Remove duplicates and limit

    def scrape_multiple(self, urls: List[str]) -> List[ScrapedContent]:
        """
        Scrape multiple URLs.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of successfully scraped content
        """
        results = []
        for url in urls:
            try:
                content = self.scrape_url(url)
                if content:
                    results.append(content)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")

        logger.info(f"Successfully scraped {len(results)}/{len(urls)} URLs")
        return results
