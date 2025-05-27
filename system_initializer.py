#!/usr/bin/env python3
# system_initializer.py - UNIFIED system initialization with all components

import os
import logging
import importlib.util
from typing import Dict, List, Any, Optional, Callable

# Import the dependency container
from dependency_container import container

# Set up logging with UTF-8 encoding to handle Unicode characters
try:
    from market_reports.utils import config_manager, system_state, logger, safe_execute
except ImportError:
    # Fallback logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('system.log', encoding='utf-8')
        ]
    )
    logger = logging.getLogger("market_intelligence")

# Import legal compliance components (LegalSearchEngine intentionally removed)
try:
    from legal_compliance import LegalRAGEngine, LegalChatbot
    LEGAL_COMPLIANCE_AVAILABLE = True
    logger.info("Legal compliance modules imported successfully (web search disabled)")
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
            # Legal compliance components (search engine removed for compliance)
            "legal_rag_engine",
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
            # Register core components first
            self._register_core_components()
            
            # Register legal components
            self._register_legal_components()
            
            if offline_mode:
                logger.info("Working in offline mode - limiting component initialization")
                try:
                    system_state.current_state = 'offline'
                except:
                    pass
            
            # Initialize core market intelligence components
            core_components = ["rag_engine", "web_search", "report_generator", 
                             "report_conversation", "pdf_exporter", "market_report_system"]
            
            for component_name in core_components:
                self._initialize_component(component_name, offline_mode)
            
            # Initialize legal compliance components
            self._initialize_legal_components(offline_mode)
            
            # Update system state
            self._update_system_state()
            
            self.initialized = True
            logger.info(f"System initialization complete. State: {getattr(system_state, 'current_state', 'unknown')}")
            
            return True
        
        except Exception as e:
            logger.error(f"Critical error during system initialization: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            try:
                system_state.current_state = 'offline'
            except:
                pass
            return False
    
    def _register_core_components(self) -> None:
        """Register core utility components in the container"""
        try:
            container.register('config_manager', config_manager)
            container.register('system_state', system_state)
        except:
            logger.warning("Could not register core utilities")
    
    def _register_legal_components(self) -> None:
        """Register legal component factories (web search intentionally excluded)"""
        self.register_component_factory('legal_rag_engine', self._create_legal_rag_engine)
        self.register_component_factory('legal_chatbot', self._create_legal_chatbot)
        logger.info("Legal compliance component factories registered (database-only mode)")
    
    def _initialize_legal_components(self, offline_mode: bool) -> None:
        """Initialize legal compliance components (database-only mode)"""
        logger.info("Initializing Legal Compliance System (Database-Only Mode)...")
        
        if not LEGAL_COMPLIANCE_AVAILABLE:
            logger.warning("Legal compliance components not available")
            try:
                system_state.set_component_status('legal_system', False, "Legal components not available")
            except:
                pass
            return
        
        # Initialize legal components in order (no search engine)
        legal_components = ['legal_rag_engine', 'legal_chatbot']
        
        for legal_component in legal_components:
            try:
                success = self._initialize_component(legal_component, offline_mode)
                if success:
                    logger.info(f"{legal_component} initialized successfully")
                else:
                    logger.warning(f"{legal_component} initialization failed - using fallback")
            except Exception as e:
                logger.error(f"{legal_component} initialization error: {e}")
        
        # Test the legal system if possible
        try:
            legal_chatbot = container.get('legal_chatbot')
            if legal_chatbot and hasattr(legal_chatbot, 'get_system_status'):
                system_status = legal_chatbot.get_system_status()
                logger.info(f"Legal system test (database-only): {system_status}")
                
                # Check if we have full RAG capability
                rag_test = system_status.get('rag_connection_test', {})
                if rag_test.get('status') == 'success':
                    logger.info(f"FULL Legal RAG system active with {rag_test.get('total_documents', 0)} documents (database-only)")
                    try:
                        system_state.set_component_status('legal_system', True, "Full RAG system with Weaviate (database-only)")
                    except:
                        pass
                else:
                    logger.info("Limited legal system active (database-only, no Weaviate connection)")
                    try:
                        system_state.set_component_status('legal_system', True, "Limited legal system (database-only)")
                    except:
                        pass
            else:
                logger.info("Basic legal system active (database-only)")
                try:
                    system_state.set_component_status('legal_system', True, "Basic legal system (database-only)")
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"Could not test legal system: {e}")
            try:
                system_state.set_component_status('legal_system', False, f"Test failed: {str(e)}")
            except:
                pass
    
    def _initialize_component(self, component_name: str, offline_mode: bool) -> bool:
        """Initialize a specific component"""
        logger.debug(f"Initializing component: {component_name}")
        
        # Skip certain components in offline mode
        if offline_mode and component_name in ['rag_engine', 'web_search', 'legal_rag_engine']:
            logger.info(f"Skipping {component_name} initialization in offline mode")
            try:
                system_state.set_component_status(component_name, False, "Component disabled in offline mode")
            except:
                pass
            return False
        
        try:
            if component_name in self.component_factories:
                component = self.component_factories[component_name](container)
                container.register(component_name, component)
                try:
                    system_state.set_component_status(component_name, True, f"Component initialized successfully")
                except:
                    pass
                logger.debug(f"Component {component_name} initialized successfully")
                return True
            else:
                logger.warning(f"No factory registered for component: {component_name}")
                try:
                    system_state.set_component_status(component_name, False, "No factory registered for this component")
                except:
                    pass
                return False
        
        except Exception as e:
            logger.error(f"Error initializing {component_name}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            try:
                system_state.set_component_status(component_name, False, f"Initialization failed: {str(e)}")
            except:
                pass
            return False
    
    def _update_system_state(self) -> None:
        """Enhanced system state update that includes legal compliance"""
        try:
            critical_components = ['rag_engine', 'web_search']
            legal_components = ['legal_rag_engine', 'legal_chatbot']
            
            available_components = sum(1 for comp in self.required_components 
                                      if system_state.get_component_status(comp).get('available', False))
            
            total_components = len(self.required_components)
            critical_available = all(system_state.get_component_status(comp).get('available', False) 
                                   for comp in critical_components)
            
            legal_available = any(system_state.get_component_status(comp).get('available', False) 
                                 for comp in legal_components)
            
            # Determine overall system state
            if critical_available and available_components >= total_components * 0.8:
                system_state.current_state = 'online'
            elif critical_available or available_components > 0:
                system_state.current_state = 'degraded'  
            else:
                system_state.current_state = 'offline'
            
            # Log legal system status
            if legal_available:
                legal_status = system_state.get_component_status('legal_system')
                if legal_status.get('available'):
                    logger.info(f"Legal compliance system: {legal_status.get('description', 'Available')}")
                else:
                    logger.info("Legal compliance system: Limited availability")
            else:
                logger.warning("Legal compliance system: Not available")
            
            logger.info(f"System state set to {system_state.current_state} "
                       f"({available_components}/{total_components} components available)")
        except Exception as e:
            logger.error(f"Error updating system state: {e}")
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview including legal components"""
        try:
            overview = {
                'system_state': getattr(system_state, 'current_state', 'unknown'),
                'initialized': self.initialized,
                'total_components': len(self.required_components),
                'available_components': 0,
                'component_status': {},
                'legal_system': {
                    'available': LEGAL_COMPLIANCE_AVAILABLE,
                    'status': 'unknown'
                }
            }
            
            # Get component status
            for component in self.required_components:
                try:
                    status = system_state.get_component_status(component)
                    overview['component_status'][component] = status
                    if status.get('available', False):
                        overview['available_components'] += 1
                except:
                    overview['component_status'][component] = {'available': False, 'description': 'Status unknown'}
            
            return overview
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {
                'system_state': 'error',
                'initialized': self.initialized,
                'error': str(e)
            }

    # COMPONENT FACTORIES

    def _create_rag_engine(self, container):
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
            return self._create_mock_rag_engine()

    def _create_mock_rag_engine(self):
        """Create mock RAG engine"""
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

    def _create_web_search(self, container):
        """Factory for Web Search component"""
        try:
            from market_reports.web_search import WebResearchEngine
            engine = WebResearchEngine()
            logger.info("Web Search Engine initialized successfully")
            return engine
        except ImportError as e:
            logger.error(f"Web Search initialization failed due to missing dependencies: {e}")
            return self._create_mock_web_search()

    def _create_mock_web_search(self):
        """Create mock web search engine"""
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

    def _create_report_generator(self, container):
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
            return self._create_mock_report_generator()

    def _create_mock_report_generator(self):
        """Create mock report generator"""
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

    def _create_report_conversation(self, container):
        """Factory for Report Conversation component"""
        try:
            from market_reports.report_conversation_enhanced import ReportConversation
            rag_engine = container.get('rag_engine')
            conversation = ReportConversation(rag_engine=rag_engine)
            logger.info("Report Conversation initialized successfully")
            return conversation
        except ImportError as e:
            logger.error(f"Report Conversation initialization failed due to missing dependencies: {e}")
            return self._create_mock_report_conversation()

    def _create_mock_report_conversation(self):
        """Create mock report conversation"""
        class MockReportConversation:
            def ask_question(self, query):
                return f"Mock conversation response for: {query}"
        
        return MockReportConversation()

    def _create_pdf_exporter(self, container):
        """Factory for PDF Exporter component"""
        try:
            from market_reports.pdf_exporter_enhanced import PDFExporter
            exporter = PDFExporter()
            logger.info("PDF Exporter initialized successfully")
            return exporter
        except ImportError as e:
            logger.error(f"PDF Exporter initialization failed due to missing dependencies: {e}")
            return self._create_mock_pdf_exporter()

    def _create_mock_pdf_exporter(self):
        """Create mock PDF exporter"""
        class MockPDFExporter:
            def export_report_to_pdf(self, report_data, output_path):
                logger.warning("PDF export not available - using mock exporter")
                return False
        
        return MockPDFExporter()

    def _create_market_report_system(self, container):
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
            return self._create_mock_market_report_system()

    def _create_mock_market_report_system(self):
        """Create mock market report system"""
        class MockMarketReportSystem:
            def create_market_report(self, title, sectors, geography, enhance_with_web=True, include_visuals=True):
                return {"report_data": {}, "json_file": "", "pdf_file": None}
            
            def list_reports(self):
                return []
            
            def delete_report(self, filename):
                return True
        
        return MockMarketReportSystem()

    # LEGAL COMPONENT FACTORIES

    def _create_legal_rag_engine(self, container):
        """Factory for Legal RAG Engine component"""
        if not LEGAL_COMPLIANCE_AVAILABLE:
            return self._create_mock_legal_rag_engine()
        
        try:
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
            
            # Try to get embedding engine
            try:
                from market_reports.rag_enhanced import embedding_engine as rag_embedding_engine
                embedding_engine = rag_embedding_engine
            except ImportError:
                logger.warning("Could not import embedding engine from rag_enhanced")
            
            # Create the legal RAG engine
            legal_rag = LegalRAGEngine(
                weaviate_client=weaviate_client,
                openai_client=openai_client,
                embedding_engine=embedding_engine
            )
            
            logger.info("Legal RAG Engine initialized successfully")
            return legal_rag
            
        except Exception as e:
            logger.error(f"Legal RAG Engine initialization failed: {e}")
            return self._create_mock_legal_rag_engine()

    def _create_mock_legal_rag_engine(self):
        """Create mock legal RAG engine"""
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

    def _create_legal_chatbot(self, container):
        """Factory for Legal Chatbot component"""
        if not LEGAL_COMPLIANCE_AVAILABLE:
            return self._create_mock_legal_chatbot()
        
        try:
            legal_rag_engine = container.get('legal_rag_engine')
            
            legal_chatbot = LegalChatbot(
                legal_rag_engine=legal_rag_engine
            )
            
            # Add enhanced methods for system status
            def get_system_status(self):
                """Get the status of the legal compliance system"""
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
                    "rag_connection_test": rag_test,
                    "session_active": self.current_session is not None,
                    "total_queries": self.current_session["metadata"]["queries_count"] if self.current_session else 0
                }
            
            # Bind the method to the chatbot instance
            legal_chatbot.get_system_status = get_system_status.__get__(legal_chatbot, LegalChatbot)
            
            logger.info("Legal Chatbot initialized successfully")
            return legal_chatbot
            
        except Exception as e:
            logger.error(f"Legal Chatbot initialization failed: {e}")
            return self._create_mock_legal_chatbot()

    def _create_mock_legal_chatbot(self):
        """Create mock legal chatbot"""
        class MockLegalChatbot:
            def __init__(self):
                self.current_session = None
            
            def start_new_session(self, user_id=None):
                import uuid
                session_id = str(uuid.uuid4())
                self.current_session = {"session_id": session_id, "messages": [], "metadata": {"queries_count": 0}}
                return session_id
            
            def ask_legal_question(self, question, document_type=None, jurisdiction=None):
                return {
                    "response": "Legal chatbot service is currently unavailable. Please ensure all legal compliance dependencies are properly installed and configured.",
                    "session_id": self.current_session["session_id"] if self.current_session else None,
                    "citations": [],
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
            
            def get_system_status(self):
                return {
                    "legal_rag_engine": "mock",
                    "rag_connection_test": {"status": "mock", "message": "Mock legal system"},
                    "session_active": self.current_session is not None,
                    "total_queries": self.current_session["metadata"]["queries_count"] if self.current_session else 0
                }
        
        logger.info("Created mock Legal Chatbot due to initialization failure")
        return MockLegalChatbot()


# Create the system initializer instance and register all factories
system_initializer = SystemInitializer()

# Register component factories
system_initializer.register_component_factory('rag_engine', system_initializer._create_rag_engine)
system_initializer.register_component_factory('web_search', system_initializer._create_web_search)
system_initializer.register_component_factory('report_generator', system_initializer._create_report_generator)
system_initializer.register_component_factory('report_conversation', system_initializer._create_report_conversation)
system_initializer.register_component_factory('pdf_exporter', system_initializer._create_pdf_exporter)
system_initializer.register_component_factory('market_report_system', system_initializer._create_market_report_system)

def initialize_system(offline_mode=False):
    """Convenience function to initialize the entire system"""
    return system_initializer.initialize_system(offline_mode)

def get_system_overview():
    """Get comprehensive system overview"""
    return system_initializer.get_system_overview()