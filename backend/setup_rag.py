#!/usr/bin/env python3
"""
Quick setup script to populate the RAG system with regulatory data
"""

import os
import time
from chromadb import Client
from chromadb.config import Settings

def populate_regulatory_database():
    """Populate the ChromaDB with basic regulatory information"""
    
    # Sample SEBI regulations for demonstration
    sebi_regulations = [
        {
            "id": "SEBI-FUTP-1",
            "title": "Prohibition of Fraudulent and Unfair Trade Practices",
            "content": """SEBI prohibits any person from:
            1. Making misleading statements or representations
            2. Artificially influencing the price of securities
            3. Spreading false or misleading information about companies
            4. Creating false market conditions
            5. Promising guaranteed returns on stock investments
            6. Manipulating stock prices through coordinated buying/selling"""
        },
        {
            "id": "SEBI-PDD-1", 
            "title": "Pump and Dump Schemes",
            "content": """Pump and dump schemes involve:
            1. Artificially inflating stock prices through misleading positive statements
            2. Creating false sense of urgency (buy now, limited time)
            3. Using social media to spread false information
            4. Promising unrealistic returns (100%+, guaranteed profits)
            5. Targeting small-cap or penny stocks
            6. Coordinated campaigns across multiple platforms"""
        },
        {
            "id": "SEBI-INSIDER-1",
            "title": "Insider Trading Prohibition", 
            "content": """SEBI prohibits trading based on:
            1. Unpublished price sensitive information (UPSI)
            2. Information about mergers, acquisitions, takeovers
            3. Financial results before public announcement
            4. Board decisions not yet disclosed
            5. Any material information that could affect stock price
            6. Information obtained through insider sources"""
        },
        {
            "id": "SEBI-ADVISOR-1",
            "title": "Investment Adviser Regulations",
            "content": """Investment advisers must:
            1. Be registered with SEBI (registration number format: INH/INA)
            2. Cannot guarantee returns or promise specific profits
            3. Must disclose conflicts of interest
            4. Cannot use misleading advertisements
            5. Must maintain proper records and compliance
            6. Cannot charge performance-based fees except in specific cases"""
        },
        {
            "id": "SEBI-IPO-1",
            "title": "IPO Fraud Prevention",
            "content": """Common IPO frauds include:
            1. Fake IPO announcements or pre-IPO investments
            2. Guaranteed allotment promises
            3. Grey market premium manipulation
            4. Fake SEBI approval claims
            5. Unlisted company share scams
            6. Premium pricing for guaranteed shares"""
        }
    ]
    
    try:
        # Initialize ChromaDB
        chroma_db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        os.makedirs(chroma_db_path, exist_ok=True)
        
        chroma_client = Client(Settings(persist_directory=chroma_db_path))
        collection = chroma_client.get_or_create_collection("sebi_docs")
        
        print("🗄️ Populating regulatory database...")
        
        for reg in sebi_regulations:
            # Simple embedding simulation (in production, use proper embeddings)
            doc_text = f"{reg['title']} - {reg['content']}"
            
            collection.add(
                documents=[doc_text],
                metadatas=[{"id": reg["id"], "title": reg["title"]}],
                ids=[reg["id"]]
            )
            
            print(f"✅ Added: {reg['title']}")
            time.sleep(0.1)  # Small delay to avoid overwhelming the system
        
        print(f"\n✅ Successfully populated database with {len(sebi_regulations)} regulatory documents")
        print(f"📊 Total documents in collection: {collection.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        return False

def test_rag_retrieval():
    """Test RAG retrieval after population"""
    try:
        from regulatory_verification import get_relevant_regulations
        
        print("\n🔍 Testing RAG retrieval...")
        
        test_queries = [
            "guaranteed returns",
            "pump and dump",
            "insider trading", 
            "IPO fraud"
        ]
        
        for query in test_queries:
            print(f"\n Query: {query}")
            result = get_relevant_regulations(query, use_gemini_embed=False)
            
            if result.get('success') and result.get('count', 0) > 0:
                print(f"✅ Found {result['count']} relevant regulations")
                for reg in result.get('regulations', [])[:1]:  # Show first result
                    print(f"   📋 {reg['text'][:100]}...")
            else:
                print(f"❌ No regulations found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing RAG: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up RAG system for SEBI fraud detection")
    print("=" * 60)
    
    # Populate database
    if populate_regulatory_database():
        # Test retrieval
        test_rag_retrieval()
        
        print("\n" + "="*60)
        print("✅ RAG system setup complete!")
        print("💡 You can now run test_rag_agents.py again to see improved results")
    else:
        print("\n❌ Setup failed")
