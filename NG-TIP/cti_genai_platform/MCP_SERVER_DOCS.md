# MCP Server Documentation

## Overview

The CTI Platform MCP (Model Context Protocol) server exposes all threat intelligence capabilities through a standardized interface that AI assistants like Claude can use directly. This enables Claude to query MISP, OpenCTI, the graph database, RAG knowledge base, and create/manage STIX objects.

## What is MCP?

**Model Context Protocol (MCP)** is Anthropic's open protocol that enables AI assistants to securely connect to external data sources and tools. Instead of building REST APIs, MCP provides a standardized way for Claude and other AI models to interact with your systems.

### Benefits of MCP over REST API

- **AI-Optimized**: Designed specifically for LLM interactions
- **Type-Safe**: Strong typing with JSON schemas
- **Standardized**: Works across all MCP-compatible clients
- **Secure**: Process-level isolation and controlled access
- **Real-Time**: Direct integration with Claude Desktop and API

## Installation

### 1. Install Dependencies

```bash
pip install mcp>=0.9.0
```

### 2. Configure Environment

Create `.env` file or set environment variables:

```bash
# LLM Configuration
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.2
export LLM_BASE_URL=http://localhost:11434

# MISP (optional)
export MISP_URL=https://your-misp-instance.com
export MISP_API_KEY=your-api-key

# OpenCTI (optional)
export OPENCTI_URL=http://localhost:8080
export OPENCTI_TOKEN=your-token

# Neo4j (optional)
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=password
```

### 3. Test MCP Server

```bash
# Run the server standalone
python mcp_server.py

# The server will start and wait for MCP client connections
```

## Claude Desktop Integration

### Setup Instructions

1. **Find Claude Desktop Config**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add CTI Platform Server**

```json
{
  "mcpServers": {
    "cti-platform": {
      "command": "python",
      "args": [
        "/absolute/path/to/cti_genai_platform/mcp_server.py"
      ],
      "env": {
        "LLM_PROVIDER": "ollama",
        "LLM_MODEL": "llama3.2",
        "LLM_BASE_URL": "http://localhost:11434",
        "MISP_URL": "https://your-misp.com",
        "MISP_API_KEY": "your-key",
        "OPENCTI_URL": "http://localhost:8080",
        "OPENCTI_TOKEN": "your-token",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Verify Connection**
   - Open Claude Desktop
   - Look for the 🔌 icon indicating MCP servers are connected
   - You should see "cti-platform" in the list

## Available MCP Tools

### 📚 RAG & Knowledge Base Tools

#### `search_threat_intelligence`
Search across all threat intelligence sources (MISP, OpenCTI, RAG knowledge base).

**Example:**
```
Search for information about APT28 campaigns targeting financial institutions
```

**Parameters:**
- `query` (required): Natural language search query
- `sources` (optional): Array of sources ["misp", "opencti", "rag", "all"]
- `limit` (optional): Maximum results per source (default: 10)

**Returns:** Results from all specified sources with event/indicator/document details

---

#### `query_knowledge_base`
Semantic search within the RAG knowledge base.

**Example:**
```
Query the knowledge base for Emotet malware TTPs
```

**Parameters:**
- `query` (required): Search query
- `top_k` (optional): Number of results (default: 5)

**Returns:** Relevant documents with similarity scores

---

#### `add_document_to_knowledge_base`
Add a threat report or analysis to the knowledge base.

**Example:**
```
Add this threat report to the knowledge base:
[report content]
```

**Parameters:**
- `content` (required): Document text
- `metadata` (optional): {source, date, tlp, title}

**Returns:** Success status and document IDs

---

### 🔍 MISP Integration Tools

#### `search_misp_events`
Search MISP events by keyword.

**Example:**
```
Search MISP for ransomware events from the last month
```

**Parameters:**
- `query` (required): Search term
- `published` (optional): Filter by published status
- `limit` (optional): Maximum results (default: 50)

**Returns:** Array of MISP events with attributes, tags, and metadata

---

#### `get_misp_event`
Get detailed information about a specific MISP event.

**Example:**
```
Get MISP event details for event ID 12345
```

**Parameters:**
- `event_id` (required): MISP event ID

**Returns:** Complete event details including all attributes, objects, and relationships

---

#### `search_misp_attributes`
Search for IOCs/attributes in MISP.

**Example:**
```
Search MISP for all SHA256 hashes related to Emotet
```

**Parameters:**
- `value` (optional): Attribute value
- `type` (optional): Attribute type (ip-src, domain, md5, sha256, etc.)
- `category` (optional): Attribute category
- `limit` (optional): Maximum results (default: 100)

**Returns:** Array of attributes/IOCs

---

### 🌐 OpenCTI Integration Tools

#### `search_opencti_indicators`
Search for indicators in OpenCTI.

**Example:**
```
Find all indicators related to APT29
```

**Parameters:**
- `search_term` (optional): Search term
- `indicator_types` (optional): Array of indicator types
- `limit` (optional): Maximum results (default: 50)

**Returns:** Array of indicators with patterns and metadata

---

#### `get_opencti_threat_actors`
Retrieve threat actor information from OpenCTI.

**Example:**
```
Get a list of all known threat actors from OpenCTI
```

**Parameters:**
- `limit` (optional): Maximum results (default: 50)

**Returns:** Array of threat actors with aliases, sophistication, and motivation

---

#### `get_opencti_malware`
Get malware information from OpenCTI.

**Example:**
```
Retrieve information about known malware families
```

**Parameters:**
- `limit` (optional): Maximum results (default: 50)

**Returns:** Array of malware with types and descriptions

---

#### `get_opencti_attack_patterns`
Get MITRE ATT&CK patterns from OpenCTI.

**Example:**
```
Get attack patterns used by APT groups
```

**Parameters:**
- `limit` (optional): Maximum results (default: 50)

**Returns:** Array of attack patterns with MITRE IDs and kill chain phases

---

### 🕸️ Graph Database Tools

#### `create_threat_actor`
Create a threat actor node in the graph.

**Example:**
```
Create a threat actor node for APT28 with aliases Fancy Bear and Sofacy
```

**Parameters:**
- `name` (required): Threat actor name
- `properties` (optional): {aliases, sophistication, motivation, etc.}

**Returns:** Success status

---

#### `create_malware`
Create a malware node in the graph.

**Example:**
```
Create a malware node for Emotet banking trojan
```

**Parameters:**
- `name` (required): Malware name
- `properties` (optional): {type, family, description, etc.}

**Returns:** Success status

---

#### `create_indicator`
Create an IOC node in the graph.

**Example:**
```
Create an indicator for IP address 192.168.1.100
```

**Parameters:**
- `value` (required): Indicator value
- `type` (required): Indicator type (ipv4-addr, domain-name, file, etc.)
- `properties` (optional): Additional metadata

**Returns:** Success status

---

#### `create_relationship`
Create a relationship between entities.

**Example:**
```
Create a relationship: APT28 USES Zebrocy malware
```

**Parameters:**
- `source_name` (required): Source entity name
- `source_type` (required): Source type (ThreatActor, Malware, etc.)
- `target_name` (required): Target entity name
- `target_type` (required): Target type
- `relationship_type` (required): Relationship (USES, TARGETS, ATTRIBUTED_TO)
- `properties` (optional): Relationship metadata

**Returns:** Success status

---

#### `query_graph_relationships`
Explore relationships for an entity.

**Example:**
```
Show me all relationships for APT28 up to 2 degrees of separation
```

**Parameters:**
- `entity_name` (required): Entity to explore
- `depth` (optional): Relationship depth 1-3 (default: 2)

**Returns:** Nodes and relationships in graph format

---

#### `search_graph_by_type`
Search for all nodes of a specific type.

**Example:**
```
List all malware in the graph database
```

**Parameters:**
- `node_type` (required): ThreatActor, Malware, Campaign, Indicator
- `limit` (optional): Maximum results (default: 50)

**Returns:** Array of nodes with properties

---

### 🎯 STIX Tools

#### `create_stix_indicator`
Create a STIX 2.1 indicator object.

**Example:**
```
Create a STIX indicator for malicious IP 10.0.0.1
```

**Parameters:**
- `pattern` (required): STIX pattern (e.g., "[ipv4-addr:value = '10.0.0.1']")
- `name` (required): Indicator name
- `indicator_type` (optional): Type (ipv4-addr, domain-name, etc.)
- `description` (optional): Description

**Returns:** STIX indicator object in JSON format

---

#### `create_stix_threat_actor`
Create a STIX 2.1 threat actor object.

**Example:**
```
Create a STIX threat actor for Lazarus Group
```

**Parameters:**
- `name` (required): Threat actor name
- `description` (optional): Description
- `aliases` (optional): Array of aliases
- `sophistication` (optional): Sophistication level

**Returns:** STIX threat actor object in JSON format

---

### 📊 System Tools

#### `get_platform_statistics`
Get statistics about the CTI platform.

**Example:**
```
Show me platform statistics and connection status
```

**Parameters:** None

**Returns:** Statistics for all components (RAG, MISP, OpenCTI, Graph DB)

---

## Usage Examples

### Example 1: Multi-Source Threat Research

**User:** "Search for all intelligence about Emotet malware across all sources"

**Claude will:**
1. Call `search_threat_intelligence` with query "Emotet malware"
2. Aggregate results from MISP, OpenCTI, and knowledge base
3. Provide comprehensive summary

---

### Example 2: Building Threat Actor Profile

**User:** "Create a comprehensive profile for APT28 including their tools and tactics"

**Claude will:**
1. Call `get_opencti_threat_actors` to get APT28 details
2. Call `query_graph_relationships` for APT28
3. Call `search_misp_events` for APT28 events
4. Call `get_opencti_attack_patterns` for their TTPs
5. Synthesize into comprehensive profile

---

### Example 3: Adding New Intelligence

**User:** "I have a new threat report about a ransomware campaign. Can you add it to the knowledge base and create the appropriate graph nodes?"

**Claude will:**
1. Call `add_document_to_knowledge_base` with report content
2. Extract threat actors, malware, and IOCs from report
3. Call `create_threat_actor`, `create_malware`, `create_indicator` as needed
4. Call `create_relationship` to link entities
5. Optionally create STIX objects with `create_stix_indicator`

---

### Example 4: IOC Lookup

**User:** "Is the IP address 192.168.1.100 in our threat intelligence?"

**Claude will:**
1. Call `search_misp_attributes` with value "192.168.1.100"
2. Call `search_opencti_indicators` with same value
3. Call `query_knowledge_base` for the IP
4. Report findings from all sources

---

### Example 5: Creating STIX Bundle

**User:** "Create a STIX bundle for a new campaign we discovered"

**Claude will:**
1. Call `create_stix_threat_actor` for the actor
2. Call `create_stix_indicator` for each IOC
3. Call `create_stix_malware` for malware used
4. Create relationships between objects
5. Return complete STIX bundle

---

## Advanced Usage

### Chaining Tools for Complex Analysis

Claude can automatically chain multiple tools together:

**User:** "Analyze the relationship between APT28 and their malware, then create STIX objects for everything"

**Workflow:**
1. `get_opencti_threat_actors` → Get APT28
2. `query_graph_relationships` → Get related malware
3. `get_opencti_malware` → Get malware details
4. `create_stix_threat_actor` → Create STIX for APT28
5. `create_stix_malware` → Create STIX for each malware
6. Return complete STIX bundle

---

### Automated Enrichment

**User:** "Enrich this IOC list with context from all our sources"

**Workflow:**
1. Parse IOC list
2. For each IOC:
   - `search_misp_attributes`
   - `search_opencti_indicators`
   - `query_knowledge_base`
3. Aggregate and format results

---

## Security Considerations

### Authentication
- MCP server runs locally with process-level isolation
- No network exposure by default
- Environment variables for sensitive credentials

### Access Control
- Server only accessible to local MCP clients
- Configure `.env` with appropriate API keys
- Limit Neo4j, MISP, OpenCTI access as needed

### Data Privacy
- All data processed locally
- No external API calls except configured TIPs
- RAG documents stored locally in ChromaDB

---

## Troubleshooting

### MCP Server Not Connecting

**Check:**
1. Python path is correct in `claude_desktop_config.json`
2. Environment variables are set
3. Dependencies installed: `pip install mcp>=0.9.0`
4. Claude Desktop restarted after config change

**Debug:**
```bash
# Run server standalone to see errors
python mcp_server.py
```

---

### Tool Errors

**Common Issues:**
1. **"MISP not configured"** → Set MISP_URL and MISP_API_KEY
2. **"Graph database not initialized"** → Check Neo4j is running
3. **"RAG engine not initialized"** → Check LLM configuration

**Check Platform Status:**
```
Ask Claude: "Get platform statistics"
```

---

### Performance Optimization

**For Large Deployments:**
1. Increase result limits in queries
2. Use specific sources in `search_threat_intelligence`
3. Limit graph depth to 1-2 for faster queries
4. Configure Neo4j with more memory

---

## Development

### Adding New Tools

1. **Define Tool** in `list_tools()`:
```python
Tool(
    name="my_new_tool",
    description="What it does",
    inputSchema={...}
)
```

2. **Implement Handler** in `_execute_tool()`:
```python
elif name == "my_new_tool":
    result = self._my_implementation(arguments)
    return result
```

3. **Test**:
```bash
python mcp_server.py
# Ask Claude to use the new tool
```

---

### Custom Integrations

Add new threat intelligence sources:

```python
# In CTIMCPServer.__init__
self.my_tip = MyTIPIntegration()

# Add tool definition and handler
Tool(name="search_my_tip", ...)
```

---

## API Reference

### Tool Response Format

All tools return JSON with this structure:

```json
{
  "results": [...],      // Main results
  "count": 10,           // Number of results
  "query": "...",        // Original query
  "timestamp": "...",    // When executed
  "error": "..."         // Error message if failed
}
```

### Error Handling

Errors return:
```json
{
  "error": "Error message",
  "tool": "tool_name",
  "arguments": {...}
}
```

---

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/cti-mcp.service`:

```ini
[Unit]
Description=CTI Platform MCP Server
After=network.target

[Service]
Type=simple
User=cti
WorkingDirectory=/opt/cti_genai_platform
Environment="LLM_PROVIDER=ollama"
Environment="LLM_MODEL=llama3.2"
ExecStart=/usr/bin/python3 mcp_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable cti-mcp
sudo systemctl start cti-mcp
```

---

## Support

For issues:
1. Check logs in `./logs`
2. Verify environment variables
3. Test components individually
4. Check GitHub issues

---

**The MCP server makes your CTI platform a first-class citizen in Claude's ecosystem!** 🎯
