#!/usr/bin/env python3
# system_initializer_legal_fixes.py - Legal Component Factories WITHOUT Web Search

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("market_intelligence")

def create_legal_rag_engine_fixed(container):
    """
    FIXED Factory for Legal RAG Engine with proper Weaviate integration (no web search)
    """
    try:
        # Try to import the FIXED legal RAG engine
        try:
            from legal_compliance.legal_rag_engine import LegalRAGEngine
            FIXED_ENGINE_AVAILABLE = True
        except ImportError:
            # If FIXED version isn't available, fall back to original
            from legal_compliance import LegalRAGEngine
            FIXED_ENGINE_AVAILABLE = False
            logger.warning("FIXED Legal RAG Engine not available, using original")
        
        # Get dependencies
        weaviate_client = None
        openai_client = None
        embedding_engine = None
        
        # Try to get Weaviate client from the main RAG engine
        rag_engine = container.get('rag_engine')
        if rag_engine:
            weaviate_client = getattr(rag_engine, 'client', None) or rag_engine.get_weaviate_client()
        
        # Try to get OpenAI client
        try:
            from market_reports.rag_enhanced import openai_client as rag_openai_client
            openai_client = rag_openai_client
        except ImportError:
            logger.warning("Could not import OpenAI client from rag_enhanced")
            # Try to get from config
            try:
                from market_reports.utils import config_manager
                openai_api_key = config_manager.get_config_value("api_keys.openai")
                if openai_api_key:
                    import openai
                    openai.api_key = openai_api_key
                    openai_client = openai
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")
        
        # Try to get embedding engine
        try:
            from market_reports.rag_enhanced import embedding_engine as rag_embedding_engine
            embedding_engine = rag_embedding_engine
        except ImportError:
            logger.warning("Could not import embedding engine from rag_enhanced")
        
        # Create the legal RAG engine (no web search)
        legal_rag = LegalRAGEngine(
            weaviate_client=weaviate_client,
            openai_client=openai_client,
            embedding_engine=embedding_engine
        )
        
        # Test the connection if it has the test method
        if hasattr(legal_rag, 'test_connection'):
            try:
                connection_test = legal_rag.test_connection()
                logger.info(f"Legal RAG Engine connection test: {connection_test}")
                
                if connection_test.get("status") == "success":
                    logger.info(f"✅ Legal RAG Engine initialized successfully with {connection_test.get('total_documents', 0)} documents")
                else:
                    logger.warning(f"⚠️ Legal RAG Engine initialized with limited functionality: {connection_test.get('message')}")
            except Exception as e:
                logger.warning(f"Could not test legal RAG connection: {e}")
        else:
            logger.info("Legal RAG Engine initialized (no connection test available)")
        
        return legal_rag
        
    except ImportError as e:
        logger.error(f"Could not import Legal RAG Engine: {e}")
        return create_mock_legal_rag_engine()
    
    except Exception as e:
        logger.error(f"Legal RAG Engine initialization failed: {e}")
        return create_mock_legal_rag_engine()

def create_legal_chatbot_enhanced_no_web(container):
    """
    Enhanced Legal Chatbot factory WITHOUT web search functionality
    """
    try:
        from legal_compliance import LegalChatbot
        
        # Get the legal RAG engine (no web search engine)
        legal_rag_engine = container.get('legal_rag_engine')
        
        # Create enhanced legal chatbot WITHOUT web search
        legal_chatbot = LegalChatbot(
            legal_rag_engine=legal_rag_engine
        )
        
        # Add enhanced methods
        def get_system_status(self):
            """Get the status of the legal compliance system (no web search)"""
            rag_status = "available" if self.legal_rag_engine else "unavailable"
            
            # Test RAG engine if available
            rag_test = None
            if self.legal_rag_engine and hasattr(self.legal_rag_engine, 'test_connection'):
                try:
                    rag_test = self.legal_rag_engine.test_connection()
                except Exception as e:
                    rag_test = {"status": "error", "message": str(e)}
            elif self.legal_rag_engine:
                rag_test = {"status": "basic", "message": "Basic legal RAG available"}
            else:
                rag_test = {"status": "unavailable", "message": "No legal RAG engine"}
            
            return {
                "legal_rag_engine": rag_status,
                "web_search_enabled": False,  # Explicitly disabled
                "rag_connection_test": rag_test,
                "session_active": self.current_session is not None,
                "total_queries": self.current_session["metadata"]["queries_count"] if self.current_session else 0
            }
        
        def test_legal_system(self):
            """Test the legal system functionality (database only)"""
            try:
                test_response = self.ask_legal_question(
                    "What are the basic requirements for company formation in Saudi Arabia?",
                    jurisdiction="Saudi Arabia"
                )
                return {
                    "status": "success" if test_response.get("success") else "limited",
                    "test_response": test_response
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        # Bind enhanced methods to the chatbot instance
        legal_chatbot.get_system_status = get_system_status.__get__(legal_chatbot, LegalChatbot)
        legal_chatbot.test_legal_system = test_legal_system.__get__(legal_chatbot, LegalChatbot)
        
        logger.info("Enhanced Legal Chatbot initialized successfully (no web search)")
        return legal_chatbot
        
    except Exception as e:
        logger.error(f"Legal Chatbot initialization failed: {e}")
        return create_mock_legal_chatbot()

def create_mock_legal_rag_engine():
    """Create a mock legal RAG engine when the real one fails"""
    
    class MockLegalRAGEngine:
        def __init__(self):
            self.weaviate_client = None
            self.legal_class = "LegalDocument"
            logger.info("Created mock Legal RAG Engine (no web search)")
        
        def search_legal_documents(self, query, limit=10, document_type=None, jurisdiction=None, practice_area=None):
            logger.warning("Using mock legal document search")
            return [{
                "content": f"Mock legal content for query: {query}",
                "title": f"Mock Legal Document: {query}",
                "document_type": document_type or "General Legal Document",
                "jurisdiction": jurisdiction or "Saudi Arabia",
                "practice_area": practice_area or "General Practice",
                "file_name": "mock_document.pdf",
                "type": "legal_document",
                "source": "Mock Database"
            }]
        
        def generate_legal_response(self, query, context_limit=None, include_citations=True, 
                                 document_type=None, jurisdiction=None, practice_area=None):
            return {
                "response": f"""Based on available legal guidance regarding '{query}':

**Legal Framework:**
This matter falls under Saudi Arabian legal jurisdiction and requires compliance with applicable regulations.

**Key Requirements:**
• Adherence to established legal procedures
• Compliance with regulatory frameworks
• Proper documentation and authorization

**Compliance Procedures:**
1. Review applicable regulations
2. Ensure proper licensing and permits
3. Maintain required documentation
4. Follow prescribed procedures

**Recommendations:**
• Consult with qualified legal counsel
• Stay updated on regulatory changes
• Maintain compliance documentation
• Regular review of legal requirements

**Note:** This is a general guidance response from our legal database. The legal compliance system is operating in limited mode. For detailed analysis, please ensure all legal dependencies are properly configured.

**Legal Disclaimer:** This information is provided for general guidance only and does not constitute legal advice. For specific legal matters, please consult with a qualified attorney licensed to practice in Saudi Arabia.""",
                "documents": self.search_legal_documents(query, context_limit or 5, document_type, jurisdiction, practice_area),
                "citations": [],
                "error": "Mock legal RAG engine - limited functionality"
            }
        
        def get_legal_categories(self):
            return ["Corporate Law", "Contract Law", "Regulatory Compliance", "Employment Law", "Commercial Law", "General Legal Document"]
        
        def get_available_jurisdictions(self):
            return ["Saudi Arabia", "GCC", "International"]
        
        def get_available_practice_areas(self):
            return ["General Practice", "Corporate Law", "Healthcare Law"]
        
        def test_connection(self):
            return {"status": "mock", "message": "Mock legal RAG engine - no real connection"}
        
        def clear_cache(self):
            pass
        
        def get_query_history(self):
            return []
    
    return MockLegalRAGEngine()

def create_mock_legal_chatbot():
    """Create a mock legal chatbot when the real one fails"""
    
    class MockLegalChatbot:
        def __init__(self):
            self.current_session = None
            self.legal_rag_engine = None
            logger.info("Created mock Legal Chatbot (no web search)")
        
        def start_new_session(self, user_id=None):
            import uuid
            session_id = str(uuid.uuid4())
            self.current_session = {
                "session_id": session_id, 
                "messages": [],
                "metadata": {"queries_count": 0}
            }
            return session_id
        
        def ask_legal_question(self, question, document_type=None, jurisdiction=None):
            if not self.current_session:
                self.start_new_session()
                
            self.current_session["metadata"]["queries_count"] += 1
            
            return {
                "response": f"""I understand you're asking about: "{question}"

**Current System Status:** The legal compliance system is operating in limited mode (database only, no web search).

**General Legal Guidance:**
For questions related to Saudi Arabian law and regulations, I recommend:

• Consulting with a qualified attorney licensed in Saudi Arabia
• Reviewing official government publications and legal databases
• Contacting relevant regulatory authorities for specific guidance
• Ensuring compliance with current laws and regulations

**System Notice:** To access full legal analysis capabilities with document search and detailed legal guidance, please ensure all legal compliance dependencies are properly installed and configured.

**Legal Disclaimer:** This information is provided for general guidance only and does not constitute legal advice. For specific legal matters, please consult with a qualified attorney licensed to practice in Saudi Arabia.""",
                "session_id": self.current_session["session_id"],
                "citations": [],
                "documents_consulted": 0,
                "success": True,
                "is_mock": True
            }
        
        def get_conversation_history(self):
            return self.current_session["messages"] if self.current_session else []
        
        def end_session(self):
            if self.current_session:
                session_id = self.current_session["session_id"]
                queries_count = self.current_session["metadata"]["queries_count"]
                self.current_session = None
                return {"session_id": session_id, "queries_count": queries_count}
            return {"error": "No active session"}
        
        def list_previous_sessions(self, user_id=None):
            return []
        
        def get_legal_categories(self):
            return ["Corporate Law", "Contract Law", "Regulatory Compliance", "Employment Law", "Commercial Law"]
        
        def get_available_jurisdictions(self):
            return ["Saudi Arabia", "GCC", "International"]
        
        def export_session_report(self, session_id=None):
            return {"error": "Legal chatbot service unavailable - using mock implementation"}
        
        def get_system_status(self):
            return {
                "legal_rag_engine": "mock",
                "web_search_enabled": False,
                "rag_connection_test": {"status": "mock", "message": "Mock legal system"},
                "session_active": self.current_session is not None,
                "total_queries": self.current_session["metadata"]["queries_count"] if self.current_session else 0
            }
        
        def test_legal_system(self):
            return {"status": "mock", "message": "Mock legal system - limited functionality (no web search)"}
    
    return MockLegalChatbot()

# Integration functions for existing system initializer (no web search)

def update_system_initializer_no_web(system_initializer):
    """
    Update the existing system initializer with legal components (no web search)
    Call this function to register the legal factories without web search
    """
    # Register the legal component factories (no web search)
    system_initializer.register_component_factory('legal_rag_engine', create_legal_rag_engine_fixed)
    system_initializer.register_component_factory('legal_chatbot', create_legal_chatbot_enhanced_no_web)
    # Removed: legal_search_engine factory
    
    logger.info("System initializer updated with legal compliance components (no web search)")

def get_legal_system_diagnostics_no_web(container) -> Dict[str, Any]:
    """
    Get comprehensive diagnostics for the legal system (no web search)
    """
    diagnostics = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "components": {},
        "overall_status": "unknown",
        "recommendations": [],
        "web_search_enabled": False
    }
    
    # Test Legal RAG Engine
    legal_rag = container.get('legal_rag_engine')
    if legal_rag:
        if hasattr(legal_rag, 'test_connection'):
            try:
                connection_test = legal_rag.test_connection()
                diagnostics["components"]["legal_rag_engine"] = {
                    "available": True,
                    "type": "real" if connection_test.get("status") == "success" else "limited",
                    "connection_test": connection_test,
                    "weaviate_connected": connection_test.get("is_ready", False),
                    "document_count": connection_test.get("total_documents", 0)
                }
            except Exception as e:
                diagnostics["components"]["legal_rag_engine"] = {
                    "available": True,
                    "type": "error",
                    "error": str(e)
                }
        else:
            diagnostics["components"]["legal_rag_engine"] = {
                "available": True,
                "type": "basic" if "Mock" not in legal_rag.__class__.__name__ else "mock",
                "note": "No connection test method available"
            }
    else:
        diagnostics["components"]["legal_rag_engine"] = {
            "available": False,
            "error": "Component not found in container"
        }
    
    # Test Legal Chatbot (no web search)
    legal_chatbot = container.get('legal_chatbot')
    if legal_chatbot:
        if hasattr(legal_chatbot, 'get_system_status'):
            try:
                chatbot_status = legal_chatbot.get_system_status()
                diagnostics["components"]["legal_chatbot"] = {
                    "available": True,
                    "type": "enhanced",
                    "system_status": chatbot_status,
                    "web_search_enabled": False
                }
            except Exception as e:
                diagnostics["components"]["legal_chatbot"] = {
                    "available": True,
                    "type": "error",
                    "error": str(e)
                }
        else:
            diagnostics["components"]["legal_chatbot"] = {
                "available": True,
                "type": "basic" if "Mock" not in legal_chatbot.__class__.__name__ else "mock",
                "web_search_enabled": False
            }
    else:
        diagnostics["components"]["legal_chatbot"] = {
            "available": False,
            "error": "Component not found in container"
        }
    
    # Note: Legal Search Engine removed
    diagnostics["components"]["legal_search_engine"] = {
        "available": False,
        "note": "Web search functionality has been disabled"
    }
    
    # Determine overall status
    available_components = sum(1 for comp in diagnostics["components"].values() 
                             if comp.get("available", False) and comp.get("type") != "error")
    total_components = len([k for k in diagnostics["components"].keys() if k != "legal_search_engine"])
    
    if available_components == total_components:
        # Check if components are real or mock
        real_components = sum(1 for comp in diagnostics["components"].values() 
                            if comp.get("available") and comp.get("type") not in ["mock", "limited"])
        
        if real_components == total_components:
            diagnostics["overall_status"] = "fully_operational"
        elif real_components > 0:
            diagnostics["overall_status"] = "partially_operational"
        else:
            diagnostics["overall_status"] = "limited_functionality"
    elif available_components > 0:
        diagnostics["overall_status"] = "degraded"
    else:
        diagnostics["overall_status"] = "offline"
    
    # Generate recommendations
    if diagnostics["overall_status"] in ["limited_functionality", "degraded"]:
        diagnostics["recommendations"].append("Install and configure Weaviate with legal document database")
        diagnostics["recommendations"].append("Configure OpenAI API key for enhanced legal analysis")
        diagnostics["recommendations"].append("Ensure all legal compliance dependencies are installed")
    
    if diagnostics["components"].get("legal_rag_engine", {}).get("document_count", 0) == 0:
        diagnostics["recommendations"].append("Load legal documents into Weaviate database")
    
    diagnostics["recommendations"].append("Note: Web search functionality has been disabled for legal compliance")
    
    return diagnostics