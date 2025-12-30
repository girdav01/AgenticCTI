"""
RAG (Retrieval-Augmented Generation) Engine
Handles document embedding, indexing, and retrieval
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import hashlib
import json

@dataclass
class Document:
    """Document representation"""
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    doc_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.doc_id:
            # Generate unique ID from content hash
            self.doc_id = hashlib.md5(self.content.encode()).hexdigest()

class RAGEngine:
    """RAG engine for CTI platform"""
    
    def __init__(
        self,
        llm_handler,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        vector_store_path: str = "./data/vector_store",
        collection_name: str = "cti_intelligence"
    ):
        self.llm_handler = llm_handler
        self.embedding_model_name = embedding_model
        self.vector_store_path = vector_store_path
        self.collection_name = collection_name
        
        # Initialize embedding model
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            # Create persistent client
            self.chroma_client = chromadb.PersistentClient(
                path=self.vector_store_path
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            print(f"Vector store initialized: {self.collection.count()} documents")
        except Exception as e:
            raise Exception(f"Failed to initialize vector store: {str(e)}")
    
    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - chunk_overlap
        
        return chunks
    
    def add_document(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk: bool = True
    ) -> List[str]:
        """Add document to vector store"""
        if metadata is None:
            metadata = {}
        
        # Chunk the document if needed
        if chunk:
            chunks = self._chunk_text(content)
        else:
            chunks = [content]
        
        doc_ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for i, chunk_text in enumerate(chunks):
            # Create document
            doc = Document(
                content=chunk_text,
                metadata={
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            
            # Generate embedding
            embedding = self.embedding_model.encode(chunk_text)
            
            doc_ids.append(f"{doc.doc_id}_{i}")
            embeddings.append(embedding.tolist())
            documents.append(chunk_text)
            metadatas.append(doc.metadata)
        
        # Add to vector store
        try:
            self.collection.add(
                ids=doc_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            print(f"Added {len(chunks)} chunks to vector store")
            return doc_ids
        except Exception as e:
            raise Exception(f"Failed to add document: {str(e)}")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Search in vector store
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=filter_metadata
            )
            
            # Format results
            documents = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    doc = {
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                        'id': results['ids'][0][i]
                    }
                    documents.append(doc)
            
            return documents
        except Exception as e:
            raise Exception(f"Search error: {str(e)}")
    
    def search_with_context(
        self,
        query: str,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Search and return formatted context for LLM"""
        results = self.search(query, top_k=top_k)
        
        context_parts = []
        for i, doc in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}] (Relevance: {doc['score']:.2f})\n{doc['content']}"
            )
        
        return {
            'query': query,
            'context': '\n\n'.join(context_parts),
            'sources': results
        }
    
    def generate_with_rag(
        self,
        query: str,
        top_k: int = 5,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using RAG"""
        # Retrieve relevant documents
        search_results = self.search_with_context(query, top_k=top_k)
        
        # Build prompt
        if system_prompt is None:
            system_prompt = "You are a cyber threat intelligence analyst. Use the provided context to answer questions accurately."
        
        full_prompt = f"""{system_prompt}

Context from knowledge base:
{search_results['context']}

Question: {query}

Provide a detailed, accurate response based on the context above."""
        
        # Generate response
        response = self.llm_handler.generate(full_prompt)
        
        return {
            'query': query,
            'response': response,
            'sources': search_results['sources'],
            'context': search_results['context']
        }
    
    def delete_document(self, doc_id: str):
        """Delete document from vector store"""
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                print(f"Deleted document {doc_id}")
        except Exception as e:
            raise Exception(f"Failed to delete document: {str(e)}")
    
    def clear_collection(self):
        """Clear all documents from collection"""
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print("Collection cleared")
        except Exception as e:
            raise Exception(f"Failed to clear collection: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            'total_documents': self.collection.count(),
            'collection_name': self.collection_name,
            'embedding_model': self.embedding_model_name
        }
