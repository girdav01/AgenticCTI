# Architecture Documentation

## System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Web Interface (Streamlit)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │Intel     │  │   AI     │  │  Graph   │  │  STIX    │  │Analytics ││
│  │Search    │  │Assistant │  │ Explorer │  │ Explorer │  │Dashboard ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Core Platform Logic                             │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                     Configuration Manager                        │  │
│  │  • Environment variables  • Runtime settings  • API keys         │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────┐          ┌──────────────┐            ┌──────────────┐
│ LLM Handler  │          │  RAG Engine  │            │Graph Manager │
│              │          │              │            │              │
│ ┌──────────┐ │          │ ┌──────────┐ │            │ ┌──────────┐ │
│ │  Ollama  │ │          │ │Embeddings│ │            │ │  Neo4j   │ │
│ ├──────────┤ │          │ ├──────────┤ │            │ │  Cypher  │ │
│ │LM Studio │ │◄────────►│ │ ChromaDB │ │◄──────────►│ │  APOC    │ │
│ ├──────────┤ │          │ ├──────────┤ │            │ │   GDS    │ │
│ │ OpenAI   │ │          │ │ Chunking │ │            │ └──────────┘ │
│ ├──────────┤ │          │ │Retrieval │ │            │              │
│ │Anthropic │ │          │ └──────────┘ │            └──────────────┘
│ └──────────┘ │          │              │
└──────────────┘          └──────────────┘
        │                         │
        └─────────┬───────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Threat Intelligence Sources                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐            │
│  │     MISP     │    │   OpenCTI    │    │    STIX      │            │
│  │              │    │              │    │  Processor   │            │
│  │ • Events     │    │ • Indicators │    │              │            │
│  │ • Attributes │    │ • Actors     │    │ • Parser     │            │
│  │ • Tags       │    │ • Malware    │    │ • Validator  │            │
│  │ • STIX Export│    │ • Campaigns  │    │ • Generator  │            │
│  │              │    │ • GraphQL    │    │              │            │
│  └──────────────┘    └──────────────┘    └──────────────┘            │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Data Storage Layer                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐            │
│  │  Vector DB   │    │   Graph DB   │    │  File Store  │            │
│  │  (ChromaDB)  │    │   (Neo4j)    │    │  (Local FS)  │            │
│  └──────────────┘    └──────────────┘    └──────────────┘            │
└────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. LLM Handler

**Purpose**: Abstraction layer for multiple LLM providers

**Providers Supported**:
- **Ollama**: Local, open-source models
- **LM Studio**: Desktop local models
- **OpenAI**: GPT-3.5, GPT-4
- **Anthropic**: Claude models
- **Azure**: Azure OpenAI

**Key Features**:
- Unified API across providers
- Automatic failover
- Response caching
- Token management

**Code Location**: `modules/llm_handler.py`

```python
# Usage Example
llm = LLMHandler(
    provider="ollama",
    model="llama3.2",
    base_url="http://localhost:11434"
)

response = llm.generate("What is APT28?")
```

### 2. RAG Engine

**Purpose**: Retrieval-Augmented Generation for enhanced responses

**Components**:
- **Embedding Model**: Sentence transformers for vector generation
- **Vector Store**: ChromaDB for similarity search
- **Document Chunker**: Intelligent text splitting
- **Retrieval**: Semantic + keyword search

**Workflow**:
```
Document → Chunk → Embed → Store
Query → Embed → Retrieve → Context → LLM → Response
```

**Code Location**: `modules/rag_engine.py`

```python
# Usage Example
rag = RAGEngine(llm_handler=llm)

# Add document
rag.add_document(
    content="Threat report...",
    metadata={"source": "ACME", "tlp": "AMBER"}
)

# Search
results = rag.search("APT campaigns", top_k=5)

# RAG query
response = rag.generate_with_rag("Explain APT28 tactics")
```

### 3. Graph Manager

**Purpose**: Manage threat intelligence relationships in graph database

**Capabilities**:
- Create nodes (Threat Actors, Malware, Campaigns, Indicators)
- Create relationships (USES, TARGETS, ATTRIBUTED_TO)
- Query relationships (BFS, DFS, shortest path)
- Import/Export STIX bundles
- Graph algorithms (centrality, community detection)

**Node Types**:
- ThreatActor
- Malware
- Campaign
- Indicator
- AttackPattern
- Vulnerability

**Relationship Types**:
- USES
- TARGETS
- ATTRIBUTED_TO
- MITIGATES
- EXPLOITS
- INDICATES

**Code Location**: `modules/graph_manager.py`

```cypher
// Example Cypher Query
MATCH (ta:ThreatActor)-[:USES]->(m:Malware)-[:INDICATES]->(i:Indicator)
WHERE ta.name = 'APT28'
RETURN ta, m, i
```

### 4. MISP Integration

**Purpose**: Interface with MISP threat intelligence platform

**API Endpoints Used**:
- `/events/restSearch` - Search events
- `/attributes/restSearch` - Search IOCs
- `/events/stix2/download` - Export STIX
- `/tags` - Retrieve tags

**Data Retrieved**:
- Events with attributes
- IOCs (IPs, domains, hashes)
- Tags and taxonomies
- Threat level indicators

**Code Location**: `modules/misp_integration.py`

### 5. OpenCTI Integration

**Purpose**: GraphQL integration with OpenCTI platform

**Queries Supported**:
- Indicators
- Threat Actors
- Malware
- Attack Patterns (MITRE ATT&CK)
- Reports
- Observables

**Code Location**: `modules/opencti_integration.py`

### 6. STIX Processor

**Purpose**: Handle STIX 2.1 objects

**Supported Objects**:
- Indicator
- Threat-Actor
- Malware
- Campaign
- Attack-Pattern
- Vulnerability
- Relationship
- Bundle

**Operations**:
- Create STIX objects
- Parse STIX bundles
- Validate STIX format
- Extract IOCs
- Convert to graph format

**Code Location**: `modules/stix_processor.py`

## Data Flow Diagrams

### Intelligence Search Flow

```
User Query
    │
    ▼
┌─────────────────┐
│  Parse Query    │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬────────┐
    │         │         │        │
    ▼         ▼         ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ MISP │ │OpenCTI│ │ RAG  │ │Graph │
└───┬──┘ └───┬──┘ └───┬──┘ └───┬──┘
    │        │        │        │
    └────────┴────┬───┴────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Aggregate      │
         │ Results        │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ LLM Generate   │
         │ Summary        │
         └────────┬───────┘
                  │
                  ▼
            User Response
```

### RAG Document Ingestion Flow

```
Document Upload
    │
    ▼
┌─────────────────┐
│  Extract Text   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Chunk Text     │
│  (1000 chars)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generate       │
│  Embeddings     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Store in       │
│  ChromaDB       │
└────────┬────────┘
         │
         ▼
    Indexed
```

### STIX Import Flow

```
STIX Bundle
    │
    ▼
┌─────────────────┐
│  Parse JSON     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validate       │
│  STIX Format    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐ ┌──────┐
│ RAG  │ │Graph │
│Store │ │ DB   │
└──────┘ └──────┘
```

## Deployment Architectures

### Local Development

```
┌──────────────────────────┐
│  Developer Laptop        │
│                          │
│  ┌────────────────────┐  │
│  │  CTI Platform      │  │
│  │  (Streamlit)       │  │
│  └────────────────────┘  │
│           │              │
│  ┌────────┴────────┐     │
│  │                 │     │
│  ▼                 ▼     │
│ ┌────┐         ┌─────┐  │
│ │Olla│         │Neo4j│  │
│ │ma  │         │     │  │
│ └────┘         └─────┘  │
└──────────────────────────┘
```

### Docker Deployment

```
┌────────────────────────────────────┐
│  Docker Host                       │
│                                    │
│  ┌──────────┐  ┌──────────┐       │
│  │   CTI    │  │  Ollama  │       │
│  │ Platform │  │          │       │
│  └────┬─────┘  └─────┬────┘       │
│       │              │            │
│  ┌────┴──────────────┴────┐       │
│  │      Docker Network    │       │
│  └────┬──────────────┬────┘       │
│       │              │            │
│  ┌────▼────┐    ┌────▼────┐       │
│  │ Neo4j   │    │ OpenCTI │       │
│  └─────────┘    └─────────┘       │
└────────────────────────────────────┘
```

### Enterprise Deployment

```
┌────────────────────────────────────────────┐
│  Load Balancer                             │
└─────────────┬──────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐       ┌─────────┐
│  App 1  │       │  App 2  │
└────┬────┘       └────┬────┘
     │                 │
     └────────┬────────┘
              │
    ┌─────────┴─────────┬─────────┐
    │                   │         │
    ▼                   ▼         ▼
┌─────────┐       ┌─────────┐ ┌─────────┐
│ Neo4j   │       │ChromaDB │ │  MISP   │
│Cluster  │       │Cluster  │ │         │
└─────────┘       └─────────┘ └─────────┘
```

## Security Architecture

### Authentication Flow

```
User → Streamlit → [Future: Auth Service] → Platform
```

### Data Encryption

- **In Transit**: TLS 1.3 for all external connections
- **At Rest**: Encrypted volumes for data storage
- **Secrets**: Environment variables, never in code

### Network Isolation

```
┌─────────────────────────────────┐
│  DMZ (Public Network)           │
│  ┌───────────────────┐          │
│  │  Load Balancer    │          │
│  └────────┬──────────┘          │
└───────────┼──────────────────────┘
            │
┌───────────┼──────────────────────┐
│  App Tier │                      │
│  ┌────────▼──────────┐           │
│  │  CTI Platform     │           │
│  └────────┬──────────┘           │
└───────────┼──────────────────────┘
            │
┌───────────┼──────────────────────┐
│  Data Tier│                      │
│  ┌────────▼──────────┬─────────┐ │
│  │  Neo4j  │ChromaDB │  MISP  │ │
│  └─────────┴─────────┴────────┘ │
└──────────────────────────────────┘
```

## Scalability Considerations

### Horizontal Scaling

- **Application**: Multiple Streamlit instances behind load balancer
- **Vector DB**: ChromaDB clustering or Qdrant
- **Graph DB**: Neo4j Causal Cluster
- **LLM**: Ollama cluster or cloud API

### Vertical Scaling

- **LLM Server**: GPU acceleration for local models
- **Vector Store**: SSD storage for faster retrieval
- **Graph DB**: RAM allocation for graph algorithms

### Caching Strategy

```
Query → Cache Check → Hit: Return
                    → Miss: Compute → Cache → Return
```

## Monitoring & Observability

### Metrics to Track

- Request latency
- LLM response time
- Vector search performance
- Graph query execution time
- Cache hit rate
- Error rates

### Logging Levels

- **ERROR**: System failures
- **WARN**: Degraded performance
- **INFO**: Normal operations
- **DEBUG**: Detailed diagnostics

---

This architecture supports the core mission: **Democratizing threat intelligence through AI and making it accessible to all security teams**.
