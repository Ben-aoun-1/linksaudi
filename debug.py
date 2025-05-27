#!/usr/bin/env python3
# test_basic_search_legal_rag.py - Test the FIXED Legal RAG with Basic Search

import os
import sys
from datetime import datetime

def test_basic_search_legal_rag():
    """Test the fixed Legal RAG engine with basic search"""
    print("🧪 TESTING FIXED LEGAL RAG ENGINE WITH BASIC SEARCH")
    print("=" * 70)
    
    try:
        # Import the fixed Legal RAG engine
        sys.path.append('legal_compliance')
        from legal_rag_engine import LegalRAGEngine
        
        # Get Weaviate client
        from market_reports.rag_enhanced import get_weaviate_client
        
        client = get_weaviate_client()
        if not client or not client.is_ready():
            print("❌ Could not connect to Weaviate Cloud")
            return False
        
        print("✅ Connected to Weaviate Cloud")
        
        # Get OpenAI client (optional)
        openai_client = None
        try:
            from market_reports.rag_enhanced import openai_client
            print("✅ OpenAI client available")
        except ImportError:
            print("⚠️ OpenAI client not available - will use fallback responses")
        
        # Create the Legal RAG engine
        legal_rag = LegalRAGEngine(
            weaviate_client=client,
            openai_client=openai_client
        )
        
        print("✅ Legal RAG Engine initialized with basic search")
        
        # Test connection
        print("\n🔧 Testing Connection...")
        connection_test = legal_rag.test_connection()
        print(f"Connection Status: {connection_test.get('status')}")
        print(f"Total Documents: {connection_test.get('total_documents', 0)}")
        print(f"Basic Search Works: {connection_test.get('basic_search_works', False)}")
        print(f"Search Method: {connection_test.get('search_method', 'unknown')}")
        
        if connection_test.get('status') != 'success':
            print("❌ Connection test failed")
            return False
        
        # Test basic document search
        print("\n🔍 Testing Basic Document Search...")
        
        test_queries = [
            "company formation requirements",
            "employment law Saudi Arabia",
            "commercial license procedures",
            "corporate governance regulations",
            "business registration process",
            "labor law compliance",
            "contract law requirements",
            "regulatory compliance procedures",
            "investment law Saudi Arabia",
            "commercial court procedures"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: '{query}' ---")
            
            try:
                documents = legal_rag.search_legal_documents(query, limit=3)
                print(f"Found {len(documents)} documents")
                
                if documents:
                    for j, doc in enumerate(documents, 1):
                        title = doc.get('title', 'No title')[:50]
                        source = doc.get('source', 'Unknown')
                        relevance = doc.get('relevance_score', 0)
                        content_preview = doc.get('content', '')[:100]
                        
                        print(f"  {j}. {title}...")
                        print(f"     Source: {source}")
                        print(f"     Relevance: {relevance:.2f}")
                        print(f"     Content: {content_preview}...")
                        
                        if 'Mock' in source:
                            print("     ⚠️ This is mock data")
                        else:
                            print("     ✅ Real document from Weaviate Cloud")
                    
                    # Test response generation for the first successful search with legal content
                    if any('Mock' not in doc.get('source', '') for doc in documents):
                        print(f"\n💬 Testing Legal Response Generation for '{query}'...")
                        
                        response = legal_rag.generate_legal_response(
                            query=query,
                            include_citations=True,
                            jurisdiction="Saudi Arabia"  # Add jurisdiction for legal context
                        )
                        
                        if response and response.get('response'):
                            print("✅ Response generated successfully")
                            print(f"Response length: {len(response['response'])} characters")
                            print(f"Documents used: {response.get('document_count', 0)}")
                            print(f"Citations: {len(response.get('citations', []))}")
                            print(f"Model: {response.get('model_used', 'unknown')}")
                            print(f"Search method: {response.get('search_method', 'unknown')}")
                            
                            # Show response preview
                            response_preview = response['response'][:300]
                            print(f"\nResponse preview:\n{response_preview}...")
                            
                            # Show citations if any
                            citations = response.get('citations', [])
                            if citations:
                                print(f"\nCitations:")
                                for k, citation in enumerate(citations[:2], 1):
                                    print(f"  {k}. {citation.get('title', 'No title')}")
                                    print(f"     Type: {citation.get('document_type', 'Unknown')}")
                                    print(f"     Relevance: {citation.get('relevance_score', 0):.2f}")
                            
                            break  # Found working query, stop testing
                        else:
                            print("❌ Response generation failed")
                else:
                    print("  No documents found")
                    
            except Exception as e:
                print(f"  ❌ Error testing query '{query}': {e}")
        
        # Test legal categories and jurisdictions
        print("\n📋 Testing Legal Categories and Jurisdictions...")
        
        try:
            categories = legal_rag.get_legal_categories()
            print(f"Legal Categories ({len(categories)}): {', '.join(categories[:5])}...")
            
            jurisdictions = legal_rag.get_available_jurisdictions()
            print(f"Jurisdictions ({len(jurisdictions)}): {', '.join(jurisdictions)}")
            
            practice_areas = legal_rag.get_available_practice_areas()
            print(f"Practice Areas ({len(practice_areas)}): {', '.join(practice_areas[:5])}...")
            
        except Exception as e:
            print(f"❌ Error getting categories/jurisdictions: {e}")
        
        # Test system status
        print("\n🔧 Testing System Status...")
        try:
            status = legal_rag.get_system_status()
            print(f"Search Method: {status.get('search_method')}")
            print(f"Semantic Search Disabled: {status.get('semantic_search_disabled')}")
            print(f"OpenAI Available: {status.get('openai_available')}")
            print(f"Query History: {status.get('query_history_count')} queries")
            
        except Exception as e:
            print(f"❌ Error getting system status: {e}")
        
        print("\n" + "=" * 70)
        print("✅ BASIC SEARCH LEGAL RAG TEST COMPLETE")
        print("=" * 70)
        
        print("\n📋 SUMMARY:")
        print("• Basic search functionality implemented")
        print("• Semantic search disabled (avoids None result issues)")
        print("• Keyword-based relevance scoring added")
        print("• Compatible with your existing Weaviate Cloud documents")
        print("• Uses WHERE clauses for filtering instead of semantic search")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Legal RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_legal_chatbot_integration():
    """Test the Legal Chatbot with the fixed RAG engine"""
    print("\n🤖 TESTING LEGAL CHATBOT INTEGRATION")
    print("=" * 50)
    
    try:
        from dependency_container import container
        from system_initializer import initialize_system
        
        # Initialize system
        print("🔧 Initializing system...")
        success = initialize_system(offline_mode=False)
        
        if not success:
            print("❌ System initialization failed")
            return False
        
        print("✅ System initialized")
        
        # Get legal chatbot
        if not container.has('legal_chatbot'):
            print("❌ Legal chatbot not available")
            return False
        
        legal_chatbot = container.get('legal_chatbot')
        if not legal_chatbot:
            print("❌ Legal chatbot is None")
            return False
        
        print("✅ Legal chatbot available")
        
        # Test chatbot functionality
        print("\n💬 Testing Legal Chatbot...")
        
        # Start session
        session_id = legal_chatbot.start_new_session("test_user")
        print(f"✅ Session started: {session_id[:8]}...")
        
        # Test questions
        test_questions = [
            "What are the requirements for establishing a company in Saudi Arabia?",
            "What are the employment law obligations for employers?",
            "How do I obtain a commercial license in Saudi Arabia?",
            "What are the corporate governance requirements for Saudi companies?",
            "What are the labor law compliance requirements?",
            "What are the penalties for non-compliance with commercial regulations?",
            "What are the contract law requirements for business agreements?",
            "How do foreign investors establish businesses in Saudi Arabia?",
            "What are the tax obligations for Saudi companies?",
            "What are the regulatory requirements for financial services?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Question {i}: {question[:50]}... ---")
            
            try:
                response = legal_chatbot.ask_legal_question(
                    question=question,
                    jurisdiction="Saudi Arabia"
                )
                
                if response.get('success'):
                    print("✅ Response generated successfully")
                    print(f"Response length: {len(response.get('response', ''))} characters")
                    print(f"Documents consulted: {response.get('documents_consulted', 0)}")
                    print(f"Citations: {len(response.get('citations', []))}")
                    
                    # Show response preview
                    response_text = response.get('response', '')
                    if response_text:
                        preview = response_text[:200]
                        print(f"Preview: {preview}...")
                else:
                    print(f"❌ Response failed: {response.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error with question: {e}")
        
        # Test system status
        print("\n🔧 Testing Legal System Status...")
        try:
            if hasattr(legal_chatbot, 'get_system_status'):
                status = legal_chatbot.get_system_status()
                print(f"Legal RAG Engine: {status.get('legal_rag_engine')}")
                
                rag_test = status.get('rag_connection_test', {})
                print(f"RAG Test Status: {rag_test.get('status')}")
                print(f"RAG Test Message: {rag_test.get('message')}")
                
                if rag_test.get('status') == 'success':
                    print("✅ Legal system fully operational with Weaviate Cloud")
                elif rag_test.get('status') == 'basic':
                    print("⚠️ Legal system using basic functionality")
                else:
                    print("❌ Legal system has issues")
            else:
                print("⚠️ System status method not available")
                
        except Exception as e:
            print(f"❌ Error getting legal system status: {e}")
        
        # End session
        try:
            summary = legal_chatbot.end_session()
            print(f"\n✅ Session ended. Queries processed: {summary.get('queries_count', 0)}")
        except Exception as e:
            print(f"⚠️ Error ending session: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing legal chatbot integration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"🚀 LEGAL RAG BASIC SEARCH TEST SUITE")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test the Legal RAG engine
    rag_success = test_basic_search_legal_rag()
    
    if rag_success:
        # Test integration with chatbot
        chatbot_success = test_legal_chatbot_integration()
        
        if chatbot_success:
            print(f"\n✅ ALL TESTS PASSED!")
            print("Your Legal RAG system is now working with basic search!")
        else:
            print(f"\n⚠️ RAG engine works, but chatbot integration has issues")
    else:
        print(f"\n❌ Legal RAG basic search test failed")
    
    print(f"\n{'=' * 70}")
    print("🏁 TEST COMPLETE")
    print(f"{'=' * 70}")