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
from ml.threat_classifier import ThreatClassifier, ThreatLevel, AlertSeverity
from yara_rules.yara_generator import YARAGenerator
from notifications.webhook_manager import WebhookManager, WebhookAlert, SlackWebhookFormatter

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

# Initialize threat classifier
threat_classifier = ThreatClassifier()

# Initialize YARA generator
yara_generator = YARAGenerator()

# Initialize webhook manager
webhook_manager = WebhookManager()


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
        entities_dict = {}
        if options.get("extract_entities", True):
            try:
                extracted = entity_extractor.extract_entities(scraped_content.content)
                entities_dict = extracted
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

        # ML-based threat classification if requested
        threat_classification = None
        if options.get("classify_threat", False):
            try:
                classification = threat_classifier.classify(
                    content=scraped_content.content,
                    entities=entities_dict,
                    title=scraped_content.title
                )
                threat_classification = {
                    "threat_type": classification.threat_type.value,
                    "threat_level": classification.threat_level.value,
                    "confidence": classification.confidence,
                    "risk_score": classification.risk_score,
                    "indicators": classification.indicators,
                    "recommendations": classification.recommended_actions
                }
                logger.info(f"Classified threat for job {job_id}: {classification.threat_type.value}")
            except Exception as e:
                logger.warning(f"Threat classification failed for job {job_id}: {e}")

        # Generate YARA rules if requested
        yara_rules = None
        if options.get("generate_yara", False) and entities_dict:
            try:
                rules = yara_generator.generate_from_entities(
                    entities=entities_dict,
                    title=scraped_content.title,
                    description=scraped_content.content[:200],
                    source_url=url
                )
                yara_rules = [r.rule_content for r in rules]
                logger.info(f"Generated {len(yara_rules)} YARA rules for job {job_id}")
            except Exception as e:
                logger.warning(f"YARA generation failed for job {job_id}: {e}")

        # Build result
        result = ScrapeResult(
            url=scraped_content.url,
            title=scraped_content.title,
            content=scraped_content.content[:10000],  # Limit content length
            publish_date=scraped_content.publish_date,
            author=scraped_content.author,
            tags=scraped_content.tags,
            entities=entities,
            metadata={
                **scraped_content.metadata,
                "threat_classification": threat_classification,
                "yara_rules": yara_rules
            }
        )

        # Update job with result
        jobs[job_id]["status"] = JobStatus.COMPLETED
        jobs[job_id]["result"] = result.dict()
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Job {job_id} completed successfully")

        # Send webhook notification if configured
        webhook_url = jobs[job_id].get("webhook_url")
        if webhook_url:
            try:
                # Determine severity based on classification
                severity = AlertSeverity.INFO
                if threat_classification:
                    threat_level_map = {
                        "critical": AlertSeverity.CRITICAL,
                        "high": AlertSeverity.HIGH,
                        "medium": AlertSeverity.MEDIUM,
                        "low": AlertSeverity.LOW,
                        "info": AlertSeverity.INFO
                    }
                    severity = threat_level_map.get(
                        threat_classification.get("threat_level", "info"),
                        AlertSeverity.INFO
                    )

                alert = webhook_manager.create_scrape_alert(
                    url=url,
                    success=True,
                    entity_count=len(entities) if entities else 0
                )
                alert.severity = severity
                if threat_classification:
                    alert.threat_classification = threat_classification

                import requests
                requests.post(webhook_url, json=alert.to_dict(), timeout=10)
                logger.info(f"Sent webhook notification for job {job_id}")
            except Exception as e:
                logger.warning(f"Failed to send webhook for job {job_id}: {e}")

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


# Advanced Features Endpoints

@app.post("/api/v1/classify", tags=["ML Classification"])
async def classify_content(
    content: str = "",
    title: Optional[str] = None,
    entities: Optional[Dict] = None
):
    """
    Classify threat content using ML.

    Returns threat type, severity, risk score, and recommendations.
    """
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content is required"
        )

    try:
        classification = threat_classifier.classify(
            content=content,
            entities=entities or {},
            title=title
        )

        return {
            "success": True,
            "classification": {
                "threat_type": classification.threat_type.value,
                "threat_level": classification.threat_level.value,
                "confidence": classification.confidence,
                "risk_score": classification.risk_score,
                "indicators": classification.indicators,
                "recommendations": classification.recommended_actions,
                "metadata": classification.metadata
            }
        }

    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )


@app.post("/api/v1/yara/generate", tags=["YARA Rules"])
async def generate_yara_rules(
    entities: Dict[str, List[str]],
    title: str = "Generated Rule",
    description: str = "",
    source_url: Optional[str] = None
):
    """
    Generate YARA rules from CTI entities.

    Provide entities dict with keys: hashes, domains, ips, malware, cves, etc.
    """
    if not entities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Entities are required"
        )

    try:
        rules = yara_generator.generate_from_entities(
            entities=entities,
            title=title,
            description=description,
            source_url=source_url
        )

        return {
            "success": True,
            "rules": [
                {
                    "name": rule.name,
                    "type": rule.rule_type.value,
                    "description": rule.description,
                    "rule_content": rule.rule_content,
                    "ioc_count": len(rule.iocs)
                }
                for rule in rules
            ],
            "count": len(rules)
        }

    except Exception as e:
        logger.error(f"YARA generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"YARA generation failed: {str(e)}"
        )


@app.get("/api/v1/yara/stats", tags=["YARA Rules"])
async def get_yara_stats():
    """Get YARA rule generation statistics."""
    stats = yara_generator.get_stats()
    return {
        "success": True,
        "stats": stats
    }


@app.post("/api/v1/webhook/test", tags=["Webhooks"])
async def test_webhook(webhook_url: HttpUrl, alert_type: str = "test"):
    """
    Test a webhook by sending a sample alert.

    Useful for validating webhook endpoints before using them.
    """
    try:
        from notifications.webhook_manager import AlertType, AlertSeverity

        alert = WebhookAlert(
            alert_id="test-" + str(uuid.uuid4()),
            alert_type=AlertType.SCRAPE_COMPLETED,
            severity=AlertSeverity.INFO,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            title="Test Alert",
            description="This is a test alert from AgenticCTI API",
            metadata={"test": True}
        )

        import requests
        response = requests.post(
            str(webhook_url),
            json=alert.to_dict(),
            timeout=10
        )
        response.raise_for_status()

        return {
            "success": True,
            "status_code": response.status_code,
            "message": "Webhook test successful"
        }

    except Exception as e:
        logger.error(f"Webhook test error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


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
