#!/usr/bin/env python3
# system_initializer.py - FIXED system initialization with correct imports

import os
import logging
import importlib.util
from typing import Dict, List, Any, Optional, Callable

# Import the dependency container
from dependency_container import container
from market_reports.utils import config_manager, system_state, logger, safe_execute

# Import legal compliance components
try:
    from legal_compliance import LegalRAGEngine, LegalChatbot, LegalSearchEngine
    LEGAL_COMPLIANCE_AVAILABLE = True
    logger.info("Legal compliance modules imported successfully")
except ImportError as e:
    LEGAL_COMPLIANCE_AVAILABLE = False
    logger.warning(f"Legal compliance modules not available: {e}")

class SystemInitializer:
    """Centralized system initialization with dependency management"""
    
    def __init__(self):
        self.required_components = [
            "rag_engine", 
            "web_search", 
            "report_generator", 
            "report_conversation", 
            "pdf_exporter", 
            "market_report_system",
            "legal_rag_engine",
            "legal_search_engine", 
            "legal_chatbot"
        ]
        self.component_factories = {}
        self.initialized = False
    
    def register_component_factory(self, name: str, factory: Callable) -> None:
        """Register a factory function for a component"""
        self.component_factories[name] = factory
    
    def initialize_system(self, offline_mode: bool = False) -> bool:
        """Initialize all system components"""
        if self.initialized:
            logger.info("System already initialized")
            return True
        
        logger.info(f"Initializing system (offline_mode={offline_mode})")
        
        try:
            self._register_core_components()
            
            if offline_mode:
                logger.info("Working in offline mode - limiting component initialization")
                system_state.current_state = 'offline'
            
            for component_name in self.required_components:
                self._initialize_component(component_name, offline_mode)
            
            self._update_system_state()
            
            self.initialized = True
            logger.info(f"System initialization complete. State: {system_state.current_state}")
            return True
        
        except Exception as e:
            logger.error(f"Critical error during system initialization: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            system_state.current_state = 'offline'
            return False
    
    def _register_core_components(self) -> None:
        """Register core utility components in the container"""
        container.register('config_manager', config_manager)
        container.register('system_state', system_state)
    
    def _initialize_component(self, component_name: str, offline_mode: bool) -> bool:
        """Initialize a specific component"""
        logger.info(f"Initializing component: {component_name}")
        
        if offline_mode and component_name in ['rag_engine', 'web_search', 'legal_rag_engine', 'legal_search_engine']:
            logger.info(f"Skipping {component_name} initialization in offline mode")
            system_state.set_component_status(component_name, False, "Component disabled in offline mode")
            return False
        
        try:
            if component_name in self.component_factories:
                component = self.component_factories[component_name](container)
                container.register(component_name, component)
                system_state.set_component_status(component_name, True, f"Component initialized successfully")
                logger.info(f"Component {component_name} initialized successfully")
                return True
            else:
                logger.warning(f"No factory registered for component: {component_name}")
                system_state.set_component_status(component_name, False, "No factory registered for this component")
                return False
        
        except Exception as e:
            logger.error(f"Error initializing {component_name}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            system_state.set_component_status(component_name, False, f"Initialization failed: {str(e)}")
            return False
    
    def _update_system_state(self) -> None:
        """Enhanced system state update that includes legal compliance"""
        critical_components = ['rag_engine', 'web_search']
        legal_components = ['legal_rag_engine', 'legal_search_engine', 'legal_chatbot']
        
        available_components = sum(1 for comp in self.required_components 
                                  if system_state.get_component_status(comp).get('available', False))
        
        total_components = len(self.required_components)
        critical_available = all(system_state.get_component_status(comp).get('available', False) 
                               for comp in critical_components)
        
        legal_available = all(system_state.get_component_status(comp).get('available', False) 
                             for comp in legal_components)
        
        if critical_available:
            system_state.current_state = 'online'
        elif available_components > 0:
            system_state.current_state = 'degraded'  
        else:
            system_state.current_state = 'offline'
        
        if legal_available:
            logger.info("Legal compliance system: Available")
        else:
            logger.info("Legal compliance system: Limited or unavailable")
        
        logger.info(f"System state set to {system_state.current_state} "
                   f"({available_components}/{total_components} components available)")

# FIXED COMPONENT FACTORIES - Using correct import paths

def create_rag_engine(container):
    """Factory for RAG Engine component"""
    try:
        from market_reports.rag_enhanced import (
            embedding_engine, 
            get_weaviate_client, 
            generate_rag_response, 
            generate_multimodal_rag_response
        )
        
        class RAGEngine:
            def __init__(self):
                self.client = None
            
            def get_weaviate_client(self):
                if not self.client:
                    try:
                        self.client = get_weaviate_client()
                    except Exception as e:
                        logger.error(f"Error getting Weaviate client: {e}")
                        self.client = None
                return self.client
            
            def generate_rag_response(self, query, context_limit=5):
                try:
                    return generate_rag_response(query, context_limit)
                except Exception as e:
                    logger.error(f"Error generating RAG response: {e}")
                    return f"Sorry, I couldn't generate a response due to an error: {str(e)}"
            
            def generate_multimodal_rag_response(self, query, context_limit=5, image_limit=2):
                try:
                    return generate_multimodal_rag_response(query, context_limit, image_limit)
                except Exception as e:
                    logger.error(f"Error generating multimodal RAG response: {e}")
                    return {"response": f"Sorry, I couldn't generate a response due to an error: {str(e)}",
                            "text_results": [], "image_results": []}
        
        engine = RAGEngine()
        logger.info("RAG Engine initialized successfully")
        return engine
    
    except Exception as e:
        logger.error(f"RAG Engine initialization failed: {e}")
        
        class MockRAGEngine:
            def __init__(self):
                self.client = None
            
            def get_weaviate_client(self):
                logger.warning("Using mock Weaviate client")
                return None
            
            def generate_rag_response(self, query, context_limit=5):
                logger.warning(f"Using mock RAG response for query: {query}")
                return f"I'm operating in limited mode and can't provide a detailed analysis on '{query}'. Please check if all dependencies are installed correctly."
            
            def generate_multimodal_rag_response(self, query, context_limit=5, image_limit=2):
                logger.warning(f"Using mock multimodal RAG response for query: {query}")
                return {
                    "response": f"I'm operating in limited mode and can't provide a detailed analysis on '{query}'. Please check if all dependencies are installed correctly.",
                    "text_results": [],
                    "image_results": []
                }
        
        logger.info("Created mock RAG Engine due to initialization failure")
        return MockRAGEngine()

def create_web_search(container):
    """Factory for Web Search component"""
    try:
        from market_reports.web_search import WebResearchEngine
        engine = WebResearchEngine()
        logger.info("Web Search Engine initialized successfully")
        return engine
    except ImportError as e:
        logger.error(f"Web Search initialization failed due to missing dependencies: {e}")
        
        # Create mock web search engine
        class MockWebSearchEngine:
            def research_topic(self, query, context="", market="", top_n=3):
                logger.warning(f"Using mock web search for query: {query}")
                return {
                    "data": [{
                        "title": f"Mock search result for {query}",
                        "url": "https://example.com",
                        "summary": f"Mock search result summary for {query}",
                        "retrieved_date": "2024-01-01"
                    }]
                }
        
        return MockWebSearchEngine()

def create_report_generator(container):
    """Factory for Report Generator component"""
    try:
        from market_reports.report_generator_enhanced import ReportGenerator
        
        rag_engine = container.get('rag_engine')
        web_search = container.get('web_search')
        
        generator = ReportGenerator(rag_engine=rag_engine, web_search=web_search)
        logger.info("Report Generator initialized successfully")
        return generator
    except ImportError as e:
        logger.error(f"Report Generator initialization failed due to missing dependencies: {e}")
        
        # Create mock report generator
        class MockReportGenerator:
            def generate_market_report(self, title, sectors, geography, enhance_with_web=True, include_visuals=True):
                logger.warning(f"Using mock report generator for: {title}")
                return {
                    "title": title,
                    "date": "2024-01-01",
                    "sectors": sectors,
                    "geography": geography,
                    "sections": [{
                        "title": "Executive Summary",
                        "content": "This is a mock report generated due to missing dependencies.",
                        "subsections": []
                    }],
                    "charts": [],
                    "sources": []
                }
        
        return MockReportGenerator()

def create_report_conversation(container):
    """Factory for Report Conversation component"""
    try:
        from market_reports.report_conversation_enhanced import ReportConversation
        rag_engine = container.get('rag_engine')
        conversation = ReportConversation(rag_engine=rag_engine)
        logger.info("Report Conversation initialized successfully")
        return conversation
    except ImportError as e:
        logger.error(f"Report Conversation initialization failed due to missing dependencies: {e}")
        
        class MockReportConversation:
            def ask_question(self, query):
                return f"Mock conversation response for: {query}"
        
        return MockReportConversation()

def create_pdf_exporter(container):
    """Factory for PDF Exporter component"""
    try:
        from market_reports.pdf_exporter_enhanced import PDFExporter
        exporter = PDFExporter()
        logger.info("PDF Exporter initialized successfully")
        return exporter
    except ImportError as e:
        logger.error(f"PDF Exporter initialization failed due to missing dependencies: {e}")
        
        class MockPDFExporter:
            def export_report_to_pdf(self, report_data, output_path):
                logger.warning("PDF export not available - using mock exporter")
                return False
        
        return MockPDFExporter()

def create_market_report_system(container):
    """Factory for Market Report System component"""
    try:
        from market_reports.market_report_system import MarketReportSystem
        
        rag_engine = container.get('rag_engine')
        web_search = container.get('web_search')
        report_generator = container.get('report_generator')
        pdf_exporter = container.get('pdf_exporter')
        
        market_report_system = MarketReportSystem(
            rag_engine=rag_engine,
            web_search=web_search,
            report_generator=report_generator,
            pdf_exporter=pdf_exporter
        )
        
        logger.info("Market Report System initialized successfully")
        return market_report_system
    except ImportError as e:
        logger.error(f"Market Report System initialization failed due to missing dependencies: {e}")
        
        class MockMarketReportSystem:
            def create_market_report(self, title, sectors, geography, enhance_with_web=True, include_visuals=True):
                return {"report_data": {}, "json_file": "", "pdf_file": None}
            
            def list_reports(self):
                return []
            
            def delete_report(self, filename):
                return True
        
        return MockMarketReportSystem()

# LEGAL COMPLIANCE FACTORIES (FIXED)

def create_legal_rag_engine(container):
    """Factory for Legal RAG Engine component - FIXED"""
    try:
        if not LEGAL_COMPLIANCE_AVAILABLE:
            raise ImportError("Legal compliance modules not available")
        
        rag_engine = container.get('rag_engine')
        weaviate_client = None
        openai_client = None
        embedding_engine = None
        
        if rag_engine:
            weaviate_client = getattr(rag_engine, 'client', None) or rag_engine.get_weaviate_client()
            
            try:
                from market_reports.rag_enhanced import openai_client as rag_openai_client
                openai_client = rag_openai_client
            except ImportError:
                logger.warning("Could not import OpenAI client from rag_enhanced")
            
            try:
                from market_reports.rag_enhanced import embedding_engine as rag_embedding_engine
                embedding_engine = rag_embedding_engine
            except ImportError:
                logger.warning("Could not import embedding engine from rag_enhanced")
        
        legal_rag = LegalRAGEngine(
            weaviate_client=weaviate_client,
            openai_client=openai_client,
            embedding_engine=embedding_engine
        )
        
        logger.info("Legal RAG Engine initialized successfully")
        return legal_rag
        
    except Exception as e:
        logger.error(f"Legal RAG Engine initialization failed: {e}")
        
        class MockLegalRAGEngine:
            def __init__(self):
                self.weaviate_client = None
                self.legal_class = "LegalDocument"
            
            def search_legal_documents(self, query, limit=10, document_type=None, jurisdiction=None):
                logger.warning("Using mock legal document search")
                return []
            
            def generate_legal_response(self, query, context_limit=None, include_citations=True, 
                                     document_type=None, jurisdiction=None):
                return {
                    "response": "Legal analysis service is currently unavailable. Please ensure all legal compliance dependencies are properly installed and configured.",
                    "documents": [],
                    "citations": [],
                    "error": "Mock legal RAG engine"
                }
            
            def get_legal_categories(self):
                return ["Corporate Law", "Contract Law", "Regulatory Compliance", "Employment Law", "Commercial Law"]
            
            def get_available_jurisdictions(self):
                return ["Saudi Arabia", "GCC", "International"]
        
        logger.info("Created mock Legal RAG Engine due to initialization failure")
        return MockLegalRAGEngine()

def create_legal_search_engine(container):
    """Factory for Legal Search Engine component - FIXED"""
    try:
        if not LEGAL_COMPLIANCE_AVAILABLE:
            raise ImportError("Legal compliance modules not available")
        
        web_search_engine = container.get('web_search')
        legal_search = LegalSearchEngine(web_search_engine=web_search_engine)
        
        # FIX: Add the missing research_topic method
        def research_topic(self, query, context="", market="", top_n=3):
            """Add missing research_topic method"""
            return self.search_legal_web_content(
                query=query, 
                jurisdiction=market or "Saudi Arabia", 
                max_results=top_n
            )
        
        # Bind the method to the instance
        legal_search.research_topic = research_topic.__get__(legal_search, LegalSearchEngine)
        
        logger.info("Legal Search Engine initialized successfully")
        return legal_search
        
    except Exception as e:
        logger.error(f"Legal Search Engine initialization failed: {e}")
        
        class MockLegalSearchEngine:
            def __init__(self):
                pass
            
            def research_topic(self, query, context="", market="", top_n=3):
                """FIXED: Add the missing research_topic method"""
                return {
                    'query': query,
                    'data': [],
                    'summary': 'Legal web search is currently unavailable.',
                    'is_mock_data': True
                }
            
            def search_legal_web_content(self, query, legal_category=None, jurisdiction="Saudi Arabia", max_results=5):
                return {
                    'query': query,
                    'legal_category': legal_category,
                    'jurisdiction': jurisdiction,
                    'sources': [],
                    'summary': 'Legal web search is currently unavailable.',
                    'key_findings': [],
                    'is_mock_data': True
                }
            
            def search_legal_precedents(self, case_type, jurisdiction="Saudi Arabia"):
                return []
            
            def search_regulatory_updates(self, sector=None, days_back=90):
                return []
            
            def search_compliance_requirements(self, business_type, jurisdiction="Saudi Arabia"):
                return {
                    'business_type': business_type,
                    'jurisdiction': jurisdiction,
                    'requirements': [],
                    'licenses_needed': [],
                    'regulatory_bodies': [],
                    'sources': [],
                    'error': 'Legal search service unavailable'
                }
        
        logger.info("Created mock Legal Search Engine due to initialization failure")
        return MockLegalSearchEngine()

def create_legal_chatbot(container):
    """Factory for Legal Chatbot component"""
    try:
        if not LEGAL_COMPLIANCE_AVAILABLE:
            raise ImportError("Legal compliance modules not available")
        
        legal_rag_engine = container.get('legal_rag_engine')
        legal_search_engine = container.get('legal_search_engine')
        
        legal_chatbot = LegalChatbot(
            legal_rag_engine=legal_rag_engine,
            web_search_engine=legal_search_engine  # FIXED: Use correct parameter name
        )
        
        logger.info("Legal Chatbot initialized successfully")
        return legal_chatbot
        
    except Exception as e:
        logger.error(f"Legal Chatbot initialization failed: {e}")
        
        class MockLegalChatbot:
            def __init__(self):
                self.current_session = None
            
            def start_new_session(self, user_id=None):
                import uuid
                session_id = str(uuid.uuid4())
                self.current_session = {"session_id": session_id, "messages": []}
                return session_id
            
            def ask_legal_question(self, question, document_type=None, jurisdiction=None, include_web_search=None):
                return {
                    "response": "Legal chatbot service is currently unavailable. Please ensure all legal compliance dependencies are properly installed and configured.",
                    "session_id": self.current_session["session_id"] if self.current_session else None,
                    "citations": [],
                    "web_sources": [],
                    "documents_consulted": 0,
                    "success": False,
                    "error": "Mock legal chatbot"
                }
            
            def get_conversation_history(self):
                return self.current_session["messages"] if self.current_session else []
            
            def end_session(self):
                if self.current_session:
                    session_id = self.current_session["session_id"]
                    self.current_session = None
                    return {"session_id": session_id, "queries_count": 0}
                return {"error": "No active session"}
            
            def list_previous_sessions(self, user_id=None):
                return []
            
            def get_legal_categories(self):
                return ["Corporate Law", "Contract Law", "Regulatory Compliance", "Employment Law", "Commercial Law"]
            
            def get_available_jurisdictions(self):
                return ["Saudi Arabia", "GCC", "International"]
            
            def export_session_report(self, session_id=None):
                return {"error": "Legal chatbot service unavailable"}
        
        logger.info("Created mock Legal Chatbot due to initialization failure")
        return MockLegalChatbot()

# Create the system initializer instance
system_initializer = SystemInitializer()

# Register component factories
system_initializer.register_component_factory('rag_engine', create_rag_engine)
system_initializer.register_component_factory('web_search', create_web_search)
system_initializer.register_component_factory('report_generator', create_report_generator)
system_initializer.register_component_factory('report_conversation', create_report_conversation)
system_initializer.register_component_factory('pdf_exporter', create_pdf_exporter)
system_initializer.register_component_factory('market_report_system', create_market_report_system)

# Register legal compliance component factories
system_initializer.register_component_factory('legal_rag_engine', create_legal_rag_engine)
system_initializer.register_component_factory('legal_search_engine', create_legal_search_engine) 
system_initializer.register_component_factory('legal_chatbot', create_legal_chatbot)

def initialize_system(offline_mode=False):
    """Convenience function to initialize the entire system"""
    return system_initializer.initialize_system(offline_mode)