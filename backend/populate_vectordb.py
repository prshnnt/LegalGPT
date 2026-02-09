"""
Script to populate ChromaDB with sample legal documents.

This is a template - replace with your actual legal documents.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.vector_store import vector_store


def add_sample_documents():
    """Add sample legal documents to ChromaDB."""
    
    # Sample Indian legal documents (replace with actual content)
    documents = [
        """Section 420 of the Indian Penal Code (IPC) deals with cheating and dishonestly inducing 
        delivery of property. Whoever cheats and thereby dishonestly induces the person deceived to 
        deliver any property to any person, or to make, alter or destroy the whole or any part of a 
        valuable security, or anything which is signed or sealed, and which is capable of being 
        converted into a valuable security, shall be punished with imprisonment of either description 
        for a term which may extend to seven years, and shall also be liable to fine.""",
        
        """The Consumer Protection Act, 2019 is an Act of the Parliament of India which aims to 
        protect the rights of consumers by establishing authorities for timely and effective 
        administration and settlement of consumer disputes. The Act replaced the Consumer Protection 
        Act, 1986. Key features include: establishment of the Central Consumer Protection Authority, 
        consumer rights, product liability, unfair trade practices, and e-commerce regulations.""",
        
        """Article 21 of the Constitution of India provides that no person shall be deprived of his 
        life or personal liberty except according to procedure established by law. This fundamental 
        right is considered the heart and soul of the Constitution. The Supreme Court has interpreted 
        this right expansively to include right to privacy, right to livelihood, right to clean 
        environment, and many other rights.""",
        
        """The Bharatiya Nyaya Sanhita (BNS), 2023 is a criminal code that replaced the Indian Penal 
        Code of 1860. It was passed by the Parliament of India in December 2023 and came into effect 
        on 1 July 2024. The BNS modernizes India's criminal law framework and addresses contemporary 
        issues while retaining the core principles of criminal jurisprudence.""",
        
        """Section 375 IPC defines rape and its various circumstances. The section has been amended 
        multiple times to strengthen provisions against sexual offenses. The punishment for rape 
        under Section 376 IPC is rigorous imprisonment for a term which shall not be less than seven 
        years but may extend to imprisonment for life, and shall also be liable to fine."""
    ]
    
    # Metadata for each document
    metadatas = [
        {
            "source": "IPC",
            "section": "420",
            "type": "statute",
            "category": "criminal_law",
            "title": "Cheating and dishonestly inducing delivery of property"
        },
        {
            "source": "Consumer Protection Act",
            "year": "2019",
            "type": "statute",
            "category": "consumer_law",
            "title": "Consumer Protection Act Overview"
        },
        {
            "source": "Constitution of India",
            "article": "21",
            "type": "constitutional_provision",
            "category": "fundamental_rights",
            "title": "Protection of life and personal liberty"
        },
        {
            "source": "Bharatiya Nyaya Sanhita",
            "year": "2023",
            "type": "statute",
            "category": "criminal_law",
            "title": "BNS 2023 Overview"
        },
        {
            "source": "IPC",
            "section": "375-376",
            "type": "statute",
            "category": "criminal_law",
            "title": "Rape and Sexual Offenses"
        }
    ]
    
    # Unique IDs for each document
    ids = [
        "ipc_420",
        "consumer_protection_2019",
        "constitution_article_21",
        "bns_2023_overview",
        "ipc_375_376"
    ]
    
    # Add to ChromaDB
    print("\n" + "="*50)
    print("Adding Sample Legal Documents to ChromaDB")
    print("="*50 + "\n")
    
    success = vector_store.add_documents(documents, metadatas, ids)
    
    if success:
        print(f"✓ Successfully added {len(documents)} documents to ChromaDB")
        print("\nDocument IDs:")
        for doc_id in ids:
            print(f"  - {doc_id}")
        print("\n" + "="*50)
        print("Documents ready for retrieval!")
        print("="*50 + "\n")
    else:
        print("✗ Failed to add documents to ChromaDB")
        print("Check if ChromaDB is properly configured.")


def test_search():
    """Test document search functionality."""
    print("\n" + "="*50)
    print("Testing Document Search")
    print("="*50 + "\n")
    
    test_queries = [
        "Section 420 IPC fraud",
        "consumer rights protection",
        "Article 21 fundamental rights"
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        results = vector_store.search_documents(query, n_results=2)
        print(f"Found {len(results)} results")
        if results:
            print(f"Top result: {results[0]['metadata'].get('title', 'N/A')}")
        print()


def main():
    """Main function."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_search()
    else:
        add_sample_documents()
        print("\nRun with --test flag to test search functionality:")
        print("  python populate_vectordb.py --test")


if __name__ == "__main__":
    main()
