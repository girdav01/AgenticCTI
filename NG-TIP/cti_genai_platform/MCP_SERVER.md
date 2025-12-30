# MCP Server for CTI Platform

The CTI GenAI Platform includes a **Model Context Protocol (MCP) server** that exposes threat intelligence data and operations to AI assistants like Claude Desktop.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that standardizes how AI applications connect to data sources. The CTI platform's MCP server allows Claude Desktop (and other MCP clients) to:

- Query threat intelligence data
- Create/Update/Delete threat entities
- Search across MISP, OpenCTI, and knowledge base
- Analyze threats with AI
- Manage STIX objects
- Access graph relationships

## Features

### 📖 Resources (Read-Only Data)
- `cti://threats/recent` - Recent threats from all sources
- `cti://indicators/latest` - Latest IOCs
- `cti://actors/active` - Active threat actors
- `cti://campaigns/ongoing` - Ongoing campaigns
- `cti://malware/trending` - Trending malware
- `cti://knowledge/documents` - Knowledge base stats
- `cti://misp/events` - MISP events (if configured)
- `cti://opencti/reports` - OpenCTI reports (if configured)

### 🛠️ Tools (Operations)

**Query Tools:**
- `search_threats` - Search across all sources
- `analyze_threat` - AI-powered threat analysis
- `get_entity` - Get entity details
- `get_relationships` - Get graph relationships

**CRUD Tools - Create:**
- `create_indicator` - Create new IOC
- `create_threat_actor` - Create new threat actor
- `create_malware` - Create new malware entity
- `create_campaign` - Create new campaign

**CRUD Tools - Update:**
- `update_entity` - Update entity properties
- `create_relationship` - Link entities

**CRUD Tools - Delete:**
- `delete_entity` - Remove entity

**Knowledge Base:**
- `add_document` - Add threat intel document
- `query_knowledge` - Query RAG knowledge base

**STIX Operations:**
- `import_stix_bundle` - Import STIX 2.1 bundle
- `export_stix_bundle` - Export as STIX bundle

## Installation & Setup

### 1. Install MCP SDK

```bash
pip install mcp
```

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the CTI server:

```json
{
  "mcpServers": {
    "cti-platform": {
      "command": "python",
      "args": ["/path/to/cti_genai_platform/mcp_server.py"],
      "env": {
        "LLM_PROVIDER": "ollama",
        "LLM_MODEL": "llama3.2",
        "LLM_BASE_URL": "http://localhost:11434",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

The CTI platform resources and tools will now be available in Claude Desktop!

## Usage Examples

### Example 1: Search for Threats

In Claude Desktop:
```
Search the CTI platform for recent APT campaigns targeting financial institutions
```

Claude will use the `search_threats` tool to query your threat intelligence sources.

### Example 2: Create a Threat Actor

```
Create a new threat actor in the CTI platform:
- Name: APT999
- Description: Advanced persistent threat targeting healthcare
- Aliases: MedicalMenace, HealthHacker
- Sophistication: advanced
```

Claude will use the `create_threat_actor` tool.

### Example 3: Analyze a Malware

```
Give me a full analysis of Emotet malware using the CTI platform
```

Claude will use the `analyze_threat` tool with the knowledge base.

### Example 4: Access Resources

```
Show me the latest indicators from the CTI platform
```

Claude will read from the `cti://indicators/latest` resource.

### Example 5: Create Relationships

```
Create a relationship in the CTI platform showing that APT28 uses Zebrocy malware
```

Claude will use the `create_relationship` tool.

## Running the Server Standalone

You can also run the MCP server standalone for testing:

```bash
# Set environment variables
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.2
export NEO4J_URI=bolt://localhost:7687

# Run server
python mcp_server.py
```

The server communicates over stdin/stdout using the MCP protocol.

## Configuration Options

Set these environment variables before starting the server:

```bash
# LLM Configuration
LLM_PROVIDER=ollama          # ollama, lmstudio, openai, anthropic
LLM_MODEL=llama3.2           # Model name
LLM_BASE_URL=http://localhost:11434  # For local LLMs
LLM_API_KEY=                 # API key for cloud providers

# MISP (optional)
MISP_URL=https://misp.local
MISP_API_KEY=your-key

# OpenCTI (optional)
OPENCTI_URL=http://localhost:8080
OPENCTI_TOKEN=your-token

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Vector Store
VECTOR_STORE_PATH=./data/vector_store
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Tool Examples

### Search Threats

```json
{
  "query": "ransomware attacks 2024",
  "sources": ["all"],
  "limit": 10
}
```

### Create Indicator

```json
{
  "pattern": "[ipv4-addr:value = '192.168.1.100']",
  "name": "Malicious C2 Server",
  "indicator_type": "ipv4-addr",
  "description": "Known command and control server",
  "labels": ["malicious-activity", "c2"]
}
```

### Analyze Threat

```json
{
  "threat_name": "APT28",
  "analysis_type": "ttps"
}
```

### Add Document to Knowledge Base

```json
{
  "content": "Full text of threat report...",
  "title": "Q4 2024 Threat Intelligence Report",
  "source": "ACME Security",
  "tlp": "AMBER"
}
```

### Query Knowledge Base

```json
{
  "query": "What are the main TTPs used by ransomware gangs?",
  "top_k": 5
}
```

## Advanced Usage

### Custom Prompts in Claude Desktop

You can guide Claude to use specific tools:

```
Using the CTI platform:
1. Search for threats related to "Cobalt Strike"
2. For each threat found, get its relationships
3. Create a summary report
```

### Batch Operations

```
Create these threat actors in the CTI platform:
1. APT40 (Chinese, espionage)
2. Lazarus Group (North Korean, financial)
3. FIN7 (Cybercrime, retail targeting)

Then link them to their known malware families
```

## Troubleshooting

### Server not appearing in Claude Desktop

1. Check configuration path is correct
2. Verify JSON syntax in config file
3. Restart Claude Desktop
4. Check Claude Desktop logs

### Connection Errors

1. Ensure environment variables are set
2. Verify Neo4j is running (if using graph features)
3. Check Ollama/LLM is accessible
4. Review server logs

### Tool Execution Fails

1. Verify required services are running
2. Check API keys/credentials
3. Ensure data directories exist
4. Review error messages in response

## Security Notes

- MCP server runs locally with your credentials
- Only accessible to MCP clients on same machine
- Environment variables should be kept secure
- Use .env files, not hardcoded values
- TLP levels are preserved in knowledge base

## Architecture

```
┌─────────────────┐
│ Claude Desktop  │
└────────┬────────┘
         │ MCP Protocol
         │ (stdio)
         ▼
┌─────────────────┐
│   MCP Server    │
│  (mcp_server.py)│
└────────┬────────┘
         │
    ┌────┴─────┬─────────┬─────────┐
    │          │         │         │
    ▼          ▼         ▼         ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
│ LLM  │  │ RAG  │  │Graph │  │ MISP │
└──────┘  └──────┘  └──────┘  └──────┘
```

## Next Steps

1. Configure Claude Desktop with the MCP server
2. Test basic queries ("Show me recent threats")
3. Try creating entities
4. Build workflows combining multiple tools
5. Integrate with your existing TI processes

## Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [Claude Desktop](https://claude.ai/download)
- CTI Platform README
- STIX 2.1 Specification

---

**The MCP server brings the power of your CTI platform directly into your AI assistant!** 🚀
