# Quick Start Guide

Get up and running with the CTI GenAI Platform in 5 minutes!

## Prerequisites

- Python 3.9+ installed
- Git installed
- (Optional) Ollama or LM Studio for local LLM

## Installation

### Option 1: Quick Setup Script (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd cti_genai_platform

# Run setup script
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Run the application
streamlit run app.py
```

### Option 2: Manual Setup

```bash
# Clone and navigate
git clone <repo-url>
cd cti_genai_platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data/vector_store cache logs

# Copy environment template
cp .env.example .env

# Run the application
streamlit run app.py
```

### Option 3: Docker

```bash
# Clone the repository
git clone <repo-url>
cd cti_genai_platform

# Copy environment template
cp .env.example .env

# Start services
docker-compose up -d

# Access at http://localhost:8501
```

## First-Time Configuration

1. **Open the application** at `http://localhost:8501`

2. **Configure LLM Provider** (Sidebar):
   - Select Provider: `ollama`
   - Base URL: `http://localhost:11434`
   - Model: `llama3.2`

3. **Click "Initialize Platform"**

4. **Start using the platform!**

## Quick Examples

### Example 1: Simple Intelligence Query

1. Go to "Intelligence Search" tab
2. Enter: `latest ransomware campaigns`
3. Click Search

### Example 2: Chat with AI

1. Go to "AI Assistant" tab
2. Ask: `What are the key indicators of Emotet malware?`
3. Get AI-powered response

### Example 3: Add Knowledge to RAG

1. Go to "Data Management" tab
2. Select "Knowledge Base" sub-tab
3. Upload a threat report PDF
4. Click "Index Document"

## Setting Up Ollama (Local LLM)

### Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai
```

### Download a Model

```bash
# Start Ollama
ollama serve

# In another terminal, pull a model
ollama pull llama3.2      # 2B parameter model, fast
ollama pull mistral       # 7B parameter model, balanced
ollama pull llama2        # Alternative model
```

### Test Ollama

```bash
ollama run llama3.2 "Hello, how are you?"
```

## Setting Up LM Studio (Alternative Local LLM)

1. Download LM Studio from https://lmstudio.ai
2. Install and open LM Studio
3. Download a model (e.g., TheBloke models)
4. Start the local server
5. Configure platform to use `lmstudio` provider

## Optional: Set Up Neo4j Graph Database

### Using Docker

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### Access Neo4j Browser
- URL: http://localhost:7474
- Username: neo4j
- Password: password

## Connecting to MISP

If you have a MISP instance:

1. Configure in sidebar:
   - Enable MISP checkbox
   - MISP URL: `https://your-misp-instance.com`
   - API Key: `your-api-key`
   
2. Click "Initialize Platform"

3. Go to "Data Management" > "Sync TIPs"

4. Click "Sync MISP Events"

## Connecting to OpenCTI

If you have an OpenCTI instance:

1. Configure in sidebar:
   - Enable OpenCTI checkbox
   - URL: `http://localhost:8080`
   - Token: `your-token`
   
2. Click "Initialize Platform"

3. Search OpenCTI data from Intelligence Search

## Common Issues & Solutions

### Issue: "LLM not available"
**Solution**: Make sure Ollama is running (`ollama serve`)

### Issue: "Connection refused to Ollama"
**Solution**: Check Ollama URL is `http://localhost:11434`

### Issue: "Neo4j connection failed"
**Solution**: Ensure Neo4j is running and credentials are correct

### Issue: "Out of memory"
**Solution**: Use smaller models (llama3.2 instead of mistral)

## Next Steps

1. **Add Threat Intelligence**: Upload reports to knowledge base
2. **Connect TIPs**: Link MISP/OpenCTI for live data
3. **Explore Graph**: Visualize threat relationships
4. **Create STIX**: Generate standard threat intelligence

## Recommended Workflow

```
Day 1: Set up platform + local LLM
Day 2: Add your first threat reports to RAG
Day 3: Connect MISP/OpenCTI (if available)
Day 4: Explore graph relationships
Day 5: Start using AI assistant for analysis
```

## Support

- Check README.md for detailed documentation
- Review example queries in README
- Check logs in `./logs` directory

## Pro Tips

1. **Local Models**: Start with `llama3.2` (fast) or `mistral` (balanced)
2. **Cloud Models**: Use GPT-4 or Claude for complex analysis
3. **Graph Database**: Essential for relationship mapping
4. **RAG Knowledge**: Add your organization's reports
5. **Hybrid Search**: Combine keyword and semantic search

---

Happy threat hunting! 🛡️
