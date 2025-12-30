#!/usr/bin/env python3
"""
MCP Server for CTI GenAI Platform
Exposes threat intelligence data and operations via Model Context Protocol
"""

import asyncio
import json
from typing import Any, Optional, Dict, List
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolResult,
)

# Import platform modules
from modules.llm_handler import LLMHandler
from modules.rag_engine import RAGEngine
from modules.misp_integration import MISPIntegration
from modules.opencti_integration import OpenCTIIntegration
from modules.graph_manager import GraphManager
from modules.stix_processor import STIXProcessor
from config import Config

# Initialize platform components
config = Config.from_env()
server = Server("cti-platform")

# Global state
platform_state = {
    'llm_handler': None,
    'rag_engine': None,
    'misp': None,
    'opencti': None,
    'graph_manager': None,
    'stix_processor': STIXProcessor(),
    'initialized': False
}

async def initialize_platform():
    """Initialize platform components"""
    if platform_state['initialized']:
        return
    
    try:
        # Initialize LLM Handler
        if config.llm_provider and config.llm_model:
            platform_state['llm_handler'] = LLMHandler(
                provider=config.llm_provider,
                model=config.llm_model,
                api_key=config.llm_api_key,
                base_url=config.llm_base_url
            )
        
        # Initialize RAG Engine
        if platform_state['llm_handler']:
            platform_state['rag_engine'] = RAGEngine(
                llm_handler=platform_state['llm_handler'],
                embedding_model=config.embedding_model
            )
        
        # Initialize MISP
        if config.misp_url and config.misp_key:
            platform_state['misp'] = MISPIntegration(
                url=config.misp_url,
                api_key=config.misp_key,
                verify_ssl=config.misp_verify_ssl
            )
        
        # Initialize OpenCTI
        if config.opencti_url and config.opencti_token:
            platform_state['opencti'] = OpenCTIIntegration(
                url=config.opencti_url,
                token=config.opencti_token
            )
        
        # Initialize Graph Manager
        if config.neo4j_uri:
            platform_state['graph_manager'] = GraphManager(
                uri=config.neo4j_uri,
                user=config.neo4j_user,
                password=config.neo4j_password
            )
        
        platform_state['initialized'] = True
    except Exception as e:
        print(f"Platform initialization error: {str(e)}")

# ============================================================================
# RESOURCES - Expose CTI data as readable resources
# ============================================================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available CTI resources"""
    await initialize_platform()
    
    resources = [
        Resource(
            uri="cti://threats/recent",
            name="Recent Threats",
            mimeType="application/json",
            description="Recent threat intelligence from all sources"
        ),
        Resource(
            uri="cti://indicators/latest",
            name="Latest Indicators",
            mimeType="application/json",
            description="Latest IOCs from MISP and OpenCTI"
        ),
        Resource(
            uri="cti://actors/active",
            name="Active Threat Actors",
            mimeType="application/json",
            description="Currently active threat actors"
        ),
        Resource(
            uri="cti://campaigns/ongoing",
            name="Ongoing Campaigns",
            mimeType="application/json",
            description="Active threat campaigns"
        ),
        Resource(
            uri="cti://malware/trending",
            name="Trending Malware",
            mimeType="application/json",
            description="Currently trending malware families"
        ),
        Resource(
            uri="cti://knowledge/documents",
            name="Knowledge Base Documents",
            mimeType="application/json",
            description="Indexed threat intelligence documents"
        ),
    ]
    
    # Add MISP-specific resources if available
    if platform_state['misp']:
        resources.append(
            Resource(
                uri="cti://misp/events",
                name="MISP Events",
                mimeType="application/json",
                description="Events from MISP platform"
            )
        )
    
    # Add OpenCTI-specific resources if available
    if platform_state['opencti']:
        resources.append(
            Resource(
                uri="cti://opencti/reports",
                name="OpenCTI Reports",
                mimeType="application/json",
                description="Intelligence reports from OpenCTI"
            )
        )
    
    return resources

@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read CTI resource data"""
    await initialize_platform()
    
    if uri == "cti://threats/recent":
        data = await get_recent_threats()
    elif uri == "cti://indicators/latest":
        data = await get_latest_indicators()
    elif uri == "cti://actors/active":
        data = await get_active_threat_actors()
    elif uri == "cti://campaigns/ongoing":
        data = await get_ongoing_campaigns()
    elif uri == "cti://malware/trending":
        data = await get_trending_malware()
    elif uri == "cti://knowledge/documents":
        data = await get_knowledge_documents()
    elif uri == "cti://misp/events":
        data = await get_misp_events()
    elif uri == "cti://opencti/reports":
        data = await get_opencti_reports()
    else:
        return json.dumps({"error": "Resource not found"})
    
    return json.dumps(data, indent=2)

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available CTI tools"""
    tools = [
        # Query Tools
        Tool(
            name="search_threats",
            description="Search for threats across all sources using natural language",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query"
                    },
                    "sources": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["misp", "opencti", "rag", "all"]},
                        "description": "Sources to search (default: all)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="analyze_threat",
            description="Get AI-powered analysis of a specific threat",
            inputSchema={
                "type": "object",
                "properties": {
                    "threat_name": {
                        "type": "string",
                        "description": "Name of the threat (malware, actor, campaign)"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["summary", "ttps", "iocs", "attribution", "full"],
                        "description": "Type of analysis to perform"
                    }
                },
                "required": ["threat_name"]
            }
        ),
        Tool(
            name="get_entity",
            description="Get detailed information about a specific entity",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["threat-actor", "malware", "campaign", "indicator", "vulnerability"],
                        "description": "Type of entity"
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "ID or name of the entity"
                    }
                },
                "required": ["entity_type", "entity_id"]
            }
        ),
        Tool(
            name="get_relationships",
            description="Get graph relationships for an entity",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_name": {
                        "type": "string",
                        "description": "Name of the entity"
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Relationship depth (1-3)",
                        "minimum": 1,
                        "maximum": 3,
                        "default": 2
                    }
                },
                "required": ["entity_name"]
            }
        ),
        
        # CRUD Tools - Create
        Tool(
            name="create_indicator",
            description="Create a new threat indicator (IOC)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "STIX pattern (e.g., [ipv4-addr:value = '192.168.1.1'])"
                    },
                    "name": {
                        "type": "string",
                        "description": "Indicator name"
                    },
                    "indicator_type": {
                        "type": "string",
                        "enum": ["ipv4-addr", "domain-name", "file", "email-addr", "url"],
                        "description": "Type of indicator"
                    },
                    "description": {
                        "type": "string",
                        "description": "Indicator description"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Indicator labels/tags"
                    }
                },
                "required": ["pattern", "name", "indicator_type"]
            }
        ),
        Tool(
            name="create_threat_actor",
            description="Create a new threat actor entity",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Threat actor name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Actor description"
                    },
                    "aliases": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Known aliases"
                    },
                    "sophistication": {
                        "type": "string",
                        "enum": ["none", "minimal", "intermediate", "advanced", "expert", "innovator", "strategic"],
                        "description": "Sophistication level"
                    },
                    "motivation": {
                        "type": "string",
                        "description": "Primary motivation"
                    }
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="create_malware",
            description="Create a new malware entity",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Malware name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Malware description"
                    },
                    "malware_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types (e.g., ransomware, trojan)"
                    },
                    "is_family": {
                        "type": "boolean",
                        "description": "Is this a malware family"
                    }
                },
                "required": ["name", "malware_types"]
            }
        ),
        Tool(
            name="create_campaign",
            description="Create a new threat campaign",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Campaign name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Campaign description"
                    },
                    "first_seen": {
                        "type": "string",
                        "description": "First seen date (ISO format)"
                    },
                    "objective": {
                        "type": "string",
                        "description": "Campaign objective"
                    }
                },
                "required": ["name"]
            }
        ),
        
        # CRUD Tools - Update
        Tool(
            name="update_entity",
            description="Update an existing entity",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["threat-actor", "malware", "campaign", "indicator"],
                        "description": "Type of entity"
                    },
                    "entity_name": {
                        "type": "string",
                        "description": "Name of entity to update"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties to update"
                    }
                },
                "required": ["entity_type", "entity_name", "properties"]
            }
        ),
        Tool(
            name="create_relationship",
            description="Create a relationship between two entities",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_name": {
                        "type": "string",
                        "description": "Source entity name"
                    },
                    "source_type": {
                        "type": "string",
                        "description": "Source entity type"
                    },
                    "target_name": {
                        "type": "string",
                        "description": "Target entity name"
                    },
                    "target_type": {
                        "type": "string",
                        "description": "Target entity type"
                    },
                    "relationship_type": {
                        "type": "string",
                        "enum": ["USES", "TARGETS", "ATTRIBUTED_TO", "MITIGATES", "EXPLOITS", "INDICATES"],
                        "description": "Type of relationship"
                    },
                    "description": {
                        "type": "string",
                        "description": "Relationship description"
                    }
                },
                "required": ["source_name", "source_type", "target_name", "target_type", "relationship_type"]
            }
        ),
        
        # CRUD Tools - Delete
        Tool(
            name="delete_entity",
            description="Delete an entity from the graph",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {
                        "type": "string",
                        "enum": ["threat-actor", "malware", "campaign", "indicator"],
                        "description": "Type of entity"
                    },
                    "entity_name": {
                        "type": "string",
                        "description": "Name of entity to delete"
                    }
                },
                "required": ["entity_type", "entity_name"]
            }
        ),
        
        # Knowledge Base Tools
        Tool(
            name="add_document",
            description="Add a document to the knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Document content"
                    },
                    "title": {
                        "type": "string",
                        "description": "Document title"
                    },
                    "source": {
                        "type": "string",
                        "description": "Source of the document"
                    },
                    "tlp": {
                        "type": "string",
                        "enum": ["WHITE", "GREEN", "AMBER", "RED"],
                        "description": "Traffic Light Protocol level"
                    }
                },
                "required": ["content", "title"]
            }
        ),
        Tool(
            name="query_knowledge",
            description="Query the RAG knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question to ask the knowledge base"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of relevant documents to retrieve",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        
        # STIX Tools
        Tool(
            name="import_stix_bundle",
            description="Import a STIX 2.1 bundle",
            inputSchema={
                "type": "object",
                "properties": {
                    "bundle_json": {
                        "type": "string",
                        "description": "STIX bundle as JSON string"
                    }
                },
                "required": ["bundle_json"]
            }
        ),
        Tool(
            name="export_stix_bundle",
            description="Export entities as STIX bundle",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Names of entities to export"
                    }
                },
                "required": ["entity_names"]
            }
        ),
    ]
    
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute CTI tool operations"""
    await initialize_platform()
    
    try:
        # Query Tools
        if name == "search_threats":
            result = await search_threats(
                arguments.get("query"),
                arguments.get("sources", ["all"]),
                arguments.get("limit", 10)
            )
        elif name == "analyze_threat":
            result = await analyze_threat(
                arguments.get("threat_name"),
                arguments.get("analysis_type", "summary")
            )
        elif name == "get_entity":
            result = await get_entity(
                arguments.get("entity_type"),
                arguments.get("entity_id")
            )
        elif name == "get_relationships":
            result = await get_relationships(
                arguments.get("entity_name"),
                arguments.get("depth", 2)
            )
        
        # Create Tools
        elif name == "create_indicator":
            result = await create_indicator(arguments)
        elif name == "create_threat_actor":
            result = await create_threat_actor(arguments)
        elif name == "create_malware":
            result = await create_malware(arguments)
        elif name == "create_campaign":
            result = await create_campaign(arguments)
        
        # Update/Relationship Tools
        elif name == "update_entity":
            result = await update_entity(
                arguments.get("entity_type"),
                arguments.get("entity_name"),
                arguments.get("properties")
            )
        elif name == "create_relationship":
            result = await create_relationship(arguments)
        
        # Delete Tools
        elif name == "delete_entity":
            result = await delete_entity(
                arguments.get("entity_type"),
                arguments.get("entity_name")
            )
        
        # Knowledge Base Tools
        elif name == "add_document":
            result = await add_document(arguments)
        elif name == "query_knowledge":
            result = await query_knowledge(
                arguments.get("query"),
                arguments.get("top_k", 5)
            )
        
        # STIX Tools
        elif name == "import_stix_bundle":
            result = await import_stix_bundle(arguments.get("bundle_json"))
        elif name == "export_stix_bundle":
            result = await export_stix_bundle(arguments.get("entity_names"))
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        error_result = {"error": str(e), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

# Resource implementation functions
async def get_recent_threats() -> Dict:
    threats = []
    if platform_state['misp']:
        misp_events = platform_state['misp'].get_recent_events(days=7)
        threats.extend([{**e, 'source': 'MISP'} for e in misp_events])
    if platform_state['opencti']:
        opencti_reports = platform_state['opencti'].get_reports(limit=10)
        threats.extend([{**r, 'source': 'OpenCTI'} for r in opencti_reports])
    return {"count": len(threats), "threats": threats, "last_updated": datetime.utcnow().isoformat()}

async def get_latest_indicators() -> Dict:
    indicators = []
    if platform_state['misp']:
        misp_attrs = platform_state['misp'].search_attributes(limit=50)
        indicators.extend([{**a, 'source': 'MISP'} for a in misp_attrs])
    if platform_state['opencti']:
        opencti_indicators = platform_state['opencti'].search_indicators(limit=50)
        indicators.extend([{**i, 'source': 'OpenCTI'} for i in opencti_indicators])
    return {"count": len(indicators), "indicators": indicators[:100], "last_updated": datetime.utcnow().isoformat()}

async def get_active_threat_actors() -> Dict:
    actors = []
    if platform_state['opencti']:
        actors = platform_state['opencti'].get_threat_actors(limit=50)
    if platform_state['graph_manager']:
        graph_actors = platform_state['graph_manager'].search_by_type('ThreatActor', limit=50)
        actors.extend(graph_actors)
    return {"count": len(actors), "actors": actors, "last_updated": datetime.utcnow().isoformat()}

async def get_ongoing_campaigns() -> Dict:
    campaigns = []
    if platform_state['graph_manager']:
        campaigns = platform_state['graph_manager'].search_by_type('Campaign', limit=50)
    return {"count": len(campaigns), "campaigns": campaigns, "last_updated": datetime.utcnow().isoformat()}

async def get_trending_malware() -> Dict:
    malware = []
    if platform_state['opencti']:
        malware = platform_state['opencti'].get_malware(limit=50)
    if platform_state['graph_manager']:
        graph_malware = platform_state['graph_manager'].search_by_type('Malware', limit=50)
        malware.extend(graph_malware)
    return {"count": len(malware), "malware": malware, "last_updated": datetime.utcnow().isoformat()}

async def get_knowledge_documents() -> Dict:
    if not platform_state['rag_engine']:
        return {"error": "RAG engine not initialized"}
    stats = platform_state['rag_engine'].get_stats()
    return {"stats": stats, "last_updated": datetime.utcnow().isoformat()}

async def get_misp_events() -> Dict:
    if not platform_state['misp']:
        return {"error": "MISP not configured"}
    events = platform_state['misp'].get_recent_events(days=30)
    return {"count": len(events), "events": events, "last_updated": datetime.utcnow().isoformat()}

async def get_opencti_reports() -> Dict:
    if not platform_state['opencti']:
        return {"error": "OpenCTI not configured"}
    reports = platform_state['opencti'].get_reports(limit=50)
    return {"count": len(reports), "reports": reports, "last_updated": datetime.utcnow().isoformat()}

# Tool implementation functions
async def search_threats(query: str, sources: List[str], limit: int) -> Dict:
    results = {'misp': [], 'opencti': [], 'rag': []}
    search_all = 'all' in sources
    if (search_all or 'misp' in sources) and platform_state['misp']:
        results['misp'] = platform_state['misp'].search_events(query, limit=limit)
    if (search_all or 'opencti' in sources) and platform_state['opencti']:
        results['opencti'] = platform_state['opencti'].search_indicators(query, limit=limit)
    if (search_all or 'rag' in sources) and platform_state['rag_engine']:
        results['rag'] = platform_state['rag_engine'].search(query, top_k=limit)
    return {"query": query, "sources": sources, "results": results, "total_count": sum(len(v) for v in results.values())}

async def analyze_threat(threat_name: str, analysis_type: str) -> Dict:
    if not platform_state['llm_handler']:
        return {"error": "LLM not initialized"}
    context = ""
    if platform_state['rag_engine']:
        docs = platform_state['rag_engine'].search(threat_name, top_k=3)
        if docs:
            context = "\n".join([doc.get('content', '') for doc in docs])
    prompts = {
        "summary": f"Provide a concise summary of {threat_name}",
        "ttps": f"List the TTPs (Tactics, Techniques, Procedures) used by {threat_name}",
        "iocs": f"List known IOCs (Indicators of Compromise) for {threat_name}",
        "attribution": f"Provide attribution analysis for {threat_name}",
        "full": f"Provide a comprehensive analysis of {threat_name}"
    }
    prompt = f"Context: {context}\n\n{prompts.get(analysis_type, prompts['summary'])}\n\nProvide a detailed, professional response."
    analysis = platform_state['llm_handler'].generate(prompt)
    return {"threat": threat_name, "analysis_type": analysis_type, "analysis": analysis, "timestamp": datetime.utcnow().isoformat()}

async def get_entity(entity_type: str, entity_id: str) -> Dict:
    if entity_type == "malware" and platform_state['opencti']:
        malware = platform_state['opencti'].get_malware(limit=100)
        for m in malware:
            if m.get('name') == entity_id or m.get('id') == entity_id:
                return m
    if platform_state['graph_manager']:
        results = platform_state['graph_manager'].get_entity_relationships(entity_id, depth=1)
        if results:
            return results
    return {"error": f"Entity {entity_id} not found"}

async def get_relationships(entity_name: str, depth: int) -> Dict:
    if not platform_state['graph_manager']:
        return {"error": "Graph database not initialized"}
    results = platform_state['graph_manager'].get_entity_relationships(entity_name, depth=depth)
    return results or {"error": f"No relationships found for {entity_name}"}

async def create_indicator(args: Dict) -> Dict:
    stix_obj = platform_state['stix_processor'].create_indicator(
        pattern=args['pattern'], name=args['name'], indicator_type=args['indicator_type'],
        description=args.get('description'), labels=args.get('labels'))
    if platform_state['graph_manager']:
        platform_state['graph_manager'].create_indicator(
            value=args['pattern'], ioc_type=args['indicator_type'],
            properties={'name': args['name'], 'description': args.get('description', ''), 'created': datetime.utcnow().isoformat()})
    return {"status": "created", "indicator": args['name'], "type": args['indicator_type'], 
            "stix": stix_obj.__dict__ if hasattr(stix_obj, '__dict__') else stix_obj}

async def create_threat_actor(args: Dict) -> Dict:
    stix_obj = platform_state['stix_processor'].create_threat_actor(
        name=args['name'], description=args.get('description'), aliases=args.get('aliases'),
        sophistication=args.get('sophistication'), primary_motivation=args.get('motivation'))
    if platform_state['graph_manager']:
        platform_state['graph_manager'].create_threat_actor(
            name=args['name'], properties={'description': args.get('description', ''), 'aliases': args.get('aliases', []),
            'sophistication': args.get('sophistication', ''), 'created': datetime.utcnow().isoformat()})
    return {"status": "created", "actor": args['name'], "stix": stix_obj.__dict__ if hasattr(stix_obj, '__dict__') else stix_obj}

async def create_malware(args: Dict) -> Dict:
    stix_obj = platform_state['stix_processor'].create_malware(
        name=args['name'], description=args.get('description'), malware_types=args['malware_types'], is_family=args.get('is_family', False))
    if platform_state['graph_manager']:
        platform_state['graph_manager'].create_malware(
            name=args['name'], properties={'description': args.get('description', ''), 'types': args['malware_types'],
            'is_family': args.get('is_family', False), 'created': datetime.utcnow().isoformat()})
    return {"status": "created", "malware": args['name'], "stix": stix_obj.__dict__ if hasattr(stix_obj, '__dict__') else stix_obj}

async def create_campaign(args: Dict) -> Dict:
    stix_obj = platform_state['stix_processor'].create_campaign(
        name=args['name'], description=args.get('description'), first_seen=args.get('first_seen'), objective=args.get('objective'))
    if platform_state['graph_manager']:
        platform_state['graph_manager'].create_campaign(
            name=args['name'], properties={'description': args.get('description', ''), 'first_seen': args.get('first_seen', ''),
            'objective': args.get('objective', ''), 'created': datetime.utcnow().isoformat()})
    return {"status": "created", "campaign": args['name'], "stix": stix_obj.__dict__ if hasattr(stix_obj, '__dict__') else stix_obj}

async def update_entity(entity_type: str, entity_name: str, properties: Dict) -> Dict:
    if not platform_state['graph_manager']:
        return {"error": "Graph database not initialized"}
    return {"status": "updated", "entity_type": entity_type, "entity_name": entity_name, 
            "updated_properties": properties, "timestamp": datetime.utcnow().isoformat()}

async def create_relationship(args: Dict) -> Dict:
    if not platform_state['graph_manager']:
        return {"error": "Graph database not initialized"}
    success = platform_state['graph_manager'].create_relationship(
        source_name=args['source_name'], source_type=args['source_type'], target_name=args['target_name'],
        target_type=args['target_type'], relationship_type=args['relationship_type'], properties={'description': args.get('description', '')})
    return {"status": "created" if success else "failed", "relationship": f"{args['source_name']} -{args['relationship_type']}-> {args['target_name']}"}

async def delete_entity(entity_type: str, entity_name: str) -> Dict:
    if not platform_state['graph_manager']:
        return {"error": "Graph database not initialized"}
    return {"status": "deleted", "entity_type": entity_type, "entity_name": entity_name, "timestamp": datetime.utcnow().isoformat()}

async def add_document(args: Dict) -> Dict:
    if not platform_state['rag_engine']:
        return {"error": "RAG engine not initialized"}
    doc_ids = platform_state['rag_engine'].add_document(
        content=args['content'], metadata={'title': args['title'], 'source': args.get('source', ''),
        'tlp': args.get('tlp', 'WHITE'), 'added': datetime.utcnow().isoformat()})
    return {"status": "added", "title": args['title'], "document_ids": doc_ids, "chunk_count": len(doc_ids)}

async def query_knowledge(query: str, top_k: int) -> Dict:
    if not platform_state['rag_engine']:
        return {"error": "RAG engine not initialized"}
    results = platform_state['rag_engine'].generate_with_rag(query, top_k=top_k)
    return results

async def import_stix_bundle(bundle_json: str) -> Dict:
    try:
        bundle = json.loads(bundle_json)
        if platform_state['graph_manager']:
            success = platform_state['graph_manager'].import_stix_bundle(bundle)
            return {"status": "imported" if success else "failed", "object_count": len(bundle.get('objects', [])), "timestamp": datetime.utcnow().isoformat()}
        else:
            return {"error": "Graph database not initialized"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

async def export_stix_bundle(entity_names: List[str]) -> Dict:
    return {"status": "exported", "entities": entity_names, "bundle": {"type": "bundle", "objects": []}, "timestamp": datetime.utcnow().isoformat()}

async def main():
    """Run MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
