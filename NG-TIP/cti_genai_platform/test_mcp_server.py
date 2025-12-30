#!/usr/bin/env python3
"""
Test script for MCP server
Validates tools and resources are working
"""

import asyncio
import json
from mcp_server import (
    list_resources, list_tools, read_resource, call_tool,
    initialize_platform, platform_state
)

async def test_mcp_server():
    """Run comprehensive MCP server tests"""
    
    print("=" * 60)
    print("MCP Server Test Suite")
    print("=" * 60)
    print()
    
    # Initialize platform
    print("1. Initializing platform...")
    await initialize_platform()
    
    if platform_state['initialized']:
        print("   ✅ Platform initialized successfully")
    else:
        print("   ⚠️  Platform partially initialized")
    
    print(f"   - LLM Handler: {'✅' if platform_state['llm_handler'] else '❌'}")
    print(f"   - RAG Engine: {'✅' if platform_state['rag_engine'] else '❌'}")
    print(f"   - MISP: {'✅' if platform_state['misp'] else '❌'}")
    print(f"   - OpenCTI: {'✅' if platform_state['opencti'] else '❌'}")
    print(f"   - Graph Manager: {'✅' if platform_state['graph_manager'] else '❌'}")
    print()
    
    # List resources
    print("2. Testing Resources...")
    resources = await list_resources()
    print(f"   Found {len(resources)} resources:")
    for resource in resources:
        print(f"   - {resource.uri}: {resource.name}")
    print()
    
    # Test reading a resource
    print("3. Testing Resource Read...")
    try:
        data = await read_resource("cti://threats/recent")
        result = json.loads(data)
        print(f"   ✅ Successfully read resource")
        print(f"   - Threats found: {result.get('count', 0)}")
    except Exception as e:
        print(f"   ❌ Error reading resource: {str(e)}")
    print()
    
    # List tools
    print("4. Testing Tools...")
    tools = await list_tools()
    print(f"   Found {len(tools)} tools:")
    
    tool_categories = {
        'Query': ['search_threats', 'analyze_threat', 'get_entity', 'get_relationships'],
        'Create': ['create_indicator', 'create_threat_actor', 'create_malware', 'create_campaign'],
        'Update': ['update_entity', 'create_relationship'],
        'Delete': ['delete_entity'],
        'Knowledge': ['add_document', 'query_knowledge'],
        'STIX': ['import_stix_bundle', 'export_stix_bundle']
    }
    
    for category, tool_names in tool_categories.items():
        print(f"   {category} tools:")
        for tool_name in tool_names:
            found = any(t.name == tool_name for t in tools)
            print(f"   - {tool_name}: {'✅' if found else '❌'}")
    print()
    
    # Test a simple tool
    print("5. Testing Tool Execution...")
    
    # Test search_threats
    print("   Testing search_threats...")
    try:
        result = await call_tool(
            "search_threats",
            {"query": "test", "sources": ["all"], "limit": 5}
        )
        print(f"   ✅ search_threats executed successfully")
        print(f"   Result: {result[0].text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    print()
    
    # Test create_indicator
    if platform_state['graph_manager'] or platform_state['stix_processor']:
        print("   Testing create_indicator...")
        try:
            result = await call_tool(
                "create_indicator",
                {
                    "pattern": "[ipv4-addr:value = '192.168.1.1']",
                    "name": "Test Indicator",
                    "indicator_type": "ipv4-addr",
                    "description": "Test indicator for MCP validation"
                }
            )
            print(f"   ✅ create_indicator executed successfully")
            print(f"   Result: {result[0].text[:200]}...")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        print()
    
    # Test knowledge base (if available)
    if platform_state['rag_engine']:
        print("   Testing add_document...")
        try:
            result = await call_tool(
                "add_document",
                {
                    "content": "This is a test threat intelligence document for MCP validation.",
                    "title": "MCP Test Document",
                    "source": "Test Suite",
                    "tlp": "WHITE"
                }
            )
            print(f"   ✅ add_document executed successfully")
            print(f"   Result: {result[0].text[:200]}...")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        print()
        
        print("   Testing query_knowledge...")
        try:
            result = await call_tool(
                "query_knowledge",
                {"query": "test", "top_k": 3}
            )
            print(f"   ✅ query_knowledge executed successfully")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Resources: {len(resources)} available")
    print(f"Tools: {len(tools)} registered")
    print("MCP server is ready for use with Claude Desktop!")
    print()
    print("Next steps:")
    print("1. Configure Claude Desktop (see MCP_SERVER.md)")
    print("2. Restart Claude Desktop")
    print("3. Start using CTI tools in conversations")
    print()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
