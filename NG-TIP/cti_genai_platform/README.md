# Next-Gen Cyber Threat Intelligence Platform

🛡️ **A GenAI-powered CTI platform with RAG, MISP & OpenCTI integration, STIX 2.1 support, and graph-based threat analysis**

## 🌟 NEW: MCP Server Integration! 🔌

**Use Claude directly with your CTI platform!** The platform now includes a Model Context Protocol (MCP) server that exposes all 20 threat intelligence tools to Claude Desktop and other MCP clients.

**Quick Start with MCP:**
1. Configure Claude Desktop with one JSON config
2. Ask Claude to search MISP, OpenCTI, or your knowledge base
3. Create STIX objects, build graphs, and analyze threats - all through natural language!

See [MCP_SERVER_DOCS.md](MCP_SERVER_DOCS.md) for complete documentation.

---

## 🌟 Features

### 🤖 GenAI Powered Intelligence
- **Multi-LLM Support**: Ollama, LM Studio, OpenAI, Anthropic Claude
- **Local LLM Ready**: Run entirely on-premises with Ollama or LM Studio
- **RAG-Enhanced**: Retrieval-Augmented Generation for accurate, context-aware responses
- **Natural Language Queries**: Ask questions in plain English about threats, campaigns, and IOCs
- **MCP Server**: Direct integration with Claude Desktop through Model Context Protocol

### 🔌 MCP (Model Context Protocol) Server
- **20 Threat Intelligence Tools**: Exposed through standardized MCP interface
- **Claude Desktop Integration**: Use Claude to query MISP, OpenCTI, graphs, and RAG
- **CRUD Operations**: Create, read, update entities across all platforms
- **Natural Language**: No API knowledge needed - just ask Claude
- **Real-Time Access**: Direct connection to all CTI data sources

### 🔗 Comprehensive Integrations
- **MISP Integration**: Full API integration with MISP threat intelligence platform
- **OpenCTI Integration**: GraphQL-based integration with OpenCTI
- **STIX 2.1 Support**: Native support for STIX 2.1 objects and bundles
- **Graph Database**: Neo4j-based relationship mapping and threat actor tracking

### 📊 Advanced Analytics
- **Threat Graph Explorer**: Visualize relationships between actors, malware, campaigns
- **Multi-Source Intelligence**: Correlate data from MISP, OpenCTI, and local knowledge base
- **Semantic Search**: Find relevant threats using meaning, not just keywords
- **AI-Powered Summaries**: Automated threat report generation

### 🔒 Enterprise Ready
- **On-Premises Deployment**: Run entirely in air-gapped environments
- **Flexible Architecture**: Modular design for easy customization
- **Vector Storage**: Efficient document indexing and retrieval
- **STIX Import/Export**: Standard-compliant threat intelligence exchange

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web Interface                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Intelligence │  │ AI Assistant │  │ Threat Graph │      │
│  │   Search     │  │              │  │   Explorer   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  LLM Handler │  │  RAG Engine  │  │ Graph Manager│      │
│  │              │  │              │  │              │      │
│  │ • Ollama     │  │ • ChromaDB   │  │ • Neo4j      │      │
│  │ • LM Studio  │  │ • Embeddings │  │ • Cypher     │      │
│  │ • OpenAI     │  │ • Retrieval  │  │ • Viz        │      │
│  │ • Anthropic  │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     MISP     │  │   OpenCTI    │  │    STIX      │      │
│  │ Integration  │  │ Integration  │  │  Processor   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Ollama or LM Studio (for local LLM)
- Neo4j (optional, for graph features)
- MISP instance (optional)
- OpenCTI instance (optional)

### Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd cti_genai_platform
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up local LLM (Ollama example)**
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.2
```

5. **Optional: Set up Neo4j**
```bash
# Using Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### Running the Application

```bash
streamlit run app.py
```

Access the platform at `http://localhost:8501`

## 🔌 MCP Server Setup (Claude Desktop Integration)

### Quick Setup

1. **Install MCP dependencies**
```bash
pip install mcp>=0.9.0
```

2. **Configure Claude Desktop**

Edit your Claude Desktop config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:
```json
{
  "mcpServers": {
    "cti-platform": {
      "command": "python",
      "args": ["/absolute/path/to/cti_genai_platform/mcp_server.py"],
      "env": {
        "LLM_PROVIDER": "ollama",
        "LLM_MODEL": "llama3.2",
        "LLM_BASE_URL": "http://localhost:11434"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Start using it!**
```
Ask Claude: "Search for APT28 campaigns across all threat intel sources"
Ask Claude: "Create a STIX bundle for this new malware campaign"
Ask Claude: "What are the relationships between APT29 and their malware?"
```

**Complete MCP Documentation:** [MCP_SERVER_DOCS.md](MCP_SERVER_DOCS.md)  
**Quick Reference:** [MCP_QUICK_REFERENCE.md](MCP_QUICK_REFERENCE.md)

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```bash
# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_BASE_URL=http://localhost:11434

# MISP Configuration (optional)
MISP_URL=https://your-misp-instance.com
MISP_API_KEY=your-api-key

# OpenCTI Configuration (optional)
OPENCTI_URL=http://localhost:8080
OPENCTI_TOKEN=your-token

# Neo4j Configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### UI Configuration

Configure all settings through the sidebar in the web interface:

1. **LLM Provider**: Select and configure your LLM
2. **MISP**: Enable and configure MISP integration
3. **OpenCTI**: Enable and configure OpenCTI integration
4. **Initialize**: Click "Initialize Platform" to start

## 📖 Usage Guide

### 1. Intelligence Search

Search across all connected sources using natural language:

```
"What are the latest APT campaigns targeting financial institutions?"
"Find all IOCs related to Emotet malware"
"Show me threat actors using spear phishing"
```

### 2. AI Assistant

Chat with the AI for threat analysis:

```
User: "Analyze the latest ransomware trends"
AI: "Based on recent intelligence from MISP and OpenCTI..."

User: "What TTPs does APT28 typically use?"
AI: "APT28 (Fancy Bear) commonly employs the following tactics..."
```

### 3. Threat Graph Explorer

Visualize relationships:
- Select entity type (Threat Actor, Malware, Campaign)
- Enter entity name
- Explore connections up to 3 degrees

### 4. STIX Management

- **Import**: Upload STIX bundles from MISP/OpenCTI
- **Create**: Generate new STIX objects
- **Export**: Share intelligence in STIX format

### 5. Data Management

- **Ingest**: Add threat reports to knowledge base
- **Sync**: Pull latest data from MISP/OpenCTI
- **Index**: Build searchable document database

## 🔧 Advanced Usage

### Using Different LLM Providers

#### Ollama (Local)
```python
# Sidebar configuration
Provider: ollama
Base URL: http://localhost:11434
Model: llama3.2, mistral, codellama
```

#### LM Studio (Local)
```python
# Sidebar configuration
Provider: lmstudio
Base URL: http://localhost:1234/v1
Model: local-model
```

#### OpenAI
```python
# Sidebar configuration
Provider: openai
API Key: sk-...
Model: gpt-4, gpt-3.5-turbo
```

#### Anthropic Claude
```python
# Sidebar configuration
Provider: anthropic
API Key: sk-ant-...
Model: claude-3-opus, claude-3-sonnet
```

### Custom RAG Document Ingestion

```python
from modules.rag_engine import RAGEngine
from modules.llm_handler import LLMHandler

# Initialize
llm = LLMHandler(provider="ollama", model="llama3.2")
rag = RAGEngine(llm_handler=llm)

# Add documents
rag.add_document(
    content="Threat report content...",
    metadata={
        "source": "ACME Threat Intel",
        "date": "2024-01-15",
        "tlp": "AMBER"
    }
)

# Search
results = rag.search("APT campaigns", top_k=5)
```

### Graph Database Queries

```python
from modules.graph_manager import GraphManager

graph = GraphManager(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# Create threat actor
graph.create_threat_actor(
    name="APT28",
    properties={
        "aliases": ["Fancy Bear", "Sofacy"],
        "sophistication": "high",
        "motivation": "espionage"
    }
)

# Create relationship
graph.create_relationship(
    source_name="APT28",
    source_type="ThreatActor",
    target_name="Zebrocy",
    target_type="Malware",
    relationship_type="USES"
)

# Query relationships
results = graph.get_entity_relationships("APT28", depth=2)
```

### STIX Object Creation

```python
from modules.stix_processor import STIXProcessor

stix = STIXProcessor()

# Create indicator
indicator = stix.create_indicator(
    pattern="[ipv4-addr:value = '192.168.1.1']",
    name="Malicious C2 IP",
    indicator_type="ipv4-addr",
    description="Known C2 server for APT28"
)

# Create bundle
bundle = stix.create_bundle([indicator])
```

## 🔒 Security Considerations

### Air-Gapped Deployment

The platform can run completely offline:

1. **Local LLM**: Use Ollama or LM Studio
2. **Local Vector Store**: ChromaDB runs locally
3. **Local Graph DB**: Neo4j runs locally
4. **No External APIs**: Disable cloud LLM providers

### Data Privacy

- All data stored locally by default
- MISP/OpenCTI connections over HTTPS
- API keys stored in environment variables
- TLS support for Neo4j connections

## 🛠️ Development

### Project Structure

```
cti_genai_platform/
├── app.py                          # Main Streamlit application
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── modules/
│   ├── __init__.py
│   ├── llm_handler.py             # Multi-LLM provider support
│   ├── rag_engine.py              # RAG and vector search
│   ├── misp_integration.py        # MISP API client
│   ├── opencti_integration.py     # OpenCTI GraphQL client
│   ├── graph_manager.py           # Neo4j graph operations
│   └── stix_processor.py          # STIX 2.1 handling
├── data/
│   └── vector_store/              # ChromaDB storage
└── README.md
```

### Adding New Features

1. Create new module in `modules/`
2. Update `modules/__init__.py`
3. Add to main app in `app.py`
4. Update documentation

## 📊 Example Queries

### Intelligence Search
- "Find all malware used by APT29 in the last 6 months"
- "What are the common TTPs in recent ransomware attacks?"
- "Show me all IOCs related to the SolarWinds compromise"

### AI Assistant
- "Summarize the tactics used by Lazarus Group"
- "Compare APT28 and APT29 attack patterns"
- "What are the key indicators for detecting Cobalt Strike?"

### Graph Queries
- "Show me all relationships for the Emotet malware"
- "Map the infrastructure used by FIN7"
- "Display the attack chain for APT1"

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional TIP integrations (TAXII, etc.)
- More visualization options
- Enhanced graph algorithms
- Additional LLM providers
- Automated threat hunting workflows

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- MISP Project
- OpenCTI Platform
- OASIS STIX
- Ollama
- LM Studio
- ChromaDB
- Neo4j

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Contact: [your-email]

## 🗺️ Roadmap

- [ ] TAXII 2.1 support
- [ ] Automated threat hunting
- [ ] Custom detection rule generation
- [ ] Integration with SIEM platforms
- [ ] Mobile app interface
- [ ] Multi-tenant support
- [ ] Advanced graph visualizations
- [ ] Machine learning-based threat scoring
- [ ] Report generation and export
- [ ] REST API for external integrations

---

**Built with ❤️ for the cybersecurity community**
