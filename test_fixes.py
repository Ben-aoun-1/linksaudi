#!/usr/bin/env python3
# test_fixes.py - Quick test script to verify the fixes

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

def test_imports():
    """Test all critical imports"""
    print("\n🎉 Fix tests completed!")
    print("\nIf all tests pass with ✅, your fixes are working correctly.")
    print("If you see ❌ or ⚠️, check the error messages above.")("Testing imports...")
    
    try:
        from dependency_container import container
        print("✅ dependency_container imported successfully")
    except ImportError as e:
        print(f"❌ dependency_container import failed: {e}")
    
    try:
        from system_initializer import initialize_system
        print("✅ system_initializer imported successfully")
    except ImportError as e:
        print(f"❌ system_initializer import failed: {e}")
    
    try:
        from legal_compliance import LegalRAGEngine, LegalChatbot, LegalSearchEngine
        print("✅ legal_compliance imported successfully")
    except ImportError as e:
        print(f"❌ legal_compliance import failed: {e}")
    
    try:
        from market_reports.utils import logger, config_manager, system_state
        print("✅ market_reports.utils imported successfully")
    except ImportError as e:
        print(f"❌ market_reports.utils import failed: {e}")

def test_system_initialization():
    """Test system initialization"""
    print("\nTesting system initialization...")
    
    try:
        from system_initializer import initialize_system
        result = initialize_system(offline_mode=True)
        
        if result:
            print("✅ System initialization successful")
        else:
            print("⚠️ System initialization completed with warnings")
            
    except Exception as e:
        print(f"❌ System initialization failed: {e}")

def test_legal_search_method():
    """Test the legal search research_topic method"""
    print("\nTesting legal search research_topic method...")
    
    try:
        from legal_compliance import LegalSearchEngine
        
        # Create instance
        legal_search = LegalSearchEngine()
        
        # Check if research_topic method exists
        if hasattr(legal_search, 'research_topic'):
            print("✅ research_topic method exists")
            
            # Test the method
            result = legal_search.research_topic("test query")
            if result and 'query' in result:
                print("✅ research_topic method works correctly")
            else:
                print("⚠️ research_topic method returned unexpected result")
        else:
            print("❌ research_topic method missing")
            
    except Exception as e:
        print(f"❌ Legal search test failed: {e}")

def test_component_creation():
    """Test component creation"""
    print("\nTesting component creation...")
    
    try:
        from system_initializer import (
            create_rag_engine, 
            create_web_search, 
            create_legal_search_engine,
            create_legal_chatbot
        )
        from dependency_container import container
        
        # Test RAG engine creation
        rag_engine = create_rag_engine(container)
        if rag_engine:
            print("✅ RAG engine created successfully")
        
        # Test web search creation  
        web_search = create_web_search(container)
        if web_search:
            print("✅ Web search engine created successfully")
        
        # Register web search for legal components
        container.register('web_search', web_search)
        
        # Test legal search engine creation
        legal_search = create_legal_search_engine(container)
        if legal_search and hasattr(legal_search, 'research_topic'):
            print("✅ Legal search engine created successfully with research_topic method")
        
        # Test legal chatbot creation
        container.register('legal_search_engine', legal_search)
        legal_chatbot = create_legal_chatbot(container)
        if legal_chatbot:
            print("✅ Legal chatbot created successfully")
            
    except Exception as e:
        print(f"❌ Component creation test failed: {e}")

if __name__ == "__main__":
    print("🔧 Running LinkSaudi Market Intelligence Platform Fix Tests\n")
    
    test_imports()
    test_system_initialization() 
    test_legal_search_method()
    test_component_creation()
    
    