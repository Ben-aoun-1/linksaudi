#!/usr/bin/env python3
# market_report_system.py - Enhanced market report system with proper encoding handling
import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from chardet.universaldetector import UniversalDetector

class MarketReportSystem:
    """Enhanced market report system with proper encoding handling"""
    
    def __init__(self, rag_engine=None, web_search=None, report_generator=None, pdf_exporter=None):
        self.rag_engine = rag_engine
        self.web_search = web_search
        self.report_generator = report_generator
        self.pdf_exporter = pdf_exporter
        self.reports_dir = "market_reports"
        
        # Create reports directory if it doesn't exist
        try:
            os.makedirs(self.reports_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating reports directory: {e}")
    
    def create_market_report(self, title: str, sectors: List[str], geography: str, 
                            enhance_with_web: bool = True, include_visuals: bool = True) -> Dict[str, Any]:
        """Create a comprehensive market report with proper encoding handling"""
        
        print(f"Creating market report: {title}")
        
        # Generate the report
        if self.report_generator:
            report_data = self.report_generator.generate_market_report(
                title=title,
                sectors=sectors,
                geography=geography,
                enhance_with_web=enhance_with_web,
                include_visuals=include_visuals
            )
        else:
            # Create a minimal report structure if no generator is available
            report_data = {
                "title": title,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sectors": sectors,
                "geography": geography,
                "sections": [
                    {
                        "title": "Executive Summary",
                        "content": "This is a placeholder. Please connect a report generator for full functionality.",
                        "subsections": []
                    }
                ],
                "charts": [],
                "sources": []
            }
        
        # Generate a filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = title.lower().replace(" ", "_").replace(",", "").replace(".", "")
        filename = f"{self.reports_dir}/{safe_title}_{timestamp}.json"
        
        # Save the report with proper encoding
        self.save_report(report_data, filename)
        
        # Export to PDF if exporter is available
        if self.pdf_exporter:
            pdf_filename = filename.replace(".json", ".pdf")
            self.pdf_exporter.export_report_to_pdf(report_data, pdf_filename)
        
        return {
            "report_data": report_data,
            "json_file": filename,
            "pdf_file": filename.replace(".json", ".pdf") if self.pdf_exporter else None
        }
    
    def create_report_from_chat(self, chat_messages: List[Dict], title: str = None, 
                               sectors: List[str] = None, geography: str = None) -> Dict[str, Any]:
        """Create a report based on chat conversation with proper formatting for executives"""
        
        # Extract information from chat history if not provided
        if not title or not sectors or not geography:
            # Combine all messages
            all_messages = " ".join([msg["content"] for msg in chat_messages])
            
            # Identify potential sectors of interest if not provided
            if not sectors:
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
                
                sectors = potential_sectors
            
            # Try to identify geography if not provided
            if not geography:
                geography = "Saudi Arabia"
                geo_keywords = [
                    "Saudi Arabia", "UAE", "Dubai", "Abu Dhabi", "Qatar", "Kuwait", "Bahrain", "Oman", 
                    "Middle East", "GCC", "MENA"
                ]
                
                for geo in geo_keywords:
                    if geo.lower() in all_messages.lower():
                        geography = geo
                        break
            
            # Generate title if not provided
            if not title:
                title = f"{geography} {', '.join(sectors[:2])} Market Analysis"
        
        # Extract user questions to understand key topics
        user_questions = [msg["content"] for msg in chat_messages if msg["role"] == "user"]
        
        # Generate report based on conversation
        return self.create_market_report(
            title=title,
            sectors=sectors,
            geography=geography,
            enhance_with_web=True,  # Always use web data for more accurate reports
            include_visuals=True     # Always include visuals for executive reports
        )
    
    def save_report(self, report_data: Dict[str, Any], filename: str) -> bool:
        """Save a report to a JSON file with proper encoding handling"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Save with UTF-8 encoding and ensure_ascii=False
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"Report saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False
    
    def load_report(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load a report from a JSON file with proper encoding handling"""
        try:
            # Try UTF-8 first
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
            except UnicodeDecodeError:
                # Fall back to latin-1 if UTF-8 fails
                with open(filename, 'r', encoding='latin-1') as f:
                    report_data = json.load(f)
            
            print(f"Report loaded from {filename}")
            return report_data
        except Exception as e:
            print(f"Error loading report: {e}")
            return None
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """List all available reports with proper encoding handling"""
        reports = []
        
        try:
            for filename in os.listdir(self.reports_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.reports_dir, filename)
                    
                    try:
                        # Try UTF-8 first
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                report_data = json.load(f)
                        except UnicodeDecodeError:
                            # Fall back to latin-1 if UTF-8 fails
                            with open(file_path, 'r', encoding='latin-1') as f:
                                report_data = json.load(f)
                        
                        reports.append({
                            "filename": filename,
                            "file_path": file_path,
                            "title": report_data.get("title", "Untitled Report"),
                            "date": report_data.get("date", "Unknown date"),
                            "sectors": report_data.get("sectors", []),
                            "geography": report_data.get("geography", "Unknown geography")
                        })
                    except Exception as e:
                        print(f"Error loading report {filename}: {e}")
        except Exception as e:
            print(f"Error listing reports: {e}")
        
        # Sort by date (newest first)
        reports.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        return reports
    
    def delete_report(self, filename: str) -> bool:
        """Delete a report with proper error handling"""
        try:
            file_path = filename if os.path.isabs(filename) else os.path.join(self.reports_dir, filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                
                # Also delete PDF if it exists
                pdf_path = file_path.replace(".json", ".pdf")
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                
                print(f"Report deleted: {filename}")
                return True
            else:
                print(f"Report not found: {filename}")
                return False
        except Exception as e:
            print(f"Error deleting report: {e}")
            return False
    
    def search_reports(self, query: str) -> List[Dict[str, Any]]:
        """Search reports for a query with proper encoding handling"""
        query = query.lower()
        results = []
        
        # Get all reports
        all_reports = self.list_reports()
        
        for report in all_reports:
            # Check if query matches title, sectors, or geography
            title = report.get("title", "").lower()
            sectors = [s.lower() for s in report.get("sectors", [])]
            geography = report.get("geography", "").lower()
            
            if query in title or any(query in sector for sector in sectors) or query in geography:
                results.append(report)
                continue
            
            # If no match in metadata, check content
            try:
                report_data = self.load_report(report.get("file_path"))
                if report_data:
                    # Search in section content
                    for section in report_data.get("sections", []):
                        section_title = section.get("title", "").lower()
                        section_content = section.get("content", "").lower()
                        
                        if query in section_title or query in section_content:
                            results.append(report)
                            break
                        
                        # Search in subsections
                        for subsection in section.get("subsections", []):
                            subsection_title = subsection.get("title", "").lower()
                            subsection_content = subsection.get("content", "").lower()
                            
                            if query in subsection_title or query in subsection_content:
                                results.append(report)
                                break
            except Exception as e:
                print(f"Error searching report {report.get('filename')}: {e}")
        
        return results

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