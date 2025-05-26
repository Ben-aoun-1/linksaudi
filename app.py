#!/usr/bin/env python3
import streamlit as st

st.set_page_config(
    page_title="LinkSaudi Market Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

try:
    from dependency_container import container
    from system_initializer import initialize_system, get_system_overview
    from error_handling import format_error_for_display
    CORE_IMPORTS_AVAILABLE = True
except ImportError as e:
    CORE_IMPORTS_AVAILABLE = False
    print(f"Core imports failed: {e}")

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

try:
    from legal_compliance import LegalRAGEngine, LegalChatbot
    LEGAL_COMPLIANCE_AVAILABLE = True
    print("Legal compliance components imported successfully")
except ImportError as e:
    LEGAL_COMPLIANCE_AVAILABLE = False
    print(f"Legal compliance components not available: {e}")

try:
    from legal_compliance.legal_rag_engine import LegalRAGEngine as FixedLegalRAGEngine
    from system_initializer_legal_fixes import (
        create_legal_rag_engine_fixed,
        create_legal_chatbot_enhanced_no_web,
        get_legal_system_diagnostics_no_web,
        update_system_initializer_no_web
    )
    FIXED_LEGAL_AVAILABLE = True
    print("✅ FIXED Legal RAG components imported successfully")
except ImportError as e:
    FIXED_LEGAL_AVAILABLE = False
    print(f"⚠️ FIXED Legal RAG components not available: {e}")

st.markdown("""
<style>
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

def initialize_session_state():
    if 'initialized' not in st.session_state:
        st.session_state['initialized'] = False
        st.session_state['offline_mode'] = False
        st.session_state['system_status'] = 'unknown'
        st.session_state['connection_status'] = 'unknown'
        
        st.session_state['history'] = []
        st.session_state['reports'] = []
        st.session_state['current_report'] = None
        st.session_state['temp_files'] = []
        st.session_state['chat_messages'] = []
        st.session_state['prompt_count'] = 0
        st.session_state['report_ready'] = False
        
        st.session_state['legal_system_available'] = False
        st.session_state['legal_system_type'] = 'unknown'
        st.session_state['legal_chat_messages'] = []
        st.session_state['current_legal_session'] = None
        st.session_state['legal_query_count'] = 0
        st.session_state['legal_document_count'] = 0
        
        st.session_state['show_legal_history'] = False
        st.session_state['show_legal_diagnostics'] = False
        st.session_state['show_session_report'] = False
        st.session_state['current_session_report'] = None

initialize_session_state()

def initialize_application():
    try:
        _create_directories()
        _create_default_config()
        
        if st.session_state['initialized']:
            logger.info("Application already initialized")
            return True
        
        if CORE_IMPORTS_AVAILABLE:
            return _initialize_with_new_architecture()
        else:
            return _initialize_with_fallback()
            
    except Exception as e:
        logger.error(f"Critical error initializing application: {e}")
        return _handle_initialization_failure()

def _create_directories():
    directories = [
        "report_charts", "market_reports", "legal_conversations", 
        "legal_cache", "logs"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def _create_default_config():
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
                "enable_web_enhancement": False,
                "cache_duration_hours": 24
            }
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info(f"Created default config file at {config_file}")

def _initialize_with_new_architecture():
    try:
        from market_reports.utils import logger, config_manager, system_state
        from dependency_container import container
        from system_initializer import initialize_system
        
        logger.info("Using refactored architecture")
        
        success = initialize_system(offline_mode=st.session_state['offline_mode'])
        
        if success:
            logger.info("System initialized successfully with new architecture")
            st.session_state['initialized'] = True
            st.session_state['system_status'] = system_state.current_state
            st.session_state['connection_status'] = system_state.current_state
            
            if container.has('market_report_system'):
                market_report_system = container.get('market_report_system')
                st.session_state['reports'] = market_report_system.list_reports()
            
            initialize_legal_compliance()
            
            return True
        return False
        
    except ImportError as e:
        logger.info(f"Refactored architecture not available: {e}")
        return False

def _initialize_with_fallback():
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
    import traceback
    logger.debug(traceback.format_exc())
    
    st.session_state['system_status'] = 'offline'
    st.session_state['connection_status'] = 'offline'
    st.session_state['offline_mode'] = True
    st.session_state['initialized'] = True
    return False

def initialize_legal_compliance():
    try:
        if not LEGAL_COMPLIANCE_AVAILABLE and not FIXED_LEGAL_AVAILABLE:
            st.session_state['legal_system_available'] = False
            st.session_state['legal_system_type'] = 'unavailable'
            return False
        
        from dependency_container import container
        
        if FIXED_LEGAL_AVAILABLE:
            try:
                from system_initializer import system_initializer
                update_system_initializer_no_web(system_initializer)
                logger.info("System initializer updated with legal components (no web search)")
            except Exception as e:
                logger.warning(f"Could not update system initializer: {e}")
        
        if container.has('legal_rag_engine') and container.has('legal_chatbot'):
            st.session_state['legal_rag_engine'] = container.get('legal_rag_engine')
            st.session_state['legal_chatbot'] = container.get('legal_chatbot')
            
            return _test_legal_system_no_web()
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

def _test_legal_system_no_web():
    if FIXED_LEGAL_AVAILABLE and hasattr(st.session_state['legal_chatbot'], 'get_system_status'):
        try:
            system_status = st.session_state['legal_chatbot'].get_system_status()
            logger.info(f"Legal system status (no web): {system_status}")
            
            rag_test = system_status.get('rag_connection_test', {})
            if rag_test.get('status') == 'success':
                st.session_state['legal_system_available'] = True
                st.session_state['legal_system_type'] = 'full_rag'
                st.session_state['legal_document_count'] = rag_test.get('total_documents', 0)
                logger.info("✅ Legal RAG system with Weaviate available (database only)")
            elif rag_test.get('status') == 'mock':
                st.session_state['legal_system_available'] = True
                st.session_state['legal_system_type'] = 'basic'
                st.session_state['legal_document_count'] = 0
                logger.info("🔵 Basic legal system available (mock, database only)")
            else:
                st.session_state['legal_system_available'] = True
                st.session_state['legal_system_type'] = 'limited'
                st.session_state['legal_document_count'] = 0
                logger.info("⚠️ Limited legal system available (database only)")
        except Exception as e:
            logger.error(f"Error testing legal system: {e}")
            st.session_state['legal_system_available'] = True
            st.session_state['legal_system_type'] = 'basic'
            st.session_state['legal_document_count'] = 0
    else:
        st.session_state['legal_system_available'] = True
        st.session_state['legal_system_type'] = 'basic'
        st.session_state['legal_document_count'] = 0
        logger.info("Basic legal compliance system available (database only)")
    
    return True

def display_status_indicator():
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
    else:
        st.markdown("""
        <div class="status-indicator degraded">
            <span>●</span>&nbsp;System degraded - Some services may be unavailable
        </div>
        """, unsafe_allow_html=True)

def display_error(error, user_message=None):
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
    container = st.empty()
    progress_bar = None
    start_time = time.time()
    
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

def _display_legal_session_management():
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
    
    if st.session_state.get('current_legal_session'):
        st.markdown(f"""
        <div class="legal-session-info">
            <strong>Current Session:</strong> {st.session_state['current_legal_session'][:8]}...<br>
            <strong>Queries in Session:</strong> {st.session_state.get('legal_query_count', 0)}
        </div>
        """, unsafe_allow_html=True)

def _display_legal_chat_interface_no_web():
    st.markdown("### 💬 Ask Your Legal Question")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        legal_question = st.text_area(
            "Enter your legal question:",
            placeholder="e.g., What are the requirements for establishing a company in Saudi Arabia?",
            height=100
        )
    
    with col2:
        st.markdown("**Filters:**")
        
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
        
        st.info("📍 **Database Only Mode**\nResponses are based on legal documents in our database only.")
    
    if st.button("🔍 Get Legal Guidance", type="primary"):
        if legal_question.strip():
            _process_legal_question_no_web(
                legal_question, 
                selected_category if selected_category != "All Categories" else None,
                selected_jurisdiction
            )
        else:
            st.warning("Please enter a legal question.")
    
    _display_legal_chat_history_no_web()

def _process_legal_question_no_web(question, category, jurisdiction):
    if 'legal_chatbot' not in st.session_state:
        st.error("Legal chatbot not available. Please check system status.")
        return
    
    try:
        update_loading, complete_loading = create_loading_state("Analyzing your legal question (database only)...")
        
        if not st.session_state.get('current_legal_session'):
            session_id = st.session_state['legal_chatbot'].start_new_session()
            st.session_state['current_legal_session'] = session_id
        
        update_loading(message="Searching legal documents in database...")
        response = st.session_state['legal_chatbot'].ask_legal_question(
            question=question,
            document_type=category,
            jurisdiction=jurisdiction
        )
        
        complete_loading(success=response.get('success', False))
        
        if response.get('success'):
            st.session_state['legal_query_count'] += 1
            
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
                'documents_consulted': response.get('documents_consulted', 0),
                'source': 'database_only'
            })
            
            st.rerun()
        else:
            st.error(f"Error processing legal question: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        complete_loading(success=False, message=f"Error: {str(e)}")
        st.error(f"Error processing legal question: {e}")

def _display_legal_chat_history_no_web():
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
                formatted_content = message['content'].replace('\n', '<br>')
                source_info = message.get('source', 'unknown')
                
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>Legal Assistant (Database Only):</strong><br>
                    {formatted_content}
                    <br><small>Source: {source_info}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if message.get('citations'):
                    with st.expander(f"📚 Citations ({len(message['citations'])})"):
                        for i, citation in enumerate(message['citations'], 1):
                            st.markdown(f"""
                            <div class="legal-citation">
                                <strong>{i}. {citation.get('title', 'Legal Document')}</strong><br>
                                Type: {citation.get('document_type', 'Unknown')}<br>
                                Jurisdiction: {citation.get('jurisdiction', 'Unknown')}<br>
                                Source: Legal Database
                            </div>
                            """, unsafe_allow_html=True)
                
                docs_consulted = message.get('documents_consulted', 0)
                if docs_consulted > 0:
                    st.info(f"📄 Consulted {docs_consulted} legal documents from database")

def _display_additional_legal_tools_no_web():
    st.markdown("### 🛠️ Additional Legal Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Session Analytics"):
            st.session_state['show_session_report'] = True
            st.rerun()
    
    with col2:
        if st.button("📋 Document Categories"):
            _show_legal_categories()
    
    _display_legal_tools_content_no_web()

def _display_legal_tools_content_no_web():
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
                        
                        st.info("📍 All responses are based on legal database documents only.")
                    else:
                        st.info("No active session to analyze.")
                except Exception as e:
                    st.error(f"Error getting session analytics: {e}")
            
            if st.button("Close Session Analytics"):
                st.session_state['show_session_report'] = False
                st.rerun()

def _show_legal_categories():
    if 'legal_chatbot' in st.session_state:
        try:
            categories = st.session_state['legal_chatbot'].get_legal_categories()
            jurisdictions = st.session_state['legal_chatbot'].get_available_jurisdictions()
            
            st.markdown("**Available Legal Categories:**")
            for category in categories:
                st.markdown(f"• {category}")
            
            st.markdown("**Available Jurisdictions:**")
            for jurisdiction in jurisdictions:
                st.markdown(f"• {jurisdiction}")
            
            st.info("📍 All legal guidance is based on documents in our legal database.")
        except Exception as e:
            st.error(f"Error getting legal categories: {e}")

def _display_chat_controls():
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
    st.markdown('<h2 class="sub-header">Legal Compliance Assistant</h2>', unsafe_allow_html=True)
    
    if not st.session_state['legal_system_available']:
        _display_legal_system_unavailable()
        return
    
    _display_legal_system_status_no_web()
    _display_legal_system_metrics()
    _display_legal_diagnostics_panel()
    _display_legal_disclaimer()
    _display_legal_session_management()
    _display_legal_chat_interface_no_web()
    _display_additional_legal_tools_no_web()
    _display_chat_controls()

def dashboard_interface():
    st.markdown('<h2 class="sub-header">🏠 Dashboard Overview</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="section-card">
        <h3>Welcome to LinkSaudi Market Intelligence Platform</h3>
        <p>Your comprehensive solution for market research, legal compliance, and business intelligence in Saudi Arabia and the GCC region.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
            <h4>⚖️ Legal Compliance (Database Only)</h4>
            <ul>
                <li>Saudi Arabian legal guidance</li>
                <li>Legal document analysis</li>
                <li>Regulatory compliance checking</li>
                <li>Consultation session management</li>
                <li>Database-only responses (no web search)</li>
            </ul>
            <p><strong>Status:</strong> {legal_description}</p>
        </div>
        """, unsafe_allow_html=True)
    
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
    st.markdown('<h2 class="sub-header">📊 Market Intelligence Reports</h2>', unsafe_allow_html=True)
    
    if not CORE_IMPORTS_AVAILABLE:
        st.error("⚠️ Market report system is not fully available. Please check system dependencies.")
        return
    
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
        
        with st.expander("🔧 Advanced Options"):
            include_visuals = "Visual Charts" in report_options
            enhance_with_web = "Web Research Enhancement" in report_options
            
            custom_focus = st.text_area(
                "Custom Research Focus (Optional)",
                placeholder="e.g., Focus on startup ecosystem, regulatory changes, market size..."
            )
        
        submitted = st.form_submit_button("🚀 Generate Report", type="primary")
        
        if submitted:
            if report_title and sectors:
                generate_market_report(report_title, sectors, geography, enhance_with_web, include_visuals, custom_focus)
            else:
                st.error("Please fill in required fields (Title and Sectors)")
    
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
    try:
        update_loading, complete_loading = create_loading_state("Generating your market report...")
        
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
                
                st.session_state['reports'].append(result['report_data'])
                st.session_state['current_report'] = result['report_data']
                
                complete_loading(success=True, message="Report generated successfully!")
                
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
    st.markdown('<h2 class="sub-header">💬 Report Analysis & Chat</h2>', unsafe_allow_html=True)
    
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
    
    report = st.session_state['current_report']
    st.markdown(f"""
    <div class="section-card">
        <h3>📄 Current Report: {report.get('title', 'Untitled Report')}</h3>
        <p><strong>Sectors:</strong> {', '.join(report.get('sectors', []))}</p>
        <p><strong>Geography:</strong> {report.get('geography', 'Unknown')}</p>
        <p><strong>Generated:</strong> {report.get('date', 'Unknown')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💬 Ask Questions About This Report")
    
    user_question = st.text_input(
        "Ask a question about the report:", 
        placeholder="e.g., What are the key market trends? Who are the main competitors?"
    )
    
    if st.button("🔍 Ask Question") and user_question:
        process_report_question(user_question, report)
    
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
    try:
        update_loading, complete_loading = create_loading_state("Analyzing your question...")
        
        from dependency_container import container
        
        if container.has('report_conversation'):
            report_conversation = container.get('report_conversation')
            response = report_conversation.ask_question(question)
            
            complete_loading(success=True)
            
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
    st.markdown("### 📄 Full Report View")
    
    st.markdown(f"""
    <div class="report-header">
        <h2>{report.get('title', 'Market Report')}</h2>
        <p>Generated on {report.get('date', 'Unknown Date')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    for section in report.get('sections', []):
        section_content = section.get('content', 'No content available').replace('\n', '<br>')
        st.markdown(f"""
        <div class="report-section">
            <h3 class="report-section-title">{section.get('title', 'Section')}</h3>
            <div style="padding: 1rem;">
                {section_content}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for subsection in section.get('subsections', []):
            st.markdown(f"**{subsection.get('title', 'Subsection')}**")
            st.markdown(subsection.get('content', 'No content available'))

def system_status_interface():
    st.markdown('<h2 class="sub-header">🔧 System Status & Diagnostics</h2>', unsafe_allow_html=True)
    
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
            
            st.markdown("### 🔍 Component Status")
            
            for component, status in system_overview.get('component_status', {}).items():
                if status.get('available'):
                    st.success(f"✅ **{component}**: {status.get('description', 'Available')}")
                else:
                    st.error(f"❌ **{component}**: {status.get('description', 'Unavailable')}")
            
            legal_system = system_overview.get('legal_system', {})
            if legal_system.get('components'):
                st.markdown("### ⚖️ Legal System Details")
                
                st.info(f"🔧 **Web Search Status:** {'Disabled' if not legal_system.get('web_search_enabled', True) else 'Enabled'}")
                
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
    st.markdown('<h2 class="sub-header">📚 Help & Documentation</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 🚀 Getting Started
    
    Welcome to the LinkSaudi Market Intelligence Platform! This comprehensive tool provides:
    
    #### 📊 Market Intelligence Features:
    - **AI-Powered Reports**: Generate detailed market analysis reports
    - **Web Research Integration**: Real-time data from web sources
    - **Interactive Analysis**: Chat with your reports to get specific insights
    - **Export Capabilities**: Download reports in PDF and JSON formats
    
    #### ⚖️ Legal Compliance Features (Database Only):
    - **Saudi Arabian Law Guidance**: Get legal guidance based on local regulations
    - **Document Analysis**: Search through legal document databases
    - **Compliance Checking**: Verify regulatory requirements
    - **Session Management**: Track and export legal consultation sessions
    - **Database Only Mode**: Responses based entirely on curated legal documents (no web search)
    
    ### 🔧 System Requirements
    
    For full functionality, ensure you have:
    - OpenAI API key configured
    - Weaviate database connection (for advanced features)
    - All Python dependencies installed
    
    ### 💡 Tips for Best Results
    
    1. **Market Reports**: Be specific about sectors and geographic focus
    2. **Legal Questions**: Include jurisdiction and business context
    3. **System Performance**: Use offline mode if experiencing connectivity issues
    4. **Legal System**: Note that web search is disabled for legal compliance
    
    ### 🆘 Troubleshooting
    
    If you encounter issues:
    1. Check the System Status page for component availability
    2. Try refreshing the system using the sidebar controls
    3. Enable offline mode for basic functionality
    4. Contact support if problems persist
    
    ### ⚖️ Legal System Notes
    
    The legal compliance system operates in **Database Only Mode**:
    - All responses are based on legal documents in our database
    - Web search functionality has been disabled for legal compliance
    - This ensures consistent and controlled responses
    - For current legal information, consult with qualified attorneys
    """)
    
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **Q: Why isn't the legal web search working?**
        A: Legal web search has been intentionally disabled. The system now operates in database-only mode for better compliance and consistency.
        
        **Q: How do I improve report quality?**
        A: Enable web research enhancement and provide specific industry focus in your queries.
        
        **Q: Can I export my data?**
        A: Yes! Use the export buttons in each section to download reports, chat history, and diagnostics.
        
        **Q: What does "offline mode" do?**
        A: Offline mode uses cached data only and disables web-based features for better performance.
        
        **Q: How accurate is the legal information?**
        A: Legal information is based on documents in our database. Always consult with qualified attorneys for specific legal matters.
        """)
    
    st.markdown("""
    ### 📞 Support
    
    For technical support or questions:
    - Check the System Status page for diagnostics
    - Review the troubleshooting steps above
    - Export system diagnostics for detailed error information
    """)
def _display_legal_system_status_no_web():
    system_type = st.session_state.get('legal_system_type', 'unknown')
    
    if system_type == 'full_rag':
        st.markdown("""
        <div class="system-status-full-rag">
            🟢 <strong>Legal RAG System Active</strong> - Connected to Weaviate legal database (Database Only)
        </div>
        """, unsafe_allow_html=True)
    elif system_type == 'limited':
        st.markdown("""
        <div class="system-status-limited">
            🟡 <strong>Limited Legal System</strong> - Basic functionality available, database only
        </div>
        """, unsafe_allow_html=True)
    elif system_type == 'basic':
        st.markdown("""
        <div class="system-status-basic">
            🔵 <strong>Basic Legal System</strong> - Using database responses only
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚪ **Legal System Status Unknown**")

def _display_legal_system_metrics():
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
    with st.expander("🔧 System Diagnostics", expanded=False):
        if st.button("Run Full Legal System Diagnostics"):
            try:
                from dependency_container import container
                if FIXED_LEGAL_AVAILABLE:
                    diagnostics = get_legal_system_diagnostics_no_web(container)
                    
                    st.markdown("### Legal System Diagnostics Report")
                    st.markdown(f"**Overall Status:** `{diagnostics['overall_status']}`")
                    st.markdown(f"**Report Generated:** {diagnostics['timestamp']}")
                    st.markdown(f"**Web Search Enabled:** {diagnostics['web_search_enabled']}")
                    
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
    st.markdown("""
    <div class="legal-disclaimer">
        <h4>⚖️ Legal Disclaimer</h4>
        <p><strong>Important:</strong> This AI assistant provides general legal information based on legal documents in our database and should not replace professional legal advice. For specific legal matters, always consult with a qualified attorney licensed in the relevant jurisdiction.</p>
        <ul>
            <li>Responses are for informational purposes only</li>
            <li>Based on legal documents in our database only (no web search)</li>
            <li>Laws and regulations may change frequently</li>
            <li>Individual circumstances may affect legal outcomes</li>
            <li>Always verify information with current legal sources</li>
        </ul>
        <p><strong>📍 Database Only Mode:</strong> This system uses only legal documents stored in our database. It does not search the web for current legal information.</p>
    </div>
    """, unsafe_allow_html=True)
def main():
    if not initialize_application():
        st.error("⚠️ Application initialization failed. Some features may not be available.")
    
    st.markdown('<h1 class="main-header">📊 LinkSaudi Market Intelligence Platform</h1>', unsafe_allow_html=True)
    
    display_status_indicator()
    
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        nav_options = [
            "🏠 Dashboard",
            "📊 Market Reports", 
            "💬 Report Chat",
            "⚖️ Legal Compliance",
            "🔧 System Status",
            "📚 Help & Documentation"
        ]
        
        selected_page = st.selectbox("Choose a section:", nav_options, key="main_navigation")
        
        st.markdown("### ⚙️ System Controls")
        
        offline_mode = st.checkbox(
            "Offline Mode", 
            value=st.session_state.get('offline_mode', False),
            help="Work with cached data only"
        )
        
        if offline_mode != st.session_state.get('offline_mode', False):
            st.session_state['offline_mode'] = offline_mode
            st.rerun()
        
        if st.button("🔄 Refresh System"):
            st.session_state['initialized'] = False
            st.rerun()
        
        st.markdown("### 📈 Quick Stats")
        st.metric("System Status", st.session_state.get('system_status', 'Unknown'))
        st.metric("Reports Generated", len(st.session_state.get('reports', [])))
        st.metric("Legal Queries", st.session_state.get('legal_query_count', 0))
        
        legal_system_info = st.session_state.get('legal_system_type', 'unknown')
        if legal_system_info != 'unknown':
            st.info(f"Legal System: {legal_system_info.replace('_', ' ').title()} (Database Only)")
    
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

if __name__ == "__main__":
    main()
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
    
    if st.session_state.get('show_legal_diagnostics', False):
        st.markdown("### Legal System Diagnostics")
        try:
            from dependency_container import container
            if FIXED_LEGAL_AVAILABLE:
                diagnostics = get_legal_system_diagnostics_no_web(container)
                
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



