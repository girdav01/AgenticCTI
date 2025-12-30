# AgenticCTI + NG-TIP Quick Start Guide

Get up and running with the integrated AgenticCTI and NG-TIP platform in under 10 minutes.

## 📋 Choose Your Deployment

AgenticCTI offers three deployment profiles to match your needs:

| Profile | Memory | Features | Best For |
|---------|--------|----------|----------|
| **Minimal** | ~2GB | Core CTI + RAG | Testing, small teams |
| **Standard** | ~3GB | + API integrations | Daily operations |
| **Full** | ~4GB | + Graph database | SOC/MSSP, advanced hunting |

**See [Deployment Options](docs/DEPLOYMENT_OPTIONS.md) for detailed comparison.**

This guide shows **Minimal** deployment. For other profiles, see the Deployment Options guide.

## 🚀 5-Minute Setup (Minimal Profile)

### 1. Prerequisites Check

```bash
# Check Docker
docker --version
docker-compose --version

# Check Git
git --version

# Check GPU (optional but recommended)
nvidia-smi
```

### 2. Clone and Configure

```bash
# Clone repository
git clone https://github.com/girdav01/AgenticCTI.git
cd AgenticCTI

# Copy environment file
cp .env.example .env

# Edit configuration (use your favorite editor)
nano .env  # or vim, code, etc.
```

**Minimum Required Configuration**:
```bash
# In .env file, update these:
LLM_MODEL=ALIENTELLIGENCE/cybersecuritythreatanalysisv2
STREAMLIT_PASSWORD=your-admin-password

# For Minimal profile, disable Neo4j to save resources:
NGTIP_NEO4J_ENABLED=false

# Optional: Set password if you plan to upgrade to Full later
NEO4J_PASSWORD=your-secure-password
```

### 3. Start All Services

```bash
# Minimal profile (no Neo4j - saves ~500MB RAM)
docker-compose up -d

# OR Full profile (includes Neo4j graph features)
# docker-compose --profile full up -d

# Wait ~30 seconds for services to initialize
sleep 30

# Check status
docker-compose ps
```

### 4. Pull Recommended Models

```bash
# Primary CTI model (required)
docker exec -it agentic-cti-ollama ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysisv2

# Code analysis model (optional but recommended)
docker exec -it agentic-cti-ollama ollama pull qwen2.5-coder:14b-q4_K_M
```

### 5. Access the Platform

Open your browser:

| Service | URL | Credentials |
|---------|-----|-------------|
| **AgenticCTI UI** | http://localhost:8501 | admin / your-password |
| **NG-TIP Platform** | http://localhost:8504 | No auth (configure in UI) |
| **AgenticCTI API** | http://localhost:8000/docs | API Docs |
| **NG-TIP API** | http://localhost:8503/docs | API Docs |
| **Neo4j Browser** ⚙️ | http://localhost:7474 | neo4j / password (Full profile only) |

⚙️ = Only available in Full deployment profile

## 🎯 First Tasks

### Test the CTI Agent

```bash
# Run agent manually once
docker exec -it agentic-cti python main.py run

# Check logs
docker-compose logs -f agentic-cti
```

### Submit a URL for Analysis

```bash
# Submit CISA advisory
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.cisa.gov/news-events/cybersecurity-advisories",
    "options": {"extract_entities": true}
  }'

# Get job ID from response, then check status
curl http://localhost:8000/api/v1/jobs/{job_id}
```

### Query Intelligence via NG-TIP

```bash
# Search knowledge base
curl -X POST http://localhost:8503/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "latest ransomware campaigns", "top_k": 5}'

# Check platform health
curl http://localhost:8503/api/health
```

### Use the UI

1. **AgenticCTI UI** (http://localhost:8501):
   - View agent status and statistics
   - Trigger manual runs
   - Configure sources

2. **NG-TIP UI** (http://localhost:8504):
   - Search intelligence across all sources
   - Chat with AI assistant about threats
   - Visualize threat graphs
   - Explore STIX objects

3. **Neo4j Browser** (http://localhost:7474):
   - Explore threat entity relationships
   - Run Cypher queries
   - Visualize attack chains

## 📊 Verify Integration

### Check Data Flow

```bash
# 1. Run AgenticCTI agent
docker exec -it agentic-cti python main.py run

# 2. Check NG-TIP received data
curl http://localhost:8503/api/statistics

# 3. View in Neo4j
# Open http://localhost:7474 and run:
# MATCH (n) RETURN n LIMIT 25
```

### Expected Results

After running the agent once, you should see:
- ✅ Intelligence items in NG-TIP statistics
- ✅ Entities in Neo4j graph
- ✅ Documents in RAG knowledge base
- ✅ Logs showing successful push to NG-TIP

## 🔧 Troubleshooting

### Services Won't Start

```bash
# Check Docker resources
docker system df

# Restart services
docker-compose down
docker-compose up -d

# View specific service logs
docker-compose logs neo4j
docker-compose logs ngtip-api
```

### Model Download Failed

```bash
# Check Ollama service
docker exec -it agentic-cti-ollama ollama list

# Manually pull model
docker exec -it agentic-cti-ollama ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysisv2

# Check disk space
df -h
```

### NG-TIP Cannot Connect to Neo4j (Full Profile Only)

```bash
# Only applies if using Full profile

# Check Neo4j is running
docker-compose logs neo4j | grep "Started"

# Verify credentials match .env
docker exec -it ngtip-neo4j cypher-shell -u neo4j -p your-password "RETURN 1;"

# Restart NG-TIP services
docker-compose restart ngtip-api ngtip-ui
```

**If using Minimal/Standard profile**: Neo4j is intentionally disabled. This is normal - graph features will show as unavailable in NG-TIP.

### Agent Not Pushing to NG-TIP

```bash
# Check NG-TIP API is accessible
curl http://localhost:8503/api/health

# Verify NGTIP_ENABLED=true in .env
grep NGTIP_ENABLED .env

# Check agent logs for errors
docker-compose logs agentic-cti | grep -i ngtip
```

## 🔄 Upgrading Deployment Profiles

### Minimal → Standard (Add API Integrations)

No Docker changes needed - just add API keys to `.env`:

```bash
# Edit .env
VIRUSTOTAL_ENABLED=true
VIRUSTOTAL_API_KEY=your-virustotal-key

SPIDERFOOT_ENABLED=true
SPIDERFOOT_URL=http://localhost:5001

# Restart to apply changes
docker-compose restart
```

### Standard → Full (Add Graph Features)

Enable Neo4j for relationship visualization:

```bash
# Edit .env
NGTIP_NEO4J_ENABLED=true
NEO4J_PASSWORD=secure-password

# Restart with full profile
docker-compose down
docker-compose --profile full up -d
```

**Data is preserved** during upgrades - no intelligence lost!

## 📚 Next Steps

### 1. Configure CTI Sources

Edit `config/cti_sources.yaml` to add your preferred threat intelligence sources:

```yaml
sources:
  - name: "Your Custom Source"
    url: "https://your-source.com/feed"
    type: "rss"
    category: "custom"
    priority: high
    enabled: true
```

### 2. Set Up Email Notifications

In `.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_TO=recipient@example.com
EMAIL_DAILY_TIME=07:00
```

### 3. Configure Scheduled Runs

The agent runs daily by default. Customize in `.env`:
```bash
EMAIL_DAILY_TIME=07:00
EMAIL_TIMEZONE=America/Montreal
```

### 4. Explore Advanced Features

- **MCP Server**: Integrate with Claude Desktop ([NG-TIP/cti_genai_platform/MCP_SERVER.md](NG-TIP/cti_genai_platform/MCP_SERVER.md))
- **Custom Agents**: Create specialized analysis agents
- **STIX Export**: Push to Trend Vision One or OpenCTI
- **API Integration**: Build custom tools on the REST APIs

## 🎓 Learning Resources

### Documentation

- **Integration Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Complete integration documentation
- **Model Recommendations**: [docs/RECOMMENDED_MODELS.md](docs/RECOMMENDED_MODELS.md) - Optimized LLM models
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- **API Docs**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - REST API reference
- **Security**: [SECURITY.md](SECURITY.md) - Security best practices

### Example Queries

**Cypher (Neo4j)**:
```cypher
// Find all threat actors and their associated malware
MATCH (ta:ThreatActor)-[:USES]->(m:Malware)
RETURN ta.name, collect(m.name) AS malware

// Find IOCs related to a specific CVE
MATCH (cve:Vulnerability {name: 'CVE-2024-1234'})-[:EXPLOITS]-(ioc:Indicator)
RETURN ioc
```

**Python API**:
```python
import requests

# Submit URL for analysis
response = requests.post(
    'http://localhost:8000/api/v1/scrape',
    json={'url': 'https://example.com/threat-report'}
)
job_id = response.json()['job_id']

# Query NG-TIP
search = requests.post(
    'http://localhost:8503/api/rag/search',
    json={'query': 'APT28 campaigns', 'top_k': 5}
)
results = search.json()
```

## 💡 Pro Tips

1. **GPU Acceleration**: If you have an NVIDIA GPU, the specialized CTI models will run significantly faster
2. **Model Selection**: Use `cybersecuritythreatanalysisv2` for CTI, `qwen2.5-coder` for malware analysis
3. **Memory**: 16GB RAM recommended for optimal performance with multiple models
4. **Monitoring**: Check `docker-compose logs -f` regularly to catch issues early
5. **Backups**: Neo4j data is in Docker volumes - back up regularly with `docker volume backup`

## 🆘 Getting Help

- **Issues**: https://github.com/girdav01/AgenticCTI/issues
- **Documentation**: See docs/ folder
- **Community**: Check GitHub Discussions

## 🎉 Success Checklist

- [ ] All services running (`docker-compose ps` shows all healthy)
- [ ] Models downloaded (check with `ollama list`)
- [ ] Agent completed first run (check logs)
- [ ] NG-TIP showing statistics (check API)
- [ ] Neo4j has data (run MATCH query)
- [ ] UIs accessible (AgenticCTI and NG-TIP)

**Once all checked, you're ready to use AgenticCTI + NG-TIP for automated threat intelligence!**

---

**Total Setup Time**: ~10 minutes (plus model download time ~5-15 minutes depending on internet speed)

For detailed information, see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md).
