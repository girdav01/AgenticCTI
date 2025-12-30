# Using This Project with Claude Code

## What is Claude Code?

Claude Code is a command-line agentic coding tool that helps you build software through conversation. It's perfect for continuing this CTI platform integration project.

## Getting Started with Claude Code

### 1. Install Claude Code

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Or using pip (if available)
pip install claude-code
```

### 2. Navigate to Your Project

```bash
cd /path/to/cti_genai_platform
```

### 3. Start Claude Code

```bash
claude-code
```

Or with a specific task:

```bash
claude-code "Integrate my AgenticCTI project from girdav01/AgenticCTI with this TIP platform"
```

## What to Tell Claude Code

When you start Claude Code in this directory, you can say:

```
I need to integrate my AgenticCTI project (from github.com/girdav01/AgenticCTI) 
with this CTI GenAI Platform. The AgenticCTI should feed threat intelligence 
data into the TIP platform. Please:

1. Clone my AgenticCTI repository
2. Analyze both codebases
3. Design the integration architecture
4. Implement data pipelines from AgenticCTI → TIP
5. Add API endpoints for agentic feeding
6. Update the MCP server to expose agentic intel
7. Create integration tests
8. Update documentation
9. Commit and push to my AgenticCTI repo
```

## Project Context for Claude Code

**Current Project Structure:**
- Streamlit web UI (`app.py`)
- 6 core modules (LLM, RAG, MISP, OpenCTI, Graph, STIX)
- MCP Server with 26 endpoints
- Docker deployment ready
- Full documentation

**Integration Goals:**
- AgenticCTI → feeds data → TIP Platform
- Automatic STIX conversion
- Real-time threat ingestion
- Graph relationship building
- MCP exposure of agentic intelligence

## Alternative: Use Claude Desktop with MCP

If you prefer to continue in Claude Desktop:

1. Configure the MCP server (see `MCP_SERVER.md`)
2. Restart Claude Desktop
3. Say: "Clone girdav01/AgenticCTI and integrate it with the CTI platform"

Claude Desktop will use the MCP tools to work with your codebase directly.

## Files to Share with Claude Code

All files are ready in this directory. Claude Code will have access to:
- Complete CTI platform source code
- MCP server implementation
- All documentation
- Configuration templates
- Test suites

## Recommended Workflow

```bash
# 1. Start Claude Code in project directory
cd cti_genai_platform
claude-code

# 2. Claude Code will help you:
#    - Clone AgenticCTI
#    - Design integration
#    - Implement connectors
#    - Test the integration
#    - Push to GitHub

# 3. You review and approve changes
# 4. Claude Code commits and pushes
```

## GitHub Authentication

Claude Code can authenticate with GitHub to clone and push. When prompted:

```bash
# It will ask for GitHub credentials or SSH key
# Or use GitHub CLI integration
gh auth login
```

## Next Steps

1. Install Claude Code CLI
2. Navigate to this project directory
3. Run `claude-code`
4. Describe the AgenticCTI integration task
5. Let Claude Code handle the technical implementation

---

**Claude Code is perfect for this because it can:**
- Clone repositories
- Read and analyze codebases
- Design architectures
- Write integration code
- Run tests
- Commit and push changes
- All through natural conversation!
