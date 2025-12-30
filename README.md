# 🛡️ AgenticCTI - Autonomous Cyber Threat Intelligence Platform

A modular, agentic Python application with full LLM autonomy for cyber threat intelligence (CTI) scanning, summarization, and export. AgenticCTI autonomously discovers CTI sources, extracts entities (TTPs, CVEs, IOCs, actors), generates actionable summaries, exports to STIX 2.1, and sends daily reports.

**🎯 NEW**: Now integrated with **NG-TIP** (Next-Gen Threat Intelligence Platform) for advanced storage, graph-based analysis, RAG-powered search, and AI-assisted threat analysis. See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for complete integration documentation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-enabled-brightgreen.svg)](https://www.docker.com/)

## ✨ Features

### 🤖 LLM Agent Autonomy
- **Multi-step agent loop** automates daily web scraping, CTI summarization, STIX export, and notification workflows
- **Autonomous source discovery** adapts feeds via configuration and discovers new CTI sources
- **Local LLM integration** (Ollama, OpenAI, Anthropic) extracts entities and generates actionable summaries
- **Entity extraction**: TTPs, CVEs, IOCs, threat actors, malware, campaigns, and more

### 📧 Reporting & Notifications
- **Daily summary emails** at configurable time (default: 07:00 AM America/Montreal)
- **Secure SMTP integration** with dynamic configuration
- **Rich HTML and plain text** email formats
- **Comprehensive logging** of all email activities and delivery status

### 📊 STIX 2.1 Export & Integration
- **STIX 2.1 compliant** export of all extracted entities
- **NG-TIP Platform** integration with graph database, RAG, and AI analysis
- **Trend Vision One** integration via STIX API
- **OpenCTI** integration via GraphQL/REST
- **HexStrike AI** integration for automated security analysis of discovered IOCs
- **Configurable endpoints** and TLP markings

### 🖥️ Streamlit UI
- **Interactive dashboard** showing agent status and statistics
- **Daily summary reports** with visualizations
- **Manual agent run** capability
- **MCP configuration page** for tools, endpoints, and schedules
- **Logs and history** viewing
- **Secure authentication** for sensitive operations

### 🔒 Security & Best Practices
- **Input validation** and data sanitization
- **Secrets management** via environment variables
- **No hardcoded credentials**
- **Comprehensive error handling** and retry mechanisms
- **Rate limiting** and respectful web scraping

### 📦 Deployment
- **Production-ready Dockerfile** with multi-stage build
- **Docker Compose** for complete stack deployment
- **Health checks** and monitoring
- **Non-root container** execution
- **MIT licensed** open-source

## 🏗️ Architecture

```
AgenticCTI/
├── agents/              # Autonomous agent orchestration
│   └── cti_agent.py    # Main CTI agent
├── parsers/            # Web scraping and entity extraction
│   ├── web_scraper.py
│   ├── source_discovery.py
│   └── entity_extractor.py
├── exporters/          # STIX export and platform integrations
│   ├── stix_exporter.py
│   ├── trend_vision_one.py
│   └── opencti_client.py
├── llm/                # LLM provider abstraction
│   ├── base.py
│   ├── ollama_provider.py
│   ├── openai_provider.py
│   └── factory.py
├── mcp/                # Model Context Protocol (config & scheduling)
│   ├── email_notifier.py
│   └── scheduler.py
├── ui/                 # Streamlit user interface
│   └── streamlit_app.py
├── utils/              # Common utilities
│   └── logging_config.py
├── config/             # Configuration files
│   ├── config.yaml
│   └── cti_sources.yaml
├── main.py             # Application entry point
├── Dockerfile          # Production Docker image
├── docker-compose.yml  # Complete stack deployment
└── requirements.txt    # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for containerized deployment)
- 16GB+ RAM recommended (for optimal LLM performance with specialized CTI models)
- NVIDIA GPU recommended (RTX 4070 Ti Super or equivalent for best performance)
- Ollama (for local LLM) or API keys for OpenAI/Anthropic

**💡 Recommended Models**: For optimal CTI analysis, we recommend specialized models like `ALIENTELLIGENCE/cybersecuritythreatanalysisv2` for threat intelligence and `qwen2.5-coder:14b` for malware analysis. See [docs/RECOMMENDED_MODELS.md](docs/RECOMMENDED_MODELS.md) for complete hardware-optimized model recommendations.

### Installation

#### Option 1: Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AgenticCTI.git
cd AgenticCTI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the application
python main.py schedule  # Start scheduler
python main.py run       # Run once
python main.py ui        # Start Streamlit UI
```

#### Option 2: Docker Deployment

```bash
# Clone the repository
git clone https://github.com/yourusername/AgenticCTI.git
cd AgenticCTI

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Access Streamlit UI
# Main agent: http://localhost:8501
# UI only: http://localhost:8502
```

### Configuration

#### Environment Variables (.env)

Key configuration options:

```bash
# LLM Provider (recommended CTI-optimized model)
LLM_PROVIDER=ollama  # Options: ollama, openai, anthropic
LLM_MODEL=ALIENTELLIGENCE/cybersecuritythreatanalysisv2  # Recommended for CTI
# Alternative: LLM_MODEL=llama3.2:latest  # General purpose
# Alternative: LLM_MODEL=qwen2.5-coder:14b-q4_K_M  # For malware/code analysis
LLM_BASE_URL=http://localhost:11434

# Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@example.com
EMAIL_TO=recipient@example.com
EMAIL_DAILY_TIME=07:00
EMAIL_TIMEZONE=America/Montreal

# STIX Export
ENABLE_STIX_EXPORT=true
STIX_EXPORT_PATH=./data/stix_exports

# Trend Vision One (optional)
TREND_VISION_ONE_ENABLED=false
TREND_VISION_ONE_API_KEY=your-api-key
TREND_VISION_ONE_REGION=us

# OpenCTI (optional)
OPENCTI_ENABLED=false
OPENCTI_URL=http://localhost:8080
OPENCTI_API_KEY=your-api-key

# Streamlit UI
STREAMLIT_AUTH_ENABLED=true
STREAMLIT_USERNAME=admin
STREAMLIT_PASSWORD=changeme  # Change this!
```

#### CTI Sources (config/cti_sources.yaml)

Add or modify CTI sources:

```yaml
sources:
  - name: "CISA Advisories"
    url: "https://www.cisa.gov/news-events/cybersecurity-advisories"
    type: "rss"
    category: "government"
    priority: high
    enabled: true
  # Add more sources...
```

## 📖 Usage

### Running the Agent

#### Manual Run
```bash
python main.py run
```

#### Scheduled Runs
```bash
python main.py schedule
```

#### Streamlit UI
```bash
python main.py ui
# Access at http://localhost:8501
```

### Using the Streamlit UI

1. **Login**: Use credentials from `.env` (default: admin/changeme)
2. **Dashboard**: View agent status, source statistics, and recent intelligence
3. **Daily Reports**: Generate and export daily CTI summaries
4. **Manual Run**: Trigger agent execution with custom parameters
5. **MCP Config**: Configure email, STIX export, scheduling, and sources
6. **Logs & History**: View application logs and activity history

### API Integration

#### STIX Export Example

```python
from exporters import STIXExporter, TrendVisionOneClient
from parsers import EntityExtractor

# Initialize
exporter = STIXExporter()
extractor = EntityExtractor()

# Extract entities
entities = extractor.extract_entities(text, title)

# Export to STIX
bundle = exporter.export_entities(
    entities=entities,
    source_url=url,
    title=title
)

# Save bundle
filepath = exporter.save_bundle(bundle)

# Upload to Trend Vision One
tvo_client = TrendVisionOneClient(api_key="your-key", region="us")
result = tvo_client.upload_stix_bundle(bundle)
```

## 🛠️ Development

### Project Structure

- **agents/**: Autonomous agent orchestration and workflow
- **parsers/**: Web scraping, source discovery, entity extraction
- **exporters/**: STIX export and CTI platform integrations
- **llm/**: LLM provider abstraction (Ollama, OpenAI, etc.)
- **mcp/**: Email notifications and task scheduling
- **ui/**: Streamlit user interface
- **utils/**: Logging and common utilities

### Adding New LLM Providers

1. Create provider class in `llm/` extending `BaseLLM`
2. Implement `generate()` and `generate_with_system()` methods
3. Update `LLMFactory` in `llm/factory.py`

### Adding New CTI Sources

Edit `config/cti_sources.yaml`:

```yaml
sources:
  - name: "Your Source"
    url: "https://example.com"
    type: "web"  # or 'rss', 'api'
    category: "news"
    priority: medium
    enabled: true
```

### Extending Entity Extraction

Modify `parsers/entity_extractor.py` to add new entity types or improve extraction logic.

## 🔧 Troubleshooting

### Common Issues

**LLM Connection Failed**
- Verify Ollama is running: `ollama list`
- Check `LLM_BASE_URL` in `.env`
- For OpenAI/Anthropic, verify API keys

**Email Not Sending**
- Verify SMTP credentials
- For Gmail, use [App Passwords](https://support.google.com/accounts/answer/185833)
- Check firewall/network restrictions

**STIX Export Errors**
- Ensure `stix2` package is installed: `pip install stix2`
- Check write permissions on export directory

**Docker Issues**
- Ensure Docker daemon is running
- Check port availability (8501, 11434)
- View logs: `docker-compose logs -f`

## 📊 Logging

Logs are written to `./logs/agentic_cti.log` with rotation:

```python
# Configure in .env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=./logs/agentic_cti.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5
```

View logs:
```bash
# Local
tail -f logs/agentic_cti.log

# Docker
docker-compose logs -f agentic-cti
```

## 🔒 Security Considerations

- **Never commit `.env`** file with real credentials
- **Change default passwords** in production
- **Use HTTPS** for API endpoints
- **Validate all inputs** from external sources
- **Keep dependencies updated**: `pip install -U -r requirements.txt`
- **Review CTI sources** before enabling
- **Monitor API rate limits** to avoid service disruptions

See [SECURITY.md](SECURITY.md) for detailed security guidelines.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [STIX 2.1](https://oasis-open.github.io/cti-documentation/) for threat intelligence standardization
- [Ollama](https://ollama.ai/) for local LLM inference
- [Streamlit](https://streamlit.io/) for rapid UI development
- The cybersecurity community for CTI sources and best practices

## 📧 Contact

For questions, issues, or suggestions:
- **Issues**: [GitHub Issues](https://github.com/yourusername/AgenticCTI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/AgenticCTI/discussions)

---

**Disclaimer**: This tool is for authorized security research and defensive purposes only. Always obtain proper authorization before scanning or monitoring systems you don't own.
