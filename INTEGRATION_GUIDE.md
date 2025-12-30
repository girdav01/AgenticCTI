# AgenticCTI + NG-TIP Integration Guide

## Overview

This guide explains the integration between **AgenticCTI** (Autonomous CTI Agent) and **NG-TIP** (Next-Gen Threat Intelligence Platform). The integration creates a comprehensive threat intelligence ecosystem where AgenticCTI autonomously collects and analyzes threat intelligence, then feeds it into NG-TIP for advanced storage, analysis, and visualization.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       AgenticCTI                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web        │  │   Entity     │  │    STIX      │          │
│  │   Scraper    │→ │   Extractor  │→ │   Exporter   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            ↓                                     │
│                   ┌─────────────────┐                            │
│                   │   NG-TIP Client │                            │
│                   └─────────────────┘                            │
└──────────────────────────│──────────────────────────────────────┘
                           │
                           │ HTTP REST API
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                         NG-TIP Platform                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  API Server  │→ │    Graph     │  │     RAG      │          │
│  │   (FastAPI)  │  │   Database   │  │    Engine    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            ↓                                     │
│                   ┌─────────────────┐                            │
│                   │  Streamlit UI   │                            │
│                   │   MCP Server    │                            │
│                   └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### AgenticCTI Components

1. **CTI Agent** (`agents/cti_agent.py`)
   - Autonomous threat intelligence collection
   - Source discovery and management
   - Entity extraction and analysis
   - Daily scheduled runs

2. **NG-TIP Client** (`exporters/ngtip_client.py`)
   - REST API client for NG-TIP integration
   - Batch ingestion of intelligence data
   - STIX bundle submission
   - Graph and RAG queries

3. **STIX Exporter** (`exporters/stix_exporter.py`)
   - Converts extracted entities to STIX 2.1 objects
   - Creates bundles for standardized sharing

### NG-TIP Components

1. **API Server** (`NG-TIP/cti_genai_platform/api_server.py`)
   - FastAPI-based REST API
   - Intelligence data ingestion endpoints
   - STIX bundle processing
   - Graph and RAG query endpoints

2. **Graph Manager** (`modules/graph_manager.py`)
   - Neo4j graph database integration
   - Entity and relationship storage
   - Graph-based queries and analysis

3. **RAG Engine** (`modules/rag_engine.py`)
   - Vector database for semantic search
   - Document indexing and retrieval
   - Context-aware intelligence queries

4. **STIX Processor** (`modules/stix_processor.py`)
   - STIX 2.1 object creation and parsing
   - Validation and processing

5. **Streamlit UI** (`app.py`)
   - Interactive dashboard
   - Intelligence search and visualization
   - AI-powered chat assistant

6. **MCP Server** (`mcp_server.py`)
   - Model Context Protocol server
   - Exposes CTI data to Claude Desktop
   - Tool-based querying

## Data Flow

### 1. Intelligence Collection (AgenticCTI)

```python
# AgenticCTI collects threat intelligence
agent.run(
    discover_new_sources=True,
    max_sources=20,
    max_articles_per_source=10
)

# Collected data structure:
{
    "url": "https://...",
    "title": "Security Advisory...",
    "publish_date": "2025-12-29",
    "entities": {
        "ttps": ["Phishing", "Credential Theft"],
        "cves": ["CVE-2024-1234"],
        "iocs": {"ipv4": ["192.168.1.1"], "domain": ["evil.com"]},
        "threat_actors": ["APT28"],
        "malware": ["Emotet"]
    },
    "summary": "...",
    "severity": "high",
    "confidence": 0.85
}
```

### 2. Data Ingestion (AgenticCTI → NG-TIP)

```python
# AgenticCTI pushes data to NG-TIP
ngtip_client.ingest_batch(intelligence_items)

# Or individual items
ngtip_client.ingest_intelligence(intelligence_data)

# Or STIX bundles
ngtip_client.ingest_stix_bundle(stix_bundle)
```

### 3. Data Processing (NG-TIP)

NG-TIP processes the ingested data:

1. **Graph Database Storage**
   - Creates nodes for entities (threat actors, malware, IOCs)
   - Creates relationships between entities
   - Enables graph-based queries

2. **RAG Knowledge Base**
   - Indexes summaries and content
   - Creates embeddings for semantic search
   - Enables natural language queries

3. **STIX Processing**
   - Validates STIX objects
   - Stores in standardized format
   - Enables interoperability

### 4. Data Access

Multiple ways to access the integrated intelligence:

1. **NG-TIP Streamlit UI** (http://localhost:8504)
   - Visual dashboard
   - Search and filtering
   - AI chat assistant
   - Graph visualization

2. **NG-TIP API** (http://localhost:8503)
   - REST API endpoints
   - Programmatic access
   - Integration with other tools

3. **MCP Server**
   - Claude Desktop integration
   - Natural language queries
   - Tool-based access

4. **AgenticCTI UI** (http://localhost:8501)
   - Agent status and statistics
   - Manual runs
   - Configuration

## Installation & Setup

### Prerequisites

- Docker and Docker Compose
- Git
- 8GB+ RAM recommended
- Ollama (for local LLM) or OpenAI/Anthropic API key

### Step 1: Clone Repository

```bash
git clone https://github.com/girdav01/AgenticCTI.git
cd AgenticCTI
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

Key configuration options:

```bash
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:latest
LLM_BASE_URL=http://localhost:11434

# NG-TIP Integration (enabled by default)
NGTIP_ENABLED=true
NGTIP_URL=http://ngtip-api:8503

# Neo4j for NG-TIP
NEO4J_PASSWORD=your-secure-password

# Email Notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
EMAIL_TO=recipient@example.com
```

### Step 3: Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Step 4: Pull LLM Model (if using Ollama)

```bash
# Pull Llama model
docker exec -it agentic-cti-ollama ollama pull llama3.2:latest
```

### Step 5: Access Services

- **AgenticCTI UI**: http://localhost:8501
- **AgenticCTI REST API**: http://localhost:8000
- **NG-TIP Platform UI**: http://localhost:8504
- **NG-TIP API**: http://localhost:8503
- **Neo4j Browser**: http://localhost:7474
- **Ollama**: http://localhost:11434

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| agentic-cti | 8501 | AgenticCTI Streamlit UI |
| agentic-cti-ui | 8502 | Additional UI instance |
| agentic-cti-api | 8000 | AgenticCTI REST API |
| ngtip-api | 8503 | NG-TIP Platform API |
| ngtip-ui | 8504 | NG-TIP Streamlit UI |
| neo4j | 7474, 7687 | Graph Database |
| ollama | 11434 | Local LLM Server |
| crawl4ai | 11235 | Advanced Web Scraper |

## Usage Examples

### Example 1: Automatic Daily Collection

AgenticCTI runs automatically on a schedule (default: daily at 7:00 AM):

```bash
# Check logs to see agent runs
docker-compose logs -f agentic-cti
```

The agent will:
1. Discover and scrape CTI sources
2. Extract entities (TTPs, CVEs, IOCs, etc.)
3. Push data to NG-TIP
4. Send email summary (if configured)

### Example 2: Manual Agent Run

```bash
# Run agent manually
docker exec -it agentic-cti python main.py run
```

### Example 3: Query Intelligence via NG-TIP UI

1. Open http://localhost:8504
2. Navigate to "Intelligence Search" tab
3. Enter query: "What are the latest APT campaigns?"
4. View results from multiple sources

### Example 4: Query via API

```bash
# Search RAG knowledge base
curl -X POST http://localhost:8503/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "CVE-2024-1234", "top_k": 5}'

# Query graph relationships
curl "http://localhost:8503/api/graph/query?entity_type=malware&entity_name=Emotet&depth=2"

# Get platform statistics
curl http://localhost:8503/api/statistics
```

### Example 5: Submit URL for Scraping

```bash
# Submit URL via AgenticCTI API
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.cisa.gov/news-events/cybersecurity-advisories",
    "options": {
      "extract_entities": true,
      "scraper_type": "auto"
    }
  }'

# Check job status
curl http://localhost:8000/api/v1/jobs/{job_id}
```

## Monitoring & Troubleshooting

### Check Service Health

```bash
# NG-TIP health check
curl http://localhost:8503/api/health

# AgenticCTI API health (add endpoint if needed)
curl http://localhost:8000/health
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f agentic-cti
docker-compose logs -f ngtip-api
docker-compose logs -f neo4j
```

### Common Issues

**Issue: NG-TIP cannot connect to Neo4j**

```bash
# Check Neo4j status
docker-compose logs neo4j

# Restart Neo4j
docker-compose restart neo4j

# Verify Neo4j credentials in .env
```

**Issue: AgenticCTI cannot push to NG-TIP**

```bash
# Check NG-TIP API status
curl http://localhost:8503/api/health

# Check network connectivity
docker exec -it agentic-cti ping ngtip-api

# Verify NGTIP_ENABLED=true in .env
```

**Issue: Ollama model not found**

```bash
# Pull the model
docker exec -it agentic-cti-ollama ollama pull llama3.2:latest

# List available models
docker exec -it agentic-cti-ollama ollama list
```

## API Reference

### NG-TIP Platform API

#### POST /api/ingest
Ingest threat intelligence data.

```json
{
  "url": "string",
  "title": "string",
  "publish_date": "string",
  "entities": {
    "ttps": ["string"],
    "cves": ["string"],
    "iocs": {"ipv4": ["string"], "domain": ["string"]},
    "threat_actors": ["string"],
    "malware": ["string"]
  },
  "summary": "string",
  "severity": "string",
  "confidence": 0.85
}
```

#### POST /api/ingest/stix
Ingest STIX 2.1 bundle.

```json
{
  "stix_bundle": {
    "type": "bundle",
    "objects": [...]
  },
  "source_info": {
    "source": "AgenticCTI"
  }
}
```

#### POST /api/ingest/batch
Batch ingest multiple items.

```json
{
  "items": [
    {...},
    {...}
  ]
}
```

#### GET /api/graph/query
Query graph database.

Parameters:
- `entity_type`: Type of entity
- `entity_name`: Name of entity
- `depth`: Relationship depth (default: 2)

#### POST /api/rag/search
Search RAG knowledge base.

```json
{
  "query": "string",
  "top_k": 5
}
```

## Advanced Configuration

### Custom CTI Sources

Edit `config/cti_sources.yaml`:

```yaml
sources:
  - name: "Custom Source"
    url: "https://example.com/feed"
    type: "rss"
    category: "custom"
    priority: high
    enabled: true
```

### LLM Provider Configuration

Switch between providers:

```bash
# Use Ollama (local)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:latest
LLM_BASE_URL=http://ollama:11434

# Use OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-...

# Use Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

### Scaling & Performance

```yaml
# docker-compose.yml
services:
  ngtip-api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Security Best Practices

1. **Change default passwords**
   ```bash
   NEO4J_PASSWORD=strong-password-here
   STREAMLIT_PASSWORD=admin-password-here
   ```

2. **Use environment-specific configs**
   - Development: `.env.dev`
   - Production: `.env.prod`

3. **Enable SSL/TLS**
   ```bash
   NGTIP_SSL_VERIFY=true
   ```

4. **Restrict network access**
   ```yaml
   # docker-compose.yml - remove port mappings for internal services
   ```

5. **Use API authentication**
   ```bash
   NGTIP_API_KEY=your-secure-api-key
   ```

## Integration with Claude Desktop (MCP)

The NG-TIP platform includes an MCP server for Claude Desktop integration.

See `NG-TIP/cti_genai_platform/MCP_SERVER.md` for detailed setup instructions.

## Contributing

Contributions are welcome! Please see the main [README.md](README.md) for contribution guidelines.

## License

MIT License - see [LICENSE](LICENSE) file.

## Support

- Issues: https://github.com/girdav01/AgenticCTI/issues
- Documentation: See individual README files in each component directory

---

**Disclaimer**: This tool is for authorized security research and defensive purposes only.
