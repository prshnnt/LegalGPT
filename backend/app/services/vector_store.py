import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


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
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )

            documents = []
            if not results.get('documents') or not results['documents'][0]:
                return documents

            for i in range(len(results['documents'][0])):
                documents.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results.get('metadatas') and len(results['metadatas'][0]) > i else {},
                    'distance': results['distances'][0][i] if results.get('distances') and len(results['distances'][0]) > i else None
                })

            return documents
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

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
            if result.get('documents') and len(result['documents']) > 0:
                return {
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0] if result.get('metadatas') and len(result['metadatas']) > 0 else {}
                }
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
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
        if not documents or not metadatas or not ids:
            logger.error("Cannot add empty documents/metadatas/ids")
            return False

        if len(documents) != len(metadatas) or len(documents) != len(ids):
            logger.error(
                f"Length mismatch: {len(documents)} documents, "
                f"{len(metadatas)} metadatas, {len(ids)} ids"
            )
            return False

        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False


# Singleton instance
vector_store = VectorStore()
