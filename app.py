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