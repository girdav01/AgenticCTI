# AgenticCTI - Detailed Code Map & Key File Locations

## Directory Structure with Key Files

```
/home/user/AgenticCTI/
├── agents/
│   ├── __init__.py
│   └── cti_agent.py                    (411 lines)
│       - CTIAgent class: Main orchestrator
│       - AgentRunResult: Result data class
│       - Methods: run(), _discover_sources(), _scrape_sources(), 
│                  _extract_entities(), _store_intelligence()
│       - Key imports: WebScraper, SourceDiscovery, EntityExtractor
│
├── parsers/
│   ├── __init__.py
│   ├── web_scraper.py                  (296 lines)
│   │   - WebScraper class: HTTP fetching + BeautifulSoup parsing
│   │   - ScrapedContent: Dataclass for scraped content
│   │   - Methods: scrape_url(), scrape_multiple()
│   │   - Metadata extraction: dates, authors, tags
│   │
│   ├── source_discovery.py             (349 lines)
│   │   - SourceDiscovery class: LLM-based source discovery
│   │   - CTISource: Dataclass for source definition
│   │   - Methods: discover_sources(), validate_source(), add_source()
│   │   - Uses LLM to identify and validate new CTI sources
│   │
│   └── entity_extractor.py             (365 lines)
│       - EntityExtractor class: Extract CTI entities
│       - CTIEntities: Dataclass with 9 entity types
│       - Methods: extract_entities(), generate_summary()
│       - Hybrid approach: regex + LLM
│       - Regex patterns: IPv4, domain, URL, hash, CVE, email
│       - LLM extraction: TTPs, actors, malware, campaigns
│
├── exporters/
│   ├── __init__.py
│   ├── stix_exporter.py                (427 lines)
│   │   - STIXExporter class: STIX 2.1 export
│   │   - Methods: export_entities(), save_bundle()
│   │   - Creates: Indicators, Vulnerabilities, ThreatActors, 
│   │             Malware, Campaigns, AttackPatterns
│   │   - TLP marking support (WHITE, GREEN, AMBER, RED)
│   │
│   ├── trend_vision_one.py
│   │   - TrendVisionOneClient class
│   │   - STIX bundle upload integration
│   │
│   └── opencti_client.py
│       - OpenCTIClient class
│       - GraphQL/REST integration
│
├── llm/
│   ├── __init__.py
│   ├── base.py
│   │   - BaseLLM: Abstract base class
│   │   - LLMMessage, LLMResponse: Data classes
│   │   - Exception classes
│   │
│   ├── ollama_provider.py
│   │   - OllamaLLM class: Ollama integration
│   │   - Methods: generate(), generate_with_system()
│   │
│   ├── openai_provider.py
│   │   - OpenAILLM class: OpenAI integration
│   │
│   └── factory.py                      (99 lines)
│       - LLMFactory: Factory pattern for LLM creation
│       - Methods: create_llm(), get_default_llm()
│       - Supports: ollama, openai, anthropic (planned)
│
├── mcp/
│   ├── __init__.py
│   ├── scheduler.py                    (214 lines)
│   │   - CTIScheduler class: Timezone-aware scheduling
│   │   - Methods: start(), stop(), run_now()
│   │   - Features: Daily scheduling with callback
│   │
│   └── email_notifier.py               (437 lines)
│       - EmailNotifier class: SMTP email with templates
│       - Methods: send_email(), send_daily_summary()
│       - HTML + plain text email generation
│       - Email history tracking
│
├── ui/
│   └── streamlit_app.py                (543 lines)
│       - Streamlit dashboard application
│       - Pages: Dashboard, Daily Reports, Manual Run, 
│              MCP Config, Logs & History
│       - Authentication support
│       - Manual agent trigger with parameters
│
├── utils/
│   ├── __init__.py
│   └── logging_config.py
│       - Logging setup with rotation
│       - Handlers for file and console output
│
├── config/
│   ├── config.yaml
│   │   - Main application config
│   │
│   └── cti_sources.yaml                (86 lines)
│       - CTI source definitions
│       - 10 pre-configured sources (CISA, SecurityWeek, etc.)
│       - Format: name, url, type, category, priority, enabled
│
├── data/                               (Generated at runtime)
│   ├── cti_intelligence_*.json         - Daily intelligence
│   ├── stix_exports/                   - STIX bundles
│   └── ...
│
├── logs/                               (Generated at runtime)
│   └── agentic_cti.log                 - Application logs
│
├── main.py                             (277 lines)
│   - Application entry point
│   - AgenticCTIApp class
│   - Commands: run, schedule, ui
│   - Component initialization
│
├── Dockerfile                          (57 lines)
│   - Production image (python:3.11-slim)
│   - Non-root user (agentic:1000)
│   - Health check
│
├── docker-compose.yml                  (143 lines)
│   - agentic-cti service (scheduler)
│   - agentic-cti-ui service (Streamlit)
│   - ollama service (LLM)
│   - Volumes and networking
│
├── requirements.txt                    (34 lines)
│   - python-dotenv, pyyaml, requests, beautifulsoup4, pytz
│   - openai, stix2, streamlit, urllib3
│
└── README.md
    - Comprehensive project documentation
```

## Data Flow Diagrams

### Single URL Processing Flow

```
INPUT: URL
│
▼
┌────────────────────────────────┐
│ WebScraper.scrape_url(url)     │
├────────────────────────────────┤
│ 1. Validate URL                │
│ 2. Apply rate limit            │
│ 3. requests.Session.get()      │
│ 4. BeautifulSoup parse         │
│ 5. Remove scripts/styles       │
│ 6. Extract metadata            │
│    - Title (title tag)         │
│    - Publish date (meta tags)  │
│    - Author (meta tags)        │
│    - Tags (keywords meta)      │
│ 7. Extract main content        │
│    - Try: article, main,       │
│    - .content, #content        │
│    - Fallback: body            │
│ 8. Sanitize & truncate         │
└────────┬───────────────────────┘
         │
         ▼
      ScrapedContent {
        url, title, content,
        publish_date, author,
        tags, metadata
      }
         │
         ▼
┌────────────────────────────────┐
│ EntityExtractor.extract_entities│
├────────────────────────────────┤
│ 1. Regex extraction:           │
│    - CVEs: CVE-YYYY-NNNNN      │
│    - IPv4: w.x.y.z pattern    │
│    - Domain: domain.tld        │
│    - URLs: http(s)://...       │
│    - Hashes: MD5/SHA1/SHA256   │
│    - Email: addr@domain        │
│                                │
│ 2. LLM extraction:             │
│    - TTPs/Techniques           │
│    - Threat Actors             │
│    - Malware families          │
│    - Campaigns                 │
│    - Industries targeted       │
│    - Countries affected        │
│    - Severity assessment       │
│                                │
│ 3. Generate summary (LLM)      │
└────────┬───────────────────────┘
         │
         ▼
      CTIEntities {
        ttps[], cves[], iocs{},
        threat_actors[], malware[],
        campaigns[], industries[],
        countries[], summary,
        severity, confidence
      }
         │
         ▼
┌────────────────────────────────┐
│ Storage & Export               │
├────────────────────────────────┤
│ 1. Store in memory:            │
│    collected_intelligence[]    │
│ 2. Save to JSON:               │
│    ./data/cti_intelligence.json│
│ 3. Optional: STIX export       │
│    STIXExporter.export_entities│
│    → Bundle (stix2)            │
│    → ./data/stix_exports/      │
└────────┬───────────────────────┘
         │
         ▼
OUTPUT: Intelligence recorded
```

### Agent Run (Scheduled or Manual)

```
TRIGGER: schedule or manual run
│
▼
┌──────────────────────────────────────┐
│ CTIAgent.run(discover_new_sources,   │
│              max_sources,             │
│              max_articles_per_source) │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ [1] Source Discovery (if enabled)    │
├──────────────────────────────────────┤
│ LLM prompt: "Discover CTI sources"   │
│ → Parse response → Validate → Add    │
│ → Save to cti_sources.yaml           │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ [2] Load Enabled Sources             │
├──────────────────────────────────────┤
│ From: cti_sources.yaml               │
│ Filter: enabled=true                 │
│ Limit: max_sources                   │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ [3] Scrape Each Source               │
├──────────────────────────────────────┤
│ For each source:                     │
│   → WebScraper.scrape_url()          │
│   → Collect ScrapedContent objects   │
│ articles_scraped += 1                │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ [4] Extract Entities                 │
├──────────────────────────────────────┤
│ For each ScrapedContent:             │
│   → EntityExtractor.extract_entities │
│   → Collect CTIEntities objects      │
│ entities_extracted += 1              │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ [5] Store Intelligence               │
├──────────────────────────────────────┤
│ Combine content + entities → dict    │
│ Append to collected_intelligence[]   │
│ Save to JSON file                    │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ AgentRunResult                       │
├──────────────────────────────────────┤
│ run_id, start_time, end_time        │
│ sources_discovered, articles_scraped│
│ entities_extracted, success         │
│ errors[], STIX_objects_created      │
└──────────────────────────────────────┘
     │
     ▼ (in main.py)
     │
┌────────────────────────────────────────────┐
│ Daily Summary Generation (opt.)            │
├────────────────────────────────────────────┤
│ Aggregate stats from collected_intelligence│
│ - Total articles, CVEs, actors            │
│ - Severity distribution                   │
│ - Top targeted industries                 │
│ - Critical findings                       │
└────┬───────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────┐
│ Email Notification (if configured)         │
├────────────────────────────────────────────┤
│ EmailNotifier.send_daily_summary()         │
│ → Generate HTML + plain text               │
│ → Send via SMTP                            │
│ → Track email history                      │
└────────────────────────────────────────────┘
```

## Key Class Relationships

```
┌─────────────────────────────────────────────────────┐
│              CTIAgent                               │
│  (Main Orchestrator - agents/cti_agent.py)         │
├─────────────────────────────────────────────────────┤
│  - llm: BaseLLM                                    │
│  - scraper: WebScraper                            │
│  - source_discovery: SourceDiscovery              │
│  - entity_extractor: EntityExtractor              │
│                                                    │
│  Methods:                                          │
│  + run(discover, max_sources, max_articles)      │
│  + get_daily_summary() → Dict                     │
│  + get_status() → Dict                            │
│  + clear_intelligence()                           │
└────────┬──────────────────────────────────────────┘
         │
         ├─────────────────────────────────────┐
         │                                     │
         ▼                                     ▼
┌────────────────────┐           ┌──────────────────────┐
│   WebScraper       │           │ SourceDiscovery      │
│ (parsers/web_      │           │ (parsers/source_     │
│  scraper.py)       │           │  discovery.py)       │
├────────────────────┤           ├──────────────────────┤
│ + scrape_url()     │           │ + discover_sources() │
│ + scrape_multiple()│           │ + validate_source()  │
│ - _apply_rate      │           │ + add_source()       │
│   _limit()         │           │ + save_sources()     │
│ - _extract_main    │           │ - Uses LLM for       │
│   _content()       │           │   discovery & valid  │
│ - _extract_        │           │                      │
│   publish_date()   │           │ CTISource dataclass: │
│ - _extract_author()│           │ - name, url, type,   │
│ - _extract_tags()  │           │   category, priority │
│                    │           │   enabled, confidence│
│ ScrapedContent:    │           └──────────────────────┘
│ - url, title,      │
│ - content, publish │
│ - date, author,    │
│ - tags, metadata   │
└────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  EntityExtractor            │
│ (parsers/entity_extractor.py)
├─────────────────────────────┤
│ + extract_entities()        │
│ + generate_summary()        │
│ - _extract_with_regex()     │
│ - _extract_with_llm()       │
│ - _merge_entities()         │
│ - _parse_llm_response()     │
│                             │
│ CTIEntities dataclass:      │
│ - ttps[], cves[], iocs{}    │
│ - threat_actors[], malware[]│
│ - campaigns[], industries[] │
│ - countries[], summary      │
│ - severity, confidence      │
└─────────────────────────────┘
```

## Code Interaction Example: Full Run

```
main.py
├─ AgenticCTIApp.__init__()
│  ├─ LLMFactory.get_default_llm()
│  ├─ CTIAgent(llm)
│  │  ├─ WebScraper(config)
│  │  ├─ SourceDiscovery(llm, path)
│  │  │  └─ _load_sources() from YAML
│  │  └─ EntityExtractor(llm)
│  ├─ EmailNotifier(smtp_config)
│  ├─ STIXExporter()
│  └─ OpenCTIClient() [if enabled]
│
└─ AgenticCTIApp.run_daily_task()
   ├─ agent.run(discover=True, max=20, max_articles=10)
   │  ├─ [if discover] source_discovery.discover_sources()
   │  │  └─ llm.generate_with_system(system_prompt, user_prompt)
   │  │     → parse response → new CTISources
   │  │
   │  ├─ source_discovery.get_enabled_sources()
   │  │  → List[CTISource]
   │  │
   │  ├─ for source in sources:
   │  │  └─ scraper.scrape_url(source.url)
   │  │     ├─ requests.get(url)
   │  │     ├─ BeautifulSoup(response.content)
   │  │     ├─ Extract title, content, metadata
   │  │     └─ return ScrapedContent
   │  │
   │  ├─ for content in scraped:
   │  │  └─ entity_extractor.extract_entities(content)
   │  │     ├─ regex patterns for IOCs & CVEs
   │  │     ├─ llm.generate_with_system() for semantic
   │  │     ├─ generate_summary() via LLM
   │  │     └─ return CTIEntities
   │  │
   │  └─ _store_intelligence(scraped, entities)
   │     ├─ Combine into intelligence_item dict
   │     ├─ collected_intelligence.append()
   │     └─ _save_intelligence() to JSON
   │
   ├─ agent.get_daily_summary()
   │  └─ Aggregate statistics from collected_intelligence
   │
   ├─ email_notifier.send_daily_summary()
   │  ├─ _generate_text_summary()
   │  ├─ _generate_html_summary()
   │  └─ send_email() via SMTP
   │
   └─ agent.clear_intelligence()
      └─ Reset for next day
```

## Important Functions/Methods by Category

### Scraping
- `WebScraper.scrape_url(url)` → ScrapedContent
- `WebScraper.scrape_multiple(urls)` → List[ScrapedContent]
- `WebScraper._extract_main_content(soup)` → str
- `WebScraper._extract_publish_date(soup)` → str
- `WebScraper._extract_author(soup)` → str
- `WebScraper._extract_tags(soup)` → List[str]

### Entity Extraction
- `EntityExtractor.extract_entities(text, title)` → CTIEntities
- `EntityExtractor._extract_with_regex(text)` → CTIEntities
- `EntityExtractor._extract_with_llm(text, title)` → CTIEntities
- `EntityExtractor._merge_entities(regex, llm)` → CTIEntities
- `EntityExtractor.generate_summary(entities, content)` → str

### Source Management
- `SourceDiscovery.discover_sources(keywords, max)` → List[CTISource]
- `SourceDiscovery.validate_source(source)` → bool
- `SourceDiscovery.add_source(source, save)` → bool
- `SourceDiscovery.save_sources()` → bool
- `SourceDiscovery.get_enabled_sources()` → List[CTISource]

### Agent Orchestration
- `CTIAgent.run(discover, max_sources, max_articles)` → AgentRunResult
- `CTIAgent._discover_sources()` → None
- `CTIAgent._scrape_sources(sources, max)` → List[ScrapedContent]
- `CTIAgent._extract_entities(scraped)` → List[CTIEntities]
- `CTIAgent._store_intelligence(content, entities)` → None
- `CTIAgent.get_daily_summary()` → Dict
- `CTIAgent.get_status()` → Dict

### Export & Integration
- `STIXExporter.export_entities(entities, url, title)` → Bundle
- `STIXExporter.save_bundle(bundle, filename)` → Path
- `TrendVisionOneClient.upload_stix_bundle(bundle)` → bool
- `OpenCTIClient.add_indicator(indicator)` → bool

### Notifications
- `EmailNotifier.send_email(to, subject, body)` → bool
- `EmailNotifier.send_daily_summary(to, summary)` → bool
- `EmailNotifier.test_connection()` → bool

### Scheduling
- `CTIScheduler.start()` → None
- `CTIScheduler.stop()` → None
- `CTIScheduler.run_now()` → None
- `CTIScheduler.get_status()` → Dict
