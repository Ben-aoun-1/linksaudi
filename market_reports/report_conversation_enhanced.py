#!/usr/bin/env python3
# report_conversation_enhanced.py - Enhanced conversational interface for reports with proper encoding handling
import os
import json
import time
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import re
from chardet.universaldetector import UniversalDetector

class ReportConversation:
    """Enhanced conversational interface for reports with proper encoding handling"""
    
    def __init__(self, rag_engine=None):
        self.rag_engine = rag_engine
        self.conversation_history = []
        self.current_report = None
    
    def load_report(self, report_path: str) -> bool:
        """Load a report with proper encoding handling"""
        try:
            # Try UTF-8 first
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    self.current_report = json.load(f)
            except UnicodeDecodeError:
                # Fall back to latin-1 if UTF-8 fails
                with open(report_path, 'r', encoding='latin-1') as f:
                    self.current_report = json.load(f)
            
            # Reset conversation history when loading a new report
            self.conversation_history = []
            
            return True
        except Exception as e:
            print(f"Error loading report: {e}")
            return False
    
    def get_report_summary(self) -> str:
        """Get a summary of the current report"""
        if not self.current_report:
            return "No report is currently loaded."
        
        # Extract basic report information
        title = self.current_report.get("title", "Untitled Report")
        date = self.current_report.get("date", "Unknown date")
        sectors = ", ".join(self.current_report.get("sectors", ["Unknown sector"]))
        geography = self.current_report.get("geography", "Unknown geography")
        
        # Count sections and charts
        section_count = len(self.current_report.get("sections", []))
        chart_count = len(self.current_report.get("charts", []))
        
        # Create summary
        summary = f"""
Report: {title}
Date: {date}
Sectors: {sectors}
Geography: {geography}
Sections: {section_count}
Charts: {chart_count}

Available sections:
"""
        
        # Add section titles
        for i, section in enumerate(self.current_report.get("sections", [])):
            summary += f"{i+1}. {section.get('title', 'Untitled Section')}\n"
            
            # Add subsection titles if any
            for j, subsection in enumerate(section.get("subsections", [])):
                summary += f"   {i+1}.{j+1}. {subsection.get('title', 'Untitled Subsection')}\n"
        
        return summary
    
    def get_section_content(self, section_index: int) -> str:
        """Get the content of a specific section with proper encoding handling"""
        if not self.current_report:
            return "No report is currently loaded."
        
        sections = self.current_report.get("sections", [])
        
        if section_index < 0 or section_index >= len(sections):
            return f"Invalid section index. Please choose a number between 1 and {len(sections)}."
        
        section = sections[section_index]
        title = section.get("title", "Untitled Section")
        content = section.get("content", "No content available.")
        
        # Format the content
        formatted_content = f"## {title}\n\n{content}\n\n"
        
        # Add subsections if any
        for subsection in section.get("subsections", []):
            sub_title = subsection.get("title", "Untitled Subsection")
            sub_content = subsection.get("content", "No content available.")
            formatted_content += f"### {sub_title}\n\n{sub_content}\n\n"
        
        # Add charts if any
        for chart in section.get("charts", []):
            chart_title = chart.get("title", "Untitled Chart")
            chart_description = chart.get("description", "No description available.")
            formatted_content += f"**{chart_title}**\n{chart_description}\n\n"
        
        return formatted_content
    
    def ask_question(self, question: str) -> str:
        """Ask a question about the report with proper encoding handling"""
        if not self.current_report:
            return "No report is currently loaded. Please load a report first."
        
        # Add question to conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Generate context from the report
        context = self._generate_context_from_report()
        
        # Use RAG to answer the question
        if self.rag_engine:
            # Create a prompt with the question, context, and conversation history
            prompt = self._create_prompt(question, context)
            
            # Generate response
            response = self.rag_engine.generate_rag_response(prompt)
        else:
            response = "I don't have enough information to answer that question. Please connect a RAG engine to enable question answering."
        
        # Add response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def _generate_context_from_report(self) -> str:
        """Generate context from the current report with proper encoding handling"""
        if not self.current_report:
            return ""
        
        context = f"Report Title: {self.current_report.get('title', 'Untitled Report')}\n"
        context += f"Date: {self.current_report.get('date', 'Unknown date')}\n"
        context += f"Sectors: {', '.join(self.current_report.get('sectors', ['Unknown sector']))}\n"
        context += f"Geography: {self.current_report.get('geography', 'Unknown geography')}\n\n"
        
        # Add section content
        for section in self.current_report.get("sections", []):
            context += f"Section: {section.get('title', 'Untitled Section')}\n"
            context += f"{section.get('content', 'No content available.')}\n\n"
            
            # Add subsection content
            for subsection in section.get("subsections", []):
                context += f"Subsection: {subsection.get('title', 'Untitled Subsection')}\n"
                context += f"{subsection.get('content', 'No content available.')}\n\n"
        
        return context
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create a prompt for the RAG engine with proper encoding handling"""
        # Include recent conversation history (last 3 exchanges)
        recent_history = self.conversation_history[-6:] if len(self.conversation_history) > 6 else self.conversation_history
        
        conversation_context = ""
        for message in recent_history[:-1]:  # Exclude the current question
            role = message["role"]
            content = message["content"]
            conversation_context += f"{role.capitalize()}: {content}\n\n"
        
        prompt = f"""
You are an expert market analyst specializing in Saudi Arabian markets. Answer the following question based on the provided report context and conversation history.

Conversation History:
{conversation_context}

Question: {question}

Report Context:
{context}

Provide a detailed, informative response based solely on the information in the report context. If the context doesn't contain enough information to answer the question fully, acknowledge the limitations of the available information. Use a professional, analytical tone suitable for investment reports.
"""
        
        return prompt
    
    def save_conversation(self, filename: str) -> bool:
        """Save the conversation history to a JSON file with proper encoding handling"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Save with UTF-8 encoding and ensure_ascii=False
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "report_title": self.current_report.get("title", "Untitled Report") if self.current_report else None,
                    "conversation": self.conversation_history
                }, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    def load_conversation(self, filename: str) -> bool:
        """Load conversation history from a JSON file with proper encoding handling"""
        try:
            # Try UTF-8 first
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except UnicodeDecodeError:
                # Fall back to latin-1 if UTF-8 fails
                with open(filename, 'r', encoding='latin-1') as f:
                    data = json.load(f)
            
            self.conversation_history = data.get("conversation", [])
            
            return True
        except Exception as e:
            print(f"Error loading conversation: {e}")
            return False
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history"""
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history"""
        self.conversation_history = []

def detect_file_encoding(filename: str) -> str:
    """Detect the encoding of a file"""
    detector = UniversalDetector()
    try:
        with open(filename, 'rb') as f:
            for line in f:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
        
        return detector.result['encoding'] or 'utf-8'
    except Exception as e:
        print(f"Error detecting encoding: {e}")
        return 'utf-8'  # Default to UTF-8 on error

def read_file_with_encoding(filename: str) -> Optional[str]:
    """Read a file with automatic encoding detection"""
    try:
        # Try to detect encoding
        encoding = detect_file_encoding(filename)
        
        # Try to read with detected encoding
        try:
            with open(filename, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # If that fails, try UTF-8
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # If UTF-8 fails, fall back to latin-1 which should always work
                with open(filename, 'r', encoding='latin-1') as f:
                    return f.read()
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        return None

def write_file_with_encoding(filename: str, content: str) -> bool:
    """Write content to a file with UTF-8 encoding"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Write with UTF-8 encoding
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error writing file {filename}: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    class MockRAGEngine:
        def generate_rag_response(self, prompt):
            return f"This is a mock response to: {prompt[:50]}..."
    
    # Initialize the conversation interface
    conversation = ReportConversation(rag_engine=MockRAGEngine())
    
    # Create a sample report
    sample_report = {
        "title": "Saudi Arabia Technology Market Report 2023",
        "date": "2023-04-24",
        "sectors": ["Software", "Hardware", "IT Services"],
        "geography": "Saudi Arabia",
        "sections": [
            {
                "title": "Executive Summary",
                "content": "This is a sample executive summary of the technology market in Saudi Arabia.",
                "subsections": []
            },
            {
                "title": "Software Sector Analysis",
                "content": "The software sector in Saudi Arabia is growing rapidly.",
                "subsections": [
                    {
                        "title": "Market Size and Growth",
                        "content": "The software market size is estimated at $5 billion with 15% annual growth."
                    }
                ]
            }
        ]
    }
    
    # Save the sample report with proper encoding
    with open("sample_report.json", 'w', encoding='utf-8') as f:
        json.dump(sample_report, f, ensure_ascii=False, indent=2)
    
    # Load the report
    conversation.load_report("sample_report.json")
    
    # Get report summary
    print(conversation.get_report_summary())
    
    # Ask a question
    response = conversation.ask_question("What is the market size of the software sector?")
    print(f"Response: {response}")
    
    # Save the conversation with proper encoding
    conversation.save_conversation("sample_conversation.json")