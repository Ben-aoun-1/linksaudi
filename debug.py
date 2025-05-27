#!/usr/bin/env python3
# test_semantic_search_fix.py - Test different semantic search approaches

def test_semantic_search_approaches():
    print("🔍 TESTING SEMANTIC SEARCH APPROACHES")
    print("=" * 60)
    
    try:
        from market_reports.rag_enhanced import get_weaviate_client
        
        client = get_weaviate_client()
        if not client or not client.is_ready():
            print("❌ Could not connect to Weaviate Cloud")
            return False
        
        print("✅ Connected to Weaviate Cloud")
        
        test_query = "legal document Saudi Arabia"
        properties = ["content", "documentTitle", "documentType", "jurisdiction"]
        
        # Test 1: Basic semantic search
        print(f"\n🧪 Test 1: Basic semantic search")
        try:
            result1 = (
                client.query
                .get("LegalDocument", properties)
                .with_near_text({"concepts": [test_query]})
                .with_limit(2)
                .do()
            )
            
            if result1 and "data" in result1 and "Get" in result1["data"]:
                docs = result1["data"]["Get"].get("LegalDocument", [])
                print(f"   ✅ Success: Found {len(docs)} documents")
                if docs:
                    print(f"   First doc: {docs[0].get('documentTitle', 'No title')}")
            else:
                print(f"   ❌ Failed: Result structure issue")
                print(f"   Result: {result1}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 2: Semantic search with certainty
        print(f"\n🧪 Test 2: Semantic search with certainty")
        try:
            result2 = (
                client.query
                .get("LegalDocument", properties)
                .with_near_text({
                    "concepts": [test_query],
                    "certainty": 0.7
                })
                .with_limit(2)
                .do()
            )
            
            if result2 and "data" in result2 and "Get" in result2["data"]:
                docs = result2["data"]["Get"].get("LegalDocument", [])
                print(f"   ✅ Success: Found {len(docs)} documents")
            else:
                print(f"   ❌ Failed: Result structure issue")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 3: Semantic search with distance
        print(f"\n🧪 Test 3: Semantic search with distance")
        try:
            result3 = (
                client.query
                .get("LegalDocument", properties)
                .with_near_text({
                    "concepts": [test_query],
                    "distance": 0.3
                })
                .with_limit(2)
                .do()
            )
            
            if result3 and "data" in result3 and "Get" in result3["data"]:
                docs = result3["data"]["Get"].get("LegalDocument", [])
                print(f"   ✅ Success: Found {len(docs)} documents")
            else:
                print(f"   ❌ Failed: Result structure issue")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 4: Simple query without semantic search
        print(f"\n🧪 Test 4: Basic query (no semantic search)")
        try:
            result4 = (
                client.query
                .get("LegalDocument", properties)
                .with_limit(2)
                .do()
            )
            
            if result4 and "data" in result4 and "Get" in result4["data"]:
                docs = result4["data"]["Get"].get("LegalDocument", [])
                print(f"   ✅ Success: Found {len(docs)} documents")
                if docs:
                    print(f"   First doc: {docs[0].get('documentTitle', 'No title')}")
                    print(f"   Content preview: {docs[0].get('content', '')[:100]}...")
            else:
                print(f"   ❌ Failed: Result structure issue")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 5: Check if vectors exist
        print(f"\n🧪 Test 5: Check if documents have vectors")
        try:
            result5 = (
                client.query
                .get("LegalDocument", properties)
                .with_additional("vector")
                .with_limit(1)
                .do()
            )
            
            if result5 and "data" in result5 and "Get" in result5["data"]:
                docs = result5["data"]["Get"].get("LegalDocument", [])
                if docs and "_additional" in docs[0]:
                    vector = docs[0]["_additional"].get("vector")
                    if vector:
                        print(f"   ✅ Documents have vectors (length: {len(vector)})")
                    else:
                        print(f"   ❌ Documents don't have vectors")
                        print(f"   💡 This means vectorization failed - semantic search won't work")
                else:
                    print(f"   ❌ No additional data returned")
            else:
                print(f"   ❌ Query failed")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print(f"\n" + "=" * 60)
        print("📋 RECOMMENDATIONS:")
        print("1. If Test 4 (basic query) works but semantic tests fail:")
        print("   → Your documents aren't properly vectorized")
        print("   → Check OpenAI API key configuration in Weaviate")
        print("2. If all tests fail:")
        print("   → There's a fundamental connection or schema issue")
        print("3. If semantic search works with certain parameters:")
        print("   → Use those parameters in your Legal RAG engine")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_semantic_search_approaches()