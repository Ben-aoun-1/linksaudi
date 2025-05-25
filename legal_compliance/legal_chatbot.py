#!/usr/bin/env python3
# legal_compliance/legal_chatbot.py - Complete Legal Chatbot

import os
import json
import time
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("legal_compliance")

# Create data directories
os.makedirs("data", exist_ok=True)
os.makedirs("data/legal_conversations", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Utility functions
def save_json_with_encoding(filename: str, data: Any, indent: int = 2) -> bool:
    """Save JSON data with proper encoding"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON {filename}: {e}")
        return False

def load_json_with_encoding(filename: str) -> Optional[Any]:
    """Load JSON data with proper encoding"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON {filename}: {e}")
        return None

class LegalChatbot:
    """Legal compliance chatbot with conversation management"""
    
    def __init__(self, legal_rag_engine=None, web_search_engine=None):
        self.legal_rag_engine = legal_rag_engine
        self.web_search_engine = web_search_engine
        self.conversations_dir = "data/legal_conversations"
        self.current_session = None
        self.session_history = []
        
        # Create conversations directory
        os.makedirs(self.conversations_dir, exist_ok=True)
        
        # Legal chatbot configuration
        self.max_history_length = 20  # Keep last 20 exchanges
        self.enable_web_enhancement = True
        self.disclaimer_shown = False
        
        logger.info("Legal Chatbot initialized")
    
    def start_new_session(self, user_id: str = None) -> str:
        """Start a new legal consultation session"""
        session_id = str(uuid.uuid4())
        self.current_session = {
            "session_id": session_id,
            "user_id": user_id or "anonymous",
            "start_time": datetime.now().isoformat(),
            "messages": [],
            "metadata": {
                "queries_count": 0,
                "document_types_consulted": set(),
                "jurisdictions_consulted": set()
            }
        }
        
        # Add welcome message
        welcome_message = self._get_welcome_message()
        self.current_session["messages"].append({
            "role": "assistant",
            "content": welcome_message,
            "timestamp": datetime.now().isoformat(),
            "message_type": "welcome"
        })
        
        logger.info(f"New legal session started: {session_id}")
        return session_id
    
    def ask_legal_question(self, question: str, document_type: str = None, 
                          jurisdiction: str = None, include_web_search: bool = None) -> Dict[str, Any]:
        """Ask a legal question and get a response"""
        try:
            if not self.current_session:
                self.start_new_session()
            
            # Log the question
            logger.info(f"Legal question in session {self.current_session['session_id']}: {question}")
            
            # Add user message to session
            user_message = {
                "role": "user",
                "content": question,
                "timestamp": datetime.now().isoformat(),
                "filters": {
                    "document_type": document_type,
                    "jurisdiction": jurisdiction
                },
                "message_type": "question"
            }
            self.current_session["messages"].append(user_message)
            
            # Generate response using legal RAG
            if self.legal_rag_engine:
                try:
                    rag_response = self.legal_rag_engine.generate_legal_response(
                        query=question,
                        document_type=document_type,
                        jurisdiction=jurisdiction,
                        include_citations=True
                    )
                    
                    base_response = rag_response.get("response", "")
                    citations = rag_response.get("citations", [])
                    documents_used = rag_response.get("documents", [])
                except Exception as e:
                    logger.error(f"Error with legal RAG: {e}")
                    base_response = f"I can provide general legal guidance on: {question}\n\nThis is a basic response. For full legal analysis, please ensure all dependencies are properly configured."
                    citations = []
                    documents_used = []
            else:
                base_response = f"Legal guidance on: {question}\n\nThis is a basic legal response. Please ensure the legal RAG engine is properly configured for detailed analysis."
                citations = []
                documents_used = []
            
            # Enhance with web search if requested
            web_sources = []
            if (include_web_search or self.enable_web_enhancement) and self.web_search_engine:
                try:
                    web_results = self.web_search_engine.research_topic(
                        query=f"{question} Saudi Arabia law",
                        context="legal compliance regulation",
                        market="Saudi Arabia",
                        top_n=2
                    )
                    
                    if "data" in web_results and web_results["data"]:
                        web_sources = web_results["data"]
                        
                        # Add web information to response
                        web_content = "\n\n**Latest Legal Developments:**\n"
                        for source in web_sources[:1]:  # Limit to 1 web source for legal accuracy
                            web_content += f"• Recent Update: {source.get('title', 'Legal Update')}\n"
                            web_content += f"  Source: {source.get('url', 'Unknown')}\n"
                        
                        base_response += web_content
                
                except Exception as e:
                    logger.warning(f"Web search enhancement failed: {e}")
            
            # Add legal disclaimer
            if not self.disclaimer_shown:
                base_response += "\n\n" + self._get_legal_disclaimer()
                self.disclaimer_shown = True
            
            # Create assistant response
            assistant_response = {
                "role": "assistant",
                "content": base_response,
                "timestamp": datetime.now().isoformat(),
                "message_type": "legal_response",
                "metadata": {
                    "documents_consulted": len(documents_used),
                    "citations_provided": len(citations),
                    "web_sources_used": len(web_sources),
                    "document_types": list(set([doc.get("document_type", "") for doc in documents_used])),
                    "jurisdictions": list(set([doc.get("jurisdiction", "") for doc in documents_used]))
                },
                "citations": citations,
                "web_sources": web_sources
            }
            
            # Add to session
            self.current_session["messages"].append(assistant_response)
            
            # Update session metadata
            self.current_session["metadata"]["queries_count"] += 1
        
            # FIXED: Check if the values are lists before using update()
            if isinstance(assistant_response.get("metadata", {}).get("document_types"), list):
                self.current_session["metadata"]["document_types_consulted"].update(
                    set(assistant_response["metadata"]["document_types"])  # Convert to set first
                )
            
            if isinstance(assistant_response.get("metadata", {}).get("jurisdictions"), list):
                self.current_session["metadata"]["jurisdictions_consulted"].update(
                    set(assistant_response["metadata"]["jurisdictions"])  # Convert to set first
                )
            
            # Keep session history manageable
            if len(self.current_session["messages"]) > self.max_history_length:
                # Keep welcome message and recent messages
                welcome_msg = self.current_session["messages"][0]
                recent_messages = self.current_session["messages"][-(self.max_history_length-1):]
                self.current_session["messages"] = [welcome_msg] + recent_messages
            
            # Auto-save session
            self._save_current_session()
            
            return {
                "response": base_response,
                "session_id": self.current_session["session_id"],
                "message_id": len(self.current_session["messages"]) - 1,
                "citations": citations,
                "web_sources": web_sources,
                "documents_consulted": len(documents_used),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing legal question: {e}")
            
            error_response = {
                "response": f"I encountered an error while processing your legal question: {str(e)}. Please try again or contact support.",
                "session_id": self.current_session["session_id"] if self.current_session else None,
                "error": str(e),
                "success": False
            }
            
            if self.current_session:
                self.current_session["messages"].append({
                    "role": "assistant",
                    "content": error_response["response"],
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "error",
                    "error": str(e)
                })
            
            return error_response
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the current session's conversation history"""
        if not self.current_session:
            return []
        return self.current_session["messages"]
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session"""
        if not self.current_session:
            return {"error": "No active session"}
        
        session = self.current_session
        return {
            "session_id": session["session_id"],
            "start_time": session["start_time"],
            "duration_minutes": self._calculate_session_duration(),
            "queries_count": session["metadata"]["queries_count"],
            "document_types_consulted": list(session["metadata"]["document_types_consulted"]),
            "jurisdictions_consulted": list(session["metadata"]["jurisdictions_consulted"]),
            "total_messages": len(session["messages"])
        }
    
    def end_session(self) -> Dict[str, Any]:
        """End the current session and return summary"""
        if not self.current_session:
            return {"error": "No active session"}
        
        # Add session end time
        self.current_session["end_time"] = datetime.now().isoformat()
        
        # Save final session state
        self._save_current_session()
        
        # Get summary
        summary = self.get_session_summary()
        
        # Clear current session
        session_id = self.current_session["session_id"]
        self.current_session = None
        self.disclaimer_shown = False
        
        logger.info(f"Legal session ended: {session_id}")
        return summary
    
    def list_previous_sessions(self, user_id: str = None) -> List[Dict]:
        """List previous legal consultation sessions"""
        try:
            sessions = []
            for filename in os.listdir(self.conversations_dir):
                if filename.startswith("legal_session_") and filename.endswith(".json"):
                    session_data = load_json_with_encoding(
                        os.path.join(self.conversations_dir, filename)
                    )
                    
                    if session_data:
                        # Filter by user_id if specified
                        if user_id and session_data.get("user_id") != user_id:
                            continue
                        
                        sessions.append({
                            "session_id": session_data["session_id"],
                            "start_time": session_data["start_time"],
                            "end_time": session_data.get("end_time", "Active"),
                            "queries_count": session_data["metadata"]["queries_count"],
                            "user_id": session_data.get("user_id", "anonymous")
                        })
            
            # Sort by start time (newest first)
            sessions.sort(key=lambda x: x["start_time"], reverse=True)
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []
    
    def get_legal_categories(self) -> List[str]:
        """Get available legal categories"""
        return [
            "Corporate Law", 
            "Contract Law", 
            "Regulatory Compliance", 
            "Employment Law", 
            "Commercial Law",
            "Banking Law",
            "Real Estate Law",
            "Intellectual Property",
            "Tax Law",
            "International Trade"
        ]
    
    def get_available_jurisdictions(self) -> List[str]:
        """Get available jurisdictions"""
        return [
            "Saudi Arabia", 
            "GCC", 
            "International",
            "UAE",
            "Qatar",
            "Kuwait",
            "Bahrain",
            "Oman"
        ]
    
    def export_session_report(self, session_id: str = None) -> Dict[str, Any]:
        """Export a detailed session report"""
        session_to_export = self.current_session
        
        if session_id:
            # Load specific session
            if not self.load_session(session_id):
                return {"error": f"Session {session_id} not found"}
            session_to_export = self.current_session
        
        if not session_to_export:
            return {"error": "No session to export"}
        
        try:
            # Create comprehensive report
            report = {
                "session_info": {
                    "session_id": session_to_export["session_id"],
                    "user_id": session_to_export.get("user_id", "anonymous"),
                    "start_time": session_to_export["start_time"],
                    "end_time": session_to_export.get("end_time", "Active"),
                    "duration_minutes": self._calculate_session_duration()
                },
                "statistics": {
                    "total_messages": len(session_to_export["messages"]),
                    "questions_asked": session_to_export["metadata"]["queries_count"],
                    "document_types_consulted": list(session_to_export["metadata"]["document_types_consulted"]),
                    "jurisdictions_consulted": list(session_to_export["metadata"]["jurisdictions_consulted"])
                },
                "conversation_summary": [],
                "generated_at": datetime.now().isoformat()
            }
            
            # Add conversation summary (questions and key points)
            for message in session_to_export["messages"]:
                if message["message_type"] in ["question", "legal_response"]:
                    summary_item = {
                        "timestamp": message["timestamp"],
                        "type": message["message_type"],
                        "content_preview": message["content"][:300] + ("..." if len(message["content"]) > 300 else ""),
                    }
                    
                    if message["message_type"] == "legal_response":
                        summary_item["citations_count"] = len(message.get("citations", []))
                        summary_item["documents_consulted"] = message.get("metadata", {}).get("documents_consulted", 0)
                    
                    report["conversation_summary"].append(summary_item)
            
            return report
            
        except Exception as e:
            logger.error(f"Error exporting session report: {e}")
            return {"error": f"Failed to export report: {str(e)}"}
    
    def load_session(self, session_id: str) -> bool:
        """Load a previous session"""
        try:
            filename = os.path.join(self.conversations_dir, f"legal_session_{session_id}.json")
            session_data = load_json_with_encoding(filename)
            
            if session_data:
                # Convert lists back to sets
                session_data["metadata"]["document_types_consulted"] = set(
                    session_data["metadata"]["document_types_consulted"]
                )
                session_data["metadata"]["jurisdictions_consulted"] = set(
                    session_data["metadata"]["jurisdictions_consulted"]
                )
                
                self.current_session = session_data
                logger.info(f"Loaded legal session: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return False
    
    def _save_current_session(self) -> bool:
        """Save the current session to disk"""
        if not self.current_session:
            return False
        
        try:
            # Convert sets to lists for JSON serialization
            session_copy = self.current_session.copy()
            session_copy["metadata"]["document_types_consulted"] = list(
                session_copy["metadata"]["document_types_consulted"]
            )
            session_copy["metadata"]["jurisdictions_consulted"] = list(
                session_copy["metadata"]["jurisdictions_consulted"]
            )
            
            filename = os.path.join(
                self.conversations_dir, 
                f"legal_session_{self.current_session['session_id']}.json"
            )
            
            return save_json_with_encoding(filename, session_copy)
            
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False
    
    def _get_welcome_message(self) -> str:
        """Get the welcome message for new sessions"""
        return """Welcome to the Legal Compliance Assistant! 

I'm here to help you with legal questions related to Saudi Arabian law and regulations. I can assist with:

• Corporate law and business regulations
• Contract law and commercial agreements  
• Employment law and labor regulations
• Regulatory compliance requirements
• Commercial licensing and permits
• International trade regulations

Please note that I provide general legal information based on available legal documents and should not replace professional legal advice. For specific legal matters, always consult with a qualified attorney.

How can I assist you with your legal question today?"""
    
    def _get_legal_disclaimer(self) -> str:
        """Get the legal disclaimer text"""
        return """
**Legal Disclaimer:** This information is provided for general guidance only and does not constitute legal advice. Laws and regulations may change, and specific circumstances may affect how laws apply to your situation. For specific legal matters, please consult with a qualified attorney licensed to practice in the relevant jurisdiction."""
    
    def _calculate_session_duration(self) -> float:
        """Calculate session duration in minutes"""
        if not self.current_session:
            return 0
        
        start_time = datetime.fromisoformat(self.current_session["start_time"])
        current_time = datetime.now()
        duration = (current_time - start_time).total_seconds() / 60
        return round(duration, 2)