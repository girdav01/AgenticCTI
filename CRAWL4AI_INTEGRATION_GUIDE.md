# Crawl4ai Integration Plan for AgenticCTI

## Executive Summary

AgenticCTI is a mature, production-ready autonomous CTI platform with solid architecture built on BeautifulSoup4 for web scraping. The codebase is well-modularized with clear separation of concerns. **Crawl4ai integration would be most beneficial as a drop-in replacement for the WebScraper component, combined with a new REST API layer for URL submission.**

## Current State Assessment

### What's Working Well
- Modular architecture with clean separation (scraping, extraction, storage, export)
- Robust LLM integration (Ollama, OpenAI, Anthropic) for semantic entity extraction
- Comprehensive entity extraction (CVEs, IOCs, TTPs, threat actors, malware, campaigns)
- STIX 2.1 export with TLP markings
- Docker-based deployment ready
- Streamlit UI for visualization and manual control
- Email notifications with beautiful HTML templates
- Timezone-aware scheduling

### Current Limitations That Crawl4ai Addresses
1. **Static Content Only:** Can't render JavaScript or handle dynamic content
2. **Single URL Processing:** Scrapes only the main page of each source, misses article links
3. **No URL API:** External applications can't submit URLs for processing
4. **No Async Processing:** All operations are synchronous, blocking
5. **Limited to Config:** Only predefined sources in YAML, no dynamic source addition
6. **No Link Discovery:** Can't automatically discover and crawl article links from index pages

## Recommended Integration Approach

### Phase 1: REST API + Basic Crawl4ai Integration (Week 1-2)

**Goal:** Add REST API and swap BeautifulSoup with Crawl4ai

**Changes Required:**

1. **Create `api/` directory with FastAPI service**
   ```python
   # api/main.py
   from fastapi import FastAPI, BackgroundTasks
   from pydantic import BaseModel
   import asyncio
   
   app = FastAPI()
   
   class URLSubmission(BaseModel):
       url: str
       recursive: bool = False
       max_depth: int = 1
   
   @app.post("/api/v1/urls/submit")
   async def submit_url(submission: URLSubmission, background_tasks: BackgroundTasks):
       """Submit URL for crawling and entity extraction"""
       job_id = uuid.uuid4()
       background_tasks.add_task(process_url_task, job_id, submission)
       return {"job_id": str(job_id), "status": "queued"}
   
   @app.get("/api/v1/jobs/{job_id}")
   async def get_job_status(job_id: str):
       """Check job status and results"""
       # Implementation
       pass
   ```

2. **Create `parsers/crawl4ai_scraper.py`**
   ```python
   # Replace WebScraper with Crawl4ai
   from crawl4ai import AsyncWebCrawler
   from typing import Optional, List
   
   class Crawl4aiScraper:
       def __init__(self, api_endpoint: str = "http://localhost:8000"):
           self.api_endpoint = api_endpoint
           self.crawler = AsyncWebCrawler()
       
       async def scrape_url(self, url: str) -> ScrapedContent:
           """Scrape using Crawl4ai"""
           result = await self.crawler.arun(url)
           # Map Crawl4ai output to ScrapedContent
           return self._parse_result(result)
       
       async def scrape_with_links(self, url: str) -> List[ScrapedContent]:
           """Scrape URL and extract article links"""
           # Implementation
           pass
   ```

3. **Update `agents/cti_agent.py`**
   ```python
   # Add async support
   async def run_async(...):
       # Use await for async operations
       pass
   
   # Or keep sync wrapper around async calls
   ```

4. **Docker Compose Updates**
   ```yaml
   services:
     # ... existing services ...
     
     crawl4ai:
       image: crawl4ai/crawl4ai:latest
       ports:
         - "8000:8000"
       networks:
         - agentic-cti-network
     
     api:
       build:
         context: .
         dockerfile: api.Dockerfile
       ports:
         - "8000:8000"  # Change to 8003
       environment:
         - CRAWL4AI_API=http://crawl4ai:8000
         - CTI_AGENT_PATH=/app
       depends_on:
         - crawl4ai
         - agentic-cti
       networks:
         - agentic-cti-network
   ```

5. **Configuration Updates**
   ```bash
   # .env additions
   CRAWL4AI_API_ENDPOINT=http://localhost:8000
   CRAWL4AI_ENABLED=true
   CRAWL4AI_TIMEOUT=30
   CRAWL4AI_JAVASCRIPT_ENABLED=true
   REST_API_ENABLED=true
   REST_API_PORT=8003
   REST_API_HOST=0.0.0.0
   ```

**Time Estimate:** 3-5 days
**Complexity:** Medium
**Risk:** Low (changes isolated to parsers/ and new api/ directory)

### Phase 2: Advanced Features (Week 3-4)

**Goal:** Full async processing, link discovery, webhooks

**Features:**
1. Link discovery and recursive crawling
2. Job queue with status persistence (Redis)
3. Webhook callbacks on completion
4. Batch URL submission
5. Rate limiting per domain

**Changes:**
- Add Redis service to docker-compose.yml
- Implement Celery or asyncio-based job queue
- Add webhook callback mechanism
- Implement link extraction patterns

**Time Estimate:** 1-2 weeks
**Complexity:** High
**Risk:** Medium (introduces distributed processing)

### Phase 3: Optimization (Week 5+)

**Goal:** Production hardening, monitoring, performance

**Features:**
1. Database layer (PostgreSQL) for job persistence
2. Advanced caching
3. Distributed crawling across workers
4. Prometheus metrics
5. Job retry logic
6. Rate limiting per API key

**Time Estimate:** Ongoing
**Complexity:** High
**Risk:** Medium

## Integration Details

### Key Files to Modify

1. **`parsers/web_scraper.py` (296 lines)**
   - Current: BeautifulSoup + requests
   - Future: Wrap Crawl4ai API calls
   - Create abstraction: `BaseScraper` interface
   - Implementations: `BeautifulSoupScraper` (legacy), `Crawl4aiScraper` (new)

2. **`agents/cti_agent.py` (411 lines)**
   - Add async support
   - Modify `_scrape_sources()` to accept scraper type
   - Add queue-based processing for async jobs
   - Keep backward compatibility with sync interface

3. **`main.py` (277 lines)**
   - Add API service startup
   - Add async event loop support
   - Support both CLI and API modes

4. **`docker-compose.yml` (143 lines)**
   - Add Crawl4ai service
   - Add API service
   - Optional: Add Redis for job queue
   - Optional: Add PostgreSQL for persistence

### New Files to Create

1. **`api/main.py` (100-150 lines)**
   - FastAPI application
   - URL submission endpoints
   - Job status endpoints
   - Health check

2. **`api/models.py` (50-100 lines)**
   - Pydantic models for request/response
   - Job schema
   - URL submission schema

3. **`api/tasks.py` (100-150 lines)**
   - Background task handlers
   - URL processing logic
   - Webhook integration

4. **`parsers/base_scraper.py` (50-100 lines)**
   - Abstract scraper interface
   - Common methods

5. **`parsers/crawl4ai_scraper.py` (150-250 lines)**
   - Crawl4ai implementation
   - Link extraction
   - Async support

6. **`api.Dockerfile`**
   - FastAPI container
   - Python 3.11
   - Port 8003

### Data Flow Changes

**Current (Synchronous):**
```
CLI/Scheduler → CTIAgent.run() 
             → WebScraper.scrape_url() (blocking)
             → EntityExtractor.extract_entities() (blocking)
             → Storage → Done
```

**After Phase 1 (REST API + Crawl4ai):**
```
REST API request → Queue (simple asyncio)
                 → Background task
                 → Crawl4ai API (async)
                 → EntityExtractor (async)
                 → Storage
                 → Response with job_id

User can poll: GET /api/v1/jobs/{job_id}
```

**After Phase 2 (Full Async):**
```
REST API request → Redis queue (Celery)
                 → Worker pool
                 → Crawl4ai API (async)
                 → EntityExtractor (async/batch)
                 → Database storage
                 → Webhook callback
                 → Email notification
```

## Testing Strategy

### Phase 1 Test Plan
1. Unit tests for Crawl4aiScraper
2. Integration tests for REST API endpoints
3. Backward compatibility tests with existing code
4. Docker Compose startup tests
5. Load testing (5-10 concurrent requests)

### Example Test Cases
```python
# test_crawl4ai_scraper.py
@pytest.mark.asyncio
async def test_scrape_url():
    scraper = Crawl4aiScraper()
    result = await scraper.scrape_url("https://example.com")
    assert result.title
    assert result.content
    assert result.url == "https://example.com"

# test_api.py
def test_submit_url():
    response = client.post("/api/v1/urls/submit", 
                          json={"url": "https://example.com"})
    assert response.status_code == 202
    assert "job_id" in response.json()

def test_get_job_status():
    # First submit
    submit_resp = client.post("/api/v1/urls/submit", 
                             json={"url": "https://example.com"})
    job_id = submit_resp.json()["job_id"]
    
    # Then check status
    status_resp = client.get(f"/api/v1/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert "status" in status_resp.json()
```

## Risk Mitigation

### Identified Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Breaking changes to WebScraper | High | Create adapter pattern, keep BS4 option |
| Crawl4ai API stability | Medium | Fallback to BS4, health checks |
| Async complexity | High | Start with simple asyncio, add Celery later |
| Performance degradation | Medium | Caching, connection pooling, monitoring |
| Job persistence on crash | Medium | Add simple SQLite initially, PostgreSQL later |

### Rollback Plan
1. Keep original WebScraper unchanged
2. Make scraper type configurable (env var)
3. Have quick fallback: `SCRAPER_TYPE=beautifulsoup` in .env
4. Version API endpoints: `/api/v1/` so v2 can coexist

## Configuration Examples

### Minimal Setup (Phase 1)
```bash
# .env
CRAWL4AI_ENABLED=true
CRAWL4AI_API_ENDPOINT=http://localhost:8000
REST_API_ENABLED=true
REST_API_PORT=8003
SCRAPER_TYPE=crawl4ai  # or 'beautifulsoup' for fallback
```

### Production Setup (Phase 3)
```bash
# .env
CRAWL4AI_ENABLED=true
CRAWL4AI_API_ENDPOINT=http://crawl4ai:8000
REST_API_ENABLED=true
REST_API_PORT=8003
REST_API_AUTH_ENABLED=true
REST_API_API_KEY_REQUIRED=true

# Job queue
QUEUE_TYPE=celery  # or 'asyncio'
REDIS_URL=redis://redis:6379
REDIS_DB=0

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/agentic_cti
DATABASE_MIGRATIONS=true

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

## API Specification (Phase 1)

### POST /api/v1/urls/submit
Submit a URL for crawling and processing

**Request:**
```json
{
  "url": "https://example.com/article",
  "recursive": false,
  "webhook_url": "https://myapp.com/webhook"
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2024-11-11T20:00:00Z",
  "estimated_completion": 30
}
```

### GET /api/v1/jobs/{job_id}
Get job status and results

**Response (200 OK - Processing):**
```json
{
  "job_id": "550e8400...",
  "status": "processing",
  "progress": 50,
  "message": "Crawling page..."
}
```

**Response (200 OK - Completed):**
```json
{
  "job_id": "550e8400...",
  "status": "completed",
  "result": {
    "url": "https://example.com/article",
    "title": "Article Title",
    "content": "...",
    "entities": {
      "cves": ["CVE-2024-1234"],
      "threat_actors": ["APT28"],
      "malware": ["Fancy Bear"],
      "iocs": {...}
    }
  }
}
```

### GET /api/v1/status
System health and statistics

**Response:**
```json
{
  "status": "healthy",
  "crawler": "crawl4ai",
  "llm_provider": "ollama",
  "queue_size": 5,
  "active_jobs": 2,
  "completed_jobs": 143,
  "uptime_seconds": 86400
}
```

## Success Metrics

### Phase 1 Success Criteria
- REST API responds to URL submissions
- Crawl4ai successfully processes URLs
- Entity extraction works with Crawl4ai output
- Backward compatibility maintained
- <3 minutes latency for single URL (end-to-end)
- 0 breaking changes to existing functionality

### Phase 2 Success Criteria
- 10+ concurrent jobs without degradation
- Webhook callbacks work reliably
- Job status persistence across restarts
- Link discovery works and finds 80%+ of article links
- Batch URL submission processes 100+ URLs

### Phase 3 Success Criteria
- Distributed crawling across multiple workers
- Sub-second metric querying via Prometheus
- 99.9% job success rate with auto-retry
- Database persistence with zero data loss
- Rate limiting enforced per API key

## Effort Estimation Summary

| Phase | Duration | Team Size | Complexity |
|-------|----------|-----------|-----------|
| 1: REST API + Crawl4ai | 1-2 weeks | 1-2 devs | Medium |
| 2: Advanced Features | 1-2 weeks | 2 devs | High |
| 3: Optimization | 2-4 weeks | 2-3 devs | High |
| **Total** | **4-8 weeks** | **2-3 devs** | **Medium-High** |

## Recommendation

**Start with Phase 1 (REST API + Crawl4ai integration).** This provides immediate value:
- External applications can submit URLs
- Better content extraction via Crawl4ai
- Non-blocking API with background processing
- Minimal risk to existing functionality

Phase 2 and 3 can be added based on production feedback and usage patterns.

## Next Steps

1. Review this integration plan with team
2. Set up development branch
3. Create minimal Phase 1 implementation
4. Deploy to staging environment
5. Load test and validate
6. Plan Phase 2 based on learnings
