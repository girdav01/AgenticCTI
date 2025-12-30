# MCP Tools Quick Reference

## 🚀 Getting Started with MCP

**Configure Claude Desktop:**
```json
{
  "mcpServers": {
    "cti-platform": {
      "command": "python",
      "args": ["/path/to/cti_genai_platform/mcp_server.py"]
    }
  }
}
```

**Restart Claude Desktop** → Look for 🔌 icon → Start using tools!

---

## 📋 All Available Tools (20 Total)

### RAG & Search (3 tools)
| Tool | Description | Example |
|------|-------------|---------|
| `search_threat_intelligence` | Multi-source intelligence search | "Search for APT28 campaigns" |
| `query_knowledge_base` | Semantic RAG search | "Find Emotet TTPs" |
| `add_document_to_knowledge_base` | Add threat reports | "Add this analysis to KB" |

### MISP Integration (3 tools)
| Tool | Description | Example |
|------|-------------|---------|
| `search_misp_events` | Search MISP events | "Find ransomware events" |
| `get_misp_event` | Get event details | "Get event 12345" |
| `search_misp_attributes` | Search IOCs | "Find SHA256 hashes for Emotet" |

### OpenCTI Integration (4 tools)
| Tool | Description | Example |
|------|-------------|---------|
| `search_opencti_indicators` | Search indicators | "Find APT29 indicators" |
| `get_opencti_threat_actors` | Get threat actors | "List all threat actors" |
| `get_opencti_malware` | Get malware info | "Get malware families" |
| `get_opencti_attack_patterns` | Get MITRE TTPs | "Show ATT&CK patterns" |

### Graph Database (6 tools)
| Tool | Description | Example |
|------|-------------|---------|
| `create_threat_actor` | Create actor node | "Create APT28 actor" |
| `create_malware` | Create malware node | "Create Emotet malware" |
| `create_indicator` | Create IOC node | "Create indicator for IP" |
| `create_relationship` | Link entities | "APT28 USES Zebrocy" |
| `query_graph_relationships` | Explore connections | "Show APT28 relationships" |
| `search_graph_by_type` | Search by type | "List all malware" |

### STIX Objects (2 tools)
| Tool | Description | Example |
|------|-------------|---------|
| `create_stix_indicator` | Create STIX indicator | "Create indicator for IP" |
| `create_stix_threat_actor` | Create STIX actor | "Create actor for Lazarus" |

### System (1 tool)
| Tool | Description | Example |
|------|-------------|---------|
| `get_platform_statistics` | Get stats | "Show platform status" |

---

## 💡 Common Use Cases

### 1. Threat Research
```
"Search for all information about Emotet across all sources"
```
**Uses:** search_threat_intelligence → Searches MISP, OpenCTI, RAG

---

### 2. IOC Lookup
```
"Check if IP 192.168.1.100 is in our threat intelligence"
```
**Uses:** search_misp_attributes, search_opencti_indicators, query_knowledge_base

---

### 3. Build Threat Profile
```
"Create a complete profile for APT28 including their tools"
```
**Uses:** get_opencti_threat_actors, query_graph_relationships, search_misp_events

---

### 4. Add Intelligence
```
"Add this threat report to the knowledge base and create graph nodes"
```
**Uses:** add_document_to_knowledge_base, create_threat_actor, create_malware, create_relationship

---

### 5. Create STIX Bundle
```
"Create STIX objects for this new campaign"
```
**Uses:** create_stix_threat_actor, create_stix_indicator, create_stix_malware

---

### 6. Relationship Mapping
```
"Map all malware used by APT29"
```
**Uses:** get_opencti_threat_actors, query_graph_relationships, get_opencti_malware

---

### 7. Bulk Analysis
```
"Analyze these 50 IOCs and tell me which are malicious"
```
**Uses:** Loop through search_misp_attributes and search_opencti_indicators

---

### 8. Campaign Tracking
```
"Track the evolution of ransomware campaigns over the last 6 months"
```
**Uses:** search_misp_events, get_opencti_attack_patterns, query_knowledge_base

---

## 🎯 Tool Selection Guide

**Want to...**
- **Search everything** → `search_threat_intelligence`
- **Find specific event** → `search_misp_events` or `get_misp_event`
- **Lookup IOC** → `search_misp_attributes` + `search_opencti_indicators`
- **Get threat actor info** → `get_opencti_threat_actors`
- **See relationships** → `query_graph_relationships`
- **Add new data** → `add_document_to_knowledge_base`
- **Create entities** → `create_threat_actor`, `create_malware`, `create_indicator`
- **Link entities** → `create_relationship`
- **Export STIX** → `create_stix_*` tools
- **Check system** → `get_platform_statistics`

---

## 🔥 Pro Tips

1. **Chain tools for complex queries** - Claude will automatically use multiple tools
2. **Be specific in queries** - "APT28 phishing campaigns" > "APT28"
3. **Use limits wisely** - Default limits are optimized, increase only if needed
4. **Check statistics first** - Use `get_platform_statistics` to verify connections
5. **Combine sources** - MISP + OpenCTI + RAG gives best results

---

## ⚡ Quick Commands

### Check Status
```
"Get platform statistics"
"Are all systems connected?"
```

### Search All Sources
```
"Search for [threat/campaign/actor] across all sources"
```

### Deep Dive
```
"Give me everything about [entity]"
"Create a comprehensive report on [topic]"
```

### Create Intelligence
```
"Add this to the knowledge base: [content]"
"Create graph nodes for: [entities]"
```

### Export
```
"Create STIX objects for [entities]"
"Generate a STIX bundle for this campaign"
```

---

## 📊 Tool Categories

```
📚 Knowledge (3)
   ├── search_threat_intelligence
   ├── query_knowledge_base
   └── add_document_to_knowledge_base

🔍 MISP (3)
   ├── search_misp_events
   ├── get_misp_event
   └── search_misp_attributes

🌐 OpenCTI (4)
   ├── search_opencti_indicators
   ├── get_opencti_threat_actors
   ├── get_opencti_malware
   └── get_opencti_attack_patterns

🕸️ Graph (6)
   ├── create_threat_actor
   ├── create_malware
   ├── create_indicator
   ├── create_relationship
   ├── query_graph_relationships
   └── search_graph_by_type

🎯 STIX (2)
   ├── create_stix_indicator
   └── create_stix_threat_actor

📊 System (1)
   └── get_platform_statistics
```

---

## 🚨 Troubleshooting

**Error: "MISP not configured"**
→ Set MISP_URL and MISP_API_KEY in environment

**Error: "Graph database not initialized"**
→ Start Neo4j and check connection

**Error: "RAG engine not initialized"**
→ Check LLM provider is configured

**No results returned**
→ Try different search terms or check source connectivity

---

**Remember:** Just ask Claude naturally - it knows how to use all these tools! 🎉
