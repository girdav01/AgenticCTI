# AgenticCTI REST API Documentation

## Overview

The AgenticCTI REST API provides endpoints for submitting URLs for scraping and CTI entity extraction. It supports both BeautifulSoup (basic) and Crawl4ai (advanced with JavaScript rendering) scrapers.

**Base URL:** `http://localhost:8000`

**API Version:** `1.0.0`

**Documentation:** `http://localhost:8000/docs` (Interactive Swagger UI)

---

## Quick Start

### 1. Start Services

```bash
# Start all services (API, Crawl4ai, Ollama, etc.)
docker-compose up -d

# Check service health
curl http://localhost:8000/health
```

### 2. Submit a URL for Scraping

```bash
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://thehackernews.com/2024/01/critical-vulnerability.html",
    "options": {
      "scraper_type": "auto",
      "extract_entities": true
    }
  }'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "message": "Job created successfully. Use GET /api/v1/jobs/550e8400-e29b-41d4-a716-446655440000 to check status."
}
```

### 3. Check Job Status

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response (Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:15Z",
  "result": {
    "url": "https://thehackernews.com/2024/01/critical-vulnerability.html",
    "title": "Critical Vulnerability Found in...",
    "content": "Security researchers have discovered...",
    "publish_date": "2024-01-15",
    "author": "John Doe",
    "tags": ["cybersecurity", "vulnerability"],
    "entities": [
      {
        "type": "cve",
        "value": "CVE-2024-1234",
        "confidence": 1.0
      },
      {
        "type": "malware",
        "value": "TrickBot",
        "confidence": 0.95
      }
    ],
    "metadata": {
      "scraper": "crawl4ai",
      "word_count": 1500
    }
  }
}
```

---

## API Endpoints

### Health Check

**GET** `/health`

Check API and service health.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "crawl4ai_available": true,
  "llm_available": true
}
```

---

### Submit Single URL

**POST** `/api/v1/scrape`

Submit a URL for scraping and entity extraction.

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "options": {
    "scraper_type": "auto",  // "auto", "beautifulsoup", or "crawl4ai"
    "wait_for": "article.loaded",  // CSS selector to wait for (Crawl4ai only)
    "screenshot": false,  // Capture screenshot (Crawl4ai only)
    "extract_links": false,  // Extract internal/external links
    "css_selector": "article.content",  // CSS selector for content
    "extract_entities": true  // Extract CTI entities
  },
  "webhook_url": "https://your-domain.com/webhook"  // Optional
}
```

**Response:** `202 Accepted`
```json
{
  "job_id": "uuid",
  "status": "pending",
  "created_at": "timestamp",
  "message": "Job created successfully..."
}
```

---

### Submit Batch URLs

**POST** `/api/v1/scrape/batch`

Submit multiple URLs (up to 100) for scraping.

**Request Body:**
```json
{
  "urls": [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
  ],
  "options": {
    "scraper_type": "auto",
    "extract_entities": true
  }
}
```

**Response:** `202 Accepted`
```json
{
  "https://example.com/article1": "job-id-1",
  "https://example.com/article2": "job-id-2",
  "https://example.com/article3": "job-id-3"
}
```

---

### Get Job Status

**GET** `/api/v1/jobs/{job_id}`

Retrieve job status and results.

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed",  // "pending", "processing", "completed", or "failed"
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "result": {
    "url": "...",
    "title": "...",
    "content": "...",
    "entities": [...]
  },
  "error": null  // Error message if status is "failed"
}
```

---

### Delete Job

**DELETE** `/api/v1/jobs/{job_id}`

Delete a job and its results.

**Response:** `204 No Content`

---

## Scraper Options

### Scraper Types

- **`auto`** (default): Automatically chooses best available scraper (prefers Crawl4ai)
- **`beautifulsoup`**: Basic HTML scraper (fast, no JavaScript support)
- **`crawl4ai`**: Advanced scraper with JavaScript rendering, screenshots, etc.

### Crawl4ai-Specific Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `wait_for` | string | null | CSS selector to wait for before scraping |
| `screenshot` | boolean | false | Capture page screenshot |
| `extract_links` | boolean | false | Extract internal/external links |
| `css_selector` | string | null | CSS selector for content extraction |

### Common Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `scraper_type` | string | "auto" | Scraper to use |
| `extract_entities` | boolean | true | Extract CTI entities (CVEs, IPs, etc.) |

---

## Entity Types

The API extracts the following CTI entity types:

| Type | Description | Examples |
|------|-------------|----------|
| `cve` | CVE identifiers | CVE-2024-1234 |
| `ip` | IP addresses | 192.168.1.1, 2001:db8::1 |
| `domain` | Domain names | malicious-site.com |
| `url` | URLs | https://evil.com/payload |
| `hash` | File hashes (MD5, SHA1, SHA256) | d41d8cd98f00b204... |
| `email` | Email addresses | attacker@evil.com |
| `malware` | Malware families | TrickBot, Emotet |
| `threat_actor` | Threat actor groups | APT28, Lazarus |
| `ttp` | Tactics, techniques, procedures | T1566 (Phishing) |
| `industry` | Targeted industries | Healthcare, Finance |
| `country` | Affected countries | United States |
| `severity` | Severity levels | Critical, High |

---

## Code Examples

### Python

```python
import requests
import time

# Submit URL
response = requests.post(
    "http://localhost:8000/api/v1/scrape",
    json={
        "url": "https://thehackernews.com/latest-threat",
        "options": {
            "scraper_type": "crawl4ai",
            "extract_entities": True,
            "screenshot": False
        }
    }
)

job = response.json()
job_id = job["job_id"]

# Poll for results
while True:
    status = requests.get(f"http://localhost:8000/api/v1/jobs/{job_id}")
    data = status.json()

    if data["status"] in ["completed", "failed"]:
        break

    time.sleep(2)

# Get results
if data["status"] == "completed":
    result = data["result"]
    print(f"Title: {result['title']}")
    print(f"Entities: {len(result['entities'])}")
    for entity in result["entities"]:
        print(f"  - {entity['type']}: {entity['value']}")
```

### JavaScript

```javascript
// Submit URL
const response = await fetch('http://localhost:8000/api/v1/scrape', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    url: 'https://thehackernews.com/latest-threat',
    options: {
      scraper_type: 'auto',
      extract_entities: true
    }
  })
});

const job = await response.json();

// Poll for results
const pollJob = async (jobId) => {
  while (true) {
    const status = await fetch(`http://localhost:8000/api/v1/jobs/${jobId}`);
    const data = await status.json();

    if (data.status === 'completed' || data.status === 'failed') {
      return data;
    }

    await new Promise(resolve => setTimeout(resolve, 2000));
  }
};

const result = await pollJob(job.job_id);
console.log('Title:', result.result.title);
console.log('Entities:', result.result.entities);
```

### cURL

```bash
#!/bin/bash

# Submit URL
JOB_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://thehackernews.com/latest-threat",
    "options": {
      "scraper_type": "auto",
      "extract_entities": true
    }
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Poll for completion
while true; do
  STATUS_RESPONSE=$(curl -s "http://localhost:8000/api/v1/jobs/$JOB_ID")
  STATUS=$(echo $STATUS_RESPONSE | jq -r '.status')

  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi

  sleep 2
done

# Display results
echo $STATUS_RESPONSE | jq '.'
```

---

## Batch Processing Example

```python
import requests

# Submit batch of URLs
urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
]

response = requests.post(
    "http://localhost:8000/api/v1/scrape/batch",
    json={
        "urls": urls,
        "options": {
            "scraper_type": "auto",
            "extract_entities": True
        }
    }
)

job_mapping = response.json()

# Track all jobs
results = {}
for url, job_id in job_mapping.items():
    # Poll each job
    while True:
        status = requests.get(f"http://localhost:8000/api/v1/jobs/{job_id}")
        data = status.json()

        if data["status"] in ["completed", "failed"]:
            results[url] = data
            break

        time.sleep(1)

# Process results
for url, job_data in results.items():
    if job_data["status"] == "completed":
        print(f"\n{url}")
        print(f"  Entities: {len(job_data['result']['entities'])}")
```

---

## Environment Variables

Configure the API using these environment variables in `.env`:

```bash
# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
API_RATE_LIMIT=100
API_RATE_LIMIT_PERIOD=60

# Crawl4ai Configuration
CRAWL4AI_BASE_URL=http://crawl4ai:11235
CRAWL4AI_API_TOKEN=  # Optional

# LLM Configuration (for entity extraction)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:latest
LLM_BASE_URL=http://ollama:11434
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": {
    "additional": "context"
  }
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 202 | Accepted | Job created, processing async |
| 400 | Bad Request | Invalid request format |
| 404 | Not Found | Job not found |
| 422 | Validation Error | Invalid parameters |
| 500 | Server Error | Internal server error |
| 503 | Service Unavailable | Crawl4ai or LLM unavailable |

---

## Rate Limiting

Default rate limits:
- **100 requests per minute** per client

Configure using `API_RATE_LIMIT` and `API_RATE_LIMIT_PERIOD` environment variables.

---

## Production Considerations

### 1. Job Storage

The current implementation uses in-memory storage. For production:

- Use Redis or a database for job storage
- Implement job cleanup (delete old completed jobs)
- Add job expiration

### 2. Authentication

Add authentication middleware:

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/api/v1/scrape")
async def scrape_url(
    request: ScrapeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify token
    pass
```

### 3. Rate Limiting

Implement proper rate limiting using libraries like `slowapi`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

### 4. Webhook Notifications

Implement webhook callbacks for job completion:

```python
if webhook_url:
    requests.post(webhook_url, json={"job_id": job_id, "status": "completed", ...})
```

### 5. Monitoring

- Add metrics (Prometheus)
- Add logging aggregation (ELK stack)
- Add distributed tracing (Jaeger)

---

## Support

- **Documentation:** http://localhost:8000/docs
- **GitHub Issues:** https://github.com/girdav01/AgenticCTI/issues
- **Main README:** [README.md](README.md)

---

## License

Same as AgenticCTI project license.
