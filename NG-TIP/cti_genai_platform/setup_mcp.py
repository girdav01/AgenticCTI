#!/usr/bin/env python3
"""
Automated MCP Setup for Claude Desktop

This script helps configure Claude Desktop to use the CTI Platform MCP server.
"""

import os
import json
import sys
import platform
from pathlib import Path


def get_claude_config_path():
    """Get Claude Desktop configuration path based on OS"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path(os.getenv("APPDATA")) / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    else:
        return None


def get_project_path():
    """Get absolute path to the CTI platform project"""
    return Path(__file__).parent.absolute()


def read_config(config_path):
    """Read existing Claude Desktop config"""
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  Warning: Existing config file is invalid JSON")
            return {}
    return {}


def write_config(config_path, config):
    """Write Claude Desktop config"""
    # Create parent directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)


def main():
    print("=" * 60)
    print("CTI Platform MCP Server Setup for Claude Desktop")
    print("=" * 60)
    print()
    
    # Get Claude config path
    config_path = get_claude_config_path()
    
    if not config_path:
        print("❌ Could not detect your operating system")
        print("Please manually configure Claude Desktop using claude_desktop_config.json")
        sys.exit(1)
    
    print(f"📁 Claude Desktop config location:")
    print(f"   {config_path}")
    print()
    
    # Get project path
    project_path = get_project_path()
    mcp_server_path = project_path / "mcp_server.py"
    
    if not mcp_server_path.exists():
        print(f"❌ mcp_server.py not found at {mcp_server_path}")
        sys.exit(1)
    
    print(f"📁 MCP Server location:")
    print(f"   {mcp_server_path}")
    print()
    
    # Read existing config
    config = read_config(config_path)
    
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Prompt for configuration
    print("🔧 Configuration:")
    print()
    
    # Environment variables
    env_vars = {}
    
    # LLM Provider
    print("LLM Provider [ollama/lmstudio/openai/anthropic] (default: ollama):")
    llm_provider = input("  > ").strip() or "ollama"
    env_vars["LLM_PROVIDER"] = llm_provider
    
    if llm_provider in ["ollama", "lmstudio"]:
        print(f"\n{llm_provider.upper()} Base URL (default: http://localhost:11434):")
        base_url = input("  > ").strip()
        if not base_url:
            base_url = "http://localhost:11434" if llm_provider == "ollama" else "http://localhost:1234/v1"
        env_vars["LLM_BASE_URL"] = base_url
        
        print(f"\n{llm_provider.upper()} Model (default: llama3.2):")
        model = input("  > ").strip() or "llama3.2"
        env_vars["LLM_MODEL"] = model
    else:
        print(f"\n{llm_provider.upper()} API Key:")
        api_key = input("  > ").strip()
        if api_key:
            env_vars["LLM_API_KEY"] = api_key
        
        print(f"\nModel name:")
        model = input("  > ").strip()
        if model:
            env_vars["LLM_MODEL"] = model
    
    # Optional integrations
    print("\n📌 Optional: Configure MISP integration? [y/N]:")
    if input("  > ").strip().lower() == 'y':
        print("MISP URL:")
        misp_url = input("  > ").strip()
        if misp_url:
            env_vars["MISP_URL"] = misp_url
        
        print("MISP API Key:")
        misp_key = input("  > ").strip()
        if misp_key:
            env_vars["MISP_API_KEY"] = misp_key
    
    print("\n📌 Optional: Configure OpenCTI integration? [y/N]:")
    if input("  > ").strip().lower() == 'y':
        print("OpenCTI URL:")
        opencti_url = input("  > ").strip()
        if opencti_url:
            env_vars["OPENCTI_URL"] = opencti_url
        
        print("OpenCTI Token:")
        opencti_token = input("  > ").strip()
        if opencti_token:
            env_vars["OPENCTI_TOKEN"] = opencti_token
    
    print("\n📌 Optional: Configure Neo4j? [y/N]:")
    if input("  > ").strip().lower() == 'y':
        print("Neo4j URI (default: bolt://localhost:7687):")
        neo4j_uri = input("  > ").strip() or "bolt://localhost:7687"
        env_vars["NEO4J_URI"] = neo4j_uri
        
        print("Neo4j User (default: neo4j):")
        neo4j_user = input("  > ").strip() or "neo4j"
        env_vars["NEO4J_USER"] = neo4j_user
        
        print("Neo4j Password:")
        neo4j_password = input("  > ").strip()
        if neo4j_password:
            env_vars["NEO4J_PASSWORD"] = neo4j_password
    
    # Create MCP server configuration
    mcp_config = {
        "command": "python" if platform.system() != "Windows" else "python.exe",
        "args": [str(mcp_server_path)],
        "env": env_vars
    }
    
    # Check if cti-platform already exists
    if "cti-platform" in config["mcpServers"]:
        print("\n⚠️  Warning: 'cti-platform' MCP server already exists in config")
        print("Overwrite? [y/N]:")
        if input("  > ").strip().lower() != 'y':
            print("❌ Setup cancelled")
            sys.exit(0)
    
    # Add to config
    config["mcpServers"]["cti-platform"] = mcp_config
    
    # Write config
    try:
        write_config(config_path, config)
        print("\n✅ Configuration saved successfully!")
        print()
        print("=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Restart Claude Desktop")
        print("2. Look for the 🔌 icon to verify MCP connection")
        print("3. Try: 'Search for APT28 across all threat intel sources'")
        print()
        print("📚 Documentation:")
        print("   - Full guide: MCP_SERVER_DOCS.md")
        print("   - Quick ref: MCP_QUICK_REFERENCE.md")
        print()
        print("🎉 Setup complete!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Error writing config: {e}")
        print("\nGenerated configuration:")
        print(json.dumps(config, indent=2))
        print("\nPlease manually add this to your Claude Desktop config file.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(0)
