# MCP Server Integration

## 🔌 Model Context Protocol (MCP) Support

The CTI platform includes a **full-featured MCP server** that integrates with Claude Desktop and other MCP clients!

### What is MCP?

MCP (Model Context Protocol) is an open protocol that lets AI assistants connect to external data sources and tools. With the CTI platform's MCP server, you can:

- **Query threat intelligence** directly from Claude Desktop
- **Create and manage** threat entities through conversation
- **Search across** MISP, OpenCTI, and knowledge base
- **Analyze threats** with AI-powered insights
- **Access graph relationships** and STIX data

### Quick Setup for Claude Desktop

1. **Install MCP SDK:**
   ```bash
   pip install mcp
   ```

2. **Configure Claude Desktop:**

   Edit your config file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "cti-platform": {
         "command": "python",
         "args": ["/path/to/cti_genai_platform/mcp_server.py"],
         "env": {
           "LLM_PROVIDER": "ollama",
           "LLM_MODEL": "llama3.2",
           "NEO4J_URI": "bolt://localhost:7687"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop** - that's it!

### Example Conversations

```
You: "Search the CTI platform for recent ransomware campaigns"
Claude: [uses search_threats tool to query your data]

You: "Create a threat actor called APT999 in the CTI platform"
Claude: [uses create_threat_actor tool]

You: "Analyze Emotet malware using the CTI knowledge base"
Claude: [uses analyze_threat tool with RAG]
```

### Available via MCP

**8 Resources** (read-only data):
- Recent threats, indicators, actors, campaigns, malware
- MISP events, OpenCTI reports, knowledge base stats

**18 Tools** (operations):
- Query: search_threats, analyze_threat, get_entity, get_relationships
- Create: create_indicator, create_threat_actor, create_malware, create_campaign
- Update: update_entity, create_relationship
- Delete: delete_entity
- Knowledge: add_document, query_knowledge
- STIX: import_stix_bundle, export_stix_bundle

See **[MCP_SERVER.md](MCP_SERVER.md)** for complete documentation.

---
