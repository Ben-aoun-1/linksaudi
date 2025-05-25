#!/usr/bin/env python3
# pdf_exporter_enhanced.py - Enhanced PDF exporter with fixed HTML formatting
import os
import json
import time
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
from datetime import datetime
from chardet.universaldetector import UniversalDetector
from bs4 import BeautifulSoup

class PDFExporter:
    """Enhanced PDF exporter with dark theme styling"""
    
    def __init__(self):
        # Check if required libraries are installed
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            self.reportlab_available = True
        except ImportError:
            print("ReportLab not installed. PDF export will not be available.")
            print("Install with: pip install reportlab")
            self.reportlab_available = False
    
    def export_report_to_pdf(self, report_data: Dict[str, Any], output_path: str) -> bool:
        """Export report to PDF with dark theme styling"""
        if not self.reportlab_available:
            print("ReportLab not installed. Cannot export to PDF.")
            return False
        
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create the PDF document
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Create custom styles with light theme colors (fixing white text issue)
            title_style = ParagraphStyle(
                'TitleStyle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                textColor=colors.black,
                backColor=colors.lightgrey
            )
            
            heading1_style = ParagraphStyle(
                'Heading1Style',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=10,
                textColor=colors.darkgreen
            )
            
            heading2_style = ParagraphStyle(
                'Heading2Style',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=8,
                textColor=colors.darkgreen
            )
            
            normal_style = ParagraphStyle(
                'NormalStyle',
                parent=styles['Normal'],
                textColor=colors.black
            )
            
            # Create a light theme for better readability
            background_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ])
            
            # Create the content elements
            elements = []
            
            # Add title with appropriate background
            # FIX: Remove the extra quotation mark in the font tag
            title_text = report_data.get('title', 'Untitled Report')
            elements.append(Paragraph(f'<font color="black"><b>{title_text}</b></font>', title_style))
            elements.append(Spacer(1, 0.25*inch))
            
            # Add metadata
            date_str = report_data.get('date', datetime.now().strftime("%Y-%m-%d"))
            sectors_str = ', '.join(report_data.get('sectors', ['Unknown']))
            geography = report_data.get('geography', 'Unknown')
            
            metadata_text = f'<font color="black">Date: {date_str}<br/>Sectors: {sectors_str}<br/>Geography: {geography}</font>'
            elements.append(Paragraph(metadata_text, normal_style))
            elements.append(Spacer(1, 0.5*inch))
            
            # Add sections
            for section in report_data.get('sections', []):
                # Section title
                section_title = section.get('title', 'Untitled Section')
                elements.append(Paragraph(f'<font color="darkgreen">{section_title}</font>', heading1_style))
                elements.append(Spacer(1, 0.1*inch))
                
                # Section content
                section_content = section.get('content', '')
                # Split content into paragraphs
                paragraphs = section_content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        # Fix the escape sequence issue in f-string
                        formatted_para = para.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                        elements.append(Paragraph(f'<font color="black">{formatted_para}</font>', normal_style))
                        elements.append(Spacer(1, 0.1*inch))
                
                # Add charts if any
                for chart in section.get('charts', []):
                    chart_path = chart.get('path', '')
                    if chart_path and os.path.exists(chart_path):
                        # Add chart title
                        chart_title = chart.get('title', 'Chart')
                        elements.append(Paragraph(f'<font color="darkgreen">{chart_title}</font>', heading2_style))
                        
                        # Add chart image
                        img = Image(chart_path, width=6*inch, height=4*inch)
                        elements.append(img)
                        
                        # Add chart description
                        chart_desc = chart.get('description', '')
                        if chart_desc:
                            elements.append(Paragraph(f'<font color="black">{chart_desc}</font>', normal_style))
                        
                        elements.append(Spacer(1, 0.2*inch))
                
                # Add subsections
                for subsection in section.get('subsections', []):
                    # Subsection title
                    subsection_title = subsection.get('title', 'Untitled Subsection')
                    elements.append(Paragraph(f'<font color="darkgreen">{subsection_title}</font>', heading2_style))
                    elements.append(Spacer(1, 0.1*inch))
                    
                    # Subsection content
                    subsection_content = subsection.get('content', '')
                    # Split content into paragraphs
                    paragraphs = subsection_content.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            # Fix the escape sequence issue in f-string
                            formatted_para = para.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
                            elements.append(Paragraph(f'<font color="black">{formatted_para}</font>', normal_style))
                            elements.append(Spacer(1, 0.1*inch))
                
                elements.append(Spacer(1, 0.3*inch))
            
            # Add sources if any
            if report_data.get('sources'):
                elements.append(Paragraph('<font color="darkgreen">Sources</font>', heading1_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for i, source in enumerate(report_data.get('sources', [])):
                    source_text = f'{i+1}. {source.get("title", "Untitled")} - {source.get("url", "")}'
                    elements.append(Paragraph(f'<font color="black">{source_text}</font>', normal_style))
                    elements.append(Spacer(1, 0.05*inch))
            
            # Add footer with generation date
            footer_text = f"Generated by LinkSaudi Market Intelligence Platform | {datetime.now().strftime('%Y-%m-%d')}"
            elements.append(Spacer(1, 0.5*inch))
            elements.append(Paragraph(f'<font color="black" size="8">{footer_text}</font>', normal_style))
            
            # Build the PDF
            doc.build(elements)
            
            print(f"PDF exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting PDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_html_content(self, html_content: str) -> str:
        """Extract clean text from HTML content with proper encoding handling"""
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
            print(f"Error extracting HTML content: {e}")
            return html_content  # Return original content on error

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