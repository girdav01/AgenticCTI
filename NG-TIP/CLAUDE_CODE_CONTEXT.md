# CTI Platform + AgenticCTI Integration - Claude Code Context

## Project Overview

This is a **Next-Generation Cyber Threat Intelligence Platform** with:
- Multi-LLM support (Ollama, LM Studio, OpenAI, Claude)
- RAG-powered knowledge base
- MISP & OpenCTI integration
- Neo4j graph database
- STIX 2.1 compliance
- MCP Server for Claude Desktop
- Streamlit web interface

## Current Status

✅ **Completed:**
- Full CTI platform with Streamlit UI
- 6 core modules (LLM, RAG, MISP, OpenCTI, Graph, STIX)
- MCP server with 26 endpoints (8 resources + 18 tools)
- Docker deployment
- Comprehensive documentation

🔄 **In Progress:**
- Integration with AgenticCTI project (github.com/girdav01/AgenticCTI)

## Integration Task

**Goal:** Integrate AgenticCTI to feed threat intelligence into the TIP platform

**Requirements:**
1. Clone girdav01/AgenticCTI repository
2. Analyze both codebases
3. Design integration architecture (AgenticCTI → TIP data flow)
4. Implement data ingestion pipelines
5. Create API endpoints for agentic feeding
6. Add STIX conversion for agentic data
7. Update graph database with agentic relationships
8. Expose agentic intel via MCP server
9. Create integration tests
10. Update documentation
11. Commit and push to girdav01/AgenticCTI repo

## Key Components to Integrate

### From TIP Platform (this project):
- **Data Ingestion:** `modules/rag_engine.py` - Can accept documents
- **Graph Storage:** `modules/graph_manager.py` - For relationships
- **STIX Processing:** `modules/stix_processor.py` - For standardization
- **MCP Server:** `mcp_server.py` - For exposure to Claude Desktop
- **API Layer:** Need to create REST endpoints

### From AgenticCTI (to be cloned):
- Agentic workflow outputs
- Threat intelligence data
- IOCs and indicators
- Analysis results
- Investigation findings

## Integration Architecture (Proposed)

```
┌─────────────────────┐
│   AgenticCTI        │
│   (Autonomous       │
│    Workflows)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Integration Layer  │
│  - Data Normalizer  │
│  - STIX Converter   │
│  - API Endpoints    │
└──────────┬──────────┘
           │
    ┌──────┴──────┬──────────┬──────────┐
    ▼             ▼          ▼          ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│  RAG   │  │ Graph  │  │ STIX   │  │  MCP   │
│ Engine │  │   DB   │  │ Store  │  │ Server │
└────────┘  └────────┘  └────────┘  └────────┘
```

## Files to Create/Modify

**New Files:**
- `modules/agentic_connector.py` - AgenticCTI integration
- `api_server.py` - REST API for data ingestion
- `integrations/agentic_pipeline.py` - Data processing pipeline
- `tests/test_agentic_integration.py` - Integration tests

**Files to Modify:**
- `mcp_server.py` - Add agentic data resources/tools
- `app.py` - Add agentic data visualization
- `config.py` - Add agentic configuration
- `README.md` - Document integration
- `requirements.txt` - Add dependencies

## Expected Data Flow

1. **AgenticCTI generates intel** → JSON/STIX output
2. **Integration layer receives** → via API/file/queue
3. **Data normalized** → converted to STIX 2.1
4. **Stored in TIP:**
   - Documents → RAG knowledge base
   - Entities → Graph database
   - Bundles → STIX processor
5. **Exposed via MCP** → Available in Claude Desktop
6. **Visible in UI** → Streamlit dashboard

## GitHub Workflow

```bash
# Claude Code should:
1. git clone https://github.com/girdav01/AgenticCTI.git
2. Analyze the AgenticCTI codebase
3. Create integration branch
4. Implement integration layer
5. Merge TIP components into AgenticCTI
6. Test integration
7. git add, commit, push to girdav01/AgenticCTI
```

## User Information

- **GitHub:** girdav01
- **Role:** Senior Security Researcher at Trend Micro
- **Location:** Montréal
- **Projects:** TMHunting, XDRAPISamples, CustomScripts, V1APITraining

## Success Criteria

✅ AgenticCTI can push data to TIP platform
✅ Data appears in RAG knowledge base
✅ Entities created in graph database
✅ Available via MCP server in Claude Desktop
✅ Visible in Streamlit UI
✅ STIX compliant
✅ Documented
✅ Tested
✅ Pushed to GitHub

## Commands for Claude Code

When you start Claude Code, say:

```
Please integrate the AgenticCTI project (github.com/girdav01/AgenticCTI) with 
this CTI TIP platform. AgenticCTI should feed threat intelligence data into the 
TIP. Create the integration layer, update both codebases, and push the merged 
project to the AgenticCTI repository.
```

## Additional Context

- This is a production-ready platform
- All code follows Python best practices
- MCP integration is a key differentiator
- STIX 2.1 compliance is required
- Docker deployment should work
- Documentation is comprehensive

---

**Ready for Claude Code to take over!**
