"""
Configuration management for CTI GenAI Platform
"""

import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    """Platform configuration"""
    
    # LLM Settings
    llm_provider: str = "ollama"  # ollama, lmstudio, openai, anthropic, azure
    llm_model: str = "llama3.2"
    llm_api_key: Optional[str] = None
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    
    # Embedding Settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # MISP Configuration
    misp_url: Optional[str] = None
    misp_key: Optional[str] = None
    misp_verify_ssl: bool = True
    
    # OpenCTI Configuration
    opencti_url: Optional[str] = None
    opencti_token: Optional[str] = None
    
    # Neo4j Configuration (Optional - for graph features)
    neo4j_enabled: bool = True
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Vector Store Configuration
    vector_store_type: str = "chroma"  # chroma, faiss, qdrant
    vector_store_path: str = "./data/vector_store"
    
    # RAG Settings
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 5
    
    # Data Paths
    data_dir: str = "./data"
    cache_dir: str = "./cache"
    logs_dir: str = "./logs"
    
    # Application Settings
    app_name: str = "CTI GenAI Platform"
    app_version: str = "1.0.0"
    debug_mode: bool = False
    
    def __post_init__(self):
        """Create necessary directories"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.vector_store_path, exist_ok=True)
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        return cls(
            llm_provider=os.getenv('LLM_PROVIDER', 'ollama'),
            llm_model=os.getenv('LLM_MODEL', 'llama3.2'),
            llm_api_key=os.getenv('LLM_API_KEY'),
            llm_base_url=os.getenv('LLM_BASE_URL', 'http://localhost:11434'),
            misp_url=os.getenv('MISP_URL'),
            misp_key=os.getenv('MISP_API_KEY'),
            opencti_url=os.getenv('OPENCTI_URL'),
            opencti_token=os.getenv('OPENCTI_TOKEN'),
            neo4j_enabled=os.getenv('NGTIP_NEO4J_ENABLED', 'true').lower() == 'true',
            neo4j_uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            neo4j_user=os.getenv('NEO4J_USER', 'neo4j'),
            neo4j_password=os.getenv('NEO4J_PASSWORD', 'password'),
        )
