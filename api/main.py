"""
AgenticCTI REST API
FastAPI application for URL submission and scraping.
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import __version__
from api.models import (
    ScrapeRequest,
    BatchScrapeRequest,
    ScrapeResult,
    JobResponse,
    JobStatusResponse,
    JobStatus,
    HealthResponse,
    ErrorResponse,
    EntityData,
    ScraperType
)
from parsers.web_scraper import WebScraper
from parsers.crawl4ai_scraper import Crawl4AIScraper
from parsers.entity_extractor import EntityExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AgenticCTI API",
    description="REST API for submitting URLs for CTI content extraction",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (replace with database in production)
jobs: Dict[str, Dict] = {}

# Initialize scrapers
beautifulsoup_scraper = WebScraper()
crawl4ai_scraper = None
crawl4ai_base_url = os.getenv("CRAWL4AI_BASE_URL", "http://crawl4ai:11235")

try:
    crawl4ai_scraper = Crawl4AIScraper(base_url=crawl4ai_base_url)
    logger.info("Crawl4ai scraper initialized successfully")
except Exception as e:
    logger.warning(f"Crawl4ai scraper initialization failed: {e}")

# Initialize entity extractor
entity_extractor = EntityExtractor()


def get_scraper(scraper_type: ScraperType):
    """Get appropriate scraper based on type."""
    if scraper_type == ScraperType.CRAWL4AI:
        if not crawl4ai_scraper:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Crawl4ai service is not available"
            )
        return crawl4ai_scraper
    elif scraper_type == ScraperType.BEAUTIFULSOUP:
        return beautifulsoup_scraper
    else:  # AUTO
        # Prefer Crawl4ai if available
        if crawl4ai_scraper and crawl4ai_scraper.health_check():
            return crawl4ai_scraper
        return beautifulsoup_scraper


async def process_scrape_job(job_id: str, url: str, options: dict):
    """
    Background task to process scraping job.

    Args:
        job_id: Unique job identifier
        url: URL to scrape
        options: Scraping options
    """
    try:
        logger.info(f"Processing job {job_id} for URL: {url}")

        # Update job status
        jobs[job_id]["status"] = JobStatus.PROCESSING
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()

        # Get scraper
        scraper = get_scraper(options.get("scraper_type", ScraperType.AUTO))

        # Scrape URL
        scrape_kwargs = {}
        if isinstance(scraper, Crawl4AIScraper):
            scrape_kwargs = {
                "wait_for": options.get("wait_for"),
                "screenshot": options.get("screenshot", False),
                "extract_links": options.get("extract_links", False),
                "css_selector": options.get("css_selector")
            }

        scraped_content = scraper.scrape_url(url, **scrape_kwargs)

        if not scraped_content:
            raise Exception("Failed to scrape content from URL")

        # Extract entities if requested
        entities = None
        if options.get("extract_entities", True):
            try:
                extracted = entity_extractor.extract_entities(scraped_content.content)
                entities = [
                    EntityData(
                        type=entity_type,
                        value=value,
                        confidence=1.0 if entity_type != "ttps" else 0.8
                    )
                    for entity_type, values in extracted.items()
                    for value in values
                ]
            except Exception as e:
                logger.warning(f"Entity extraction failed for job {job_id}: {e}")

        # Build result
        result = ScrapeResult(
            url=scraped_content.url,
            title=scraped_content.title,
            content=scraped_content.content[:10000],  # Limit content length
            publish_date=scraped_content.publish_date,
            author=scraped_content.author,
            tags=scraped_content.tags,
            entities=entities,
            metadata=scraped_content.metadata
        )

        # Update job with result
        jobs[job_id]["status"] = JobStatus.COMPLETED
        jobs[job_id]["result"] = result.dict()
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Job {job_id} completed successfully")

        # TODO: Send webhook notification if configured

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "AgenticCTI API",
        "version": __version__,
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    crawl4ai_available = False
    if crawl4ai_scraper:
        crawl4ai_available = crawl4ai_scraper.health_check()

    # Simple LLM check (could be improved)
    llm_available = True  # Assume available for now

    return HealthResponse(
        status="healthy",
        version=__version__,
        crawl4ai_available=crawl4ai_available,
        llm_available=llm_available
    )


@app.post("/api/v1/scrape", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Scraping"])
async def scrape_url(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Submit a URL for scraping.

    Returns a job ID that can be used to check the status and retrieve results.
    """
    # Generate job ID
    job_id = str(uuid.uuid4())

    # Create job
    jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "url": str(request.url),
        "options": request.options.dict() if request.options else {},
        "webhook_url": str(request.webhook_url) if request.webhook_url else None
    }

    # Schedule background task
    background_tasks.add_task(
        process_scrape_job,
        job_id,
        str(request.url),
        jobs[job_id]["options"]
    )

    logger.info(f"Created job {job_id} for URL: {request.url}")

    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        created_at=jobs[job_id]["created_at"],
        message=f"Job created successfully. Use GET /api/v1/jobs/{job_id} to check status."
    )


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
async def get_job_status(job_id: str):
    """Get status and results of a scraping job."""
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    job = jobs[job_id]

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        result=ScrapeResult(**job["result"]) if job.get("result") else None,
        error=job.get("error")
    )


@app.post("/api/v1/scrape/batch", response_model=Dict[str, str], status_code=status.HTTP_202_ACCEPTED, tags=["Scraping"])
async def scrape_batch(request: BatchScrapeRequest, background_tasks: BackgroundTasks):
    """
    Submit multiple URLs for scraping.

    Returns a mapping of URLs to job IDs.
    """
    job_ids = {}

    for url in request.urls:
        # Generate job ID
        job_id = str(uuid.uuid4())

        # Create job
        jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "url": str(url),
            "options": request.options.dict() if request.options else {},
            "webhook_url": str(request.webhook_url) if request.webhook_url else None
        }

        # Schedule background task
        background_tasks.add_task(
            process_scrape_job,
            job_id,
            str(url),
            jobs[job_id]["options"]
        )

        job_ids[str(url)] = job_id

    logger.info(f"Created {len(job_ids)} batch jobs")

    return job_ids


@app.delete("/api/v1/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Jobs"])
async def delete_job(job_id: str):
    """Delete a job and its results."""
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    del jobs[job_id]
    logger.info(f"Deleted job {job_id}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred",
            details={"exception": str(exc)}
        ).dict()
    )


if __name__ == "__main__":
    # Run with uvicorn
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
