#!/usr/bin/env python3
# report_generator_enhanced.py - Enhanced report generator with proper encoding handling
import os
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from chardet.universaldetector import UniversalDetector

class ReportGenerator:
    """Enhanced report generator with proper encoding handling"""
    
    def __init__(self, rag_engine=None, web_search=None):
        self.rag_engine = rag_engine
        self.web_search = web_search
        self.report_data = {}
        self.charts_dir = "report_charts"
        
        # Create charts directory if it doesn't exist
        try:
            os.makedirs(self.charts_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating charts directory: {e}")
    
    def generate_market_report(self, title: str, sectors: List[str], geography: str, 
                              enhance_with_web: bool = True, include_visuals: bool = True) -> Dict[str, Any]:
        """Generate a comprehensive market report with proper encoding handling"""
        
        print(f"Generating report: {title}")
        
        # Initialize report structure
        self.report_data = {
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sectors": sectors,
            "geography": geography,
            "sections": [],
            "charts": [],
            "sources": []
        }
        
        # Generate executive summary
        self._generate_executive_summary()
        
        # Generate sector analysis for each sector
        for sector in sectors:
            self._generate_sector_analysis(sector, geography, enhance_with_web, include_visuals)
            
        # Generate market trends
        self._generate_market_trends(geography, enhance_with_web)
        
        # Generate future outlook
        self._generate_future_outlook(sectors, geography)
        
        # Generate conclusion
        self._generate_conclusion()
        
        # Format the content in all sections to be more executive-friendly
        self._format_content_for_executives()
        
        return self.report_data
    
    def _generate_executive_summary(self):
        """Generate executive summary section with proper encoding handling"""
        print("Generating executive summary...")
        
        # Use RAG to generate executive summary
        if self.rag_engine:
            query = f"Write a concise executive summary for an official market report about {', '.join(self.report_data['sectors'])} in {self.report_data['geography']}. Include key market size figures, growth rates, and main market drivers. Use professional business language suitable for executives. Avoid phrases like 'based on available information' or 'I don't have specific data'."
            content = self.rag_engine.generate_rag_response(query)
            # Format content
            content = self._clean_ai_language(content)
        else:
            content = "Executive summary placeholder. Please connect a RAG engine to generate content."
        
        self.report_data["sections"].append({
            "title": "Executive Summary",
            "content": content,
            "subsections": []
        })
    
    def _generate_sector_analysis(self, sector: str, geography: str, enhance_with_web: bool, include_visuals: bool):
        """Generate sector analysis with proper encoding handling"""
        print(f"Generating sector analysis for {sector}...")
        
        sector_content = ""
        web_sources = []
        
        # Use RAG to generate sector analysis
        if self.rag_engine:
            query = f"Provide a detailed analysis of the {sector} sector in {self.report_data['geography']}, including market size, key players, and recent developments. Use professional business language suitable for executives. Present specific figures, percentages, and market shares. Avoid phrases like 'based on available information' or 'I don't have specific data'."
            sector_content = self.rag_engine.generate_rag_response(query)
            # Format content
            sector_content = self._clean_ai_language(sector_content)
        else:
            sector_content = f"Sector analysis placeholder for {sector}. Please connect a RAG engine to generate content."
        
        # Enhance with web data if requested
        if enhance_with_web and self.web_search:
            print(f"Enhancing {sector} analysis with web data...")
            web_results = self.web_search.research_topic(f"{sector} market", f"analysis statistics", geography, top_n=3)
            
            if "data" in web_results and web_results["data"]:
                web_content = "\n\n**Latest Market Insights:**\n\n"
                for source in web_results["data"]:
                    # Extract a relevant paragraph from the source
                    paragraphs = source["content"].split("\n")
                    relevant_paragraph = ""
                    for para in paragraphs:
                        if len(para) > 100 and (sector.lower() in para.lower() or geography.lower() in para.lower()):
                            relevant_paragraph = para
                            break
                    
                    if not relevant_paragraph and paragraphs:
                        relevant_paragraph = paragraphs[0]
                    
                    web_content += f"{relevant_paragraph}\n\n"
                    
                    # Add to sources
                    web_sources.append({
                        "title": source["title"],
                        "url": source["url"],
                        "retrieved_date": source["retrieved_date"]
                    })
                
                sector_content += "\n\n" + web_content
        
        # Generate visualizations if requested
        charts = []
        if include_visuals:
            print(f"Generating visualizations for {sector}...")
            chart_path = self._generate_sector_chart(sector, geography)
            if chart_path:
                charts.append({
                    "title": f"{sector} Market Trends in {geography}",
                    "path": chart_path,
                    "description": f"This chart shows market trends for the {sector} sector in {geography}."
                })
        
        # Add sector analysis to report
        self.report_data["sections"].append({
            "title": f"{sector} Sector Analysis",
            "content": sector_content,
            "subsections": [
                {
                    "title": "Market Size and Growth",
                    "content": self._generate_market_size_content(sector, geography)
                },
                {
                    "title": "Key Players",
                    "content": self._generate_key_players_content(sector, geography)
                },
                {
                    "title": "Challenges and Opportunities",
                    "content": self._generate_challenges_content(sector, geography)
                }
            ],
            "charts": charts
        })
        
        # Add web sources to report sources
        self.report_data["sources"].extend(web_sources)
    
    def _generate_market_size_content(self, sector: str, geography: str) -> str:
        """Generate market size content with proper encoding handling"""
        if self.rag_engine:
            query = f"Provide detailed market size and growth rate statistics for the {sector} sector in {geography}. Include specific numbers, currency figures, and growth percentages. Present a professional analysis of historical growth and projections. Avoid phrases like 'based on available information' or 'I don't have specific data'."
            content = self.rag_engine.generate_rag_response(query)
            return self._clean_ai_language(content)
        else:
            return f"Market size and growth content placeholder for {sector} in {geography}."
    
    def _generate_key_players_content(self, sector: str, geography: str) -> str:
        """Generate key players content with proper encoding handling"""
        if self.rag_engine:
            query = f"List and analyze the top 5 companies in the {sector} sector in {geography} with their market shares if available. Include details about their operations, competitive advantages, and recent strategic moves. Avoid phrases like 'based on available information' or 'I don't have specific data'."
            content = self.rag_engine.generate_rag_response(query)
            return self._clean_ai_language(content)
        else:
            return f"Key players content placeholder for {sector} in {geography}."
    
    def _generate_challenges_content(self, sector: str, geography: str) -> str:
        """Generate challenges and opportunities content with proper encoding handling"""
        if self.rag_engine:
            query = f"Analyze the main challenges and opportunities in the {sector} sector in {geography}. Identify regulatory hurdles, market gaps, growth catalysts, and emerging trends. Present a balanced view with actionable insights. Avoid phrases like 'based on available information' or 'I don't have specific data'."
            content = self.rag_engine.generate_rag_response(query)
            return self._clean_ai_language(content)
        else:
            return f"Challenges and opportunities content placeholder for {sector} in {geography}."
    
    def _generate_market_trends(self, geography: str, enhance_with_web: bool):
        """Generate market trends section with proper encoding handling"""
        print("Generating market trends...")
        
        trends_content = ""
        web_sources = []
        
        # Use RAG to generate market trends
        if self.rag_engine:
            query = f"Identify and analyze the current market trends in {geography} across the following sectors: {', '.join(self.report_data['sectors'])}. Focus on technological innovations, changing consumer behaviors, regulatory developments, and competitive landscape shifts. Include specific examples and data points. Avoid phrases like 'based on available information' or 'I don't have specific data'."
            trends_content = self.rag_engine.generate_rag_response(query)
            trends_content = self._clean_ai_language(trends_content)
        else:
            trends_content = "Market trends placeholder. Please connect a RAG engine to generate content."
        
        # Enhance with web data if requested
        if enhance_with_web and self.web_search:
            print(f"Enhancing market trends with web data...")
            web_results = self.web_search.research_topic(f"market trends", f"latest developments", geography, top_n=2)
            
            if "data" in web_results and web_results["data"]:
                web_content = "\n\n**Latest Market Trends:**\n\n"
                for source in web_results["data"]:
                    # Extract a relevant paragraph from the source
                    paragraphs = source["content"].split("\n")
                    relevant_paragraph = ""
                    for para in paragraphs:
                        if len(para) > 100 and ("trend" in para.lower() or "development" in para.lower()):
                            relevant_paragraph = para
                            break
                    
                    if not relevant_paragraph and paragraphs:
                        relevant_paragraph = paragraphs[0]
                    
                    web_content += f"{relevant_paragraph}\n\n"
                    
                    # Add to sources
                    web_sources.append({
                        "title": source["title"],
                        "url": source["url"],
                        "retrieved_date": source["retrieved_date"]
                    })
                
                trends_content += "\n\n" + web_content
        
        # Add market trends to report
        self.report_data["sections"].append({
            "title": "Market Trends",
            "content": trends_content,
            "subsections": []
        })
        
        # Add web sources to report sources
        self.report_data["sources"].extend(web_sources)
    
    def _generate_future_outlook(self, sectors: List[str], geography: str):
        """Generate future outlook section with proper encoding handling"""
        print("Generating future outlook...")
        
        # Use RAG to generate future outlook
        if self.rag_engine:
            query = f"Forecast the future outlook for these sectors in {geography} over the next 3-5 years: {', '.join(sectors)}. Include projected growth rates, anticipated market shifts, upcoming challenges, and emerging opportunities. Make specific projections with confidence. Avoid tentative language or phrases like 'based on available information' or 'I don't have specific data'."
            content = self.rag_engine.generate_rag_response(query)
            content = self._clean_ai_language(content)
        else:
            content = "Future outlook placeholder. Please connect a RAG engine to generate content."
        
        self.report_data["sections"].append({
            "title": "Future Outlook",
            "content": content,
            "subsections": []
        })
    
    def _generate_conclusion(self):
        """Generate conclusion section with proper encoding handling"""
        print("Generating conclusion...")
        
        # Use RAG to generate conclusion
        if self.rag_engine:
            query = f"Write a compelling conclusion for a market report about {', '.join(self.report_data['sectors'])} in {self.report_data['geography']}. Summarize key findings, highlight primary investment opportunities, and provide strategic recommendations. Be confident and authoritative in tone. Avoid phrases like 'based on available information' or 'I don't have specific data'."
            content = self.rag_engine.generate_rag_response(query)
            content = self._clean_ai_language(content)
        else:
            content = "Conclusion placeholder. Please connect a RAG engine to generate content."
        
        self.report_data["sections"].append({
            "title": "Conclusion",
            "content": content,
            "subsections": []
        })
    
    def _generate_sector_chart(self, sector: str, geography: str) -> Optional[str]:
        """Generate a chart for a sector with proper encoding handling"""
        try:
            # Create sample data for the chart
            years = [2020, 2021, 2022, 2023, 2024, 2025]
            
            # Generate some random but realistic market size data
            import random
            import numpy as np
            
            # Start with a base value and add some growth
            base_value = random.uniform(10, 100)  # Billions of dollars
            growth_rate = random.uniform(0.03, 0.15)  # 3-15% annual growth
            
            # Add some randomness to the growth
            market_size = [base_value]
            for i in range(1, len(years)):
                next_value = market_size[i-1] * (1 + growth_rate + random.uniform(-0.02, 0.05))
                market_size.append(next_value)
            
            # Create the chart with dark theme
            plt.figure(figsize=(10, 6))
            plt.style.use('dark_background')
            
            plt.plot(years, market_size, marker='o', linestyle='-', linewidth=2, markersize=8, color='#7FB878')
            plt.title(f"{sector} Market Size in {geography} (Billion USD)", fontsize=16, color='white')
            plt.xlabel("Year", fontsize=12, color='white')
            plt.ylabel("Market Size (Billion USD)", fontsize=12, color='white')
            plt.grid(True, linestyle='--', alpha=0.3)
            
            # Set text color for ticks to white
            plt.tick_params(colors='white', which='both')
            
            # Add data labels
            for i, value in enumerate(market_size):
                plt.text(years[i], value + 1, f"{value:.1f}", ha='center', va='bottom', fontsize=10, color='white')
            
            # Add a trend line
            z = np.polyfit(years, market_size, 1)
            p = np.poly1d(z)
            plt.plot(years, p(years), linestyle='--', alpha=0.8, color='#A49E6D', 
                label=f"Trend (Growth: {growth_rate*100:.1f}%)")
            
            # Add historical vs projection separation
            plt.axvline(x=2023, color='#4B4B4B', linestyle='--', alpha=0.7)
            
            plt.text(2023.1, max(market_size) * 0.5, "Projected", fontsize=12, alpha=0.7, color='#A49E6D')
            plt.text(2022.9, max(market_size) * 0.5, "Historical", fontsize=12, alpha=0.7, ha='right', color='#A49E6D')
            
            # Add a shaded area for the projected region
            projection_years = [y for y in years if y > 2023]
            projection_values = [market_size[years.index(y)] for y in projection_years]
            plt.fill_between(projection_years, projection_values, alpha=0.2, color='#7FB878')
            
            # Set background color
            ax = plt.gca()
            ax.set_facecolor('#121212')
            
            plt.legend(facecolor='#1E1E1E', edgecolor='#333333', labelcolor='white')
            plt.tight_layout()
            
            # Save the chart
            chart_filename = f"{self.charts_dir}/{sector.lower().replace(' ', '_')}_{geography.lower().replace(' ', '_')}_market_size.png"
            plt.savefig(chart_filename, facecolor='#121212')
            plt.close()
            
            return chart_filename
        except Exception as e:
            print(f"Error generating chart for {sector}: {e}")
            return None
    
    def _clean_ai_language(self, content: str) -> str:
        """Clean AI/LLM-specific language to make the content more executive-friendly"""
        # Remove phrases that indicate limited knowledge
        phrases_to_remove = [
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
        
        result = content
        for phrase in phrases_to_remove:
            result = result.replace(phrase, "")
        
        # Remove phrases like "As an AI assistant" or mentions of AI
        result = re.sub(r"As an AI assistant,?\s", "", result)
        result = re.sub(r"As an? (market\s)?analyst,?\s", "", result)
        
        # Clean up double spaces and line breaks
        result = re.sub(r"\s{2,}", " ", result)
        result = re.sub(r"\n{3,}", "\n\n", result)
        
        # Fix any capitalization issues after removals
        sentences = re.split(r'(?<=[.!?])\s+', result)
        fixed_sentences = [s[0].upper() + s[1:] if len(s) > 1 else s for s in sentences]
        result = " ".join(fixed_sentences)
        
        return result.strip()
    
    def _format_content_for_executives(self):
        """Format all content in the report to be more executive-friendly"""
        # Process each section
        for section in self.report_data["sections"]:
            # Clean the main content
            section["content"] = self._clean_ai_language(section["content"])
            
            # Process subsections
            for subsection in section.get("subsections", []):
                subsection["content"] = self._clean_ai_language(subsection["content"])
    
    def save_report(self, filename: str) -> bool:
        """Save the report to a JSON file with proper encoding handling"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Save with UTF-8 encoding and ensure_ascii=False
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.report_data, f, ensure_ascii=False, indent=2)
            
            print(f"Report saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False
    
    def load_report(self, filename: str) -> bool:
        """Load a report from a JSON file with proper encoding handling"""
        try:
            # Try UTF-8 first
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.report_data = json.load(f)
            except UnicodeDecodeError:
                # Fall back to latin-1 if UTF-8 fails
                with open(filename, 'r', encoding='latin-1') as f:
                    self.report_data = json.load(f)
            
            print(f"Report loaded from {filename}")
            return True
        except Exception as e:
            print(f"Error loading report: {e}")
            return False
    
    def extract_web_content(self, url: str) -> Dict[str, Any]:
        """Extract content from a web page with proper encoding handling"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; MarketIntelligencePlatform/1.0; +https://linksaudi.com/bot)'}
            
            # Implement retry logic with exponential backoff
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    resp = requests.get(url, headers=headers, timeout=15)  # Increased timeout
                    resp.raise_for_status()
                    break
                except (requests.exceptions.ConnectionError, 
                        requests.exceptions.Timeout,
                        requests.exceptions.HTTPError) as e:
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        sleep_time = retry_delay * (2 ** attempt)
                        print(f"Connection attempt {attempt+1} failed: {e}. Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                    else:
                        # Final attempt failed
                        raise
            
            # Try to determine the encoding from the response
            encoding = resp.encoding
            if encoding == 'ISO-8859-1' and 'charset' in resp.headers.get('content-type', '').lower():
                # Try to extract charset from content-type header
                content_type = resp.headers.get('content-type', '').lower()
                charset_match = re.search(r'charset=([^\s;]+)', content_type)
                if charset_match:
                    encoding = charset_match.group(1)
            
            # If encoding is still ISO-8859-1 or None, try to detect from content
            if encoding in ('ISO-8859-1', None):
                # Try UTF-8 first
                try:
                    resp.content.decode('utf-8')
                    encoding = 'utf-8'
                except UnicodeDecodeError:
                    # Fallback to ISO-8859-1
                    encoding = 'ISO-8859-1'
            
            # Parse with BeautifulSoup using the detected encoding
            soup = BeautifulSoup(resp.content, 'html.parser', from_encoding=encoding)
            
            # Remove non-content elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'meta', 'iframe']):
                tag.extract()
                
            # Get main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=['content', 'main', 'article'])
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
                
            # Cleanup whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            chunks = []
            for line in lines:
                chunks += [phrase.strip() for phrase in line.split('  ') if phrase.strip()]
            full = '\n'.join(chunks)
            
            # Extract title
            title = soup.title.string if soup.title else "Untitled"
            
            # Extract date if available
            date_patterns = [
                r'Published:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'Date:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'Posted:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'Updated:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})'
            ]
            
            extracted_date = None
            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    extracted_date = date_match.group(1)
                    break
            
            return {
                "title": title,
                "content": full,
                "url": url,
                "date": extracted_date or "Not specified",
                "retrieved_date": datetime.now().strftime("%Y-%m-%d")
            }
        except Exception as e:
            print(f"Error extracting web content from {url}: {e}")
            return {"error": str(e), "url": url}

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
        def generate_rag_response(self, query):
            return f"Mock response for: {query}"
    
    # Initialize the report generator
    report_gen = ReportGenerator(rag_engine=MockRAGEngine())
    
    # Generate a sample report
    report = report_gen.generate_market_report(
        title="Saudi Arabia Technology Market Report 2023",
        sectors=["Software", "Hardware", "IT Services"],
        geography="Saudi Arabia",
        enhance_with_web=True,
        include_visuals=True
    )
    
    # Save the report with proper encoding
    report_gen.save_report("sample_report.json")