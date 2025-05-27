#!/usr/bin/env python3
# system_initializer.py - Lightweight system initialization

import os
import logging
from typing import Dict, Any, Callable
from dependency_container import container

try:
    from market_reports.utils import logger, system_state
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("market_intelligence")
    
    # Simple system state fallback
    class SystemState:
        def __init__(self):
            self.current_state = 'unknown'
            self.components = {}
        
        def set_component_status(self, name: str, available: bool, description: str = ""):
            self.components[name] = {'available': available, 'description': description}
        
        def get_component_status(self, name: str) -> Dict[str, Any]:
            return self.components.get(name, {'available': False, 'description': 'Not found'})
    
    system_state = SystemState()

try:
    from legal_compliance import LegalRAGEngine, LegalChatbot
    LEGAL_AVAILABLE = True
except ImportError:
    LEGAL_AVAILABLE = False
    logger.warning("Legal compliance not available")

class SystemInitializer:
    """Lightweight system initializer"""
    
    def __init__(self):
        self.required_components = [
            "rag_engine", "web_search", "report_generator", 
            "market_report_system", "legal_rag_engine", "legal_chatbot"
        ]
        self.initialized = False
    
    def initialize_system(self, offline_mode: bool = False) -> bool:
        """Initialize all components"""
        if self.initialized:
            return True
        
        logger.info(f"Initializing system (offline={offline_mode})")
        
        try:
            # Register factories
            container.register_factory('rag_engine', self._create_rag_engine)
            container.register_factory('web_search', self._create_web_search)
            container.register_factory('report_generator', self._create_report_generator)
            container.register_factory('market_report_system', self._create_market_report_system)
            
            if LEGAL_AVAILABLE:
                container.register_factory('legal_rag_engine', self._create_legal_rag_engine)
                container.register_factory('legal_chatbot', self._create_legal_chatbot)
            
            # Initialize core components
            for component in self.required_components:
                if offline_mode and component == 'web_search':
                    continue
                self._initialize_component(component)
            
            self._update_system_state()
            self.initialized = True
            logger.info("System initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            system_state.current_state = 'offline'
            return False
    
    def _initialize_component(self, name: str) -> bool:
        """Initialize single component"""
        try:
            component = container.get(name)
            system_state.set_component_status(name, bool(component), 
                                            f"Component {'available' if component else 'failed'}")
            return bool(component)
        except Exception as e:
            logger.error(f"Component {name} failed: {e}")
            system_state.set_component_status(name, False, f"Error: {str(e)}")
            return False
    
    def _update_system_state(self):
        """Update overall system state"""
        available = sum(1 for comp in self.required_components 
                       if system_state.get_component_status(comp).get('available', False))
        total = len(self.required_components)
        
        if available >= total * 0.8:
            system_state.current_state = 'online'
        elif available > 0:
            system_state.current_state = 'degraded'
        else:
            system_state.current_state = 'offline'
        
        logger.info(f"System state: {system_state.current_state} ({available}/{total} components)")
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system overview"""
        return {
            'system_state': system_state.current_state,
            'initialized': self.initialized,
            'total_components': len(self.required_components),
            'available_components': sum(1 for comp in self.required_components 
                                      if system_state.get_component_status(comp).get('available', False))
        }
    
    # Component Factories (Lightweight)
    
    def _create_rag_engine(self, container):
        """Create RAG engine"""
        try:
            from market_reports.rag_enhanced import get_weaviate_client, generate_rag_response
            
            class LightweightRAGEngine:
                def __init__(self):
                    self.client = get_weaviate_client()
                
                def generate_rag_response(self, query, context_limit=5):
                    try:
                        return generate_rag_response(query, context_limit)
                    except Exception as e:
                        return f"RAG response unavailable: {str(e)}"
            
            return LightweightRAGEngine()
        except Exception as e:
            logger.error(f"RAG engine creation failed: {e}")
            return self._create_mock_rag_engine()
    
    def _create_web_search(self, container):
        """Create web search engine"""
        try:
            from market_reports.web_search import WebResearchEngine
            return WebResearchEngine()
        except Exception as e:
            logger.error(f"Web search creation failed: {e}")
            
            class MockWebSearch:
                def research_topic(self, query, **kwargs):
                    return {"data": [{"title": f"Mock result for {query}", "url": "mock://url"}]}
            return MockWebSearch()
    
    def _create_report_generator(self, container):
        """Create report generator"""
        try:
            from market_reports.report_generator_enhanced import ReportGenerator
            return ReportGenerator(rag_engine=container.get('rag_engine'), 
                                 web_search=container.get('web_search'))
        except Exception as e:
            logger.error(f"Report generator creation failed: {e}")
            
            class MockReportGenerator:
                def generate_market_report(self, title, sectors, geography, **kwargs):
                    return {"title": title, "sections": [{"title": "Mock Section", "content": "Mock content"}]}
            return MockReportGenerator()
    
    def _create_market_report_system(self, container):
        """Create market report system"""
        try:
            from market_reports.market_report_system import MarketReportSystem
            return MarketReportSystem(
                rag_engine=container.get('rag_engine'),
                web_search=container.get('web_search'),
                report_generator=container.get('report_generator')
            )
        except Exception as e:
            logger.error(f"Market report system creation failed: {e}")
            
            class MockMarketReportSystem:
                def create_market_report(self, **kwargs):
                    return {"report_data": {"title": "Mock Report"}}
                def list_reports(self):
                    return []
            return MockMarketReportSystem()
    
    def _create_legal_rag_engine(self, container):
        """Create legal RAG engine"""
        if not LEGAL_AVAILABLE:
            return None
        
        try:
            rag_engine = container.get('rag_engine')
            weaviate_client = getattr(rag_engine, 'client', None) if rag_engine else None
            return LegalRAGEngine(weaviate_client=weaviate_client)
        except Exception as e:
            logger.error(f"Legal RAG creation failed: {e}")
            return None
    
    def _create_legal_chatbot(self, container):
        """Create legal chatbot"""
        if not LEGAL_AVAILABLE:
            return None
        
        try:
            legal_rag = container.get('legal_rag_engine')
            return LegalChatbot(legal_rag_engine=legal_rag)
        except Exception as e:
            logger.error(f"Legal chatbot creation failed: {e}")
            return None
    
    def _create_mock_rag_engine(self):
        """Mock RAG engine fallback"""
        class MockRAGEngine:
            def __init__(self):
                self.client = None
            def generate_rag_response(self, query, context_limit=5):
                return f"Mock response for: {query}"
        return MockRAGEngine()

# Global initializer
system_initializer = SystemInitializer()

def initialize_system(offline_mode=False):
    """Initialize system"""
    return system_initializer.initialize_system(offline_mode)

def get_system_overview():
    """Get system overview"""
    return system_initializer.get_system_overview()