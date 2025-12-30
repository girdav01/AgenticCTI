# AgenticCTI Deployment Options

Choose the deployment profile that best fits your needs. AgenticCTI offers flexible deployment options to balance features with resource requirements.

## Quick Reference

| Profile | Command | Memory | Use Case |
|---------|---------|--------|----------|
| **Minimal** | `docker-compose up` | ~2GB | Basic CTI collection, small teams |
| **Standard** | `docker-compose up` + enable integrations | ~3GB | Daily CTI operations with enrichment |
| **Full** | `docker-compose --profile full up` | ~4GB | Advanced threat hunting, SOC/MSSP |

## Deployment Profiles

### 1. Minimal Deployment (Default)

**What you get:**
- ✅ AgenticCTI core (autonomous CTI collection)
- ✅ Ollama for local LLM inference
- ✅ NG-TIP platform with RAG (semantic search)
- ✅ STIX 2.1 export
- ✅ Email reports
- ✅ REST API
- ✅ Streamlit UIs

**What's excluded:**
- ❌ Neo4j graph database (graph visualization disabled)
- ❌ Optional integrations (VirusTotal, SpiderFoot, Trend Vision One)

**Resource Requirements:**
- **RAM**: ~2GB
- **CPU**: 2 cores
- **Disk**: 10GB (models + data)

**Startup Command:**
```bash
# Set Neo4j to disabled in .env
NGTIP_NEO4J_ENABLED=false

# Start minimal stack
docker-compose up -d
```

**Best for:**
- Individual researchers
- Small security teams
- Learning and testing
- Resource-constrained environments
- Quick daily threat intelligence feeds

---

### 2. Standard Deployment (Recommended)

**What you get:**
- Everything from Minimal +
- ✅ Optional integrations (configure as needed):
  - VirusTotal (multi-engine malware scanning)
  - SpiderFoot (OSINT enrichment)
  - Trend Vision One (sandbox + intelligence)
- ⚠️ Still without Neo4j graph (can add separately)

**Resource Requirements:**
- **RAM**: ~3GB
- **CPU**: 2-4 cores
- **Disk**: 10GB

**Configuration (.env):**
```bash
# Enable optional integrations
VIRUSTOTAL_ENABLED=true
VIRUSTOTAL_API_KEY=your-api-key

SPIDERFOOT_ENABLED=true
SPIDERFOOT_URL=http://localhost:5001

TREND_VISION_ONE_ENABLED=true
TREND_VISION_ONE_API_KEY=your-api-key

# Neo4j still disabled for resource savings
NGTIP_NEO4J_ENABLED=false
```

**Startup Command:**
```bash
docker-compose up -d
```

**Best for:**
- Daily CTI operations
- Malware analysis workflows
- Enriched threat intelligence
- Medium-sized security teams
- Budget-conscious deployments with API access

---

### 3. Full Deployment (All Features)

**What you get:**
- Everything from Standard +
- ✅ Neo4j graph database
- ✅ Graph relationship visualization
- ✅ Advanced threat hunting
- ✅ Entity relationship queries
- ✅ Threat actor network analysis

**Resource Requirements:**
- **RAM**: ~4GB (Neo4j adds ~500MB)
- **CPU**: 4+ cores recommended
- **Disk**: 15GB (includes graph data)

**Configuration (.env):**
```bash
# Enable all features
NGTIP_NEO4J_ENABLED=true
NEO4J_PASSWORD=your-secure-password

# Plus optional integrations (see Standard)
VIRUSTOTAL_ENABLED=true
SPIDERFOOT_ENABLED=true
TREND_VISION_ONE_ENABLED=true
```

**Startup Command:**
```bash
# Use 'full' profile to include Neo4j
docker-compose --profile full up -d

# OR use 'graph' profile for just Neo4j
docker-compose --profile graph up -d
```

**Best for:**
- SOC/MSSP operations
- APT campaign tracking
- Large-scale threat intelligence
- Advanced threat hunting
- Organizations needing relationship graphs
- Research requiring threat correlation

---

## Feature Comparison Matrix

| Feature | Minimal | Standard | Full |
|---------|---------|----------|------|
| **Core Features** ||||
| Autonomous CTI Collection | ✅ | ✅ | ✅ |
| LLM Entity Extraction | ✅ | ✅ | ✅ |
| STIX 2.1 Export | ✅ | ✅ | ✅ |
| Email Reports | ✅ | ✅ | ✅ |
| REST API | ✅ | ✅ | ✅ |
| Streamlit UI | ✅ | ✅ | ✅ |
| **NG-TIP Platform** ||||
| RAG Semantic Search | ✅ | ✅ | ✅ |
| LLM Analysis | ✅ | ✅ | ✅ |
| Intelligence Ingestion | ✅ | ✅ | ✅ |
| STIX Processing | ✅ | ✅ | ✅ |
| Graph Visualization | ❌ | ❌ | ✅ |
| Entity Relationships | ❌ | ❌ | ✅ |
| Threat Actor Networks | ❌ | ❌ | ✅ |
| **Malware Analysis** ||||
| Script Analysis (LLM) | ✅ | ✅ | ✅ |
| Shellcode Analysis | ✅ | ✅ | ✅ |
| YARA/Sigma Rules | ✅ | ✅ | ✅ |
| Trend Vision One Sandbox | ⚙️ | ✅ | ✅ |
| VirusTotal Multi-Engine | ⚙️ | ✅ | ✅ |
| SpiderFoot OSINT | ⚙️ | ✅ | ✅ |
| **Resource Usage** ||||
| Memory (RAM) | ~2GB | ~3GB | ~4GB |
| CPU Cores | 2 | 2-4 | 4+ |
| Disk Space | 10GB | 10GB | 15GB |
| Docker Containers | 7 | 7-9 | 8-10 |

**Legend:**
- ✅ = Included
- ❌ = Not included
- ⚙️ = Configurable (disabled by default)

---

## Component Breakdown

### Services by Profile

#### Minimal (7 containers):
1. `agentic-cti` - Main CTI agent
2. `agentic-cti-ui` - Streamlit UI
3. `agentic-cti-api` - REST API
4. `ollama` - Local LLM server
5. `crawl4ai` - Advanced web scraper
6. `ngtip-api` - NG-TIP API server
7. `ngtip-ui` - NG-TIP Streamlit UI

#### Standard (+ external services):
- All Minimal services +
- External VirusTotal API (if enabled)
- External/local SpiderFoot (if enabled)
- External Trend Vision One (if enabled)

#### Full (8-10 containers):
- All Minimal services +
- `neo4j` - Graph database
- Optional: `spiderfoot` container (if self-hosted)

---

## Migration Between Profiles

### Upgrading: Minimal → Standard

**No docker changes needed**, just add API keys:

```bash
# Edit .env
VIRUSTOTAL_ENABLED=true
VIRUSTOTAL_API_KEY=your-key

SPIDERFOOT_ENABLED=true
SPIDERFOOT_URL=http://localhost:5001

# Restart services
docker-compose restart
```

### Upgrading: Standard → Full

**Enable Neo4j profile:**

```bash
# Edit .env
NGTIP_NEO4J_ENABLED=true
NEO4J_PASSWORD=secure-password

# Restart with full profile
docker-compose down
docker-compose --profile full up -d
```

**Data is preserved** - existing intelligence will be available in graph once Neo4j starts.

### Downgrading: Full → Standard

**Disable Neo4j:**

```bash
# Edit .env
NGTIP_NEO4J_ENABLED=false

# Restart without profile
docker-compose down
docker-compose up -d
```

**Note**: Graph data is preserved in volumes. Re-enable anytime without data loss.

---

## Use Case Recommendations

### Individual Researcher / Student
**Profile**: Minimal
**Why**: Low cost, all core features, perfect for learning

### Small Security Team (1-5 people)
**Profile**: Standard
**Why**: Enriched intelligence with API integrations, no graph overhead

### Medium Security Team / MSSP (5-20 people)
**Profile**: Standard or Full
**Why**: Full if doing APT tracking, Standard if focused on daily IOCs

### Large SOC / Enterprise (20+ people)
**Profile**: Full
**Why**: Graph features critical for correlating threats across teams

### Malware Analysis Lab
**Profile**: Standard
**Why**: VirusTotal + Trend sandbox sufficient, graph not critical

### Threat Intelligence Platform
**Profile**: Full
**Why**: Graph relationships essential for comprehensive TIP

---

## Cost Comparison

### Infrastructure Costs

| Profile | Cloud VM (monthly) | On-Prem Hardware |
|---------|-------------------|------------------|
| **Minimal** | $20-40 (2GB RAM) | Basic workstation |
| **Standard** | $40-80 (4GB RAM) | Mid-range workstation |
| **Full** | $80-120 (8GB RAM) | High-end workstation |

### API Costs (Optional - Standard/Full)

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **VirusTotal** | 4 req/min | $500+/month |
| **SpiderFoot** | Self-hosted free | - |
| **Trend Vision One** | Trial available | Enterprise pricing |

**Total Monthly (Standard)**: $40-80 infrastructure + $0 APIs (free tiers)
**Total Monthly (Full)**: $80-120 infrastructure + $0-500 APIs

---

## Performance Expectations

### Collection Throughput

| Profile | Daily Sources | Articles/Day | Processing Time |
|---------|--------------|--------------|----------------|
| Minimal | 10-20 | 100-200 | 5-10 min |
| Standard | 20-50 | 200-500 | 10-20 min |
| Full | 50-100+ | 500-1000+ | 20-30 min |

### Query Response Times

| Operation | Minimal | Standard | Full |
|-----------|---------|----------|------|
| RAG Search | 1-2s | 1-2s | 1-2s |
| Entity Lookup | N/A | 2-5s (API) | 0.5-1s (graph) |
| Relationship Query | N/A | N/A | 1-3s |
| Graph Visualization | N/A | N/A | 2-5s |

---

## Troubleshooting by Profile

### Minimal Issues

**"Out of memory" errors:**
- Reduce `LLM_MAX_TOKENS` in .env (try 4096)
- Use smaller model: `llama3.2:1b` instead of `llama3.2:3b`

**Slow processing:**
- Reduce `AGENT_MAX_SOURCES` (try 10)
- Reduce `AGENT_MAX_ARTICLES_PER_SOURCE` (try 5)

### Standard Issues

**API rate limits:**
- VirusTotal: Increase `VIRUSTOTAL_RATE_LIMIT` (default 15s)
- Use free tiers wisely (cache results)

**Integration failures:**
- Check API keys are valid
- Verify network connectivity
- Review service-specific logs

### Full Issues

**Neo4j won't start:**
- Check port 7687 not in use: `lsof -i :7687`
- Verify `NEO4J_PASSWORD` is set
- Check Neo4j logs: `docker logs ngtip-neo4j`

**Graph queries slow:**
- Add indexes in Neo4j browser
- Limit query depth (default: 2)
- Prune old data periodically

---

## Quick Start Commands

### Minimal Deployment
```bash
# Clone and configure
git clone https://github.com/girdav01/AgenticCTI.git
cd AgenticCTI
cp .env.example .env

# Edit .env - set NGTIP_NEO4J_ENABLED=false

# Start
docker-compose up -d

# Access
# - AgenticCTI UI: http://localhost:8501
# - NG-TIP UI: http://localhost:8504
# - API: http://localhost:8000
```

### Standard Deployment
```bash
# Same as minimal, but add to .env:
# VIRUSTOTAL_ENABLED=true
# VIRUSTOTAL_API_KEY=your-key
# SPIDERFOOT_ENABLED=true
# NGTIP_NEO4J_ENABLED=false

docker-compose up -d
```

### Full Deployment
```bash
# Same as standard, but:
# NGTIP_NEO4J_ENABLED=true
# NEO4J_PASSWORD=secure-password

docker-compose --profile full up -d

# Access Neo4j browser
# http://localhost:7474
# Username: neo4j
# Password: (from .env NEO4J_PASSWORD)
```

---

## Summary & Recommendations

**Start with Minimal** if:
- You're new to CTI
- Testing AgenticCTI
- Limited resources
- No API budget

**Upgrade to Standard** when:
- You have API keys (VirusTotal, Trend)
- Need malware enrichment
- Processing 20+ sources daily
- Have modest API budget

**Deploy Full** when:
- Running a SOC/MSSP
- Tracking APT campaigns
- Need relationship graphs
- 4GB+ RAM available
- Advanced threat hunting required

**Remember**: You can always start small and scale up. All profiles preserve data when upgrading.

---

## Additional Resources

- [Quick Start Guide](../QUICKSTART.md)
- [Integration Guide](../INTEGRATION_GUIDE.md)
- [Malware Analysis Guide](MALWARE_ANALYSIS.md)
- [Recommended Models](RECOMMENDED_MODELS.md)

For questions: https://github.com/girdav01/AgenticCTI/issues
