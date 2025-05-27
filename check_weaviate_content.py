#!/usr/bin/env python3
# check_weaviate_content.py - Check what's actually in your Weaviate Cloud

import os
import json
from datetime import datetime

def check_weaviate_legal_documents():
    """Check what legal documents are in Weaviate Cloud"""
    print("🔍 CHECKING WEAVIATE CLOUD LEGAL DOCUMENTS")
    print("=" * 60)
    
    try:
        # Import the Weaviate client
        from market_reports.rag_enhanced import get_weaviate_client
        
        client = get_weaviate_client()
        if not client:
            print("❌ Could not connect to Weaviate Cloud")
            return False
        
        if not client.is_ready():
            print("❌ Weaviate Cloud is not ready")
            return False
        
        print("✅ Connected to Weaviate Cloud")
        
        # Check schema
        schema = client.schema.get()
        legal_class_found = False
        
        print("\n📋 Available Classes:")
        for class_def in schema.get("classes", []):
            class_name = class_def["class"]
            print(f"   - {class_name}")
            if class_name == "LegalDocument":
                legal_class_found = True
        
        if not legal_class_found:
            print("\n❌ LegalDocument class not found in schema!")
            print("💡 You need to create the LegalDocument class and add legal documents")
            return False
        
        print("\n✅ LegalDocument class found")
        
        # Count documents
        try:
            count_result = client.query.aggregate("LegalDocument").with_meta_count().do()
            if count_result and "data" in count_result:
                agg_data = count_result["data"]["Aggregate"].get("LegalDocument", [])
                if agg_data and "meta" in agg_data[0]:
                    doc_count = agg_data[0]["meta"]["count"]
                    print(f"\n📊 Total Legal Documents: {doc_count}")
                else:
                    print("\n❌ Could not get document count")
                    return False
            else:
                print("\n❌ Count query failed")
                return False
        except Exception as e:
            print(f"\n❌ Error counting documents: {e}")
            return False
        
        # Get sample documents
        if doc_count > 0:
            print("\n📄 Sample Documents:")
            try:
                sample_result = client.query.get("LegalDocument", [
                    "content", "documentTitle", "documentType", "jurisdiction"
                ]).with_limit(5).do()
                
                if sample_result and "data" in sample_result and "Get" in sample_result["data"]:
                    docs = sample_result["data"]["Get"].get("LegalDocument", [])
                    
                    for i, doc in enumerate(docs, 1):
                        title = doc.get("documentTitle", "No title")
                        doc_type = doc.get("documentType", "Unknown")
                        jurisdiction = doc.get("jurisdiction", "Unknown")
                        content = doc.get("content", "No content")[:100] + "..."
                        
                        print(f"\n   Document {i}:")
                        print(f"   Title: {title}")
                        print(f"   Type: {doc_type}")
                        print(f"   Jurisdiction: {jurisdiction}")
                        print(f"   Content: {content}")
                else:
                    print("   No documents retrieved")
            except Exception as e:
                print(f"   Error retrieving sample documents: {e}")
        
        # Check if semantic search is enabled
        print("\n🔍 Checking Semantic Search Capability:")
        try:
            # Try semantic search
            semantic_result = client.query.get("LegalDocument", [
                "documentTitle", "content"
            ]).with_near_text({"concepts": ["law", "legal"]}).with_limit(1).do()
            
            if semantic_result and "data" in semantic_result:
                print("   ✅ Semantic search is working!")
            else:
                print("   ❌ Semantic search failed")
        except Exception as e:
            print(f"   ❌ Semantic search error: {e}")
            print("   💡 You may need to configure text vectorization in Weaviate")
        
        # Summary and recommendations
        print("\n" + "=" * 60)
        print("📋 SUMMARY & RECOMMENDATIONS")
        print("=" * 60)
        
        if doc_count == 0:
            print("❌ No legal documents found!")
            print("💡 You need to upload legal documents to Weaviate Cloud")
            
        elif doc_count == 1:
            print("⚠️ Only 1 legal document found!")
            print("💡 Add more legal documents for better responses")
            print("💡 Current single document may not match your queries")
            
        elif doc_count < 10:
            print(f"⚠️ Only {doc_count} legal documents found")
            print("💡 Consider adding more legal documents for comprehensive coverage")
            
        else:
            print(f"✅ {doc_count} legal documents found - good coverage!")
        
        print("\n🔧 Next Steps:")
        if doc_count <= 1:
            print("1. Upload more legal documents to your Weaviate Cloud instance")
            print("2. Ensure documents have proper fields: content, documentTitle, documentType, jurisdiction")
            print("3. Enable text vectorization for semantic search")
        else:
            print("1. Test legal queries that match your document content")
            print("2. Check if documents contain relevant keywords")
            print("3. Verify semantic search is working properly")
        
        return doc_count > 0
        
    except Exception as e:
        print(f"❌ Error checking Weaviate Cloud: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_legal_rag_with_specific_query():
    """Test legal RAG with a specific query"""
    print("\n🧪 TESTING LEGAL RAG WITH SPECIFIC QUERY")
    print("=" * 60)
    
    try:
        from dependency_container import container
        
        if not container.has('legal_rag_engine'):
            print("❌ Legal RAG engine not available")
            return False
        
        legal_rag = container.get('legal_rag_engine')
        if not legal_rag:
            print("❌ Legal RAG engine is None")
            return False
        
        # Test with different queries
        test_queries = [
            "law",
            "legal",
            "company",
            "business",
            "contract",
            "regulation"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            try:
                docs = legal_rag.search_legal_documents(query, limit=2)
                print(f"   Found {len(docs)} documents")
                
                if docs:
                    for i, doc in enumerate(docs, 1):
                        title = doc.get('title', 'No title')[:50]
                        source = doc.get('source', 'Unknown')
                        print(f"   {i}. {title}... (Source: {source})")
                        
                        if 'Mock' in source:
                            print("      ⚠️ This is mock data")
                        else:
                            print("      ✅ Real document from Weaviate Cloud")
                    
                    # If we found real documents, test response generation
                    if any('Mock' not in doc.get('source', '') for doc in docs):
                        print(f"\n💬 Testing response generation for '{query}'...")
                        response = legal_rag.generate_legal_response(query)
                        
                        if response and response.get('response'):
                            print("   ✅ Response generated successfully")
                            print(f"   Response length: {len(response['response'])} characters")
                            print(f"   Documents used: {response.get('document_count', 0)}")
                            print(f"   Model: {response.get('model_used', 'unknown')}")
                        else:
                            print("   ❌ Response generation failed")
                        break
                else:
                    print("   No documents found")
            except Exception as e:
                print(f"   ❌ Error testing query '{query}': {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing legal RAG: {e}")
        return False

if __name__ == "__main__":
    print("🔧 WEAVIATE CLOUD DIAGNOSTIC TOOL")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check Weaviate content
    weaviate_ok = check_weaviate_legal_documents()
    
    if weaviate_ok:
        # Test legal RAG
        test_legal_rag_with_specific_query()
    
    print(f"\n{'=' * 60}")
    print("🏁 DIAGNOSTIC COMPLETE")
    print(f"{'=' * 60}")