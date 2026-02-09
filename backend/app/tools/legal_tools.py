from typing import Dict, List
from app.services.vector_store import vector_store


def search_legal_documents(query: str, max_results: int = 5) -> Dict:
    """
    Tool for searching relevant legal documents and case laws.
    
    Args:
        query: The search query describing what legal information is needed
        max_results: Maximum number of documents to retrieve (default: 5)
    
    Returns:
        Dictionary containing search results with document content and metadata
    """
    documents = vector_store.search_documents(query, n_results=max_results)
    
    return {
        "query": query,
        "results_count": len(documents),
        "documents": documents
    }


def get_document_by_reference(doc_id: str) -> Dict:
    """
    Tool for retrieving a specific legal document by its reference ID.
    
    Args:
        doc_id: The unique identifier of the legal document
    
    Returns:
        Dictionary containing the document content and metadata
    """
    document = vector_store.get_document_by_id(doc_id)
    
    if document:
        return {
            "success": True,
            "document": document
        }
    else:
        return {
            "success": False,
            "error": f"Document with ID '{doc_id}' not found"
        }


# Tool definitions for DeepAgent
LEGAL_TOOLS = [
    {
        "name": "search_legal_documents",
        "description": "Search for relevant Indian legal documents, case laws, statutes, and legal precedents based on a query. Use this when you need to find specific legal information, case references, or statutory provisions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query describing what legal information is needed (e.g., 'Section 420 IPC fraud cases', 'consumer protection act 2019')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of documents to retrieve",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_document_by_reference",
        "description": "Retrieve a specific legal document using its reference ID or citation. Use this when you have a specific document identifier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "The unique identifier or reference of the legal document"
                }
            },
            "required": ["doc_id"]
        }
    }
]


# Tool execution mapping
TOOL_FUNCTIONS = {
    "search_legal_documents": search_legal_documents,
    "get_document_by_reference": get_document_by_reference
}
