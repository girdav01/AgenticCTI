# Crawl4ai + REST API Quick Start Guide

This guide will help you get started with the Crawl4ai integration and REST API for submitting URLs to scrape.

## What's New?

✅ **Crawl4ai Integration** - Advanced web scraping with JavaScript rendering
✅ **REST API** - Submit URLs via HTTP API
✅ **Async Job Processing** - Non-blocking URL scraping
✅ **Entity Extraction** - Automatic CTI entity extraction from scraped content

---

## Prerequisites

- Docker & Docker Compose installed
- 8GB+ RAM recommended
- Ports available: 8000 (API), 11235 (Crawl4ai), 8501-8502 (UI), 11434 (Ollama)

---

## Quick Start (5 minutes)

### Step 1: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit .env and set minimal required values:
# - LLM_PROVIDER=ollama (default, no API key needed)
# - USE_CRAWL4AI=true (optional, for main agent)
```

### Step 2: Start All Services

```bash
# Start all services (API, Crawl4ai, Ollama, UI)
docker-compose up -d

# Check services are healthy
docker-compose ps
```

Expected output:
```
NAME                    STATUS
agentic-cti             Up
agentic-cti-api         Up
agentic-cti-crawl4ai    Up (healthy)
agentic-cti-ollama      Up
agentic-cti-ui          Up
```

### Step 3: Verify API is Running

```bash
# Check API health
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "crawl4ai_available": true,
  "llm_available": true
}
```

### Step 4: Submit Your First URL

```bash
# Submit a URL for scraping
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://thehackernews.com",
    "options": {
      "scraper_type": "auto",
      "extract_entities": true
    }
  }'
```

Response:
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "created_at": "2024-01-15T10:00:00Z",
  "message": "Job created successfully. Use GET /api/v1/jobs/abc-123-def-456 to check status."
}
```

### Step 5: Check Job Status

```bash
# Replace JOB_ID with the job_id from step 4
curl http://localhost:8000/api/v1/jobs/abc-123-def-456
```

When complete, you'll get:
```json
{
  "job_id": "abc-123-def-456",
  "status": "completed",
  "result": {
    "url": "https://thehackernews.com",
    "title": "The Hacker News - Latest News",
    "content": "...",
    "entities": [
      {"type": "cve", "value": "CVE-2024-1234", "confidence": 1.0},
      {"type": "malware", "value": "TrickBot", "confidence": 0.95}
    ]
  }
}
```

---

## Interactive API Documentation

Once the API is running, visit:

**Swagger UI:** http://localhost:8000/docs
**ReDoc:** http://localhost:8000/redoc

These provide interactive API documentation where you can test endpoints directly from your browser.

---

## Common Use Cases

### 1. Scrape with Crawl4ai (JavaScript Support)

```bash
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/dynamic-page",
    "options": {
      "scraper_type": "crawl4ai",
      "wait_for": ".content-loaded",
      "extract_links": true,
      "extract_entities": true
    }
  }'
```

### 2. Batch URL Submission

```bash
curl -X POST "http://localhost:8000/api/v1/scrape/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/article1",
      "https://example.com/article2",
      "https://example.com/article3"
    ],
    "options": {
      "scraper_type": "auto",
      "extract_entities": true
    }
  }'
```

### 3. Python Integration

```python
import requests
import time

def scrape_url(url):
    # Submit job
    response = requests.post(
        "http://localhost:8000/api/v1/scrape",
        json={
            "url": url,
            "options": {
                "scraper_type": "auto",
                "extract_entities": True
            }
        }
    )
    job_id = response.json()["job_id"]

    # Poll for completion
    while True:
        status = requests.get(f"http://localhost:8000/api/v1/jobs/{job_id}")
        data = status.json()

        if data["status"] in ["completed", "failed"]:
            return data

        time.sleep(2)

# Use it
result = scrape_url("https://thehackernews.com/latest")
print(f"Found {len(result['result']['entities'])} entities")
```

---

## Architecture Overview

```
┌─────────────┐
│   Client    │
│  (You)      │
└──────┬──────┘
       │ HTTP POST /api/v1/scrape
       │
       ▼
┌─────────────────────────────────┐
│  AgenticCTI REST API            │
│  (FastAPI on :8000)             │
│  - Job queue management         │
│  - Background processing        │
└──────┬──────────────────────────┘
       │
       ├─────────────────┬──────────────────┐
       │                 │                  │
       ▼                 ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Crawl4ai   │   │   Ollama    │   │ BeautifulSoup│
│  (:11235)   │   │  (:11434)   │   │  (Fallback)  │
│  - JS render│   │  - LLM      │   │  - Basic     │
│  - Advanced │   │  - Entity   │   │  - Fast      │
└─────────────┘   │    Extract  │   └─────────────┘
                  └─────────────┘
```

---

## Service Endpoints

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| REST API | 8000 | http://localhost:8000 | Submit URLs, check jobs |
| API Docs | 8000 | http://localhost:8000/docs | Interactive API docs |
| Crawl4ai | 11235 | http://localhost:11235 | Web scraping engine |
| Ollama | 11434 | http://localhost:11434 | LLM for entity extraction |
| Streamlit UI | 8502 | http://localhost:8502 | Web dashboard |

---

## Scraper Comparison

| Feature | BeautifulSoup | Crawl4ai |
|---------|---------------|----------|
| Speed | ⚡⚡⚡ Fast | ⚡⚡ Medium |
| JavaScript | ❌ No | ✅ Yes |
| Screenshots | ❌ No | ✅ Yes |
| Link Extraction | ⚠️ Basic | ✅ Advanced |
| Dynamic Content | ❌ No | ✅ Yes |
| Resource Usage | 💾 Low | 💾 High |
| Best For | Static pages, RSS feeds | SPAs, dynamic sites |

**Recommendation:** Use `"scraper_type": "auto"` to let the system choose automatically.

---

## Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs agentic-cti-api

# Common issue: Port already in use
# Solution: Change API_PORT in .env
```

### Crawl4ai not available

```bash
# Check Crawl4ai status
curl http://localhost:11235/health

# Check logs
docker-compose logs agentic-cti-crawl4ai

# Restart service
docker-compose restart agentic-cti-crawl4ai
```

### Jobs stuck in "pending"

```bash
# Check API logs for errors
docker-compose logs -f agentic-cti-api

# Jobs are processed in background - wait a few seconds
# For complex pages, Crawl4ai may take 10-30 seconds
```

### Entity extraction not working

```bash
# Ensure Ollama is running
curl http://localhost:11434/api/tags

# Pull the model if needed
docker exec -it agentic-cti-ollama ollama pull llama3.2:latest
```

---

## Performance Tips

### 1. Crawl4ai vs BeautifulSoup

- Use **BeautifulSoup** for static HTML pages (faster, lower resource usage)
- Use **Crawl4ai** for JavaScript-heavy sites (slower, higher quality)
- Use **auto** to let the system decide

### 2. Batch Processing

- Submit multiple URLs in a single batch request
- Reduces API overhead
- URLs are processed in parallel

### 3. Resource Limits

- **Crawl4ai**: Each scrape uses ~200-500MB RAM
- **Ollama**: LLM uses ~2-4GB RAM
- Recommended: 8GB+ total RAM for production

### 4. Rate Limiting

Default limits:
- 100 requests per minute per client
- Configure via `API_RATE_LIMIT` and `API_RATE_LIMIT_PERIOD` in `.env`

---

## Next Steps

1. **Read Full API Documentation:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
2. **Explore Integration Guide:** [CRAWL4AI_INTEGRATION_GUIDE.md](CRAWL4AI_INTEGRATION_GUIDE.md)
3. **Check Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Browse Code:** [CODE_MAP.md](CODE_MAP.md)

---

## Production Deployment

For production use, consider:

1. **Job Storage**: Replace in-memory storage with Redis/PostgreSQL
2. **Authentication**: Add API key or OAuth authentication
3. **Rate Limiting**: Implement stricter rate limits
4. **Monitoring**: Add Prometheus metrics and Grafana dashboards
5. **Scaling**: Use Kubernetes for horizontal scaling
6. **Caching**: Cache frequently accessed content
7. **Webhooks**: Implement webhook callbacks for job completion

See [CRAWL4AI_INTEGRATION_GUIDE.md](CRAWL4AI_INTEGRATION_GUIDE.md) Phase 3 for details.

---

## Support

- **Issues:** https://github.com/girdav01/AgenticCTI/issues
- **Documentation:** http://localhost:8000/docs
- **Main README:** [README.md](README.md)

---

## License

Same as AgenticCTI project license.
