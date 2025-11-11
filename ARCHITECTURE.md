# AgenticCTI Architecture Analysis & Crawl4ai Integration Plan

## 1. Current Scraping/Crawling Implementation

### WebScraper Module (`parsers/web_scraper.py`)
**Current Technology Stack:**
- **Library:** BeautifulSoup4 + requests
- **Features:**
  - Basic HTTP/HTTPS fetching with configurable timeouts
  - Retry logic with exponential backoff (up to 3 retries on 429, 500-504 errors)
  - Per-domain rate limiting (configurable, default 0.5s between requests)
  - User-agent customization
  - Session management with connection pooling

**Current Capabilities:**
- Scrapes single URLs: `scrape_url(url) -> ScrapedContent`
- Batch scraping: `scrape_multiple(urls) -> List[ScrapedContent]`
- Metadata extraction: title, publish_date, author, tags
- Content cleaning: removes scripts, styles, nav, footer, header elements
- Main content extraction using CSS selectors (article, main, .content, etc.)

**Limitations:**
- Static HTML parsing only
- No JavaScript rendering capability
- No handling of dynamic content loading
- Limited to simple HTML selectors
- No cookie/session persistence for restricted content
- No browser automation capabilities

### WebScraper Data Flow
```
URL → requests.get() → BeautifulSoup parse → CSS selectors
                                            → Regex extraction (dates, authors, tags)
                                            → Content sanitization
                                            → ScrapedContent object
```

## 2. Article/URL Processing Workflow

### Processing Pipeline (`agents/cti_agent.py`)
AgenticCTI uses a multi-stage agent workflow:

```
┌─────────────────────────────────────────────────────────────┐
│                   CTI Agent Execution Loop                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  1. SOURCE DISCOVERY (Optional)       │
         │  - LLM-based discovery of new feeds  │
         │  - Validation of new sources         │
         │  - Config file updates               │
         └──────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  2. GET ACTIVE SOURCES                │
         │  - Load from cti_sources.yaml        │
         │  - Filter enabled sources            │
         │  - Limit to max_sources (def: 20)   │
         └──────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  3. SCRAPE SOURCES                    │
         │  - WebScraper.scrape_url() per source│
         │  - Main page scraping (RSS not impl.)│
         │  - Returns ScrapedContent objects    │
         └──────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  4. ENTITY EXTRACTION                 │
         │  - Regex-based: CVEs, IPs, hashes    │
         │  - LLM-based: TTPs, threat actors,   │
         │    malware, campaigns, industries    │
         │  - Returns CTIEntities objects       │
         └──────────────────────────────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────┐
         │  5. STORAGE & EXPORT                  │
         │  - Store as JSON to files            │
         │  - Generate daily summary            │
         │  - Export to STIX (optional)         │
         │  - Send email (optional)             │
         └──────────────────────────────────────┘
```

### Data Structures
```python
ScrapedContent(
    url: str,
    title: str,
    content: str,
    publish_date: Optional[str],
    author: Optional[str],
    tags: Optional[List[str]],
    metadata: Optional[Dict]
)

CTIEntities(
    ttps: List[str],
    cves: List[str],
    iocs: Dict[str, List[str]],  # ipv4, domain, url, md5, sha1, sha256, email
    threat_actors: List[str],
    malware: List[str],
    campaigns: List[str],
    industries: List[str],
    countries: List[str],
    summary: str,
    severity: str,  # low, medium, high, critical
    confidence: float
)
```

### Current Limitations
- Only processes URLs configured in `config/cti_sources.yaml`
- No way to submit arbitrary URLs via API
- No async/background URL processing
- No webhook callbacks for completion
- Max 10 articles per source by default
- No RSS feed parsing (placeholder only)

## 3. Existing API Structure

### Current State: NO REST API
The application currently has **NO REST/HTTP API** for:
- URL submission
- Status queries
- Trigger runs
- Webhook callbacks

### Current Interfaces

**1. CLI Interface** (`main.py`)
```bash
python main.py run        # Execute once
python main.py schedule   # Run on schedule (default)
python main.py ui         # Launch Streamlit UI
```

**2. Streamlit UI** (`ui/streamlit_app.py`)
- Dashboard view
- Daily reports
- Manual run trigger (limited parameters)
- Configuration UI
- Logs viewer

**3. Programmatic Interface** (Python-only)
```python
from agents import CTIAgent
from llm import LLMFactory

agent = CTIAgent(llm=LLMFactory.get_default_llm())
result = agent.run(
    discover_new_sources=True,
    max_sources=20,
    max_articles_per_source=10
)
```

## 4. Docker Setup and Configuration

### Dockerfile Architecture
```dockerfile
- Base: python:3.11-slim
- System deps: gcc, g++, git, curl
- Non-root user: agentic (UID 1000)
- Exposed port: 8501 (Streamlit)
- Health check: curl to Streamlit health endpoint
- Default command: python main.py schedule
```

### Docker Compose Stack

**Services:**
1. **agentic-cti** (Main service)
   - Container: agentic-cti
   - Port: 8501
   - Command: `python main.py schedule`
   - Depends on: ollama

2. **agentic-cti-ui** (Separate UI container)
   - Container: agentic-cti-ui
   - Port: 8502
   - Command: `python main.py ui`
   - Shares volumes with main service

3. **ollama** (LLM inference)
   - Image: ollama/ollama:latest
   - Port: 11434
   - Volume: ollama-data (persistent)

**Volumes:**
- `./data` → `/app/data` (intelligence storage)
- `./logs` → `/app/logs` (application logs)
- `./config` → `/app/config` (configuration)
- `ollama-data` (LLM model cache)

**Networks:**
- `agentic-cti-network` (bridge network)

### Environment Configuration
```bash
# LLM
LLM_PROVIDER=ollama|openai|anthropic
LLM_MODEL=llama3.2:latest
LLM_BASE_URL=http://ollama:11434
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4096

# Email
SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
EMAIL_FROM, EMAIL_TO, EMAIL_DAILY_TIME, EMAIL_TIMEZONE

# STIX
ENABLE_STIX_EXPORT=true
STIX_EXPORT_PATH=/app/data/stix_exports

# Integration
TREND_VISION_ONE_ENABLED, TREND_VISION_ONE_API_KEY
OPENCTI_ENABLED, OPENCTI_URL, OPENCTI_API_KEY

# Streamlit
STREAMLIT_AUTH_ENABLED=true
STREAMLIT_USERNAME=admin
STREAMLIT_PASSWORD=changeme

# Agent
AGENT_RUN_INTERVAL=86400
AGENT_MAX_SOURCES=20
AGENT_MAX_ARTICLES_PER_SOURCE=10

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/agentic_cti.log
```

## 5. Current Integration with Crawl4ai

### Current Status
**NO Crawl4ai integration exists.**

The project uses:
- **BeautifulSoup4** for HTML parsing
- **requests** for HTTP fetching
- **LLMs** for entity extraction and validation

### Why Crawl4ai Would Be Beneficial

1. **JavaScript Rendering:** Modern CTI sources use SPAs/dynamic content
2. **Better Content Extraction:** Semantic analysis vs CSS selectors
3. **Structured Data:** LLM-powered content cleaning and structuring
4. **Screenshot Capability:** Visual content extraction
5. **Link Following:** Automatic discovery of article links from index pages
6. **Async Processing:** Built-in async crawling support
7. **Smart Retry:** Better handling of rate limiting and blocking

## 6. Architecture Overview - High Level

```
┌────────────────────────────────────────────────────────────────┐
│                        AgenticCTI Stack                         │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐       ┌──────────────┐     ┌──────────────┐  │
│  │ CLI/Scheduler│       │  Streamlit   │     │    REST API  │  │
│  │              │       │     UI       │     │   (PLANNED)  │  │
│  └──────┬───────┘       └──────┬───────┘     └──────┬───────┘  │
│         │                      │                     │          │
│         └──────────────────────┼─────────────────────┘          │
│                                │                                │
│                    ┌───────────▼──────────┐                     │
│                    │   CTI Agent Loop     │                     │
│                    │ (agents/cti_agent.py)│                     │
│                    └───┬─────────────────┬┘                     │
│                        │                 │                      │
│         ┌──────────────┼─────────────────┼──────────────┐       │
│         │              │                 │              │       │
│         ▼              ▼                 ▼              ▼       │
│    ┌─────────┐    ┌─────────┐      ┌─────────┐    ┌─────────┐ │
│    │ Source  │    │   Web   │      │ Entity  │    │ Export/ │ │
│    │Discovery│    │ Scraper │      │ Extract │    │ Storage │ │
│    │  (LLM)  │    │(Beautif│      │ (LLM)   │    │         │ │
│    │         │    │ Soup4)  │      │         │    │ STIX    │ │
│    └─────────┘    └─────────┘      └─────────┘    │ JSON    │ │
│                        │                           │ Email   │ │
│                   [NOW: Single page]               └─────────┘ │
│                   [FUTURE: Crawl4ai]                            │
│                                                                 │
│    ┌──────────────────────┐        ┌──────────────────────┐   │
│    │    LLM Providers     │        │  CTI Platform        │   │
│    │  - Ollama            │        │  Integrations        │   │
│    │  - OpenAI            │        │  - OpenCTI           │   │
│    │  - Anthropic         │        │  - Trend Vision One  │   │
│    └──────────────────────┘        └──────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

## 7. Codebase Statistics

- **Total Lines:** 5,296 (Python + YAML)
- **Main Components:**
  - `agents/` - 411 lines (orchestration)
  - `parsers/` - 680 lines (scraping, extraction, discovery)
  - `exporters/` - 726 lines (STIX, integrations)
  - `llm/` - 512 lines (LLM abstraction)
  - `mcp/` - 437 lines (email, scheduling)
  - `ui/` - 543 lines (Streamlit dashboard)
  - `main.py` - 277 lines (entry point)

## 8. Key Integration Points for Crawl4ai

### Where Crawl4ai Fits
```
Current Flow:
URL (single page) → requests → BeautifulSoup → CTIEntities

Proposed Flow:
URL (index/article) → Crawl4ai API → Extract content & links 
                                    → Discover article links
                                    → Async crawl articles
                                    → Return structured data
                   → Entity Extraction (LLM) → Storage
```

### Required Changes for Crawl4ai Integration

1. **New REST API Endpoint** (FastAPI/Flask)
   - `POST /api/urls/submit` - Submit URL for crawling
   - `GET /api/jobs/{job_id}` - Check job status
   - `POST /api/sources/` - Add dynamic sources
   - `GET /api/status` - System status

2. **Crawl4ai Service Integration**
   - Initialize Crawl4ai client
   - Add async job queue (Celery or asyncio)
   - Implement link discovery logic
   - Handle batch crawling

3. **Database Layer** (Optional but recommended)
   - Replace JSON file storage
   - Track job status and history
   - Store crawled URLs to avoid duplicates
   - Rate limiting per domain

4. **Docker Compose Updates**
   - Add Crawl4ai service
   - Add FastAPI service
   - Optional: Add Redis for job queue
   - Optional: Add PostgreSQL for persistence

5. **Configuration Updates**
   - Crawl4ai API endpoint URL
   - Crawl4ai API key (if needed)
   - Job queue settings
   - Link discovery patterns

## 9. Recommended Architecture for Crawl4ai Integration

```
┌─────────────────────────────────────────────────────────────┐
│             REST API (FastAPI) - NEW                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ POST /urls  │  │ GET /jobs    │  │ GET /status      │   │
│  │ POST /run   │  │ GET /history │  │ POST /sources    │   │
│  └──────┬──────┘  └──────────────┘  └──────────────────┘   │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│            Job Queue & Async Processing - NEW               │
│     (Celery w/ Redis or asyncio.Queue)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Crawl4ai Task Worker                                │   │
│  │  - Submit URL to Crawl4ai service                    │   │
│  │  - Wait for result                                   │   │
│  │  - Extract links for recursive crawling              │   │
│  │  - Return structured HTML                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  CTI Agent Processing (Enhanced)                            │
│  - Now accepts both scheduled and ad-hoc URLs              │
│  - Crawl4ai replaces BeautifulSoup in scraper layer       │
│  - Entity extraction remains LLM-based                      │
│  - STIX export and email still work                         │
└─────────────────────────────────────────────────────────────┘
```

## 10. Summary: Where Crawl4ai Fits

### Current Bottlenecks
1. ❌ Static HTML parsing only
2. ❌ Single page per source (no article discovery)
3. ❌ No REST API for external submissions
4. ❌ No async/background job processing
5. ❌ Limited to configured sources
6. ❌ No JavaScript rendering for modern sites

### Crawl4ai Benefits
1. ✅ JavaScript rendering and DOM manipulation
2. ✅ Intelligent link extraction and recursion
3. ✅ LLM-powered content cleaning
4. ✅ Async crawling capability
5. ✅ Smart retry and rate limiting
6. ✅ Screenshot and visual content support
7. ✅ Structured data extraction

### Implementation Priority

**Phase 1: REST API + Simple Integration**
- Add FastAPI layer with basic endpoints
- Add `/api/urls/submit` endpoint
- Keep Crawl4ai as drop-in replacement for WebScraper
- Simple async job queue

**Phase 2: Advanced Features**
- Link discovery and recursive crawling
- Batch URL submission
- Webhook callbacks
- Job status persistence

**Phase 3: Optimization**
- Database layer (PostgreSQL)
- Advanced rate limiting
- Distributed crawling
- Performance monitoring
