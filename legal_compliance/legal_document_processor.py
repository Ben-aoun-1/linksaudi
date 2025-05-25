#!/usr/bin/env python3
# legal_compliance/legal_document_processor.py - Legal Document Processing and Analysis

import os
import json
import re
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Set up logging
logger = logging.getLogger("legal_compliance")

class LegalDocumentProcessor:
    """
    Processes legal documents for analysis and indexing
    Handles PDF, Word, and text documents containing legal content
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.doc', '.txt', '.md']
        self.legal_patterns = self._initialize_legal_patterns()
        self.document_cache = {}
        
        # Create processing directories
        os.makedirs("data/legal_documents", exist_ok=True)
        os.makedirs("data/processed_legal", exist_ok=True)
        
        logger.info("Legal Document Processor initialized")
    
    def process_legal_document(self, file_path: str, document_metadata: Dict = None) -> Dict[str, Any]:
        """
        Process a legal document and extract structured information
        
        Args:
            file_path: Path to the legal document
            document_metadata: Optional metadata about the document
            
        Returns:
            Dictionary with processed document information
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Document not found: {file_path}")
            
            file_extension = Path(file_path).suffix.lower()
            if file_extension not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_extension}")
            
            logger.info(f"Processing legal document: {file_path}")
            
            # Generate document hash for caching
            doc_hash = self._generate_document_hash(file_path)
            
            # Check cache
            if doc_hash in self.document_cache:
                logger.info("Returning cached document processing result")
                return self.document_cache[doc_hash]
            
            # Extract text content
            text_content = self._extract_text_content(file_path, file_extension)
            
            # Process legal content
            processed_doc = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_extension': file_extension,
                'document_hash': doc_hash,
                'processed_date': datetime.now().isoformat(),
                'metadata': document_metadata or {},
                'content': {
                    'raw_text': text_content,
                    'cleaned_text': self._clean_legal_text(text_content),
                    'word_count': len(text_content.split()),
                    'character_count': len(text_content)
                },
                'legal_analysis': self._analyze_legal_content(text_content),
                'structure': self._analyze_document_structure(text_content),
                'citations': self._extract_legal_citations(text_content),
                'key_terms': self._extract_legal_key_terms(text_content)
            }
            
            # Cache the result
            self.document_cache[doc_hash] = processed_doc
            
            # Save processed document
            self._save_processed_document(processed_doc)
            
            logger.info(f"Successfully processed legal document: {file_path}")
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error processing legal document {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'processed_date': datetime.now().isoformat(),
                'success': False
            }
    
    def batch_process_documents(self, directory_path: str, document_type: str = None) -> List[Dict[str, Any]]:
        """
        Process multiple legal documents in a directory
        
        Args:
            directory_path: Path to directory containing legal documents
            document_type: Optional document type classification
            
        Returns:
            List of processed document results
        """
        try:
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            logger.info(f"Batch processing legal documents in: {directory_path}")
            
            results = []
            processed_count = 0
            error_count = 0
            
            for file_path in Path(directory_path).rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                    try:
                        metadata = {'document_type': document_type} if document_type else {}
                        result = self.process_legal_document(str(file_path), metadata)
                        results.append(result)
                        
                        if 'error' not in result:
                            processed_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        error_count += 1
                        results.append({
                            'file_path': str(file_path),
                            'error': str(e),
                            'success': False
                        })
            
            logger.info(f"Batch processing complete: {processed_count} successful, {error_count} errors")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return []
    
    def _extract_text_content(self, file_path: str, file_extension: str) -> str:
        """Extract text content from various file formats"""
        try:
            if file_extension == '.txt' or file_extension == '.md':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_extension == '.pdf':
                return self._extract_pdf_text(file_path)
            
            elif file_extension in ['.docx', '.doc']:
                return self._extract_word_text(file_path)
            
            else:
                raise ValueError(f"Unsupported file extension: {file_extension}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            # Try to import PyPDF2 or pdfplumber for PDF processing
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                logger.warning("PyPDF2 not available, using fallback PDF text extraction")
                return f"[PDF content from {os.path.basename(file_path)} - PDF processing library not available]"
                
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return f"[Error extracting PDF content: {str(e)}]"
    
    def _extract_word_text(self, file_path: str) -> str:
        """Extract text from Word documents"""
        try:
            # Try to import python-docx for Word processing
            try:
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                logger.warning("python-docx not available, using fallback Word text extraction")
                return f"[Word document content from {os.path.basename(file_path)} - Word processing library not available]"
                
        except Exception as e:
            logger.error(f"Error extracting Word text: {e}")
            return f"[Error extracting Word content: {str(e)}]"
    
    def _clean_legal_text(self, text: str) -> str:
        """Clean and normalize legal text"""
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers
        cleaned = re.sub(r'Page \d+.*?\n', '', cleaned)
        cleaned = re.sub(r'\n\d+\n', '\n', cleaned)
        
        # Clean up common OCR errors in legal documents
        cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)  # Add space between words
        cleaned = re.sub(r'(\d+)([A-Za-z])', r'\1 \2', cleaned)  # Space between numbers and letters
        
        # Normalize legal numbering
        cleaned = re.sub(r'Article\s*(\d+)', r'Article \1', cleaned)
        cleaned = re.sub(r'Section\s*(\d+)', r'Section \1', cleaned)
        cleaned = re.sub(r'Chapter\s*(\d+)', r'Chapter \1', cleaned)
        
        # Remove extra line breaks
        cleaned = re.sub(r'\n+', '\n', cleaned)
        
        return cleaned.strip()
    
    def _analyze_legal_content(self, text: str) -> Dict[str, Any]:
        """Analyze legal content and extract legal-specific information"""
        analysis = {
            'document_type': self._identify_document_type(text),
            'jurisdiction': self._identify_jurisdiction(text),
            'legal_categories': self._identify_legal_categories(text),
            'law_references': self._extract_law_references(text),
            'regulatory_references': self._extract_regulatory_references(text),
            'dates': self._extract_legal_dates(text),
            'penalties': self._extract_penalties(text),
            'requirements': self._extract_requirements(text),
            'definitions': self._extract_definitions(text)
        }
        
        return analysis
    
    def _analyze_document_structure(self, text: str) -> Dict[str, Any]:
        """Analyze the structure of the legal document"""
        structure = {
            'has_title': bool(re.search(r'^[A-Z\s]+', text.split('\n')[0])) if text.split('\n') else False,
            'sections': self._extract_sections(text),
            'articles': self._extract_articles(text),
            'chapters': self._extract_chapters(text),
            'paragraphs': len(re.findall(r'\n\s*\n', text)),
            'numbered_items': len(re.findall(r'\n\s*\d+\.', text)),
            'bullet_points': len(re.findall(r'\n\s*[•\-\*]', text)),
            'total_lines': len(text.split('\n'))
        }
        
        return structure
    
    def _extract_legal_citations(self, text: str) -> List[Dict[str, str]]:
        """Extract legal citations from the text"""
        citations = []
        
        # Royal Decree patterns
        royal_decree_pattern = r'Royal Decree No\.\s*([A-Z]*/?M?/?\d+)'
        for match in re.finditer(royal_decree_pattern, text, re.IGNORECASE):
            citations.append({
                'type': 'Royal Decree',
                'reference': match.group(0),
                'number': match.group(1),
                'position': match.start()
            })
        
        # Law references
        law_pattern = r'Law No\.\s*(\d+/\d+|\d+)'
        for match in re.finditer(law_pattern, text, re.IGNORECASE):
            citations.append({
                'type': 'Law',
                'reference': match.group(0),
                'number': match.group(1),
                'position': match.start()
            })
        
        # Regulation references
        regulation_pattern = r'Regulation No\.\s*(\d+/\d+|\d+)'
        for match in re.finditer(regulation_pattern, text, re.IGNORECASE):
            citations.append({
                'type': 'Regulation',
                'reference': match.group(0),
                'number': match.group(1),
                'position': match.start()
            })
        
        # Article references
        article_pattern = r'Article\s+(\d+)'
        for match in re.finditer(article_pattern, text, re.IGNORECASE):
            citations.append({
                'type': 'Article',
                'reference': match.group(0),
                'number': match.group(1),
                'position': match.start()
            })
        
        return citations
    
    def _extract_legal_key_terms(self, text: str) -> List[str]:
        """Extract key legal terms from the document"""
        key_terms = []
        
        # Common legal terms in Arabic and English
        legal_terms = [
            'contract', 'agreement', 'liability', 'obligation', 'penalty', 'fine',
            'compliance', 'violation', 'breach', 'damages', 'compensation',
            'license', 'permit', 'authorization', 'registration', 'certification',
            'shareholder', 'board of directors', 'general assembly', 'capital',
            'company', 'corporation', 'partnership', 'establishment',
            'court', 'judge', 'litigation', 'arbitration', 'dispute',
            'regulation', 'law', 'decree', 'decision', 'circular',
            'ministry', 'authority', 'commission', 'committee'
        ]
        
        text_lower = text.lower()
        for term in legal_terms:
            if term in text_lower:
                # Count occurrences
                count = text_lower.count(term)
                if count > 2:  # Only include terms that appear multiple times
                    key_terms.append(term)
        
        return key_terms
    
    def _identify_document_type(self, text: str) -> str:
        """Identify the type of legal document"""
        text_lower = text.lower()
        
        type_patterns = {
            'Royal Decree': ['royal decree', 'مرسوم ملكي'],
            'Law': ['law no.', 'قانون رقم'],
            'Regulation': ['regulation no.', 'لائحة رقم'],
            'Decision': ['decision no.', 'قرار رقم'],
            'Circular': ['circular no.', 'تعميم رقم'],
            'Contract': ['contract', 'agreement', 'عقد'],
            'Companies Law': ['companies law', 'company law', 'قانون الشركات'],
            'Commercial Law': ['commercial law', 'trade law', 'قانون تجاري'],
            'Labor Law': ['labor law', 'employment law', 'قانون العمل']
        }
        
        for doc_type, patterns in type_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return doc_type
        
        return 'Unknown'
    
    def _identify_jurisdiction(self, text: str) -> str:
        """Identify the jurisdiction of the legal document"""
        text_lower = text.lower()
        
        jurisdiction_patterns = {
            'Saudi Arabia': ['saudi arabia', 'kingdom of saudi arabia', 'المملكة العربية السعودية'],
            'UAE': ['united arab emirates', 'uae', 'الإمارات العربية المتحدة'],
            'Qatar': ['qatar', 'state of qatar', 'دولة قطر'],
            'Kuwait': ['kuwait', 'state of kuwait', 'دولة الكويت'],
            'Bahrain': ['bahrain', 'kingdom of bahrain', 'مملكة البحرين'],
            'Oman': ['oman', 'sultanate of oman', 'سلطنة عمان']
        }
        
        for jurisdiction, patterns in jurisdiction_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return jurisdiction
        
        return 'Unknown'
    
    def _identify_legal_categories(self, text: str) -> List[str]:
        """Identify legal categories covered in the document"""
        categories = []
        text_lower = text.lower()
        
        category_patterns = {
            'Corporate Law': ['company', 'corporation', 'shareholder', 'board of directors'],
            'Contract Law': ['contract', 'agreement', 'obligation', 'breach'],
            'Employment Law': ['employee', 'employer', 'labor', 'work', 'employment'],
            'Commercial Law': ['trade', 'business', 'commercial', 'merchant'],
            'Banking Law': ['bank', 'banking', 'financial', 'credit'],
            'Real Estate Law': ['property', 'real estate', 'land', 'building'],
            'Tax Law': ['tax', 'taxation', 'revenue', 'customs'],
            'Criminal Law': ['crime', 'criminal', 'penalty', 'punishment'],
            'Administrative Law': ['administrative', 'government', 'public'],
            'International Law': ['international', 'treaty', 'bilateral']
        }
        
        for category, patterns in category_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                categories.append(category)
        
        return categories
    
    def _extract_law_references(self, text: str) -> List[str]:
        """Extract references to laws"""
        law_refs = []
        
        patterns = [
            r'Law No\.\s*(\d+/\d+|\d+)',
            r'قانون رقم\s*(\d+/\d+|\d+)',
            r'Companies Law',
            r'Commercial Law',
            r'Labor Law'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            law_refs.extend(matches)
        
        return list(set(law_refs))  # Remove duplicates
    
    def _extract_regulatory_references(self, text: str) -> List[str]:
        """Extract references to regulations"""
        reg_refs = []
        
        patterns = [
            r'Regulation No\.\s*(\d+/\d+|\d+)',
            r'لائحة رقم\s*(\d+/\d+|\d+)',
            r'Royal Decree No\.\s*([A-Z]*/?M?/?\d+)',
            r'مرسوم ملكي رقم\s*([A-Z]*/?M?/?\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            reg_refs.extend(matches)
        
        return list(set(reg_refs))  # Remove duplicates
    
    def _extract_legal_dates(self, text: str) -> List[str]:
        """Extract legal dates from the document"""
        dates = []
        
        # Date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            r'Hijri\s+\d{1,2}/\d{1,2}/\d{4}'  # Hijri dates
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))
    
    def _extract_penalties(self, text: str) -> List[str]:
        """Extract penalty and fine information"""
        penalties = []
        
        penalty_patterns = [
            r'fine of.*?(?:SAR|riyal|SR)\s*[\d,]+',
            r'penalty.*?(?:SAR|riyal|SR)\s*[\d,]+',
            r'imprisonment.*?(?:month|year|day)',
            r'suspension.*?(?:month|year|day)',
            r'revocation of license'
        ]
        
        for pattern in penalty_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            penalties.extend(matches)
        
        return penalties
    
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract legal requirements"""
        requirements = []
        
        requirement_patterns = [
            r'shall.*?(?:\.|;|\n)',
            r'must.*?(?:\.|;|\n)',
            r'required to.*?(?:\.|;|\n)',
            r'obligation to.*?(?:\.|;|\n)',
            r'mandatory.*?(?:\.|;|\n)'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            requirements.extend(matches[:10])  # Limit to avoid too many results
        
        return requirements
    
    def _extract_definitions(self, text: str) -> Dict[str, str]:
        """Extract legal definitions from the document"""
        definitions = {}
        
        # Look for definition sections
        definition_patterns = [
            r'Definition[s]?.*?\n(.*?)(?=\n[A-Z]|\nArticle|\nSection|$)',
            r'For the purpose[s]? of.*?\n(.*?)(?=\n[A-Z]|\nArticle|\nSection|$)',
            r'"([^"]+)"\s+means\s+([^.\n]+)'
        ]
        
        for pattern in definition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    term, definition = match
                    definitions[term.strip()] = definition.strip()
        
        return definitions
    
    def _extract_sections(self, text: str) -> List[str]:
        """Extract section headings"""
        sections = re.findall(r'Section\s+(\d+[A-Za-z]*)', text, re.IGNORECASE)
        return sections
    
    def _extract_articles(self, text: str) -> List[str]:
        """Extract article numbers"""
        articles = re.findall(r'Article\s+(\d+[A-Za-z]*)', text, re.IGNORECASE)
        return articles
    
    def _extract_chapters(self, text: str) -> List[str]:
        """Extract chapter headings"""
        chapters = re.findall(r'Chapter\s+(\d+[A-Za-z]*)', text, re.IGNORECASE)
        return chapters
    
    def _generate_document_hash(self, file_path: str) -> str:
        """Generate a hash for the document for caching purposes"""
        with open(file_path, 'rb') as f:
            file_content = f.read()
            return hashlib.md5(file_content).hexdigest()
    
    def _save_processed_document(self, processed_doc: Dict[str, Any]) -> bool:
        """Save processed document to disk"""
        try:
            file_name = processed_doc['file_name']
            doc_hash = processed_doc['document_hash']
            output_path = f"data/processed_legal/{doc_hash}_{file_name}.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_doc, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved processed document to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving processed document: {e}")
            return False
    
    def _initialize_legal_patterns(self) -> Dict[str, List[str]]:
        """Initialize legal pattern matching"""
        return {
            'citations': [
                r'Royal Decree No\.\s*([A-Z]*/?M?/?\d+)',
                r'Law No\.\s*(\d+/\d+|\d+)',
                r'Regulation No\.\s*(\d+/\d+|\d+)',
                r'Article\s+(\d+)'
            ],
            'dates': [
                r'\d{1,2}/\d{1,2}/\d{4}',
                r'\d{4}-\d{1,2}-\d{1,2}',
                r'Hijri\s+\d{1,2}/\d{1,2}/\d{4}'
            ],
            'penalties': [
                r'fine of.*?(?:SAR|riyal|SR)\s*[\d,]+',
                r'imprisonment.*?(?:month|year|day)'
            ]
        }
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed documents"""
        return {
            'total_cached_documents': len(self.document_cache),
            'supported_formats': self.supported_formats,
            'processing_date': datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """Clear the document processing cache"""
        self.document_cache.clear()
        logger.info("Document processing cache cleared")

# Utility functions for legal document processing
def validate_legal_document(file_path: str) -> Dict[str, Any]:
    """Validate if a file is a legal document"""
    try:
        processor = LegalDocumentProcessor()
        
        # Basic file validation
        if not os.path.exists(file_path):
            return {'valid': False, 'reason': 'File not found'}
        
        file_extension = Path(file_path).suffix.lower()
        if file_extension not in processor.supported_formats:
            return {'valid': False, 'reason': f'Unsupported format: {file_extension}'}
        
        # Check file size (avoid processing very large files)
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return {'valid': False, 'reason': 'File too large (>50MB)'}
        
        return {'valid': True, 'file_size': file_size, 'format': file_extension}
        
    except Exception as e:
        return {'valid': False, 'reason': f'Validation error: {str(e)}'}

def extract_legal_summary(processed_document: Dict[str, Any]) -> str:
    """Extract a summary from a processed legal document"""
    try:
        doc_type = processed_document.get('legal_analysis', {}).get('document_type', 'Legal Document')
        jurisdiction = processed_document.get('legal_analysis', {}).get('jurisdiction', 'Unknown')
        categories = processed_document.get('legal_analysis', {}).get('legal_categories', [])
        
        summary = f"{doc_type} from {jurisdiction}"
        
        if categories:
            summary += f" covering {', '.join(categories[:3])}"
        
        word_count = processed_document.get('content', {}).get('word_count', 0)
        if word_count > 0:
            summary += f" ({word_count:,} words)"
        
        return summary
        
    except Exception as e:
        logger.error(f"Error extracting legal summary: {e}")
        return "Legal document summary unavailable"