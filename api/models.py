"""
Pydantic models for API request/response validation.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator


class ScraperType(str, Enum):
    """Available scraper types."""
    BEAUTIFULSOUP = "beautifulsoup"
    CRAWL4AI = "crawl4ai"
    AUTO = "auto"  # Automatically choose best scraper


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapeOptions(BaseModel):
    """Options for scraping configuration."""
    scraper_type: ScraperType = Field(
        default=ScraperType.AUTO,
        description="Scraper to use (auto, beautifulsoup, or crawl4ai)"
    )
    wait_for: Optional[str] = Field(
        default=None,
        description="CSS selector to wait for (Crawl4ai only)"
    )
    screenshot: bool = Field(
        default=False,
        description="Capture screenshot (Crawl4ai only)"
    )
    extract_links: bool = Field(
        default=False,
        description="Extract internal/external links"
    )
    css_selector: Optional[str] = Field(
        default=None,
        description="CSS selector for content extraction"
    )
    extract_entities: bool = Field(
        default=True,
        description="Extract CTI entities from content"
    )
    classify_threat: bool = Field(
        default=False,
        description="Classify threat using ML (adds threat_type, risk_score, etc.)"
    )
    generate_yara: bool = Field(
        default=False,
        description="Generate YARA detection rules from findings"
    )


class ScrapeRequest(BaseModel):
    """Request to scrape a URL."""
    url: HttpUrl = Field(
        ...,
        description="URL to scrape"
    )
    options: Optional[ScrapeOptions] = Field(
        default_factory=ScrapeOptions,
        description="Scraping options"
    )
    webhook_url: Optional[HttpUrl] = Field(
        default=None,
        description="Webhook URL to call when scraping completes"
    )

    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is valid and uses http/https."""
        if not str(v).startswith(('http://', 'https://')):
            raise ValueError("URL must use http or https protocol")
        return v


class BatchScrapeRequest(BaseModel):
    """Request to scrape multiple URLs."""
    urls: List[HttpUrl] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of URLs to scrape (max 100)"
    )
    options: Optional[ScrapeOptions] = Field(
        default_factory=ScrapeOptions,
        description="Scraping options applied to all URLs"
    )
    webhook_url: Optional[HttpUrl] = Field(
        default=None,
        description="Webhook URL to call when all scraping completes"
    )


class EntityData(BaseModel):
    """Extracted entity information."""
    type: str = Field(..., description="Entity type (e.g., CVE, malware, IP)")
    value: str = Field(..., description="Entity value")
    context: Optional[str] = Field(None, description="Surrounding context")
    confidence: Optional[float] = Field(None, description="Extraction confidence")


class ScrapeResult(BaseModel):
    """Result of scraping a URL."""
    url: str = Field(..., description="Scraped URL")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Extracted content")
    publish_date: Optional[str] = Field(None, description="Publication date")
    author: Optional[str] = Field(None, description="Author name")
    tags: Optional[List[str]] = Field(None, description="Page tags/keywords")
    entities: Optional[List[EntityData]] = Field(None, description="Extracted CTI entities")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class JobResponse(BaseModel):
    """Response for submitted job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: str = Field(..., description="Job creation timestamp")
    message: str = Field(..., description="Status message")


class JobStatusResponse(BaseModel):
    """Response for job status query."""
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: str = Field(..., description="Job creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    result: Optional[ScrapeResult] = Field(None, description="Scraping result if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    """API health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    crawl4ai_available: bool = Field(..., description="Crawl4ai service availability")
    llm_available: bool = Field(..., description="LLM service availability")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
