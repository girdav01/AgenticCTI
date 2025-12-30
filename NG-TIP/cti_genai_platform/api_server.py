"""
NG-TIP Platform API Server
REST API for ingesting threat intelligence data from AgenticCTI
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import json
import uuid

from modules.stix_processor import STIXProcessor
from modules.graph_manager import GraphManager
from modules.rag_engine import RAGEngine
from modules.llm_handler import LLMHandler
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NG-TIP Platform API",
    description="Next-Gen Threat Intelligence Platform API for data ingestion and querying",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
config = Config.from_env()
stix_processor = STIXProcessor()
graph_manager = None
rag_engine = None
llm_handler = None

# Pydantic models
class IntelligenceData(BaseModel):
    """Intelligence data from AgenticCTI"""
    url: str
    title: str
    publish_date: Optional[str] = None
    author: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    severity: str = "medium"
    confidence: float = 0.5
    timestamp: Optional[str] = None


class STIXBundleIngestion(BaseModel):
    """STIX bundle ingestion request"""
    stix_bundle: Dict[str, Any]
    source_info: Optional[Dict[str, str]] = Field(default_factory=dict)
    timestamp: Optional[str] = None


class BatchIngestionRequest(BaseModel):
    """Batch ingestion request"""
    items: List[IntelligenceData]


class GraphQueryRequest(BaseModel):
    """Graph query request"""
    entity_type: str
    entity_name: str
    depth: int = 2


class RAGSearchRequest(BaseModel):
    """RAG search request"""
    query: str
    top_k: int = 5


class IngestionResponse(BaseModel):
    """Response for ingestion requests"""
    id: str
    status: str
    message: str
    processed_at: str
    object_count: Optional[int] = None


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global graph_manager, rag_engine, llm_handler

    try:
        logger.info("Initializing NG-TIP Platform API...")

        # Initialize LLM Handler
        llm_handler = LLMHandler(
            provider=config.llm_provider,
            model=config.llm_model,
            api_key=config.llm_api_key,
            base_url=config.llm_base_url
        )

        # Initialize RAG Engine
        rag_engine = RAGEngine(
            llm_handler=llm_handler,
            embedding_model=config.embedding_model
        )

        # Initialize Graph Manager (optional)
        if config.neo4j_enabled:
            graph_manager = GraphManager(
                uri=config.neo4j_uri,
                user=config.neo4j_user,
                password=config.neo4j_password
            )
            if graph_manager.driver:
                logger.info("Graph Manager initialized successfully")
            else:
                logger.warning("Graph Manager failed to connect - graph features disabled")
        else:
            logger.info("Neo4j disabled - graph features will not be available")

        logger.info("NG-TIP Platform API initialized successfully")

    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if graph_manager:
        graph_manager.close()
    logger.info("NG-TIP Platform API shutdown complete")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "NG-TIP Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "stix_processor": stix_processor is not None,
            "graph_manager": graph_manager is not None,
            "rag_engine": rag_engine is not None,
            "llm_handler": llm_handler is not None
        }
    }
    return health_status


@app.post("/api/ingest", response_model=IngestionResponse, tags=["Ingestion"])
async def ingest_intelligence(
    data: IntelligenceData,
    background_tasks: BackgroundTasks
):
    """
    Ingest threat intelligence data from AgenticCTI.

    Processes the intelligence data and stores it in:
    - Graph database (entities and relationships)
    - RAG knowledge base (for semantic search)
    - STIX objects (for standardization)
    """
    try:
        ingestion_id = str(uuid.uuid4())
        logger.info(f"Ingesting intelligence: {data.title} (ID: {ingestion_id})")

        # Process in background
        background_tasks.add_task(process_intelligence, ingestion_id, data.dict())

        return IngestionResponse(
            id=ingestion_id,
            status="accepted",
            message="Intelligence data accepted for processing",
            processed_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error ingesting intelligence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@app.post("/api/ingest/stix", response_model=IngestionResponse, tags=["Ingestion"])
async def ingest_stix_bundle(
    bundle_data: STIXBundleIngestion,
    background_tasks: BackgroundTasks
):
    """
    Ingest STIX 2.1 bundle from AgenticCTI.

    Processes STIX objects and stores them in the graph database.
    """
    try:
        ingestion_id = str(uuid.uuid4())
        object_count = len(bundle_data.stix_bundle.get('objects', []))

        logger.info(f"Ingesting STIX bundle with {object_count} objects (ID: {ingestion_id})")

        # Process in background
        background_tasks.add_task(process_stix_bundle, ingestion_id, bundle_data.dict())

        return IngestionResponse(
            id=ingestion_id,
            status="accepted",
            message=f"STIX bundle with {object_count} objects accepted for processing",
            processed_at=datetime.utcnow().isoformat(),
            object_count=object_count
        )

    except Exception as e:
        logger.error(f"Error ingesting STIX bundle: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STIX ingestion failed: {str(e)}"
        )


@app.post("/api/ingest/batch", tags=["Ingestion"])
async def ingest_batch(
    batch_data: BatchIngestionRequest,
    background_tasks: BackgroundTasks
):
    """
    Batch ingest multiple intelligence items.
    """
    try:
        batch_id = str(uuid.uuid4())
        logger.info(f"Batch ingesting {len(batch_data.items)} items (ID: {batch_id})")

        # Process each item
        for item in batch_data.items:
            background_tasks.add_task(process_intelligence, str(uuid.uuid4()), item.dict())

        return {
            "batch_id": batch_id,
            "status": "accepted",
            "message": f"{len(batch_data.items)} items accepted for processing",
            "processed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error batch ingesting: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch ingestion failed: {str(e)}"
        )


@app.get("/api/graph/query", tags=["Query"])
async def query_graph(
    entity_type: str,
    entity_name: str,
    depth: int = 2
):
    """
    Query graph database for entity relationships.
    """
    try:
        if not graph_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Graph database not available"
            )

        logger.info(f"Querying graph: {entity_type} - {entity_name}")

        # Query graph
        result = graph_manager.get_entity_relationships(entity_name, depth=depth)

        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "depth": depth,
            "result": result
        }

    except Exception as e:
        logger.error(f"Error querying graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Graph query failed: {str(e)}"
        )


@app.post("/api/rag/search", tags=["Query"])
async def search_rag(search_request: RAGSearchRequest):
    """
    Search RAG knowledge base.
    """
    try:
        if not rag_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG engine not available"
            )

        logger.info(f"RAG search: {search_request.query}")

        # Search RAG
        results = rag_engine.search(search_request.query, top_k=search_request.top_k)

        return {
            "query": search_request.query,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error searching RAG: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG search failed: {str(e)}"
        )


@app.get("/api/statistics", tags=["Statistics"])
async def get_statistics():
    """
    Get platform statistics.
    """
    try:
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "NG-TIP",
            "version": "1.0.0",
            "graph_available": graph_manager is not None,
            "rag_available": rag_engine is not None
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statistics retrieval failed: {str(e)}"
        )


# Background processing functions
async def process_intelligence(ingestion_id: str, data: Dict[str, Any]):
    """
    Background task to process intelligence data.
    """
    try:
        logger.info(f"Processing intelligence: {ingestion_id}")

        # Add to RAG knowledge base
        if rag_engine and data.get('summary'):
            rag_engine.add_document(
                content=data['summary'],
                metadata={
                    'source': data.get('url'),
                    'title': data.get('title'),
                    'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
                    'severity': data.get('severity')
                }
            )
            logger.info(f"Added to RAG: {ingestion_id}")

        # Add entities to graph
        if graph_manager and data.get('entities'):
            entities = data['entities']

            # Create nodes for each entity type
            for entity_type, entity_values in entities.items():
                if isinstance(entity_values, list):
                    for value in entity_values:
                        graph_manager.create_entity_node(
                            entity_type=entity_type,
                            entity_name=value,
                            properties={
                                'source': data.get('url'),
                                'discovered_at': datetime.utcnow().isoformat()
                            }
                        )
                elif isinstance(entity_values, dict):
                    for key, values in entity_values.items():
                        for value in values:
                            graph_manager.create_entity_node(
                                entity_type=key,
                                entity_name=value,
                                properties={
                                    'source': data.get('url'),
                                    'discovered_at': datetime.utcnow().isoformat()
                                }
                            )

            logger.info(f"Added entities to graph: {ingestion_id}")

        logger.info(f"Processing complete: {ingestion_id}")

    except Exception as e:
        logger.error(f"Error processing intelligence {ingestion_id}: {e}", exc_info=True)


async def process_stix_bundle(ingestion_id: str, bundle_data: Dict[str, Any]):
    """
    Background task to process STIX bundle.
    """
    try:
        logger.info(f"Processing STIX bundle: {ingestion_id}")

        stix_bundle = bundle_data.get('stix_bundle', {})
        objects = stix_bundle.get('objects', [])

        # Process each STIX object
        for obj in objects:
            obj_type = obj.get('type')
            obj_name = obj.get('name', obj.get('id'))

            if graph_manager and obj_type and obj_name:
                # Create node in graph
                graph_manager.create_entity_node(
                    entity_type=obj_type,
                    entity_name=obj_name,
                    properties=obj
                )

        logger.info(f"STIX bundle processing complete: {ingestion_id}")

    except Exception as e:
        logger.error(f"Error processing STIX bundle {ingestion_id}: {e}", exc_info=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8503,
        reload=False,
        log_level="info"
    )
