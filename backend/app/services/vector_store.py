import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
from app.core.config import settings


class VectorStore:
    """Service for managing legal documents in ChromaDB."""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"description": "Indian legal documents and case laws"}
        )
    
    def search_documents(
        self, 
        query: str, 
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for relevant legal documents based on query.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of relevant documents with metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata
        )
        
        documents = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                documents.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        
        return documents
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """
        Retrieve a specific document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None
        """
        try:
            result = self.collection.get(ids=[doc_id])
            if result['documents']:
                return {
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0] if result['metadatas'] else {}
                }
        except Exception as e:
            print(f"Error retrieving document: {e}")
        return None
    
    def add_documents(
        self, 
        documents: List[str], 
        metadatas: List[Dict],
        ids: List[str]
    ) -> bool:
        """
        Add documents to the collection (for admin use).
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: List of unique IDs
            
        Returns:
            Success status
        """
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False


# Singleton instance
vector_store = VectorStore()
