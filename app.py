#!/usr/bin/env python3
# app.py - LinkSaudi Market Intelligence Platform with FIXED Legal RAG Integration
# Comprehensive Streamlit application with organized structure

# =============================================================================
# PAGE CONFIGURATION (Must be first)
# =============================================================================

import streamlit as st

st.set_page_config(
    page_title="LinkSaudi Market Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# IMPORTS AND DEPENDENCIES
# =============================================================================

# Standard library imports
import os
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Third-party imports
import matplotlib.pyplot as plt
import pandas as pd

# Core system imports
try:
    from dependency_container import container
    from system_initializer import initialize_system, get_system_overview
    from error_handling import format_error_for_display
    CORE_IMPORTS_AVAILABLE = True
except ImportError as e:
    CORE_IMPORTS_AVAILABLE = False
    print(f"Core imports failed: {e}")

# Market intelligence imports
try:
    from market_reports.utils import (
        logger, config_manager, system_state, 
        read_file_with_encoding, write_file_with_encoding, 
        save_json_with_encoding, load_json_with_encoding, clean_ai_language
    )
    MARKET_UTILS_AVAILABLE = True
except ImportError as e:
    MARKET_UTILS_AVAILABLE = False
    print(f"Market intelligence utils not available: {e}")

# Legal compliance imports - Original
try:
    from legal_compliance import LegalRAGEngine, LegalChatbot, LegalSearchEngine
    LEGAL_COMPLIANCE_AVAILABLE = True
    print("Legal compliance components imported successfully")
except ImportError as e:
    LEGAL_COMPLIANCE_AVAILABLE = False
    print(f"Legal compliance components not available: {e}")

# Legal compliance imports - FIXED versions
try:
    from legal_compliance.legal_rag_engine import LegalRAGEngine as FixedLegalRAGEngine
    from system_initializer_legal_fixes import (
        create_legal_rag_engine_fixed,
        create_legal_chatbot_enhanced,
        get_legal_system_diagnostics,
        update_system_initializer_with_fixed_legal
    )
    FIXED_LEGAL_AVAILABLE = True
    print("✅ FIXED Legal RAG components imported successfully")
except ImportError as e:
    FIXED_LEGAL_AVAILABLE = False
    print(f"⚠️ FIXED Legal RAG components not available: {e}")

# =============================================================================
# CUSTOM CSS STYLING
# =============================================================================

st.markdown("""
<style>
    /* Dark theme colors */
    :root {
        --primary-green: #609156;
        --secondary-green: #7FB878;
        --dark-bg: #121212;
        --dark-card-bg: #1E1E1E;
        --dark-text: #FFFFFF;
        --dark-secondary-text: #CCCCCC;
        --dark-accent: #A49E6D;
        --dark-border: #333333;
        --error-red: #FF5252;
        --warning-amber: #FFC107;
        --success-green: #81C784;
        --info-blue: #64B5F6;
    }
    
    /* Global styles */
    .stApp {
        background-color: var(--dark-bg) !important;
        color: var(--dark-text) !important;
    }
    
    /* Headers */
    .main-header {
        color: var(--primary-green);
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .sub-header {
        color: var(--secondary-green);
        font-size: 1.8rem;
        font-weight: 600;
        margin: 1.5rem 0;
        border-bottom: 2px solid var(--dark-accent);
        padding-bottom: 0.5rem;
    }
    
    /* Cards and containers */
    .section-card {
        background: linear-gradient(135deg, var(--dark-card-bg) 0%, #2D2D2D 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid var(--dark-border);
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Chat interface */
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid var(--primary-green);
    }
    
    .user-message {
        background: linear-gradient(135deg, #2D4A3D 0%, #1F3329 100%);
        border-left-color: var(--secondary-green);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, var(--dark-card-bg) 0%, #252525 100%);
        border-left-color: var(--dark-accent);
    }
    
    /* Status indicators */
    .status-indicator {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .status-indicator.online {
        background: linear-gradient(135deg, var(--success-green) 0%, #66BB6A 100%);
        color: #1B5E20;
    }
    
    .status-indicator.degraded {
        background: linear-gradient(135deg, var(--warning-amber) 0%, #FFB74D 100%);
        color: #E65100;
    }
    
    .status-indicator.offline {
        background: linear-gradient(135deg, var(--error-red) 0%, #EF5350 100%);
        color: #B71C1C;
    }
    
    /* Loading animations */
    .loading-container {
        text-align: center;
        padding: 2rem;
    }
    
    .spinner {
        border: 3px solid var(--dark-border);
        border-top: 3px solid var(--primary-green);
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto 1rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-text {
        color: var(--dark-secondary-text);
        font-style: italic;
    }
    
    /* Error handling */
    .error-container {
        background: linear-gradient(135deg, #4A2C2A 0%, #3D1E1C 100%);
        border: 1px solid var(--error-red);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-message {
        color: var(--error-red);
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .error-details {
        color: var(--dark-secondary-text);
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    
    .error-suggestions {
        color: var(--dark-secondary-text);
        font-size: 0.9rem;
    }
    
    .error-suggestions ul {
        margin: 0.5rem 0;
        padding-left: 1.5rem;
    }
    
    /* Report styling */
    .report-header {
        background: linear-gradient(135deg, var(--primary-green) 0%, var(--secondary-green) 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px 10px 0 0;
        text-align: center;
    }
    
    .report-section {
        background: var(--dark-card-bg);
        margin: 1rem 0;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--dark-border);
    }
    
    .report-section-title {
        background: linear-gradient(135deg, var(--dark-accent) 0%, #8B7F47 100%);
        color: white;
        padding: 1rem;
        margin: 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    /* Legal compliance specific styles */
    .legal-disclaimer {
        background: linear-gradient(135deg, #4A3C2A 0%, #3D2E1C 100%);
        border: 2px solid var(--warning-amber);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    .legal-session-info {
        background: var(--dark-card-bg);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid var(--info-blue);
    }
    
    .legal-citation {
        background: #2A2A3A;
        border-radius: 6px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-left: 3px solid var(--secondary-green);
        font-size: 0.9rem;
    }
    
    .legal-warning {
        background: linear-gradient(135deg, #4A2A2A 0%, #3D1C1C 100%);
        border: 1px solid var(--warning-amber);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: var(--warning-amber);
    }
    
    /* Legal system status indicators */
    .system-status-full-rag {
        background: linear-gradient(135deg, #2E7D32 0%, #388E3C 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    
    .system-status-limited {
        background: linear-gradient(135deg, #F57C00 0%, #FF9800 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    
    .system-status-basic {
        background: linear-gradient(135deg, #1976D2 0%, #2196F3 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        # Core system state
        st.session_state['initialized'] = False
        st.session_state['offline_mode'] = False
        st.session_state['system_status'] = 'unknown'
        st.session_state['connection_status'] = 'unknown'
        
        # Market intelligence state
        st.session_state['history'] = []
        st.session_state['reports'] = []
        st.session_state['current_report'] = None
        st.session_state['temp_files'] = []
        st.session_state['chat_messages'] = []
        st.session_state['prompt_count'] = 0
        st.session_state['report_ready'] = False
        
        # Legal compliance state - Enhanced
        st.session_state['legal_system_available'] = False
        st.session_state['legal_system_type'] = 'unknown'  # full_rag, limited, basic, unavailable
        st.session_state['legal_chat_messages'] = []
        st.session_state['current_legal_session'] = None
        st.session_state['legal_query_count'] = 0
        st.session_state['legal_document_count'] = 0
        
        # Legal UI state
        st.session_state['show_legal_history'] = False
        st.session_state['show_legal_diagnostics'] = False
        st.session_state['show_precedent_search'] = False
        st.session_state['show_compliance_tool'] = False
        st.session_state['show_session_report'] = False
        st.session_state['current_session_report'] = None

# Initialize session state
initialize_session_state()

# =============================================================================
# SYSTEM INITIALIZATION FUNCTIONS
# =============================================================================

def initialize_application():
    """Initialize the application with proper error handling"""
    try:
        # Create necessary directories
        _create_directories()
        
        # Create default config if needed
        _create_default_config()
        
        # Check if we're already initialized
        if st.session_state['initialized']:
            logger.info("Application already initialized")
            return True
        
        # Try to initialize using new architecture
        if CORE_IMPORTS_AVAILABLE:
            return _initialize_with_new_architecture()
        else:
            return _initialize_with_fallback()
            
    except Exception as e:
        logger.error(f"Critical error initializing application: {e}")
        return _handle_initialization_failure()

def _create_directories():
    """Create necessary application directories"""
    directories = [
        "report_charts", "market_reports", "legal_conversations", 
        "legal_cache", "logs"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def _create_default_config():
    """Create default configuration file if it doesn't exist"""
    config_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, "config.json")
    if not os.path.exists(config_file):
        default_config = {
            "api_keys": {
                "openai": "",
                "weaviate": {
                    "url": "http://localhost:8080",
                    "api_key": ""
                }
            },
            "embedding": {
                "model": "text-embedding-3-small",
                "dimensions": 1536,
                "use_local_fallback": True
            },
            "system": {
                "min_search_interval": 5,
                "max_retries": 3,
                "chart_dir": "report_charts",
                "report_dir": "market_reports",
                "log_level": "INFO"
            },
            "legal": {
                "weaviate_class": "LegalDocument",
                "max_context_documents": 10,
                "enable_web_enhancement": True,
                "cache_duration_hours": 24
            }
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info(f"Created default config file at {config_file}")

def _initialize_with_new_architecture():
    """Initialize using the new refactored architecture"""
    try:
        from market_reports.utils import logger, config_manager, system_state
        from dependency_container import container
        from system_initializer import initialize_system
        
        logger.info("Using refactored architecture")
        
        # Initialize using new system
        success = initialize_system(offline_mode=st.session_state['offline_mode'])
        
        if success:
            logger.info("System initialized successfully with new architecture")
            st.session_state['initialized'] = True
            st.session_state['system_status'] = system_state.current_state
            st.session_state['connection_status'] = system_state.current_state
            
            # Load existing reports
            if container.has('market_report_system'):
                market_report_system = container.get('market_report_system')
                st.session_state['reports'] = market_report_system.list_reports()
            
            # Initialize legal compliance with FIXED components
            initialize_legal_compliance()
            
            return True
        return False
        
    except ImportError as e:
        logger.info(f"Refactored architecture not available: {e}")
        return False

def _initialize_with_fallback():
    """Initialize using fallback approach"""
    try:
        if st.session_state['offline_mode']:
            logger.info("Working in offline mode. Some features may be limited.")
            st.session_state['connection_status'] = 'offline'
            st.session_state['system_status'] = 'offline'
            st.session_state['initialized'] = True
            return True
        return True
    except Exception as e:
        logger.error(f"Critical error during legacy initialization: {e}")
        return False

def _handle_initialization_failure():
    """Handle initialization failure gracefully"""
    import traceback
    logger.debug(traceback.format_exc())
    
    # Set system to offline mode due to initialization failure
    st.session_state['system_status'] = 'offline'
    st.session_state['connection_status'] = 'offline'
    st.session_state['offline_mode'] = True
    st.session_state['initialized'] = True
    return False

def initialize_legal_compliance():
    """Initialize legal compliance components with FIXED RAG system"""
    try:
        if not LEGAL_COMPLIANCE_AVAILABLE and not FIXED_LEGAL_AVAILABLE:
            st.session_state['legal_system_available'] = False
            st.session_state['legal_system_type'] = 'unavailable'
            return False
        
        # Get dependencies from container
        from dependency_container import container
        
        # Update system initializer with FIXED legal components if available
        if FIXED_LEGAL_AVAILABLE:
            try:
                from system_initializer import system_initializer
                update_system_initializer_with_fixed_legal(system_initializer)
                logger.info("System initializer updated with FIXED legal components")
            except Exception as e:
                logger.warning(f"Could not update system initializer: {e}")
        
        # Check if legal components are available in container
        if container.has('legal_rag_engine') and container.has('legal_chatbot'):
            st.session_state['legal_rag_engine'] = container.get('legal_rag_engine')
            st.session_state['legal_chatbot'] = container.get('legal_chatbot')
            st.session_state['legal_search_engine'] = container.get('legal_search_engine')
            
            # Test the legal system if FIXED version is available
            return _test_legal_system()
        else:
            st.session_state['legal_system_available'] = False
            st.session_state['legal_system_type'] = 'unavailable'
            logger.warning("Legal compliance components not found in container")
            return False
    
    except Exception as e:
        logger.error(f"Error initializing legal compliance: {e}")
        st.session_state['legal_system_available'] = False
        st.session_state['legal_system_type'] = 'unavailable'
        return False

def _test_legal_system():
    """Test legal system capabilities and set appropriate status"""
    if FIXED_LEGAL_AVAILABLE and hasattr(st.session_state['legal_chatbot'], 'get_system_status'):
        try:
            system_status = st.session_state['legal_chatbot'].get_system_status()
            logger.info(f"Legal system status: {system_status}")
            
            # Check if we have a real RAG connection
            rag_test = system_status.get('rag_connection_test', {})
            if rag_test.get('status') == 'success':
                st.session_state['legal_system_available'] = True
                st.session_state['legal_system_type'] = 'full_rag'
                st.session_state['legal_document_count'] = rag_test.get('total_documents', 0)
                logger.info("✅ FULL Legal RAG system with Weaviate available")
            elif rag_test.get('status') == 'mock':
                st.session_state['legal_system_available'] = True
                st.session_state['legal_system_type'] = 'basic'
                st.session_state['legal_document_count'] = 0
                logger.info("🔵 Basic legal system available (mock)")
            else:
                st.session_state['legal_system_available'] = True
                st.session_state['legal_system_type'] = 'limited'
                st.session_state['legal_document_count'] = 0
                logger.info("⚠️ Limited legal system available (no Weaviate connection)")
        except Exception as e:
            logger.error(f"Error testing legal system: {e}")
            st.session_state['legal_system_available'] = True
            st.session_state['legal_system_type'] = 'basic'
            st.session_state['legal_document_count'] = 0
    else:
        st.session_state['legal_system_available'] = True
        st.session_state['legal_system_type'] = 'basic'
        st.session_state['legal_document_count'] = 0
        logger.info("Basic legal compliance system available")
    
    return True

# =============================================================================
# UI UTILITY FUNCTIONS
# =============================================================================

def display_status_indicator():
    """Display system status indicator"""
    status = st.session_state['system_status']
    
    if status == 'online':
        st.markdown("""
        <div class="status-indicator online">
            <span>●</span>&nbsp;System online - All services available
        </div>
        """, unsafe_allow_html=True)
    elif status == 'offline':
        st.markdown("""
        <div class="status-indicator offline">
            <span>●</span>&nbsp;System offline - Working with cached data only
        </div>
        """, unsafe_allow_html=True)
    else:  # degraded
        st.markdown("""
        <div class="status-indicator degraded">
            <span>●</span>&nbsp;System degraded - Some services may be unavailable
        </div>
        """, unsafe_allow_html=True)

def display_error(error, user_message=None):
    """Display error message with suggestions"""
    if CORE_IMPORTS_AVAILABLE:
        error_data = format_error_for_display(error, user_message)
    else:
        error_data = {
            'user_message': user_message or "An error occurred",
            'technical_details': str(error),
            'suggestions': ["Try refreshing the page", "Contact support"]
        }
    
    st.markdown(f"""
    <div class="error-container">
        <div class="error-message">{error_data['user_message']}</div>
        <div class="error-details">{error_data['technical_details']}</div>
        <div class="error-suggestions">
            <strong>Suggestions:</strong>
            <ul>
                {''.join([f'<li>{suggestion}</li>' for suggestion in error_data['suggestions']])}
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_loading_state(message="Processing your request...", show_spinner=True):
    """Create a consistent loading state with progress reporting capability"""
    container = st.empty()
    progress_bar = None
    start_time = time.time()
    
    # Initialize UI elements
    if show_spinner:
        with container.container():
            st.markdown(f"""
            <div class="loading-container">
                <div class="spinner"></div>
                <div class="loading-text">{message}</div>
            </div>
            """, unsafe_allow_html=True)
            progress_bar = st.progress(0)
    else:
        container.info(message)
    
    def update(progress=None, message=None):
        """Update the loading state"""
        nonlocal container, progress_bar
        
        if message:
            with container.container():
                st.markdown(f"""
                <div class="loading-container">
                    <div class="spinner"></div>
                    <div class="loading-text">{message}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if progress_bar:
                    if progress is not None:
                        progress_bar.progress(progress)
                    else:
                        progress_bar = st.progress(0)
        elif progress is not None and progress_bar:
            progress_bar.progress(progress)
    
    def complete(success=True, message=None):
        """Complete the loading state"""
        nonlocal container, start_time
        
        elapsed_time = time.time() - start_time
        
        if success:
            if message:
                container.success(f"{message} (Completed in {elapsed_time:.2f}s)")
            else:
                container.success(f"Completed in {elapsed_time:.2f}s")
        else:
            if message:
                container.error(f"{message} (Failed after {elapsed_time:.2f}s)")
            else:
                container.error(f"Failed after {elapsed_time:.2f}s")
    
    return update, complete

# =============================================================================
# LEGAL COMPLIANCE INTERFACE
# =============================================================================
def _display_legal_system_unavailable():
    """Display UI when legal system is not available"""
    st.error("⚠️ Legal compliance system is not available. Please contact support.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Try to Initialize Legal System"):
            initialize_legal_compliance()
            st.rerun()
    with col2:
        if st.button("Run Legal System Diagnostics"):
            st.session_state['show_legal_diagnostics'] = True
            st.rerun()
    
    # Show diagnostics if requested
    if st.session_state.get('show_legal_diagnostics', False):
        st.markdown("### Legal System Diagnostics")
        try:
            from dependency_container import container
            if FIXED_LEGAL_AVAILABLE:
                from system_initializer_legal_fixes import get_legal_system_diagnostics
                diagnostics = get_legal_system_diagnostics(container)
                
                st.markdown(f"**Overall Status:** {diagnostics['overall_status']}")
                
                for component, status in diagnostics['components'].items():
                    if status.get('available'):
                        component_type = status.get('type', 'unknown')
                        if component_type == 'real':
                            st.success(f"✅ {component}: Fully operational")
                        elif component_type == 'enhanced':
                            st.success(f"✅ {component}: Enhanced version")
                        elif component_type == 'limited':
                            st.warning(f"⚠️ {component}: Limited functionality")
                        else:
                            st.info(f"ℹ️ {component}: {component_type}")
                    else:
                        st.error(f"❌ {component}: {status.get('error', 'Unavailable')}")
                
                if diagnostics.get('recommendations'):
                    st.markdown("**Recommendations:**")
                    for rec in diagnostics['recommendations']:
                        st.markdown(f"• {rec}")
            else:
                st.warning("FIXED legal diagnostics not available")
            
            if st.button("Hide Diagnostics"):
                st.session_state['show_legal_diagnostics'] = False
                st.rerun()
        except Exception as e:
            st.error(f"Could not run diagnostics: {e}")

def _display_legal_system_status():
    """Display enhanced legal system status"""
    system_type = st.session_state.get('legal_system_type', 'unknown')
    
    if system_type == 'full_rag':
        st.markdown("""
        <div class="system-status-full-rag">
            🟢 <strong>Full Legal RAG System Active</strong> - Connected to Weaviate legal database with AI-powered analysis
        </div>
        """, unsafe_allow_html=True)
    elif system_type == 'limited':
        st.markdown("""
        <div class="system-status-limited">
            🟡 <strong>Limited Legal System</strong> - Basic functionality available, no database connection
        </div>
        """, unsafe_allow_html=True)
    elif system_type == 'basic':
        st.markdown("""
        <div class="system-status-basic">
            🔵 <strong>Basic Legal System</strong> - Using fallback responses for demonstration
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚪ **Legal System Status Unknown**")

def _display_legal_system_metrics():
    """Display legal system metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        system_type = st.session_state.get('legal_system_type', 'unknown')
        if system_type == 'full_rag':
            system_status = "🟢 Full RAG"
        elif system_type == 'limited':
            system_status = "🟡 Limited"
        elif system_type == 'basic':
            system_status = "🔵 Basic"
        else:
            system_status = "⚪ Unknown"
        st.metric("System Type", system_status)
    
    with col2:
        st.metric("Queries Today", st.session_state['legal_query_count'])
    
    with col3:
        legal_session_active = st.session_state['current_legal_session'] is not None
        st.metric("Session", "Active" if legal_session_active else "None")
    
    with col4:
        doc_count = st.session_state.get('legal_document_count', 0)
        if doc_count > 0:
            st.metric("Legal Documents", f"{doc_count:,}")
        else:
            st.metric("Legal Documents", "N/A")

def _display_legal_diagnostics_panel():
    """Display legal diagnostics panel"""
    with st.expander("🔧 System Diagnostics", expanded=False):
        if st.button("Run Full Legal System Diagnostics"):
            try:
                from dependency_container import container
                if FIXED_LEGAL_AVAILABLE:
                    from system_initializer_legal_fixes import get_legal_system_diagnostics
                    diagnostics = get_legal_system_diagnostics(container)
                    
                    st.markdown("### Legal System Diagnostics Report")
                    st.markdown(f"**Overall Status:** `{diagnostics['overall_status']}`")
                    st.markdown(f"**Report Generated:** {diagnostics['timestamp']}")
                    
                    st.markdown("#### Component Status")
                    for component, status in diagnostics['components'].items():
                        with st.container():
                            if status.get('available'):
                                component_type = status.get('type', 'unknown')
                                if component_type == 'real':
                                    st.success(f"✅ **{component}**: Fully operational")
                                elif component_type == 'enhanced':
                                    st.success(f"✅ **{component}**: Enhanced version")
                                elif component_type == 'limited':
                                    st.warning(f"⚠️ **{component}**: Limited functionality")
                                elif component_type == 'mock':
                                    st.info(f"🔵 **{component}**: Mock implementation")
                                else:
                                    st.info(f"ℹ️ **{component}**: {component_type}")
                                
                                # Show additional details if available
                                if 'connection_test' in status:
                                    test_result = status['connection_test']
                                    if test_result.get('total_documents', 0) > 0:
                                        st.markdown(f"   📄 Documents: {test_result['total_documents']:,}")
                                    st.markdown(f"   🔗 Connection: {test_result.get('message', 'OK')}")
                            else:
                                st.error(f"❌ **{component}**: {status.get('error', 'Unavailable')}")
                    
                    if diagnostics.get('recommendations'):
                        st.markdown("#### Recommendations")
                        for rec in diagnostics['recommendations']:
                            st.markdown(f"💡 {rec}")
                else:
                    st.warning("FIXED legal diagnostics not available")
            except Exception as e:
                st.error(f"Could not run diagnostics: {e}")

def _display_legal_disclaimer():
    """Display legal disclaimer"""
    st.markdown("""
    <div class="legal-disclaimer">
        <h4>⚖️ Legal Disclaimer</h4>
        <p><strong>Important:</strong> This AI assistant provides general legal information based on available legal documents and should not replace professional legal advice. For specific legal matters, always consult with a qualified attorney licensed to practice in the relevant jurisdiction.</p>
        <ul>
            <li>Responses are for informational purposes only</li>
            <li>Laws and regulations may change frequently</li>
            <li>Individual circumstances may affect legal outcomes</li>
            <li>Always verify information with current legal sources</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def _display_legal_session_management():
    """Display legal session management interface"""
    st.markdown("### 💬 Legal Consultation Session")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.get('current_legal_session'):
            if st.button("End Current Session"):
                if 'legal_chatbot' in st.session_state:
                    try:
                        summary = st.session_state['legal_chatbot'].end_session()
                        st.success(f"Session ended. {summary.get('queries_count', 0)} queries processed.")
                        st.session_state['current_legal_session'] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error ending session: {e}")
        else:
            if st.button("Start New Legal Session"):
                if 'legal_chatbot' in st.session_state:
                    try:
                        session_id = st.session_state['legal_chatbot'].start_new_session()
                        st.session_state['current_legal_session'] = session_id
                        st.success(f"New legal session started: {session_id[:8]}...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error starting session: {e}")
    
    with col2:
        if st.button("View Session History"):
            st.session_state['show_legal_history'] = not st.session_state.get('show_legal_history', False)
            st.rerun()
    
    with col3:
        if st.session_state.get('current_legal_session') and st.button("Export Session Report"):
            st.session_state['show_session_report'] = True
            st.rerun()
    
    # Display current session info
    if st.session_state.get('current_legal_session'):
        st.markdown(f"""
        <div class="legal-session-info">
            <strong>Current Session:</strong> {st.session_state['current_legal_session'][:8]}...<br>
            <strong>Queries in Session:</strong> {st.session_state.get('legal_query_count', 0)}
        </div>
        """, unsafe_allow_html=True)

def _display_legal_chat_interface():
    """Display the main legal chat interface"""
    st.markdown("### 💬 Ask Your Legal Question")
    
    # Chat input and filters
    col1, col2 = st.columns([3, 1])
    
    with col1:
        legal_question = st.text_area(
            "Enter your legal question:",
            placeholder="e.g., What are the requirements for establishing a company in Saudi Arabia?",
            height=100
        )
    
    with col2:
        st.markdown("**Filters:**")
        
        # Get available categories and jurisdictions
        legal_categories = ["All Categories"]
        jurisdictions = ["Saudi Arabia"]
        
        if 'legal_chatbot' in st.session_state:
            try:
                legal_categories.extend(st.session_state['legal_chatbot'].get_legal_categories())
                jurisdictions.extend(st.session_state['legal_chatbot'].get_available_jurisdictions())
            except:
                pass
        
        selected_category = st.selectbox("Legal Category:", legal_categories)
        selected_jurisdiction = st.selectbox("Jurisdiction:", jurisdictions)
        include_web_search = st.checkbox("Include web search", value=True)
    
    # Submit button
    if st.button("🔍 Get Legal Guidance", type="primary"):
        if legal_question.strip():
            _process_legal_question(
                legal_question, 
                selected_category if selected_category != "All Categories" else None,
                selected_jurisdiction,
                include_web_search
            )
        else:
            st.warning("Please enter a legal question.")
    
    # Display chat history
    _display_legal_chat_history()

def _process_legal_question(question, category, jurisdiction, include_web_search):
    """Process a legal question and display the response"""
    if 'legal_chatbot' not in st.session_state:
        st.error("Legal chatbot not available. Please check system status.")
        return
    
    try:
        # Create loading state
        update_loading, complete_loading = create_loading_state("Analyzing your legal question...")
        
        # Ensure session is active
        if not st.session_state.get('current_legal_session'):
            session_id = st.session_state['legal_chatbot'].start_new_session()
            st.session_state['current_legal_session'] = session_id
        
        # Process the question
        update_loading(message="Searching legal documents...")
        response = st.session_state['legal_chatbot'].ask_legal_question(
            question=question,
            document_type=category,
            jurisdiction=jurisdiction,
            include_web_search=include_web_search
        )
        
        complete_loading(success=response.get('success', False))
        
        if response.get('success'):
            # Update query count
            st.session_state['legal_query_count'] += 1
            
            # Add to chat messages for display
            if 'legal_chat_messages' not in st.session_state:
                st.session_state['legal_chat_messages'] = []
            
            st.session_state['legal_chat_messages'].append({
                'type': 'user',
                'content': question,
                'timestamp': datetime.now().isoformat(),
                'category': category,
                'jurisdiction': jurisdiction
            })
            
            st.session_state['legal_chat_messages'].append({
                'type': 'assistant',
                'content': response['response'],
                'timestamp': datetime.now().isoformat(),
                'citations': response.get('citations', []),
                'web_sources': response.get('web_sources', []),
                'documents_consulted': response.get('documents_consulted', 0)
            })
            
            st.rerun()
        else:
            st.error(f"Error processing legal question: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        complete_loading(success=False, message=f"Error: {str(e)}")
        st.error(f"Error processing legal question: {e}")

def _display_legal_chat_history():
    """Display the legal chat history"""
    if st.session_state.get('legal_chat_messages'):
        st.markdown("### 📝 Conversation History")
        
        for message in st.session_state['legal_chat_messages']:
            if message['type'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {message['content']}<br>
                    <small>Category: {message.get('category', 'General')} | Jurisdiction: {message.get('jurisdiction', 'Saudi Arabia')}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Fix: Extract the content replacement outside the f-string
                formatted_content = message['content'].replace('\n', '<br>')
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>Legal Assistant:</strong><br>
                    {formatted_content}
                </div>
                """, unsafe_allow_html=True)
                
                # Show citations if available
                if message.get('citations'):
                    with st.expander(f"📚 Citations ({len(message['citations'])})"):
                        for i, citation in enumerate(message['citations'], 1):
                            st.markdown(f"""
                            <div class="legal-citation">
                                <strong>{i}. {citation.get('title', 'Legal Document')}</strong><br>
                                Type: {citation.get('document_type', 'Unknown')}<br>
                                Jurisdiction: {citation.get('jurisdiction', 'Unknown')}<br>
                                Source: {citation.get('source', 'Unknown')}
                            </div>
                            """, unsafe_allow_html=True)
                
                # Show web sources if available
                if message.get('web_sources'):
                    with st.expander(f"🌐 Web Sources ({len(message['web_sources'])})"):
                        for source in message['web_sources']:
                            st.markdown(f"**{source.get('title', 'Web Source')}**")
                            st.markdown(f"URL: {source.get('url', 'N/A')}")
                            st.markdown(f"Summary: {source.get('summary', 'N/A')}")
                            st.markdown("---")


def _display_additional_legal_tools():
    """Display additional legal tools"""
    st.markdown("### 🛠️ Additional Legal Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Legal Precedent Search"):
            st.session_state['show_precedent_search'] = True
            st.rerun()
    
    with col2:
        if st.button("📋 Compliance Requirements"):
            st.session_state['show_compliance_tool'] = True
            st.rerun()
    
    with col3:
        if st.button("📊 Session Analytics"):
            st.session_state['show_session_report'] = True
            st.rerun()
    
    # Display tools if requested
    _display_legal_tools_content()

def _display_legal_tools_content():
    """Display content for additional legal tools"""
    
    # Legal Precedent Search
    if st.session_state.get('show_precedent_search'):
        with st.expander("🔍 Legal Precedent Search", expanded=True):
            case_type = st.text_input("Case Type:", placeholder="e.g., Commercial dispute")
            jurisdiction = st.selectbox("Jurisdiction:", ["Saudi Arabia", "GCC", "International"])
            
            if st.button("Search Precedents") and case_type:
                if 'legal_search_engine' in st.session_state:
                    try:
                        precedents = st.session_state['legal_search_engine'].search_legal_precedents(
                            case_type, jurisdiction
                        )
                        if precedents:
                            for precedent in precedents:
                                st.markdown(f"**{precedent.get('case_title', 'Legal Case')}**")
                                st.markdown(f"Summary: {precedent.get('summary', 'N/A')}")
                                st.markdown("---")
                        else:
                            st.info("No precedents found for this case type.")
                    except Exception as e:
                        st.error(f"Error searching precedents: {e}")
            
            if st.button("Close Precedent Search"):
                st.session_state['show_precedent_search'] = False
                st.rerun()
    
    # Compliance Requirements Tool
    if st.session_state.get('show_compliance_tool'):
        with st.expander("📋 Compliance Requirements Tool", expanded=True):
            business_type = st.text_input("Business Type:", placeholder="e.g., Technology company")
            jurisdiction = st.selectbox("Jurisdiction:", ["Saudi Arabia", "UAE", "Qatar"])
            
            if st.button("Get Compliance Requirements") and business_type:
                if 'legal_search_engine' in st.session_state:
                    try:
                        requirements = st.session_state['legal_search_engine'].search_compliance_requirements(
                            business_type, jurisdiction
                        )
                        
                        if requirements.get('requirements'):
                            st.markdown("**Legal Requirements:**")
                            for req in requirements['requirements']:
                                st.markdown(f"• {req}")
                        
                        if requirements.get('licenses_needed'):
                            st.markdown("**Licenses Needed:**")
                            for license in requirements['licenses_needed']:
                                st.markdown(f"• {license}")
                        
                        if requirements.get('regulatory_bodies'):
                            st.markdown("**Regulatory Bodies:**")
                            for body in requirements['regulatory_bodies']:
                                st.markdown(f"• {body}")
                    except Exception as e:
                        st.error(f"Error getting compliance requirements: {e}")
            
            if st.button("Close Compliance Tool"):
                st.session_state['show_compliance_tool'] = False
                st.rerun()
    
    # Session Report
    if st.session_state.get('show_session_report'):
        with st.expander("📊 Session Analytics", expanded=True):
            if 'legal_chatbot' in st.session_state:
                try:
                    session_summary = st.session_state['legal_chatbot'].get_session_summary()
                    
                    if 'error' not in session_summary:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Session Duration", f"{session_summary.get('duration_minutes', 0):.1f} min")
                            st.metric("Questions Asked", session_summary.get('queries_count', 0))
                        
                        with col2:
                            st.metric("Document Types", len(session_summary.get('document_types_consulted', [])))
                            st.metric("Jurisdictions", len(session_summary.get('jurisdictions_consulted', [])))
                        
                        if session_summary.get('document_types_consulted'):
                            st.markdown("**Document Types Consulted:**")
                            st.markdown(", ".join(session_summary['document_types_consulted']))
                        
                        if session_summary.get('jurisdictions_consulted'):
                            st.markdown("**Jurisdictions Consulted:**")
                            st.markdown(", ".join(session_summary['jurisdictions_consulted']))
                    else:
                        st.info("No active session to analyze.")
                except Exception as e:
                    st.error(f"Error getting session analytics: {e}")
            
            if st.button("Close Session Analytics"):
                st.session_state['show_session_report'] = False
                st.rerun()

# Clear chat history button
def _display_chat_controls():
    """Display chat control buttons"""
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Chat History"):
            st.session_state['legal_chat_messages'] = []
            st.success("Chat history cleared!")
            st.rerun()
    
    with col2:
        if st.button("📥 Download Chat History"):
            if st.session_state.get('legal_chat_messages'):
                chat_data = {
                    'session_id': st.session_state.get('current_legal_session', 'unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'messages': st.session_state['legal_chat_messages']
                }
                
                import json
                json_str = json.dumps(chat_data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"legal_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.warning("No chat history to download.")
def legal_compliance_interface():

    """Enhanced Legal compliance chatbot interface with FIXED RAG diagnostics"""
    st.markdown('<h2 class="sub-header">Legal Compliance Assistant</h2>', unsafe_allow_html=True)
    
    # Check if legal system is available
    if not st.session_state['legal_system_available']:
        _display_legal_system_unavailable()
        return
    
    # Display enhanced system status
    _display_legal_system_status()
    
    # Display system metrics
    _display_legal_system_metrics()
    
    # System diagnostics expander
    _display_legal_diagnostics_panel()
    
    # Display legal disclaimer
    _display_legal_disclaimer()
    
    # Session management
    _display_legal_session_management()
    
    # Main legal chat interface
    _display_legal_chat_interface()
    
    # Additional legal tools
    _display_additional_legal_tools()

def _display_legal_system_unavailable():
    """Display UI when legal system is not available"""
    st.error("⚠️ Legal compliance system is not available. Please contact support.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Try to Initialize Legal System"):
            initialize_legal_compliance()
            st.rerun()
    with col2:
        if st.button("Run Legal System Diagnostics"):
            st.session_state['show_legal_diagnostics'] = True
            st.rerun()
    
    # Show diagnostics if requested
    if st.session_state.get('show_legal_diagnostics', False):
        st.markdown("### Legal System Diagnostics")
        try:
            from dependency_container import container
            if FIXED_LEGAL_AVAILABLE:
                diagnostics = get_legal_system_diagnostics(container)
                
                st.markdown(f"**Overall Status:** {diagnostics['overall_status']}")
                
                for component, status in diagnostics['components'].items():
                    if status.get('available'):
                        component_type = status.get('type', 'unknown')
                        if component_type == 'real':
                            st.success(f"✅ {component}: Fully operational")
                        elif component_type == 'enhanced':
                            st.success(f"✅ {component}: Enhanced version")
                        elif component_type == 'limited':
                            st.warning(f"⚠️ {component}: Limited functionality")
                        else:
                            st.info(f"ℹ️ {component}: {component_type}")
                    else:
                        st.error(f"❌ {component}: {status.get('error', 'Unavailable')}")
                
                if diagnostics.get('recommendations'):
                    st.markdown("**Recommendations:**")
                    for rec in diagnostics['recommendations']:
                        st.markdown(f"• {rec}")
            else:
                st.warning("FIXED legal diagnostics not available")
            
            if st.button("Hide Diagnostics"):
                st.session_state['show_legal_diagnostics'] = False
                st.rerun()
        except Exception as e:
            st.error(f"Could not run diagnostics: {e}")

def _display_legal_system_status():
    """Display enhanced legal system status"""
    system_type = st.session_state.get('legal_system_type', 'unknown')
    
    if system_type == 'full_rag':
        st.markdown("""
        <div class="system-status-full-rag">
            🟢 <strong>Full Legal RAG System Active</strong> - Connected to Weaviate legal database with AI-powered analysis
        </div>
        """, unsafe_allow_html=True)
    elif system_type == 'limited':
        st.markdown("""
        <div class="system-status-limited">
            🟡 <strong>Limited Legal System</strong> - Basic functionality available, no database connection
        </div>
        """, unsafe_allow_html=True)
    elif system_type == 'basic':
        st.markdown("""
        <div class="system-status-basic">
            🔵 <strong>Basic Legal System</strong> - Using fallback responses for demonstration
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚪ **Legal System Status Unknown**")

def _display_legal_system_metrics():
    """Display legal system metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        system_type = st.session_state.get('legal_system_type', 'unknown')
        if system_type == 'full_rag':
            system_status = "🟢 Full RAG"
        elif system_type == 'limited':
            system_status = "🟡 Limited"
        elif system_type == 'basic':
            system_status = "🔵 Basic"
        else:
            system_status = "⚪ Unknown"
        st.metric("System Type", system_status)
    
    with col2:
        st.metric("Queries Today", st.session_state['legal_query_count'])
    
    with col3:
        legal_session_active = st.session_state['current_legal_session'] is not None
        st.metric("Session", "Active" if legal_session_active else "None")
    
    with col4:
        doc_count = st.session_state.get('legal_document_count', 0)
        if doc_count > 0:
            st.metric("Legal Documents", f"{doc_count:,}")

# =============================================================================
# MAIN APPLICATION INTERFACE - Add this to the end of your app.py file
# =============================================================================

def main():
    """Main application interface"""
    
    # Initialize the application
    if not initialize_application():
        st.error("⚠️ Application initialization failed. Some features may not be available.")
    
    # Display main header
    st.markdown('<h1 class="main-header">📊 LinkSaudi Market Intelligence Platform</h1>', unsafe_allow_html=True)
    
    # Display system status
    display_status_indicator()
    
    # Create sidebar navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        # Navigation options
        nav_options = [
            "🏠 Dashboard",
            "📊 Market Reports", 
            "💬 Report Chat",
            "⚖️ Legal Compliance",
            "🔧 System Status",
            "📚 Help & Documentation"
        ]
        
        selected_page = st.selectbox("Choose a section:", nav_options, key="main_navigation")
        
        # System controls
        st.markdown("### ⚙️ System Controls")
        
        # Offline mode toggle
        offline_mode = st.checkbox(
            "Offline Mode", 
            value=st.session_state.get('offline_mode', False),
            help="Work with cached data only"
        )
        
        if offline_mode != st.session_state.get('offline_mode', False):
            st.session_state['offline_mode'] = offline_mode
            st.rerun()
        
        # System refresh
        if st.button("🔄 Refresh System"):
            st.session_state['initialized'] = False
            st.rerun()
        
        # Quick system info
        st.markdown("### 📈 Quick Stats")
        st.metric("System Status", st.session_state.get('system_status', 'Unknown'))
        st.metric("Reports Generated", len(st.session_state.get('reports', [])))
        st.metric("Legal Queries", st.session_state.get('legal_query_count', 0))
    
    # Main content area based on navigation
    if selected_page == "🏠 Dashboard":
        dashboard_interface()
    
    elif selected_page == "📊 Market Reports":
        market_reports_interface()
    
    elif selected_page == "💬 Report Chat":
        report_chat_interface()
    
    elif selected_page == "⚖️ Legal Compliance":
        legal_compliance_interface()
    
    elif selected_page == "🔧 System Status":
        system_status_interface()
    
    elif selected_page == "📚 Help & Documentation":
        help_documentation_interface()

def dashboard_interface():
    """Dashboard overview interface"""
    st.markdown('<h2 class="sub-header">🏠 Dashboard Overview</h2>', unsafe_allow_html=True)
    
    # Welcome message
    st.markdown("""
    <div class="section-card">
        <h3>Welcome to LinkSaudi Market Intelligence Platform</h3>
        <p>Your comprehensive solution for market research, legal compliance, and business intelligence in Saudi Arabia and the GCC region.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # System overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "System Status", 
            st.session_state.get('system_status', 'Unknown').title(),
            delta="Online" if st.session_state.get('system_status') == 'online' else None
        )
    
    with col2:
        st.metric("Market Reports", len(st.session_state.get('reports', [])))
    
    with col3:
        st.metric("Legal Queries", st.session_state.get('legal_query_count', 0))
    
    with col4:
        legal_system_available = st.session_state.get('legal_system_available', False)
        st.metric("Legal System", "Active" if legal_system_available else "Inactive")
    
    # Feature overview
    st.markdown("### 🚀 Available Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="section-card">
            <h4>📊 Market Intelligence</h4>
            <ul>
                <li>AI-powered market research reports</li>
                <li>Real-time web data integration</li>
                <li>Interactive report generation</li>
                <li>PDF export capabilities</li>
                <li>Conversational report analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        legal_status = st.session_state.get('legal_system_type', 'unavailable')
        legal_description = {
            'full_rag': 'Full RAG system with legal database',
            'limited': 'Limited functionality without database',
            'basic': 'Basic responses for demonstration',
            'unavailable': 'System not available'
        }.get(legal_status, 'Unknown status')
        
        st.markdown(f"""
        <div class="section-card">
            <h4>⚖️ Legal Compliance</h4>
            <ul>
                <li>Saudi Arabian legal guidance</li>
                <li>Regulatory compliance checking</li>
                <li>Legal document analysis</li>
                <li>Precedent research</li>
                <li>Consultation session management</li>
            </ul>
            <p><strong>Status:</strong> {legal_description}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Generate New Report", type="primary"):
            st.session_state['main_navigation'] = "📊 Market Reports"
            st.rerun()
    
    with col2:
        if st.button("⚖️ Ask Legal Question", type="primary"):
            st.session_state['main_navigation'] = "⚖️ Legal Compliance" 
            st.rerun()
    
    with col3:
        if st.button("🔧 System Diagnostics"):
            st.session_state['main_navigation'] = "🔧 System Status"
            st.rerun()

def market_reports_interface():
    """Market reports generation interface"""
    st.markdown('<h2 class="sub-header">📊 Market Intelligence Reports</h2>', unsafe_allow_html=True)
    
    # Check if market report system is available
    if not CORE_IMPORTS_AVAILABLE:
        st.error("⚠️ Market report system is not fully available. Please check system dependencies.")
        return
    
    # Report generation form
    with st.form("report_generation_form"):
        st.markdown("### 📝 Generate New Market Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_title = st.text_input(
                "Report Title*",
                placeholder="e.g., Saudi Arabia Technology Market Analysis 2024"
            )
            
            sectors = st.multiselect(
                "Industry Sectors*",
                ["Technology", "Healthcare", "Finance", "Energy", "Real Estate", 
                 "Manufacturing", "Retail", "Tourism", "Agriculture", "Construction"],
                default=["Technology"]
            )
        
        with col2:
            geography = st.selectbox(
                "Geographic Focus*",
                ["Saudi Arabia", "GCC", "MENA", "Global"]
            )
            
            report_options = st.multiselect(
                "Report Features",
                ["Web Research Enhancement", "Visual Charts", "Executive Summary", "Competitive Analysis"],
                default=["Web Research Enhancement", "Visual Charts"]
            )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            include_visuals = "Visual Charts" in report_options
            enhance_with_web = "Web Research Enhancement" in report_options
            
            custom_focus = st.text_area(
                "Custom Research Focus (Optional)",
                placeholder="e.g., Focus on startup ecosystem, regulatory changes, market size..."
            )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Generate Report", type="primary")
        
        if submitted:
            if report_title and sectors:
                generate_market_report(report_title, sectors, geography, enhance_with_web, include_visuals, custom_focus)
            else:
                st.error("Please fill in required fields (Title and Sectors)")
    
    # Display existing reports
    st.markdown("### 📚 Generated Reports")
    
    if st.session_state.get('reports'):
        for i, report in enumerate(st.session_state['reports']):
            with st.expander(f"📄 {report.get('title', f'Report {i+1}')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Date:** {report.get('date', 'Unknown')}")
                    st.markdown(f"**Sectors:** {', '.join(report.get('sectors', []))}")
                
                with col2:
                    st.markdown(f"**Geography:** {report.get('geography', 'Unknown')}")
                    st.markdown(f"**Sections:** {len(report.get('sections', []))}")
                
                with col3:
                    if st.button(f"📖 View Report {i+1}"):
                        st.session_state['current_report'] = report
                        st.session_state['main_navigation'] = "💬 Report Chat"
                        st.rerun()
    else:
        st.info("No reports generated yet. Create your first report using the form above!")

def generate_market_report(title, sectors, geography, enhance_with_web, include_visuals, custom_focus):
    """Generate a market report"""
    try:
        # Create loading state
        update_loading, complete_loading = create_loading_state("Generating your market report...")
        
        # Try to use the market report system
        from dependency_container import container
        
        if container.has('market_report_system'):
            market_report_system = container.get('market_report_system')
            
            update_loading(progress=0.3, message="Researching market data...")
            
            result = market_report_system.create_market_report(
                title=title,
                sectors=sectors,
                geography=geography,
                enhance_with_web=enhance_with_web,
                include_visuals=include_visuals,
                custom_focus=custom_focus
            )
            
            if result and result.get('report_data'):
                update_loading(progress=0.8, message="Finalizing report...")
                
                # Add to session state
                st.session_state['reports'].append(result['report_data'])
                st.session_state['current_report'] = result['report_data']
                
                complete_loading(success=True, message="Report generated successfully!")
                
                # Show success message with next steps
                st.success("✅ Report generated successfully!")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📖 View Report"):
                        st.session_state['main_navigation'] = "💬 Report Chat"
                        st.rerun()
                
                with col2:
                    if result.get('pdf_file'):
                        st.download_button(
                            "📥 Download PDF",
                            data=open(result['pdf_file'], 'rb').read(),
                            file_name=f"{title.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
            else:
                complete_loading(success=False, message="Report generation failed")
                st.error("Failed to generate report. Please try again.")
        else:
            complete_loading(success=False, message="Market report system not available")
            st.error("Market report system is not available. Please check system status.")
            
    except Exception as e:
        complete_loading(success=False, message=f"Error: {str(e)}")
        st.error(f"Error generating report: {str(e)}")

def report_chat_interface():
    """Report chat and analysis interface"""
    st.markdown('<h2 class="sub-header">💬 Report Analysis & Chat</h2>', unsafe_allow_html=True)
    
    # Check if we have a current report
    if not st.session_state.get('current_report'):
        st.info("No report selected. Please generate or select a report first.")
        
        if st.session_state.get('reports'):
            st.markdown("### 📚 Available Reports")
            for i, report in enumerate(st.session_state['reports']):
                if st.button(f"📄 Select: {report.get('title', f'Report {i+1}')}"):
                    st.session_state['current_report'] = report
                    st.rerun()
        else:
            st.markdown("### 🚀 Get Started")
            if st.button("📊 Generate Your First Report"):
                st.session_state['main_navigation'] = "📊 Market Reports"
                st.rerun()
        return
    
    # Display current report info
    report = st.session_state['current_report']
    st.markdown(f"""
    <div class="section-card">
        <h3>📄 Current Report: {report.get('title', 'Untitled Report')}</h3>
        <p><strong>Sectors:</strong> {', '.join(report.get('sectors', []))}</p>
        <p><strong>Geography:</strong> {report.get('geography', 'Unknown')}</p>
        <p><strong>Generated:</strong> {report.get('date', 'Unknown')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat interface
    st.markdown("### 💬 Ask Questions About This Report")
    
    # Chat input
    user_question = st.text_input(
        "Ask a question about the report:", 
        placeholder="e.g., What are the key market trends? Who are the main competitors?"
    )
    
    if st.button("🔍 Ask Question") and user_question:
        process_report_question(user_question, report)
    
    # Display chat history
    if st.session_state.get('chat_messages'):
        st.markdown("### 📝 Conversation History")
        
        for message in st.session_state['chat_messages']:
            if message['type'] == 'user':
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>Assistant:</strong> {message['content']}
                </div>
                """, unsafe_allow_html=True)
    
    # Report actions
    st.markdown("### 🛠️ Report Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View Full Report"):
            display_full_report(report)
    
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state['chat_messages'] = []
            st.rerun()
    
    with col3:
        if st.button("📥 Export Report"):
            st.download_button(
                "Download JSON",
                data=json.dumps(report, indent=2),
                file_name=f"{report.get('title', 'report').replace(' ', '_')}.json",
                mime="application/json"
            )

def process_report_question(question, report):
    """Process a question about the report"""
    try:
        # Create loading state
        update_loading, complete_loading = create_loading_state("Analyzing your question...")
        
        # Try to use report conversation system
        from dependency_container import container
        
        if container.has('report_conversation'):
            report_conversation = container.get('report_conversation')
            response = report_conversation.ask_question(question)
            
            complete_loading(success=True)
            
            # Add to chat history
            if 'chat_messages' not in st.session_state:
                st.session_state['chat_messages'] = []
            
            st.session_state['chat_messages'].append({
                'type': 'user', 
                'content': question,
                'timestamp': datetime.now().isoformat()
            })
            
            st.session_state['chat_messages'].append({
                'type': 'assistant', 
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            
            st.rerun()
        else:
            complete_loading(success=False, message="Report conversation system not available")
            st.error("Report conversation system is not available.")
            
    except Exception as e:
        complete_loading(success=False, message=f"Error: {str(e)}")
        st.error(f"Error processing question: {str(e)}")

def display_full_report(report):
    """Display the full report"""
    st.markdown("### 📄 Full Report View")
    
    # Report header
    st.markdown(f"""
    <div class="report-header">
        <h2>{report.get('title', 'Market Report')}</h2>
        <p>Generated on {report.get('date', 'Unknown Date')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Report sections
    for section in report.get('sections', []):
        # Fix: Extract the content replacement outside the f-string
        section_content = section.get('content', 'No content available').replace('\n', '<br>')
        st.markdown(f"""
        <div class="report-section">
            <h3 class="report-section-title">{section.get('title', 'Section')}</h3>
            <div style="padding: 1rem;">
                {section_content}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display subsections if available
        for subsection in section.get('subsections', []):
            st.markdown(f"**{subsection.get('title', 'Subsection')}**")
            st.markdown(subsection.get('content', 'No content available'))
def system_status_interface():
    """System status and diagnostics interface"""
    st.markdown('<h2 class="sub-header">🔧 System Status & Diagnostics</h2>', unsafe_allow_html=True)
    
    # Overall system status
    st.markdown("### 📊 System Overview")
    
    if CORE_IMPORTS_AVAILABLE:
        try:
            system_overview = get_system_overview()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("System State", system_overview.get('system_state', 'Unknown').title())
            
            with col2:
                st.metric("Components Available", 
                         f"{system_overview.get('available_components', 0)}/{system_overview.get('total_components', 0)}")
            
            with col3:
                st.metric("Initialization", "Complete" if system_overview.get('initialized') else "Incomplete")
            
            with col4:
                legal_status = system_overview.get('legal_system', {}).get('status', 'unknown')
                st.metric("Legal System", legal_status.title())
            
            # Component status details
            st.markdown("### 🔍 Component Status")
            
            for component, status in system_overview.get('component_status', {}).items():
                if status.get('available'):
                    st.success(f"✅ **{component}**: {status.get('description', 'Available')}")
                else:
                    st.error(f"❌ **{component}**: {status.get('description', 'Unavailable')}")
            
            # Legal system details
            legal_system = system_overview.get('legal_system', {})
            if legal_system.get('components'):
                st.markdown("### ⚖️ Legal System Details")
                
                for comp_name, comp_status in legal_system['components'].items():
                    if comp_status.get('available'):
                        comp_type = comp_status.get('type', 'unknown')
                        if comp_type == 'real':
                            st.success(f"✅ **{comp_name}**: Fully operational")
                        elif comp_type == 'enhanced':
                            st.success(f"✅ **{comp_name}**: Enhanced version")
                        elif comp_type == 'limited':
                            st.warning(f"⚠️ **{comp_name}**: Limited functionality")
                        else:
                            st.info(f"ℹ️ **{comp_name}**: {comp_type}")
                    else:
                        st.error(f"❌ **{comp_name}**: {comp_status.get('error', 'Unavailable')}")
        
        except Exception as e:
            st.error(f"Error getting system overview: {e}")
    else:
        st.warning("Core system imports not available. Limited status information.")
    
    # System controls
    st.markdown("### ⚙️ System Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reinitialize System"):
            st.session_state['initialized'] = False
            initialize_application()
            st.success("System reinitialized!")
            st.rerun()
    
    with col2:
        if st.button("🧹 Clear All Cache"):
            # Clear various caches
            st.session_state['chat_messages'] = []
            st.session_state['legal_chat_messages'] = []
            st.success("Cache cleared!")
    
    with col3:
        if st.button("📊 Export Diagnostics"):
            if CORE_IMPORTS_AVAILABLE:
                diagnostics = get_system_overview()
                st.download_button(
                    "Download Diagnostics",
                    data=json.dumps(diagnostics, indent=2),
                    file_name=f"system_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.error("Diagnostics export not available")

def help_documentation_interface():
    """Help and documentation interface"""
    st.markdown('<h2 class="sub-header">📚 Help & Documentation</h2>', unsafe_allow_html=True)
    
    # User guide
    st.markdown("""
    ### 🚀 Getting Started
    
    Welcome to the LinkSaudi Market Intelligence Platform! This comprehensive tool provides:
    
    #### 📊 Market Intelligence Features:
    - **AI-Powered Reports**: Generate detailed market analysis reports
    - **Web Research Integration**: Real-time data from web sources
    - **Interactive Analysis**: Chat with your reports to get specific insights
    - **Export Capabilities**: Download reports in PDF and JSON formats
    
    #### ⚖️ Legal Compliance Features:
    - **Saudi Arabian Law Guidance**: Get legal guidance based on local regulations
    - **Document Analysis**: Search through legal document databases
    - **Compliance Checking**: Verify regulatory requirements
    - **Session Management**: Track and export legal consultation sessions
    
    ### 🔧 System Requirements
    
    For full functionality, ensure you have:
    - OpenAI API key configured
    - Weaviate database connection (for advanced features)
    - All Python dependencies installed
    
    ### 💡 Tips for Best Results
    
    1. **Market Reports**: Be specific about sectors and geographic focus
    2. **Legal Questions**: Include jurisdiction and business context
    3. **System Performance**: Use offline mode if experiencing connectivity issues
    
    ### 🆘 Troubleshooting
    
    If you encounter issues:
    1. Check the System Status page for component availability
    2. Try refreshing the system using the sidebar controls
    3. Enable offline mode for basic functionality
    4. Contact support if problems persist
    """)
    
    # FAQ section
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **Q: Why isn't the legal system working?**
        A: Check if Weaviate is running and legal documents are loaded. The system can work in limited mode without these.
        
        **Q: How do I improve report quality?**
        A: Enable web research enhancement and provide specific industry focus in your queries.
        
        **Q: Can I export my data?**
        A: Yes! Use the export buttons in each section to download reports, chat history, and diagnostics.
        
        **Q: What does "offline mode" do?**
        A: Offline mode uses cached data only and disables web-based features for better performance.
        """)
    
    # Contact information
    st.markdown("""
    ### 📞 Support
    
    For technical support or questions:
    - Check the System Status page for diagnostics
    - Review the troubleshooting steps above
    - Export system diagnostics for detailed error information
    """)

# =============================================================================
# RUN THE APPLICATION
# =============================================================================

if __name__ == "__main__":
    main()