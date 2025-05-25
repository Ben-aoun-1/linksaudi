#!/usr/bin/env python3
# system_initializer.py - Centralized system initialization for all components

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
            # Add legal compliance components
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
            # Initialize core utilities first
            self._register_core_components()
            
            # If offline mode, skip components that require online services
            if offline_mode:
                logger.info("Working in offline mode - limiting component initialization")
                system_state.current_state = 'offline'
            
            # Initialize each component
            for component_name in self.required_components:
                self._initialize_component(component_name, offline_mode)
            
            # Update overall system state
            self._update_system_state()
            
            self.initialized = True
            logger.info(f"System initialization complete. State: {system_state.current_state}")
            return True
        
        except Exception as e:
            logger.error(f"Critical error during system initialization: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            
            # Set system to offline mode due to initialization failure
            system_state.current_state = 'offline'
            return False
    
    def _register_core_components(self) -> None:
        """Register core utility components in the container"""
        # Register config manager
        container.register('config_manager', config_manager)
        
        # Register system state manager
        container.register('system_state', system_state)
    
    def _initialize_component(self, component_name: str, offline_mode: bool) -> bool:
        """Initialize a specific component"""
        logger.info(f"Initializing component: {component_name}")
        
        # Skip external service components in offline mode
        if offline_mode and component_name in ['rag_engine', 'web_search', 'legal_rag_engine', 'legal_search_engine']:
            logger.info(f"Skipping {component_name} initialization in offline mode")
            system_state.set_component_status(component_name, False, "Component disabled in offline mode")
            return False
        
        try:
            # Check if we have a factory for this component
            if component_name in self.component_factories:
                # Use the factory to create the component
                component = self.component_factories[component_name](container)
                
                # Register the component in the container
                container.register(component_name, component)
                
                # Update component status
                system_state.set_component_status(
                    component_name, 
                    True, 
                    f"Component initialized successfully"
                )
                
                logger.info(f"Component {component_name} initialized successfully")
                return True
            else:
                logger.warning(f"No factory registered for component: {component_name}")
                system_state.set_component_status(
                    component_name, 
                    False, 
                    "No factory registered for this component"
                )
                return False
        
        except Exception as e:
            logger.error(f"Error initializing {component_name}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            
            system_state.set_component_status(
                component_name, 
                False, 
                f"Initialization failed: {str(e)}"
            )
            return False
    
    def _update_system_state(self) -> None:
        """Enhanced system state update that includes legal compliance"""
        # Critical components that must be available for online mode
        critical_components = ['rag_engine', 'web_search']
        
        # Legal components (optional but tracked)
        legal_components = ['legal_rag_engine', 'legal_search_engine', 'legal_chatbot']
        
        # Count available components
        available_components = sum(1 for comp in self.required_components 
                                  if system_state.get_component_status(comp).get('available', False))
        
        total_components = len(self.required_components)
        critical_available = all(system_state.get_component_status(comp).get('available', False) 
                               for comp in critical_components)
        
        # Check legal system availability
        legal_available = all(system_state.get_component_status(comp).get('available', False) 
                             for comp in legal_components)
        
        if critical_available:
            system_state.current_state = 'online'
        elif available_components > 0:
            system_state.current_state = 'degraded'  
        else:
            system_state.current_state = 'offline'
        
        # Log legal system status separately
        if legal_available:
            logger.info("Legal compliance system: Available")
        else:
            logger.info("Legal compliance system: Limited or unavailable")
        
        logger.info(f"System state set to {system_state.current_state} " 
                   f"({available_components}/{total_components} components available)")

# Create standard component factories

def create_rag_engine(container):
    """Factory for RAG Engine component"""
    try:
        # Try importing the original module first
        try:
            import rag_enhanced
            
            # Create a wrapper class to simplify the interface
            class RAGEngine:
                def __init__(self):
                    self.client = None
                    self.embedding_engine = None
                    try:
                        # Initialize embedding engine
                        self.embedding_engine = rag_enhanced.embedding_engine
                    except Exception as e:
                        logger.error(f"Error initializing embedding engine: {e}")
                        self.embedding_engine = None
                
                def get_weaviate_client(self):
                    if not self.client:
                        try:
                            self.client = rag_enhanced.get_weaviate_client()
                        except Exception as e:
                            logger.error(f"Error getting Weaviate client: {e}")
                            self.client = None
                    return self.client
                
                def generate_rag_response(self, query, context_limit=5):
                    try:
                        return rag_enhanced.generate_rag_response(query, context_limit)
                    except Exception as e:
                        logger.error(f"Error generating RAG response: {e}")
                        return f"Sorry, I couldn't generate a response due to an error: {str(e)}"
                
                def generate_multimodal_rag_response(self, query, context_limit=5, image_limit=2):
                    try:
                        return rag_enhanced.generate_multimodal_rag_response(query, context_limit, image_limit)
                    except Exception as e:
                        logger.error(f"Error generating multimodal RAG response: {e}")
                        return {"response": f"Sorry, I couldn't generate a response due to an error: {str(e)}",
                                "text_results": [], "image_results": []}
            
            # Create the engine
            engine = RAGEngine()
            logger.info("RAG Engine initialized successfully using original module")
            return engine
        
        except ImportError:
            # Try the refactored version
            logger.info("Original rag_enhanced not found, trying refactored version")
            from rag_enhanced import (
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
            
            # Create the engine
            engine = RAGEngine()
            logger.info("RAG Engine initialized successfully using refactored module")
            return engine
    
    except Exception as e:
        logger.error(f"RAG Engine initialization failed: {e}")
        
        # Create a mock RAG engine that provides basic functionality
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
        from web_search import WebResearchEngine
        
        # Create the engine
        engine = WebResearchEngine()
        logger.info("Web Search Engine initialized successfully")
        return engine
    except ImportError as e:
        logger.error(f"Web Search initialization failed due to missing dependencies: {e}")
        raise

def create_report_generator(container):
    """Factory for Report Generator component"""
    try:
        from report_generator_enhanced import ReportGenerator
        
        # Get required dependencies
        rag_engine = container.get('rag_engine')
        web_search = container.get('web_search')
        
        # Create the generator
        generator = ReportGenerator(
            rag_engine=rag_engine,
            web_search=web_search
        )
        
        logger.info("Report Generator initialized successfully")
        return generator
    except ImportError as e:
        logger.error(f"Report Generator initialization failed due to missing dependencies: {e}")
        raise

def create_report_conversation(container):
    """Factory for Report Conversation component"""
    try:
        from report_conversation_enhanced import ReportConversation
        
        # Get required dependencies
        rag_engine = container.get('rag_engine')
        
        # Create the conversation handler
        conversation = ReportConversation(rag_engine=rag_engine)
        
        logger.info("Report Conversation initialized successfully")
        return conversation
    except ImportError as e:
        logger.error(f"Report Conversation initialization failed due to missing dependencies: {e}")
        raise

def create_pdf_exporter(container):
    """Factory for PDF Exporter component"""
    try:
        from pdf_exporter_enhanced import PDFExporter
        
        # Create the exporter
        exporter = PDFExporter()
        
        logger.info("PDF Exporter initialized successfully")
        return exporter
    except ImportError as e:
        logger.error(f"PDF Exporter initialization failed due to missing dependencies: {e}")
        raise

def create_market_report_system(container):
    """Factory for Market Report System component"""
    try:
        from market_report_system import MarketReportSystem
        
        # Get required dependencies
        rag_engine = container.get('rag_engine')
        web_search = container.get('web_search')
        report_generator = container.get('report_generator')
        pdf_exporter = container.get('pdf_exporter')
        
        # Create the market report system
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
        raise

# LEGAL COMPLIANCE COMPONENT FACTORIES

def create_legal_rag_engine(container):
    """Factory for Legal RAG Engine component"""
    try:
        if not LEGAL_COMPLIANCE_AVAILABLE:
            raise ImportError("Legal compliance modules not available")
        
        # Get required dependencies (reuse existing components)
        rag_engine = container.get('rag_engine')
        weaviate_client = None
        openai_client = None
        embedding_engine = None
        
        # Extract components from existing RAG engine if available
        if rag_engine:
            weaviate_client = getattr(rag_engine, 'client', None) or rag_engine.get_weaviate_client()
            
            # Try to get OpenAI client from existing setup
            try:
                from rag_enhanced import openai_client as rag_openai_client
                openai_client = rag_openai_client
            except ImportError:
                logger.warning("Could not import OpenAI client from rag_enhanced")
            
            # Try to get embedding engine
            try:
                from rag_enhanced import embedding_engine as rag_embedding_engine
                embedding_engine = rag_embedding_engine
            except ImportError:
                logger.warning("Could not import embedding engine from rag_enhanced")
        
        # Create legal RAG engine
        legal_rag = LegalRAGEngine(
            weaviate_client=weaviate_client,
            openai_client=openai_client,
            embedding_engine=embedding_engine
        )
        
        logger.info("Legal RAG Engine initialized successfully")
        return legal_rag
        
    except Exception as e:
        logger.error(f"Legal RAG Engine initialization failed: {e}")
        
        # Create a mock legal RAG engine
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
    """Factory for Legal Search Engine component"""
    try:
        if not LEGAL_COMPLIANCE_AVAILABLE:
            raise ImportError("Legal compliance modules not available")
        
        # Get web search engine dependency
        web_search_engine = container.get('web_search')
        
        # Create legal search engine
        legal_search = LegalSearchEngine(web_search_engine=web_search_engine)
        
        logger.info("Legal Search Engine initialized successfully")
        return legal_search
        
    except Exception as e:
        logger.error(f"Legal Search Engine initialization failed: {e}")
        
        # Create a mock legal search engine
        class MockLegalSearchEngine:
            def __init__(self):
                pass
            
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
        
        # Get required dependencies
        legal_rag_engine = container.get('legal_rag_engine')
        legal_search_engine = container.get('legal_search_engine')
        
        # Create legal chatbot
        legal_chatbot = LegalChatbot(
            legal_rag_engine=legal_rag_engine,
            web_search_engine=legal_search_engine
        )
        
        logger.info("Legal Chatbot initialized successfully")
        return legal_chatbot
        
    except Exception as e:
        logger.error(f"Legal Chatbot initialization failed: {e}")
        
        # Create a mock legal chatbot
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