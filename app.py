#!/usr/bin/env python3
# improved_app_refactored.py - Refactored Streamlit application using the new architecture

# First, set page configuration before ANY other Streamlit imports or commands
import streamlit as st

st.set_page_config(
    page_title="LinkSaudi Market Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import everything else
import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import re

# Import our centralized utilities and initializer
try:
    from dependency_container import container
    from system_initializer import initialize_system
    from error_handling import format_error_for_display
    CORE_IMPORTS_AVAILABLE = True
except ImportError as e:
    CORE_IMPORTS_AVAILABLE = False
    print(f"Core imports failed: {e}")

# Import market intelligence components
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

# Import legal compliance components
try:
    from legal_compliance import LegalRAGEngine, LegalChatbot, LegalSearchEngine
    LEGAL_COMPLIANCE_AVAILABLE = True
    print("Legal compliance components imported successfully")
except ImportError as e:
    LEGAL_COMPLIANCE_AVAILABLE = False
    print(f"Legal compliance components not available: {e}")

# Custom CSS for improved UI with dark theme (same as before)
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
    
    .section-card {
        background: linear-gradient(135deg, var(--dark-card-bg) 0%, #2D2D2D 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid var(--dark-border);
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state['initialized'] = False
    st.session_state['offline_mode'] = False
    st.session_state['history'] = []
    st.session_state['reports'] = []
    st.session_state['current_report'] = None
    st.session_state['system_status'] = 'unknown'
    st.session_state['temp_files'] = []
    st.session_state['connection_status'] = 'unknown'
    st.session_state['chat_messages'] = []
    st.session_state['prompt_count'] = 0
    st.session_state['report_ready'] = False
    
    # Legal compliance session state
    st.session_state['legal_system_available'] = False
    st.session_state['legal_chat_messages'] = []
    st.session_state['current_legal_session'] = None
    st.session_state['legal_query_count'] = 0
    st.session_state['show_legal_history'] = False
    st.session_state['show_precedent_search'] = False
    st.session_state['show_compliance_tool'] = False
    st.session_state['show_session_report'] = False
    st.session_state['current_session_report'] = None

def initialize_application():
    """Initialize the application with proper error handling"""
    try:
        # Create necessary directories
        os.makedirs("report_charts", exist_ok=True)
        os.makedirs("market_reports", exist_ok=True)
        os.makedirs("legal_conversations", exist_ok=True)
        os.makedirs("legal_cache", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Create config file directory
        config_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(config_dir, exist_ok=True)
        
        # Check if config file exists, create it if it doesn't
        config_file = os.path.join(config_dir, "config.json")
        if not os.path.exists(config_file):
            default_config = {
                "api_keys": {
                    "openai": "",
                    "weaviate": {
                        "url": "",
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
                }
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
                logger.info(f"Created default config file at {config_file}")
        
        # Check if we're already initialized
        if st.session_state['initialized']:
            logger.info("Application already initialized")
            return True
        
        # Try to import core modules first
        try:
            from market_reports.utils import logger, config_manager, system_state
            from dependency_container import container
            from system_initializer import initialize_system
            
            CORE_IMPORTS_AVAILABLE = True
            logger.info("Using refactored architecture")
            
            # Initialize using new system
            success = initialize_system(offline_mode=st.session_state['offline_mode'])
            
            if success:
                logger.info("System initialized successfully with new architecture")
                st.session_state['initialized'] = True
                st.session_state['system_status'] = system_state.current_state
                st.session_state['connection_status'] = system_state.current_state
                
                # Load any existing reports
                if container.has('market_report_system'):
                    market_report_system = container.get('market_report_system')
                    st.session_state['reports'] = market_report_system.list_reports()
                
                # Initialize legal compliance
                initialize_legal_compliance()
                
                return True
        except ImportError as e:
            logger.info(f"Refactored architecture not available: {e}")
            logger.info("Falling back to original initialization")
            CORE_IMPORTS_AVAILABLE = False
        
        # If we get here, the refactored architecture is not available
        # Try to initialize using the original approach
        try:
            # Check if we're in offline mode
            if st.session_state['offline_mode']:
                logger.info("Working in offline mode. Some features may be limited.")
                st.session_state['connection_status'] = 'offline'
                st.session_state['system_status'] = 'offline'
                st.session_state['initialized'] = True
                return True
                
            # Legacy initialization code here (same as original)
            # ... (rest of legacy initialization)
            
            return True
            
        except Exception as e:
            logger.error(f"Critical error during legacy initialization: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            
            # Set system to offline mode due to initialization failure
            st.session_state['system_status'] = 'offline'
            st.session_state['connection_status'] = 'offline'
            st.session_state['offline_mode'] = True
            st.session_state['initialized'] = True  # Set to True so we don't keep trying
            return False
    
    except Exception as e:
        logger.error(f"Critical error initializing application: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        
        st.session_state['system_status'] = 'offline'
        st.session_state['connection_status'] = 'offline'
        st.session_state['offline_mode'] = True
        st.session_state['initialized'] = True  # Set to True so we don't keep trying
        return False

def initialize_legal_compliance():
    """Initialize legal compliance components"""
    try:
        if not LEGAL_COMPLIANCE_AVAILABLE:
            st.session_state['legal_system_available'] = False
            return False
        
        # Get dependencies from container
        from dependency_container import container
        
        # Check if legal components are available in container
        if container.has('legal_rag_engine') and container.has('legal_chatbot'):
            st.session_state['legal_rag_engine'] = container.get('legal_rag_engine')
            st.session_state['legal_chatbot'] = container.get('legal_chatbot')
            st.session_state['legal_search_engine'] = container.get('legal_search_engine')
            st.session_state['legal_system_available'] = True
            logger.info("Legal compliance system initialized successfully")
            return True
        else:
            st.session_state['legal_system_available'] = False
            logger.warning("Legal compliance components not found in container")
            return False
    
    except Exception as e:
        logger.error(f"Error initializing legal compliance: {e}")
        st.session_state['legal_system_available'] = False
        return False

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
    error_data = format_error_for_display(error, user_message)
    
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

def legal_compliance_interface():
    """Legal compliance chatbot interface"""
    st.markdown('<h2 class="sub-header">Legal Compliance Assistant</h2>', unsafe_allow_html=True)
    
    # Check if legal system is available
    if not st.session_state['legal_system_available']:
        st.error("⚠️ Legal compliance system is not available. Please contact support.")
        if st.button("Try to Initialize Legal System"):
            initialize_legal_compliance()
            st.rerun()
        return
    
    # Display legal disclaimer
    with st.expander("⚖️ Legal Disclaimer - Please Read", expanded=False):
        st.markdown("""
        <div class="legal-disclaimer">
        <strong>Important Legal Disclaimer:</strong><br><br>
        
        This Legal Compliance Assistant provides general legal information based on available legal documents 
        and should not replace professional legal advice. The information provided:<br><br>
        
        • Is for general guidance only<br>
        • May not reflect the most recent legal changes<br>
        • Should not be considered as legal advice<br>
        • May not apply to your specific situation<br><br>
        
        <strong>For specific legal matters, always consult with a qualified attorney licensed to practice 
        in the relevant jurisdiction.</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Legal system status
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("System Status", "🟢 Online" if st.session_state['legal_system_available'] else "🔴 Offline")
    with col2:
        st.metric("Queries Today", st.session_state['legal_query_count'])
    with col3:
        legal_session_active = st.session_state['current_legal_session'] is not None
        st.metric("Session", "Active" if legal_session_active else "None")
    
    # Session management
    st.markdown("### Session Management")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Start New Legal Session", use_container_width=True):
            if 'legal_chatbot' in st.session_state and st.session_state['legal_chatbot']:
                session_id = st.session_state['legal_chatbot'].start_new_session()
                st.session_state['current_legal_session'] = session_id
                st.session_state['legal_chat_messages'] = []
                st.success(f"New legal session started: {session_id[:8]}...")
                st.rerun()
    
    with col2:
        if st.button("End Current Session", use_container_width=True):
            if st.session_state['current_legal_session'] and 'legal_chatbot' in st.session_state:
                summary = st.session_state['legal_chatbot'].end_session()
                st.session_state['current_legal_session'] = None
                st.info(f"Session ended. Queries processed: {summary.get('queries_count', 0)}")
                st.rerun()
    
    with col3:
        if st.button("View Session History", use_container_width=True):
            if 'legal_chatbot' in st.session_state and st.session_state['legal_chatbot']:
                sessions = st.session_state['legal_chatbot'].list_previous_sessions()
                if sessions:
                    st.session_state['show_legal_history'] = True
                else:
                    st.info("No previous sessions found.")
    
    # Display session history if requested
    if st.session_state.get('show_legal_history', False):
        st.markdown("### Previous Legal Sessions")
        sessions = st.session_state['legal_chatbot'].list_previous_sessions()
        
        for session in sessions[:5]:  # Show last 5 sessions
            with st.expander(f"Session {session['session_id'][:8]} - {session['start_time'][:10]}"):
                st.write(f"**Queries:** {session['queries_count']}")
                st.write(f"**Status:** {session['end_time']}")
                if st.button(f"Load Session", key=f"load_{session['session_id']}"):
                    if st.session_state['legal_chatbot'].load_session(session['session_id']):
                        st.session_state['current_legal_session'] = session['session_id']
                        st.success("Session loaded successfully!")
                        st.rerun()
        
        if st.button("Hide History"):
            st.session_state['show_legal_history'] = False
            st.rerun()
    
    st.markdown("---")
    
    # Main legal chat interface
    st.markdown("### Legal Question & Answer")
    
    # Display conversation history
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state['legal_chat_messages']):
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>Legal Assistant:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
                
                # Show citations if available
                if message.get("citations"):
                    with st.expander("📚 Legal References", expanded=False):
                        for citation in message["citations"]:
                            st.markdown(f"""
                            <div class="legal-citation">
                            <strong>{citation.get('title', 'Unknown')}</strong> ({citation.get('document_type', 'Unknown Type')})<br>
                            {f"Law No: {citation['law_number']}<br>" if citation.get('law_number') else ""}
                            {f"Jurisdiction: {citation['jurisdiction']}<br>" if citation.get('jurisdiction') else ""}
                            {f"Source: {citation['source']}" if citation.get('source') else ""}
                            </div>
                            """, unsafe_allow_html=True)
                
                # Show web sources if available
                if message.get("web_sources"):
                    with st.expander("🌐 Latest Legal Updates", expanded=False):
                        for source in message["web_sources"]:
                            st.write(f"• [{source.get('title', 'Unknown')}]({source.get('url', '#')})")
                            st.write(f"  Retrieved: {source.get('retrieved_date', 'Unknown')}")
    
    # Legal query input form
    with st.form(key="legal_query_form", clear_on_submit=True):
        # Query input
        user_question = st.text_area(
            "Ask your legal question:",
            height=120,
            placeholder="e.g., What are the requirements for establishing a company in Saudi Arabia? or What are the penalties for contract violations?",
            help="Be as specific as possible for the most accurate legal guidance."
        )
        
        # Filters and options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Get available categories from legal system
            legal_categories = []
            if 'legal_chatbot' in st.session_state and st.session_state['legal_chatbot']:
                legal_categories = st.session_state['legal_chatbot'].get_legal_categories()
            
            document_type = st.selectbox(
                "Document Type (Optional):",
                options=["All Types"] + legal_categories,
                help="Filter by specific type of legal document"
            )
            if document_type == "All Types":
                document_type = None
        
        with col2:
            # Get available jurisdictions
            jurisdictions = []
            if 'legal_chatbot' in st.session_state and st.session_state['legal_chatbot']:
                jurisdictions = st.session_state['legal_chatbot'].get_available_jurisdictions()
            
            jurisdiction = st.selectbox(
                "Jurisdiction:",
                options=jurisdictions if jurisdictions else ["Saudi Arabia", "GCC", "International"],
                help="Select the relevant legal jurisdiction"
            )
        
        with col3:
            include_web_search = st.checkbox(
                "Include Latest Updates",
                value=True,
                help="Search for recent legal developments and updates"
            )
        
        # Submit button
        submit_legal_query = st.form_submit_button(
            "Get Legal Guidance",
            use_container_width=True
        )
        
        if submit_legal_query and user_question.strip():
            # Ensure we have an active session
            if not st.session_state['current_legal_session']:
                if 'legal_chatbot' in st.session_state and st.session_state['legal_chatbot']:
                    session_id = st.session_state['legal_chatbot'].start_new_session()
                    st.session_state['current_legal_session'] = session_id
            
            # Add user message to chat
            st.session_state['legal_chat_messages'].append({
                "role": "user",
                "content": user_question
            })
            
            # Process the legal query
            if 'legal_chatbot' in st.session_state and st.session_state['legal_chatbot']:
                with st.spinner("Analyzing your legal question..."):
                    try:
                        legal_response = st.session_state['legal_chatbot'].ask_legal_question(
                            question=user_question,
                            document_type=document_type,
                            jurisdiction=jurisdiction,
                            include_web_search=include_web_search
                        )
                        
                        if legal_response.get('success', False):
                            # Add assistant response to chat
                            assistant_message = {
                                "role": "assistant",
                                "content": legal_response['response'],
                                "citations": legal_response.get('citations', []),
                                "web_sources": legal_response.get('web_sources', []),
                                "documents_consulted": legal_response.get('documents_consulted', 0)
                            }
                            st.session_state['legal_chat_messages'].append(assistant_message)
                            
                            # Update query count
                            st.session_state['legal_query_count'] += 1
                            
                            # Show success message
                            st.success(f"✅ Legal analysis complete! Consulted {legal_response.get('documents_consulted', 0)} legal documents.")
                            
                        else:
                            st.error("❌ Error processing your legal question. Please try again.")
                            st.session_state['legal_chat_messages'].append({
                                "role": "assistant",
                                "content": legal_response.get('response', 'An error occurred while processing your question.')
                            })
                    
                    except Exception as e:
                        st.error(f"❌ An error occurred: {str(e)}")
                        st.session_state['legal_chat_messages'].append({
                            "role": "assistant",
                            "content": f"I apologize, but I encountered an error while processing your legal question: {str(e)}"
                        })
            
            # Refresh the page to show new messages
            st.rerun()
    
    # Additional legal tools
    st.markdown("---")
    st.markdown("### Additional Legal Tools")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Search Legal Precedents", use_container_width=True):
            st.session_state['show_precedent_search'] = True
    
    with col2:
        if st.button("📋 Compliance Requirements", use_container_width=True):
            st.session_state['show_compliance_tool'] = True
    
    with col3:
        if st.button("📊 Session Report", use_container_width=True):
            if st.session_state['current_legal_session'] and 'legal_chatbot' in st.session_state:
                report = st.session_state['legal_chatbot'].export_session_report()
                st.session_state['current_session_report'] = report
                st.session_state['show_session_report'] = True
    
    # Show additional tools if requested
    if st.session_state.get('show_precedent_search', False):
        st.markdown("#### Legal Precedent Search")
        with st.form("precedent_search_form"):
            case_type = st.text_input("Case Type:", placeholder="e.g., contract dispute, employment termination")
            precedent_jurisdiction = st.selectbox("Jurisdiction:", ["Saudi Arabia", "GCC", "International"])
            
            if st.form_submit_button("Search Precedents"):
                if case_type and 'legal_search_engine' in st.session_state:
                    with st.spinner("Searching for legal precedents..."):
                        precedents = st.session_state['legal_search_engine'].search_legal_precedents(
                            case_type, precedent_jurisdiction
                        )
                        
                        if precedents:
                            st.success(f"Found {len(precedents)} relevant precedents:")
                            for prec in precedents:
                                with st.expander(f"📖 {prec['case_title']}"):
                                    st.write(f"**Type:** {prec['case_type']}")
                                    st.write(f"**Jurisdiction:** {prec['jurisdiction']}")
                                    st.write(f"**Summary:** {prec['summary']}")
                                    if prec['source_url']:
                                        st.write(f"**Source:** [View Full Case]({prec['source_url']})")
                        else:
                            st.info("No precedents found for the specified case type.")
        
        if st.button("Close Precedent Search"):
            st.session_state['show_precedent_search'] = False
            st.rerun()
    
    if st.session_state.get('show_compliance_tool', False):
        st.markdown("#### Compliance Requirements Checker")
        with st.form("compliance_check_form"):
            business_type = st.text_input(
                "Business Type:", 
                placeholder="e.g., fintech, healthcare, manufacturing, retail"
            )
            compliance_jurisdiction = st.selectbox("Jurisdiction:", ["Saudi Arabia", "GCC"])
            
            if st.form_submit_button("Check Compliance Requirements"):
                if business_type and 'legal_search_engine' in st.session_state:
                    with st.spinner("Checking compliance requirements..."):
                        compliance_info = st.session_state['legal_search_engine'].search_compliance_requirements(
                            business_type, compliance_jurisdiction
                        )
                        
                        if not compliance_info.get('error'):
                            st.success("Compliance requirements found:")
                            
                            if compliance_info['requirements']:
                                st.markdown("**Key Requirements:**")
                                for req in compliance_info['requirements']:
                                    st.write(f"• {req}")
                            
                            if compliance_info['licenses_needed']:
                                st.markdown("**Licenses Required:**")
                                for license in compliance_info['licenses_needed']:
                                    st.write(f"• {license}")
                            
                            if compliance_info['regulatory_bodies']:
                                st.markdown("**Regulatory Bodies:**")
                                for body in compliance_info['regulatory_bodies']:
                                    st.write(f"• {body}")
                        else:
                            st.error("Could not retrieve compliance requirements. Please try again.")
        
        if st.button("Close Compliance Tool"):
            st.session_state['show_compliance_tool'] = False
            st.rerun()
    
    if st.session_state.get('show_session_report', False):
        st.markdown("#### Session Report")
        report = st.session_state.get('current_session_report', {})
        
        if report and 'error' not in report:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Messages", report['statistics']['total_messages'])
                st.metric("Questions Asked", report['statistics']['questions_asked'])
            
            with col2:
                st.metric("Document Types", len(report['statistics']['document_types_consulted']))
                st.metric("Jurisdictions", len(report['statistics']['jurisdictions_consulted']))
            
            # Download report as JSON
            import json
            report_json = json.dumps(report, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Download Full Report",
                data=report_json.encode('utf-8'),
                file_name=f"legal_session_report_{report['session_info']['session_id'][:8]}.json",
                mime="application/json"
            )
        else:
            st.error("Could not generate session report.")
        
        if st.button("Close Report"):
            st.session_state['show_session_report'] = False
            st.rerun()

def generate_report_from_chat():
    """Generate a report based on the chat history"""
    if len(st.session_state['chat_messages']) < 5:
        st.warning("Not enough conversation data to generate a meaningful report.")
        return None
    
    # Extract information from chat history to identify topics, sectors, and geography
    all_messages = " ".join([msg["content"] for msg in st.session_state['chat_messages']])
    
    # Identify potential sectors of interest
    potential_sectors = []
    sector_keywords = [
        "technology", "software", "hardware", "healthcare", "pharmaceutical", 
        "finance", "banking", "real estate", "construction", "manufacturing",
        "retail", "e-commerce", "energy", "oil", "gas", "renewable", 
        "automotive", "transportation", "logistics", "agriculture", "food", 
        "telecommunications", "media", "tourism", "hospitality", "education"
    ]
    
    for keyword in sector_keywords:
        if keyword.lower() in all_messages.lower():
            potential_sectors.append(keyword.title())
    
    if not potential_sectors:
        potential_sectors = ["General Market"]
    
    # Try to identify geography (default to Saudi Arabia)
    geography = "Saudi Arabia"
    geo_keywords = [
        "Saudi Arabia", "UAE", "Dubai", "Abu Dhabi", "Qatar", "Kuwait", "Bahrain", "Oman", 
        "Middle East", "GCC", "MENA"
    ]
    
    for geo in geo_keywords:
        if geo.lower() in all_messages.lower():
            geography = geo
            break
    
    # Generate title based on conversation
    title = f"{geography} {', '.join(potential_sectors[:2])} Market Analysis"
    
    # Create loading state
    update_loading, complete_loading = create_loading_state("Generating comprehensive report...")
    
    try:
        # Get the market report system from container
        from dependency_container import container
        market_report_system = container.get('market_report_system')
        
        # Generate the report
        if market_report_system and not st.session_state['offline_mode']:
            update_loading(0.2, "Analyzing conversation...")
            
            # Create a summary of the conversation
            conversation_summary = "The following report is based on a conversation about "
            conversation_summary += f"{', '.join(potential_sectors)} in {geography}. "
            
            # Add some questions from the conversation
            user_questions = [msg["content"] for msg in st.session_state['chat_messages'] 
                             if msg["role"] == "user"]
            conversation_summary += "Key topics included: "
            conversation_summary += "; ".join(user_questions[:3])
            
            update_loading(0.4, "Generating market insights...")
            
            # Generate the full report
            result = market_report_system.create_market_report(
                title=title,
                sectors=potential_sectors,
                geography=geography,
                enhance_with_web=True,  # Always use web data to enhance the report
                include_visuals=True     # Always include visuals
            )
            
            update_loading(0.9, "Finalizing report...")
            
            # Update reports list
            st.session_state['reports'] = market_report_system.list_reports()
            
            # Save report metadata with proper encoding
            report_metadata = {
                "title": title,
                "sectors": potential_sectors,
                "geography": geography,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "file_path": result.get("json_file", ""),
                "pdf_path": result.get("pdf_file", ""),
                "conversation_based": True,
                "conversation_summary": conversation_summary
            }
            save_json_with_encoding("report_metadata.json", report_metadata)
            
            complete_loading(True, "Report generated successfully")
            
            return result
        else:
            # Offline mode or no market report system
            complete_loading(False, "Could not generate report - system offline")
            return None
    except Exception as e:
        complete_loading(False, "Error generating report")
        display_error(e, "Failed to generate the report.")
        return None

def chat_interface():
    """Main chat interface that generates comprehensive reports using existing modules"""
    st.markdown('<h2 class="sub-header">Market Intelligence Chat</h2>', unsafe_allow_html=True)
    
    # Add instructions for users
    st.info("💡 Ask about any Saudi Arabian market topic and get a comprehensive report with analysis, data, and insights.")
    
    # Display conversation
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state['chat_messages']):
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>Market Intelligence Report:</strong> {message["content"]}
                    {f'<br><br><small>📊 <a href="#{message.get("report_id", "")}">View Full Report</a></small>' if message.get("report_id") else ""}
                </div>
                """, unsafe_allow_html=True)
    
    # Input for new messages
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Ask about any Saudi Arabian market topic:", 
            height=100, 
            placeholder="e.g., What is the current state of wheat investment in Saudi Arabia? or Analyze the renewable energy sector..."
        )
        
        # Add options for report customization
        col1, col2 = st.columns(2)
        with col1:
            include_web_data = st.checkbox("Include latest web data", value=True)
            include_visuals = st.checkbox("Include data visualizations", value=True)
        with col2:
            generate_full_report = st.checkbox("Generate full report", value=True, help="Generate a comprehensive report instead of just a chat response")
        
        submit_button = st.form_submit_button("Generate Analysis", use_container_width=True)
        
        if submit_button and user_input:
            # Add user message to chat history
            st.session_state['chat_messages'].append({"role": "user", "content": user_input})
            
            # Increment prompt counter
            st.session_state['prompt_count'] += 1
            
            if generate_full_report:
                # Generate comprehensive report
                report_result = generate_report_from_single_query(
                    user_input,
                    include_web_data=include_web_data,
                    include_visuals=include_visuals
                )
                
                if report_result:
                    # Add summary to chat and reference to full report
                    summary = extract_report_summary(report_result["report_data"])
                    st.session_state['chat_messages'].append({
                        "role": "assistant", 
                        "content": summary,
                        "report_id": report_result.get("json_file", ""),
                        "type": "report_summary"
                    })
                    
                    st.success("✅ Comprehensive report generated! Check the 'Generated Reports' tab to view the full report.")
                else:
                    st.session_state['chat_messages'].append({
                        "role": "assistant", 
                        "content": "I encountered an issue generating the comprehensive report. Please try again or contact support."
                    })
            else:
                # Generate regular RAG response
                create_loading_state_simple = st.empty()
                with create_loading_state_simple:
                    with st.spinner("Analyzing your question..."):
                        try:
                            # Get rag_engine from the container
                            from dependency_container import container
                            rag_engine = container.get('rag_engine')
                            web_search = container.get('web_search')
                            
                            if rag_engine and not st.session_state['offline_mode']:
                                # Get RAG response
                                response = rag_engine.generate_rag_response(user_input)
                                
                                # Format response to remove LLM artifacts
                                response = clean_ai_language(response)
                                
                                # Enhance with web data if requested
                                if include_web_data and web_search:
                                    web_results = web_search.research_topic(user_input, top_n=2)
                                    if web_results.get('data'):
                                        response += "\n\n**Latest Market Updates:**\n"
                                        for source in web_results['data'][:1]:
                                            response += f"• {source.get('title', 'Recent development')}\n"
                                
                                # Add assistant message to chat history
                                st.session_state['chat_messages'].append({"role": "assistant", "content": response})
                            else:
                                # Offline mode
                                mock_response = generate_mock_response(user_input)
                                st.session_state['chat_messages'].append({"role": "assistant", "content": mock_response})
                        except Exception as e:
                            display_error(e, "Failed to generate a response to your question.")
                            st.session_state['chat_messages'].append({
                                "role": "assistant", 
                                "content": f"I apologize, but I encountered an issue analyzing your question. Please try again with a more specific query."
                            })
            
            # Force refresh
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()

def generate_report_from_single_query(query: str, include_web_data: bool = True, include_visuals: bool = True) -> Optional[Dict]:
    """Generate a comprehensive report from a single query"""
    
    # Analyze query to extract sectors and topics
    sectors, geography, title = analyze_query_for_sectors(query)
    
    # Create loading state
    update_loading, complete_loading = create_loading_state("Generating comprehensive market report...")
    
    try:
        # Get market_report_system from container
        from dependency_container import container
        market_report_system = container.get('market_report_system')
        
        if market_report_system and not st.session_state['offline_mode']:
            update_loading(0.2, "Analyzing query...")
            
            update_loading(0.4, "Generating comprehensive analysis...")
            
            # Use existing market report system to generate report
            result = market_report_system.create_market_report(
                title=title,
                sectors=sectors,
                geography=geography,
                enhance_with_web=include_web_data,
                include_visuals=include_visuals
            )
            
            update_loading(0.9, "Finalizing report...")
            
            # Update reports list
            if market_report_system:
                st.session_state['reports'] = market_report_system.list_reports()
            
            complete_loading(True, "Report generated successfully!")
            return result
        else:
            complete_loading(False, "Report system not available")
            return None
    except Exception as e:
        complete_loading(False, f"Error generating report: {str(e)}")
        display_error(e, "Failed to generate the comprehensive report.")
        return None

def analyze_query_for_sectors(query: str) -> tuple:
    """Analyze query to extract sectors and topics"""
    try:
        # Try to use the text processor if available
        from market_reports.text_processing import text_processor
        return text_processor.analyze_query_for_market_report(query)
    except ImportError:
        # Fallback implementation if text_processing module isn't available
        query_lower = query.lower()
        
        # Extract sectors based on keywords with more specific matching
        sectors = []
        sector_mapping = {
            "Electric Vehicles": ["electric vehicle", "electric car", "ev", "electric mobility", "electric transport", "tesla", "electrical vehicle"],
            "Automotive": ["automotive", "car", "vehicle", "automobile", "motor", "transportation"],
            "Technology": ["technology", "software", "digital", "ai", "tech", "it", "artificial intelligence"],
            "Energy": ["energy", "oil", "gas", "renewable", "solar", "wind", "petroleum", "power"],
            "Agriculture": ["agriculture", "wheat", "farming", "crops", "food", "agricultural"],
            "Finance": ["finance", "banking", "investment", "fintech", "insurance", "financial"],
            "Real Estate": ["real estate", "construction", "housing", "property", "development"],
            "Tourism": ["tourism", "travel", "hospitality", "entertainment", "hotel"],
            "Healthcare": ["healthcare", "medical", "pharmaceutical", "health", "medicine"],
            "Manufacturing": ["manufacturing", "industrial", "production", "factory"],
            "Transportation": ["transportation", "logistics", "shipping", "aviation", "freight"],
            "Retail": ["retail", "e-commerce", "shopping", "consumer", "market"],
            "Mining": ["mining", "minerals", "extraction", "resources"]
        }
        
        # Check for exact phrase matches first
        for sector, keywords in sector_mapping.items():
            for keyword in keywords:
                if keyword in query_lower:
                    sectors.append(sector)
                    break  # Only add sector once
        
        # Remove duplicates while preserving order
        sectors = list(dict.fromkeys(sectors))
        
        # Special handling for electric vehicles
        if any(keyword in query_lower for keyword in ["electric vehicle", "electric car", "ev", "electrical vehicle"]):
            # Remove general "Automotive" if "Electric Vehicles" is present
            if "Electric Vehicles" in sectors and "Automotive" in sectors:
                sectors.remove("Automotive")
            # Ensure Electric Vehicles is first if present
            if "Electric Vehicles" in sectors:
                sectors.remove("Electric Vehicles")
                sectors.insert(0, "Electric Vehicles")
        
        # Default to General Market if no specific sector found
        if not sectors:
            sectors = ["General Market"]
        
        # Extract geography (default to Saudi Arabia)
        geography = "Saudi Arabia"
        geo_keywords = {
            "UAE": ["uae", "emirates", "dubai", "abu dhabi"],
            "Qatar": ["qatar", "doha"],
            "Kuwait": ["kuwait"],
            "Bahrain": ["bahrain"],
            "Oman": ["oman"],
            "Egypt": ["egypt"],
            "GCC": ["gcc", "gulf cooperation council"],
            "MENA": ["mena", "middle east"]
        }
        
        for geo, keywords in geo_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                geography = geo
                break
        
        # Generate title based on main sector and query intent
        main_sector = sectors[0] if sectors else "Market"
        
        # Identify query intent
        intent_keywords = {
            "investment": ["investment", "invest", "funding", "finance", "capital"],
            "market_analysis": ["market", "analysis", "overview", "landscape", "industry"],
            "trends": ["trend", "future", "outlook", "forecast", "prediction"],
            "opportunities": ["opportunity", "potential", "growth", "development"],
            "comparison": ["compare", "comparison", "vs", "versus", "against"],
            "challenges": ["challenge", "problem", "risk", "barrier", "issue"]
        }
        
        intent = "market_analysis"  # default
        for intent_type, keywords in intent_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                intent = intent_type
                break
        
        # Generate title based on sector and intent
        if intent == "investment":
            title = f"{geography} {main_sector} Investment Analysis"
        elif intent == "trends":
            title = f"{geography} {main_sector} Trends & Outlook"
        elif intent == "opportunities":
            title = f"{geography} {main_sector} Market Opportunities"
        elif intent == "comparison":
            title = f"{geography} {main_sector} Comparative Analysis"
        elif intent == "challenges":
            title = f"{geography} {main_sector} Challenges & Solutions"
        else:
            title = f"{geography} {main_sector} Market Analysis"
        
        return sectors, geography, title

def display_reports():
    """Display generated reports"""
    st.markdown('<h2 class="sub-header">Generated Reports</h2>', unsafe_allow_html=True)
    
    # Refresh reports list
    if st.button("Refresh Reports List"):
        # Try to get market_report_system from container if available
        try:
            from dependency_container import container
            if container.has('market_report_system'):
                market_report_system = container.get('market_report_system')
                st.session_state['reports'] = market_report_system.list_reports()
                st.success("Reports list refreshed")
        except ImportError:
            # Use legacy approach if container not available
            if 'market_report_system' in st.session_state and st.session_state['market_report_system']:
                st.session_state['reports'] = st.session_state['market_report_system'].list_reports()
                st.success("Reports list refreshed")
            else:
                st.warning("Market report system not available")
    
    # Display reports
    if 'reports' in st.session_state and st.session_state['reports']:
        for report in st.session_state['reports']:
            with st.container():
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown(f"### {report['title']}")
                st.markdown(f"**Date:** {report['date']}")
                st.markdown(f"**Sectors:** {', '.join(report['sectors'])}")
                st.markdown(f"**Geography:** {report['geography']}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"View Report", key=f"view_{report['filename']}"):
                        # Load report with proper encoding
                        try:
                            # Try using utils if available
                            from market_reports.utils import load_json_with_encoding
                            st.session_state['current_report'] = load_json_with_encoding(report['file_path'])
                        except ImportError:
                            # Fallback approach
                            try:
                                with open(report['file_path'], 'r', encoding='utf-8') as f:
                                    import json
                                    st.session_state['current_report'] = json.load(f)
                            except UnicodeDecodeError:
                                with open(report['file_path'], 'r', encoding='latin-1') as f:
                                    import json
                                    st.session_state['current_report'] = json.load(f)
                
                with col2:
                    # PDF download button
                    pdf_path = report.get('file_path', '').replace(".json", ".pdf")
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="Download PDF",
                                data=f,
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf",
                                key=f"pdf_{report['filename']}"
                            )
                
                with col3:
                    # Delete button
                    if st.button(f"Delete Report", key=f"delete_{report['filename']}"):
                        try:
                            # Try using container
                            from dependency_container import container
                            if container.has('market_report_system'):
                                market_report_system = container.get('market_report_system')
                                if market_report_system.delete_report(report['file_path']):
                                    st.session_state['reports'] = market_report_system.list_reports()
                                    st.rerun()
                        except ImportError:
                            # Legacy approach
                            if 'market_report_system' in st.session_state and st.session_state['market_report_system']:
                                if st.session_state['market_report_system'].delete_report(report['file_path']):
                                    st.session_state['reports'] = st.session_state['market_report_system'].list_reports()
                                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No reports found. Chat with the Market Intelligence Assistant to generate a report.")
    
    # Display current report if selected
    if 'current_report' in st.session_state and st.session_state['current_report']:
        st.markdown('<div class="report-header">', unsafe_allow_html=True)
        st.markdown(f"# {st.session_state['current_report']['title']}")
        st.markdown(f"**Date:** {st.session_state['current_report']['date']}")
        st.markdown(f"**Sectors:** {', '.join(st.session_state['current_report']['sectors'])}")
        st.markdown(f"**Geography:** {st.session_state['current_report']['geography']}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display sections
        for section in st.session_state['current_report']['sections']:
            with st.container():
                st.markdown('<div class="report-section">', unsafe_allow_html=True)
                st.markdown(f"<h2 class='report-section-title'>{section['title']}</h2>", unsafe_allow_html=True)
                st.markdown(section['content'])
                
                # Display charts if any
                for chart in section.get('charts', []):
                    if 'path' in chart and os.path.exists(chart['path']):
                        st.image(chart['path'], caption=chart['title'])
                
                # Display subsections
                for subsection in section.get('subsections', []):
                    st.markdown(f"<h3>{subsection['title']}</h3>", unsafe_allow_html=True)
                    st.markdown(subsection['content'])
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Display sources if any
        if st.session_state['current_report'].get('sources'):
            st.markdown("## Sources")
            for source in st.session_state['current_report']['sources']:
                st.markdown(f"- [{source['title']}]({source['url']}) (Retrieved: {source['retrieved_date']})")
        
        # Export report as JSON
        if st.button("Export Report as JSON"):
            import json
            report_json = json.dumps(st.session_state['current_report'], ensure_ascii=False, indent=2)
            st.download_button(
                label="Download JSON",
                data=report_json.encode('utf-8'),
                file_name=f"{st.session_state['current_report']['title'].replace(' ', '_')}.json",
                mime="application/json"
            )
        
        # Clear current report button
        if st.button("Close Report"):
            st.session_state['current_report'] = None
            st.rerun()

def extract_report_summary(report_data: dict) -> str:
    """Extract a summary from the generated report for chat display"""
    try:
        # Try to use text processor if available
        from market_reports.text_processing import text_processor
        return text_processor.extract_report_summary(report_data)
    except ImportError:
        # Fallback implementation
        if not report_data or not isinstance(report_data, dict):
            return "Report generated successfully. Please check the Reports tab for the full analysis."
        
        # Try to get executive summary or first section
        sections = report_data.get("sections", [])
        if sections:
            for section in sections:
                if section.get("title", "").lower() in ["executive summary", "summary"]:
                    content = section.get("content", "")
                    # Return first 300 characters
                    return content[:300] + "..." if len(content) > 300 else content
            
            # If no executive summary, return first section content
            first_section = sections[0]
            content = first_section.get("content", "")
            return f"**{first_section.get('title', 'Analysis')}**: {content[:250]}..." if len(content) > 250 else content
        
        return f"Comprehensive analysis of {report_data.get('title', 'market topic')} completed. The report includes detailed market insights, investment opportunities, and strategic recommendations."

def generate_mock_response(query: str) -> str:
    """Generate a mock response when systems are offline"""
    query_lower = query.lower()
    
    if "wheat" in query_lower and "investment" in query_lower:
        return """
        Based on the latest market intelligence, Saudi Arabia's wheat investment landscape shows significant potential:

        **Key Highlights:**
        • Government allocated SAR 2.1 billion for agricultural development in 2024
        • Wheat production capacity increased by 15% through modern irrigation systems
        • Private sector investment in agricultural technology grew by 40%
        • Strategic partnerships with international agricultural companies expanding

        **Investment Opportunities:**
        • Advanced farming technology and automation
        • Water-efficient irrigation systems
        • Grain storage and logistics infrastructure
        • Research and development in drought-resistant wheat varieties

        The sector benefits from strong government support under Vision 2030's food security initiatives.
        """
    elif "technology" in query_lower:
        return """
        Saudi Arabia's technology sector demonstrates robust growth driven by Vision 2030:

        **Market Overview:**
        • Technology market valued at SAR 25 billion with 12% annual growth
        • Major investments in AI, fintech, and smart city technologies
        • Government digital transformation budget of SAR 8 billion
        • 500+ tech startups established in 2023

        **Key Drivers:**
        • NEOM and other giga-projects creating tech demand
        • Digital government initiatives and e-services expansion
        • Growing venture capital ecosystem
        • Strategic partnerships with global tech companies

        Strong fundamentals support continued sector expansion and innovation.
        """
    else:
        topic = query.split()[0:3]
        topic_str = " ".join(topic).title()
        return f"""
        Analysis of {topic_str} in Saudi Arabia reveals promising market dynamics:

        **Current Status:**
        • Market experiencing steady growth aligned with Vision 2030 objectives
        • Increasing government and private sector investment
        • Growing international partnerships and collaborations
        • Favorable regulatory environment supporting development

        **Opportunities:**
        • Emerging market segments with high growth potential
        • Technology adoption and digital transformation
        • Infrastructure development and modernization
        • Export opportunities to regional markets

        **Outlook:**
        Positive growth trajectory expected with continued policy support and investment inflows.
        """

def about_page():
    """About page with information about the platform"""
    st.markdown('<h2 class="sub-header">About LinkSaudi Market Intelligence Platform</h2>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("""
        The LinkSaudi Market Intelligence Platform is a comprehensive tool for analyzing Saudi Arabian markets. 
        It combines advanced AI with a rich database of market reports to provide accurate, up-to-date information.
        
        ### Key Features:
        
        - **Market Intelligence Chat**: Ask questions about Saudi Arabian markets and get expert answers
        - **Report Generation**: Automatically generate comprehensive market reports based on your conversations
        - **Legal Compliance Assistant**: Get legal guidance and compliance information for Saudi Arabian law
        - **Data Visualization**: View market trends and data through interactive charts
        - **Web Verification**: Reports are enhanced with the latest information from the web
        
        ### About LinkSaudi:
        
        LinkSaudi is a leading provider of business intelligence and market research for Saudi Arabia. 
        We help businesses understand the Saudi market, identify opportunities, and make informed decisions.
        
        [Visit our website](https://linksaudi.com) for more information.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display system status in about page
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### System Status")
        
        # Display component statuses if available
        try:
            from dependency_container import container
            from market_reports.utils import system_state
            
            st.markdown(f"**Current State:** {system_state.current_state}")
            
            st.markdown("#### Market Intelligence Components:")
            for component_name in ['rag_engine', 'web_search', 'report_generator', 
                                  'report_conversation', 'pdf_exporter', 'market_report_system']:
                status = system_state.get_component_status(component_name)
                if status['available']:
                    st.success(f"✅ {component_name}: Available")
                else:
                    st.error(f"❌ {component_name}: {status['description']}")
            
            # Display legal system status
            st.markdown("#### Legal Compliance Components:")
            legal_status = container.get_legal_system_status()
            if legal_status['available']:
                st.success("✅ Legal Compliance System: Fully Available")
            else:
                st.warning(f"⚠️ Legal Compliance System: Limited ({len(legal_status['missing_components'])} components missing)")
                for component, info in legal_status['components'].items():
                    if info['available']:
                        st.success(f"✅ {component}: Available")
                    else:
                        st.error(f"❌ {component}: {info['type']}")
                        
        except ImportError:
            # Fallback status display
            st.markdown(f"**Current State:** {st.session_state.get('system_status', 'unknown')}")
            st.markdown("System information is limited in legacy mode.")
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    # Display header
    st.markdown('<h1 class="main-header">LinkSaudi Market Intelligence Platform</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://linksaudi.com/wp-content/uploads/2023/03/LinkSaudi-Logo-1.png", width=200)
        st.markdown("## Navigation")
        
        # Navigation - MODIFIED TO INCLUDE LEGAL COMPLIANCE
        page = st.radio("Select a page", [
            "Market Intelligence Chat", 
            "Generated Reports", 
            "Legal Compliance",  # NEW PAGE
            "About"
        ])
        
        # Status indicator
        display_status_indicator()
        
        # Initialize system if not already initialized
        if not st.session_state['initialized']:
            if st.button("Initialize System"):
                with st.spinner("Initializing system..."):
                    initialize_application()
        else:
            # Initialize legal compliance if not done
            if not st.session_state.get('legal_system_available', False):
                if st.button("Initialize Legal System"):
                    with st.spinner("Initializing legal compliance..."):
                        initialize_legal_compliance()
        
        # Display system info
        st.markdown("### System Info")
        st.markdown(f"Status: {st.session_state['system_status']}")
        if st.session_state.get('legal_system_available'):
            st.markdown("Legal: ✅ Available")
        else:
            st.markdown("Legal: ❌ Unavailable")
        
        # Clear chat button
        if st.button("Clear Chat History"):
            st.session_state['chat_messages'] = []
            st.session_state['legal_chat_messages'] = []  # ADDED FOR LEGAL
            st.session_state['prompt_count'] = 0
            st.session_state['legal_query_count'] = 0  # ADDED FOR LEGAL
            st.session_state['report_ready'] = False
            st.success("Chat history cleared")
    
    # Initialize system if not already initialized
    if not st.session_state['initialized']:
        initialize_application()
    
    # Main page content - MODIFIED TO INCLUDE LEGAL COMPLIANCE
    if page == "Market Intelligence Chat":
        chat_interface()
    elif page == "Generated Reports":
        display_reports()
    elif page == "Legal Compliance":  # NEW PAGE
        legal_compliance_interface()
    elif page == "About":
        about_page()

if __name__ == "__main__":
    main()