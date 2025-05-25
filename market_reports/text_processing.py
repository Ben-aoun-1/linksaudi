#!/usr/bin/env python3
# text_processing.py - Centralized text processing module

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger("market_intelligence")

class TextProcessor:
    """Centralized text processing functionality for the application"""
    
    def __init__(self):
        # Initialize known AI phrases to remove
        self.ai_phrases = [
            "I don't have specific information about",
            "Based on the available information,",
            "I don't have access to",
            "I don't have current data on",
            "The information provided doesn't",
            "Based on the context provided,",
            "I don't have enough information to",
            "Without more specific information,",
            "The context doesn't mention",
            "I don't have the specific details",
            "As an AI assistant",
            "As an AI language model",
            "As a language model",
            "I don't have access to real-time data",
            "I cannot provide specific",
            "I cannot confirm",
            "My knowledge is limited to",
            "Beyond my training data",
            "My training data only goes up to",
            "I apologize, but I don't have",
            "I cannot browse the internet",
            "I'm not able to access",
            "I'm not able to provide",
            "I'm unable to provide",
            "I can't provide specific"
        ]
        
        # AI role identification patterns
        self.ai_role_patterns = [
            r"As an AI assistant,?\s",
            r"As an? (market\s)?analyst,?\s",
            r"As an? language model,?\s",
        ]
        
        # Sector keywords for topic detection
        self.sector_keywords = {
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
        
        # Geography keywords for region detection
        self.geography_keywords = {
            "Saudi Arabia": ["saudi", "saudi arabia", "ksa", "kingdom"],
            "UAE": ["uae", "emirates", "dubai", "abu dhabi"],
            "Qatar": ["qatar", "doha"],
            "Kuwait": ["kuwait"],
            "Bahrain": ["bahrain"],
            "Oman": ["oman"],
            "Egypt": ["egypt"],
            "GCC": ["gcc", "gulf cooperation council"],
            "MENA": ["mena", "middle east"]
        }
    
    def clean_ai_language(self, content: str) -> str:
        """
        Clean AI/LLM-specific language to make content more professional
        
        Args:
            content: The text content to clean
        
        Returns:
            Cleaned content with AI-specific language removed
        """
        if not content:
            return ""
        
        result = content
        
        # Remove phrases that indicate limited knowledge
        for phrase in self.ai_phrases:
            result = result.replace(phrase, "")
        
        # Remove phrases like "As an AI assistant" or mentions of AI
        for pattern in self.ai_role_patterns:
            result = re.sub(pattern, "", result)
        
        # Clean up double spaces and line breaks
        result = re.sub(r"\s{2,}", " ", result)
        result = re.sub(r"\n{3,}", "\n\n", result)
        
        # Fix any capitalization issues after removals
        sentences = re.split(r'(?<=[.!?])\s+', result)
        fixed_sentences = [s[0].upper() + s[1:] if len(s) > 1 else s for s in sentences]
        result = " ".join(fixed_sentences)
        
        return result.strip()
    
    def extract_html_content(self, html_content: str) -> str:
        """
        Extract clean text from HTML content with proper encoding handling
        
        Args:
            html_content: HTML content to extract text from
        
        Returns:
            Extracted plain text
        """
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser', from_encoding='utf-8')
            
            # Remove script and style elements
            for element in soup(['script', 'style']):
                element.extract()
                
            # Get text
            text = soup.get_text()
            
            # Handle line breaks and white space
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting HTML content: {e}")
            return html_content  # Return original content on error
    
    def extract_sectors_from_text(self, text: str) -> List[str]:
        """
        Extract sector keywords from text
        
        Args:
            text: The text to analyze
        
        Returns:
            List of detected sectors
        """
        text_lower = text.lower()
        sectors = []
        
        # Check for exact phrase matches first
        for sector, keywords in self.sector_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    sectors.append(sector)
                    break  # Only add sector once
        
        # Remove duplicates while preserving order
        sectors = list(dict.fromkeys(sectors))
        
        # Special handling for electric vehicles
        if any(keyword in text_lower for keyword in ["electric vehicle", "electric car", "ev", "electrical vehicle"]):
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
        
        return sectors
    
    def extract_geography_from_text(self, text: str, default: str = "Saudi Arabia") -> str:
        """
        Extract geography/region from text
        
        Args:
            text: The text to analyze
            default: Default geography if none detected
        
        Returns:
            Detected geography or default
        """
        text_lower = text.lower()
        
        for region, keywords in self.geography_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return region
        
        return default
    
    def analyze_query_for_market_report(self, query: str) -> Tuple[List[str], str, str]:
        """
        Analyze query to extract sectors, geography, and generate title
        
        Args:
            query: User query to analyze
        
        Returns:
            Tuple of (sectors list, geography string, title string)
        """
        # Extract sectors
        sectors = self.extract_sectors_from_text(query)
        
        # Extract geography
        geography = self.extract_geography_from_text(query)
        
        # Identify query intent to create an appropriate title
        query_lower = query.lower()
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
        main_sector = sectors[0] if sectors else "Market"
        
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
    
    def extract_report_summary(self, report_data: Dict) -> str:
        """
        Extract a summary from the generated report for chat display
        
        Args:
            report_data: The report data dictionary
        
        Returns:
            A concise summary of the report
        """
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
    
    def format_json_for_display(self, json_data: Dict, indent: int = 2) -> str:
        """
        Format JSON data for display in the UI
        
        Args:
            json_data: Dictionary data to format
            indent: Indentation level
        
        Returns:
            Formatted JSON string
        """
        import json
        try:
            return json.dumps(json_data, ensure_ascii=False, indent=indent)
        except Exception as e:
            logger.error(f"Error formatting JSON: {e}")
            return str(json_data)

# Create a singleton instance
text_processor = TextProcessor()

if __name__ == "__main__":
    # Self-test
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Testing text_processing.py")
    
    # Test cleaning AI language
    test_text = "As an AI assistant, I don't have access to specific information about the latest market trends."
    cleaned = text_processor.clean_ai_language(test_text)
    logger.info(f"Original: '{test_text}'")
    logger.info(f"Cleaned: '{cleaned}'")
    
    # Test sector extraction
    test_query = "What is the current state of electric vehicles investment in Saudi Arabia?"
    sectors = text_processor.extract_sectors_from_text(test_query)
    logger.info(f"Sectors detected in '{test_query}': {sectors}")
    
    # Test query analysis
    sectors, geography, title = text_processor.analyze_query_for_market_report(test_query)
    logger.info(f"Query analysis for '{test_query}':")
    logger.info(f"  Sectors: {sectors}")
    logger.info(f"  Geography: {geography}")
    logger.info(f"  Generated title: {title}")
    
    logger.info("Text processing tests complete")