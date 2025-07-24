"""
ChromaDB vector database setup and management.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorDatabase:
    """ChromaDB vector database manager."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self._embedding_function = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with optimized settings."""
        try:
            # Ensure ChromaDB directory exists
            os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
            
            # Configure ChromaDB for large collections (new client format)
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_DB_PATH
            )
            
            # Initialize embedding function
            self._embedding_function = embedding_functions.DefaultEmbeddingFunction()
            
            # Create or get main collection
            self.collection = self.client.get_or_create_collection(
                name="documents",
                embedding_function=self._embedding_function
            )
            
            logger.info(f"ChromaDB initialized at {settings.CHROMA_DB_PATH}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> bool:
        """Add a single document to the vector database."""
        return await self.add_documents(
            documents=[content],
            metadatas=[metadata],
            ids=[document_id],
            embeddings=[embedding] if embedding else None
        )
    
    async def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """Add documents to the vector database."""
        try:
            if embeddings:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            logger.info(f"Added {len(documents)} documents to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to vector database: {e}")
            return False
    
    async def add_documents_batch(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None,
        batch_size: int = 100
    ) -> bool:
        """Add documents in batches for better performance."""
        try:
            total_docs = len(documents)
            
            for i in range(0, total_docs, batch_size):
                end_idx = min(i + batch_size, total_docs)
                
                batch_documents = documents[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                batch_ids = ids[i:end_idx]
                batch_embeddings = embeddings[i:end_idx] if embeddings else None
                
                success = await self.add_documents(
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    ids=batch_ids,
                    embeddings=batch_embeddings
                )
                
                if not success:
                    logger.error(f"Failed to add batch {i//batch_size + 1}")
                    return False
                
                logger.info(f"Added batch {i//batch_size + 1}/{(total_docs-1)//batch_size + 1}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents in batches: {e}")
            return False
    
    async def similarity_search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform similarity search."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "document": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"][0] else {},
                        "distance": results["distances"][0][i] if results["distances"][0] else 0.0,
                        "relevance_score": 1.0 - results["distances"][0][i] if results["distances"][0] else 1.0
                    })
            
            return {
                "results": formatted_results,
                "total": len(formatted_results)
            }
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return {"results": [], "total": 0}
    
    async def similarity_search_with_embeddings(
        self,
        query_embeddings: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform similarity search using pre-computed embeddings."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embeddings],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results (same as above)
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "document": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"][0] else {},
                        "distance": results["distances"][0][i] if results["distances"][0] else 0.0,
                        "relevance_score": 1.0 - results["distances"][0][i] if results["distances"][0] else 1.0
                    })
            
            return {
                "results": formatted_results,
                "total": len(formatted_results)
            }
            
        except Exception as e:
            logger.error(f"Similarity search with embeddings failed: {e}")
            return {"results": [], "total": 0}
    
    async def delete_document_embeddings(self, document_id: str) -> bool:
        """Delete all embeddings for a specific document."""
        try:
            # Query for all chunks related to this document
            results = self.collection.get(
                where={"parent_document_id": document_id},
                include=["metadatas"]
            )
            
            if results["ids"]:
                await self.delete_documents(results["ids"])
                logger.info(f"Deleted {len(results['ids'])} embeddings for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete embeddings for document {document_id}: {e}")
            return False
    
    async def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents from the vector database."""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
    
    async def update_documents(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """Update existing documents in the vector database."""
        try:
            self.collection.update(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            logger.info(f"Updated {len(ids)} documents in vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update documents: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            count = self.collection.count()
            return {
                "name": self.collection.name,
                "count": count,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"name": "unknown", "count": 0, "metadata": {}}
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.collection.count()
            return {
                "name": self.collection.name,
                "document_count": count,
                "metadata": self.collection.metadata,
                "embedding_function": str(self._embedding_function)
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"name": "unknown", "document_count": 0, "metadata": {}}
    
    def reset_collection(self) -> bool:
        """Reset the collection (delete all documents)."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name="documents")
            self.collection = self.client.create_collection(
                name="documents",
                embedding_function=self._embedding_function
            )
            logger.info("Collection reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False


# Global vector database instance
vector_db = VectorDatabase()