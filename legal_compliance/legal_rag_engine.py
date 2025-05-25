#!/usr/bin/env python3
# legal_compliance/legal_rag_engine_fixed.py - FIXED Legal RAG Engine with proper Weaviate integration

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Set up logging
logger = logging.getLogger("legal_compliance")

class LegalRAGEngine:
    """
    FIXED Legal-specific RAG engine that properly queries LegalDocument class in Weaviate
    with correct property mappings and semantic search
    """
    
    def __init__(self, weaviate_client=None, openai_client=None, embedding_engine=None, openai_api_key=None):
        self.weaviate_client = weaviate_client
        self.openai_client = openai_client
        self.embedding_engine = embedding_engine
        self.legal_class = "LegalDocument"
        self.cache = {}
        self.query_history = []
        
        # Initialize OpenAI client if API key provided
        if openai_api_key and not self.openai_client:
            try:
                import openai
                openai.api_key = openai_api_key
                self.openai_client = openai
            except ImportError:
                logger.warning("OpenAI library not available")
        
        # Legal-specific configuration
        self.temperature = 0.2  # Lower temperature for legal accuracy
        self.max_tokens = 1500  # More tokens for detailed legal responses
        self.context_limit = 10  # More context for comprehensive legal analysis
        
        # Property mappings based on your actual Weaviate schema
        self.property_mappings = {
            'content': 'content',
            'title': 'documentTitle', 
            'document_type': 'documentType',
            'jurisdiction': 'jurisdiction',
            'practice_area': 'practiceArea',
            'file_name': 'filename',
            'file_path': 'filePath',
            'processing_date': 'processingDate',
            'page_number': 'pageNumber',
            'total_pages': 'totalPages',
            'word_count': 'wordCount',
            'file_size': 'fileSize',
            'chunk_index': 'chunkIndex'
        }
        
        logger.info("FIXED Legal RAG Engine initialized with proper Weaviate schema mapping")
    
    def search_legal_documents(self, query: str, limit: int = 10, 
                              document_type: str = None, jurisdiction: str = None,
                              practice_area: str = None) -> List[Dict]:
        """
        FIXED: Search legal documents in Weaviate with correct property names and semantic search
        """
        try:
            if not self.weaviate_client:
                logger.warning("Weaviate client not available - using mock data")
                return self._get_mock_legal_documents(query, limit)
            
            logger.info(f"Searching legal documents for: {query}")
            
            # Build the query with CORRECT property names from your schema
            properties_to_retrieve = [
                "content",
                "documentTitle", 
                "documentType",
                "jurisdiction",
                "practiceArea",
                "filename",
                "filePath",
                "processingDate",
                "pageNumber",
                "totalPages",
                "wordCount",
                "chunkIndex"
            ]
            
            # Use semantic search with near_text (Weaviate's built-in vectorization)
            query_builder = (
                self.weaviate_client.query
                .get(self.legal_class, properties_to_retrieve)
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
            )
            
            # Add filters if specified using CORRECT property names
            where_conditions = []
            
            if document_type:
                where_conditions.append({
                    "path": "documentType",
                    "operator": "Equal",
                    "valueText": document_type
                })
            
            if jurisdiction:
                where_conditions.append({
                    "path": "jurisdiction", 
                    "operator": "Equal",
                    "valueText": jurisdiction
                })
                
            if practice_area:
                where_conditions.append({
                    "path": "practiceArea",
                    "operator": "Equal", 
                    "valueText": practice_area
                })
            
            # Apply filters if any
            if where_conditions:
                if len(where_conditions) == 1:
                    query_builder = query_builder.with_where(where_conditions[0])
                else:
                    query_builder = query_builder.with_where({
                        "operator": "And",
                        "operands": where_conditions
                    })
            
            # Execute the query
            result = query_builder.do()
            
            # Process results with correct property mapping
            documents = []
            if result and "data" in result and "Get" in result["data"]:
                legal_data = result["data"]["Get"].get(self.legal_class, [])
                
                for item in legal_data:
                    # Map Weaviate properties to standardized format
                    document = {
                        "content": item.get("content", ""),
                        "title": item.get("documentTitle", "Untitled Legal Document"),
                        "document_type": item.get("documentType", "Unknown"),
                        "jurisdiction": item.get("jurisdiction", "Unknown"),
                        "practice_area": item.get("practiceArea", "General Practice"),
                        "file_name": item.get("filename", ""),
                        "file_path": item.get("filePath", ""),
                        "processing_date": item.get("processingDate", "Unknown"),
                        "page_number": item.get("pageNumber", 0),
                        "total_pages": item.get("totalPages", 0),
                        "word_count": item.get("wordCount", 0),
                        "chunk_index": item.get("chunkIndex", 0),
                        "type": "legal_document",
                        "source": "Legal Database"
                    }
                    documents.append(document)
            
            logger.info(f"Found {len(documents)} legal documents from Weaviate")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching legal documents in Weaviate: {e}")
            logger.error(f"Error details: {str(e)}")
            # Return mock data on error
            return self._get_mock_legal_documents(query, limit)
    
    def generate_legal_response(self, query: str, context_limit: int = None, 
                               include_citations: bool = True,
                               document_type: str = None, 
                               jurisdiction: str = None,
                               practice_area: str = None) -> Dict[str, Any]:
        """
        FIXED: Generate a comprehensive legal response using proper RAG with OpenAI
        """
        try:
            logger.info(f"Generating legal response for: {query}")
            
            # Track query for compliance
            self.query_history.append({
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "document_type": document_type,
                "jurisdiction": jurisdiction,
                "practice_area": practice_area
            })
            
            # Search for relevant legal documents using FIXED search
            context_limit = context_limit or self.context_limit
            legal_documents = self.search_legal_documents(
                query=query, 
                limit=context_limit,
                document_type=document_type,
                jurisdiction=jurisdiction,
                practice_area=practice_area
            )
            
            if not legal_documents:
                return {
                    "response": "I couldn't find relevant legal documents to answer your question. Please try rephrasing your query or ensure the legal database contains relevant documents.",
                    "documents": [],
                    "citations": [],
                    "warning": "No legal documents found"
                }
            
            # Format context for the LLM prompt
            context = self._format_legal_context(legal_documents)
            
            # Create comprehensive legal prompt
            prompt = self._create_comprehensive_legal_prompt(query, context, include_citations)
            
            # Generate response using OpenAI
            if self.openai_client:
                try:
                    # Try different OpenAI client versions
                    if hasattr(self.openai_client, 'ChatCompletion'):
                        # OpenAI v0.x
                        response = self.openai_client.ChatCompletion.create(
                            model="gpt-4",
                            messages=[
                                {
                                    "role": "system", 
                                    "content": """You are an expert legal analyst specializing in Saudi Arabian law and regulations. 
                                    You provide accurate, well-researched legal analysis based on the provided legal documents. 
                                    Always include appropriate disclaimers about seeking professional legal advice for specific situations.
                                    Be precise with citations and clearly distinguish between mandatory requirements and recommendations."""
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=self.temperature,
                            max_tokens=self.max_tokens
                        )
                        response_text = response.choices[0].message.content
                    else:
                        # OpenAI v1.x
                        response = self.openai_client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {
                                    "role": "system", 
                                    "content": """You are an expert legal analyst specializing in Saudi Arabian law and regulations. 
                                    You provide accurate, well-researched legal analysis based on the provided legal documents. 
                                    Always include appropriate disclaimers about seeking professional legal advice for specific situations.
                                    Be precise with citations and clearly distinguish between mandatory requirements and recommendations."""
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=self.temperature,
                            max_tokens=self.max_tokens
                        )
                        response_text = response.choices[0].message.content
                    
                except Exception as openai_error:
                    logger.error(f"OpenAI API error: {openai_error}")
                    response_text = self._generate_fallback_response(query, legal_documents)
            else:
                logger.warning("OpenAI client not available, using fallback response")
                response_text = self._generate_fallback_response(query, legal_documents)
            
            # Extract citations if requested
            citations = []
            if include_citations:
                citations = self._extract_citations(legal_documents)
            
            # Create comprehensive response object
            legal_response = {
                "response": response_text,
                "documents": legal_documents,
                "citations": citations,
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "document_count": len(legal_documents),
                "filters_applied": {
                    "document_type": document_type,
                    "jurisdiction": jurisdiction,
                    "practice_area": practice_area
                },
                "search_method": "weaviate_semantic_search",
                "model_used": "gpt-4" if self.openai_client else "fallback"
            }
            
            logger.info(f"Generated legal response with {len(legal_documents)} documents")
            return legal_response
            
        except Exception as e:
            logger.error(f"Error generating legal response: {e}")
            return {
                "response": f"I encountered an error while analyzing your legal question: {str(e)}. Please try again or contact support.",
                "documents": [],
                "citations": [],
                "error": str(e)
            }
    
    def _format_legal_context(self, documents: List[Dict]) -> str:
        """Format legal documents for context with proper structure"""
        context = "=== LEGAL DOCUMENTS CONTEXT ===\n\n"
        
        for i, doc in enumerate(documents, 1):
            context += f"--- Legal Document {i} ---\n"
            context += f"Title: {doc.get('title', 'Untitled')}\n"
            context += f"Document Type: {doc.get('document_type', 'Unknown')}\n"
            context += f"Jurisdiction: {doc.get('jurisdiction', 'Unknown')}\n"
            context += f"Practice Area: {doc.get('practice_area', 'General')}\n"
            context += f"File: {doc.get('file_name', 'Unknown')}\n"
            
            if doc.get('page_number'):
                context += f"Page: {doc.get('page_number')}/{doc.get('total_pages', 'Unknown')}\n"
                
            # Limit content length but ensure we get meaningful text
            content = doc.get('content', '')
            if len(content) > 2000:
                content = content[:2000] + "..."
            context += f"Content: {content}\n\n"
        
        return context
    
    def _create_comprehensive_legal_prompt(self, query: str, context: str, include_citations: bool) -> str:
        """Create a comprehensive legal-specific prompt"""
        prompt = f"""
Based on the provided legal documents from the Saudi Arabian legal database, please provide a comprehensive legal analysis for the following question:

QUESTION: {query}

{context}

ANALYSIS REQUIREMENTS:
1. Provide a direct, precise answer to the legal question
2. Reference specific legal provisions, articles, or sections when available
3. Explain the relevant legal principles and their practical implications
4. Distinguish between mandatory requirements and recommendations
5. Include relevant procedural requirements or compliance steps
6. Address any potential penalties or consequences if applicable
7. Highlight any recent changes or updates in the law
8. Provide practical guidance for implementation or compliance

{"9. Include proper citations to the specific legal documents referenced" if include_citations else ""}

LEGAL ANALYSIS STRUCTURE:
**Legal Framework:**
[Identify the relevant laws, regulations, or legal framework]

**Key Requirements:**
[List the main legal requirements or obligations]

**Compliance Procedures:**
[Outline the steps needed for compliance]

**Penalties/Consequences:**
[Describe any penalties for non-compliance]

**Practical Recommendations:**
[Provide actionable recommendations]

**Legal Disclaimer:**
This analysis is based on the provided legal documents and is for informational purposes only. For specific legal advice applicable to your situation, please consult with a qualified attorney licensed to practice in Saudi Arabia.

LEGAL ANALYSIS:
"""
        return prompt
    
    def _generate_fallback_response(self, query: str, documents: List[Dict]) -> str:
        """Generate a fallback response when OpenAI is not available"""
        response = f"Based on the legal documents in our database regarding '{query}', here are the key findings:\n\n"
        
        # Extract key information from documents
        doc_types = set()
        jurisdictions = set()
        key_points = []
        
        for doc in documents[:3]:  # Use top 3 documents
            doc_types.add(doc.get('document_type', 'Unknown'))
            jurisdictions.add(doc.get('jurisdiction', 'Unknown'))
            
            # Extract some meaningful content
            content = doc.get('content', '')[:300]
            if content:
                key_points.append(f"• From {doc.get('title', 'Legal Document')}: {content}...")
        
        response += f"**Document Types Consulted:** {', '.join(doc_types)}\n"
        response += f"**Jurisdictions:** {', '.join(jurisdictions)}\n\n"
        response += "**Key Information:**\n"
        response += '\n'.join(key_points[:3])
        
        response += "\n\n**Note:** This is a basic analysis. For detailed legal advice, please consult with a qualified attorney."
        
        return response
    
    def _extract_citations(self, documents: List[Dict]) -> List[Dict]:
        """Extract citation information from documents"""
        citations = []
        for doc in documents:
            citation = {
                "title": doc.get('title', 'Untitled'),
                "document_type": doc.get('document_type', 'Unknown'),
                "jurisdiction": doc.get('jurisdiction', 'Unknown'),
                "practice_area": doc.get('practice_area', 'General'),
                "file_name": doc.get('file_name', ''),
                "page_number": doc.get('page_number', ''),
                "processing_date": doc.get('processing_date', 'Unknown'),
                "source": "Legal Database"
            }
            citations.append(citation)
        return citations
    
    def _get_mock_legal_documents(self, query: str, limit: int) -> List[Dict]:
        """Generate mock legal documents when Weaviate is not available"""
        mock_docs = [
            {
                "content": f"Saudi Arabian legal framework regarding {query}. This document outlines the key legal requirements and compliance procedures that must be followed according to Saudi law.",
                "title": f"Legal Guide: {query}",
                "document_type": "Legal Guidance",
                "jurisdiction": "Saudi Arabia",
                "practice_area": "General Practice",
                "file_name": "legal_guide.pdf",
                "processing_date": datetime.now().isoformat(),
                "page_number": 1,
                "total_pages": 10,
                "word_count": 50,
                "type": "legal_document",
                "source": "Mock Legal Database"
            }
        ]
        return mock_docs[:limit]
    
    def get_legal_categories(self) -> List[str]:
        """Get available legal document categories from Weaviate"""
        try:
            if not self.weaviate_client:
                return self._get_default_categories()
            
            # Query to get unique document types from Weaviate
            result = self.weaviate_client.query.aggregate(self.legal_class).with_fields("documentType { count }").do()
            
            categories = []
            if result and "data" in result and "Aggregate" in result["data"]:
                agg_data = result["data"]["Aggregate"].get(self.legal_class, [])
                for item in agg_data:
                    if "documentType" in item:
                        for cat_info in item["documentType"]:
                            if "value" in cat_info:
                                categories.append(cat_info["value"])
            
            return sorted(list(set(categories))) if categories else self._get_default_categories()
            
        except Exception as e:
            logger.error(f"Error getting legal categories from Weaviate: {e}")
            return self._get_default_categories()
    
    def get_available_jurisdictions(self) -> List[str]:
        """Get available jurisdictions from Weaviate"""
        try:
            if not self.weaviate_client:
                return ["Saudi Arabia", "GCC", "International"]
            
            # Query to get unique jurisdictions from Weaviate
            result = self.weaviate_client.query.aggregate(self.legal_class).with_fields("jurisdiction { count }").do()
            
            jurisdictions = []
            if result and "data" in result and "Aggregate" in result["data"]:
                agg_data = result["data"]["Aggregate"].get(self.legal_class, [])
                for item in agg_data:
                    if "jurisdiction" in item:
                        for jur_info in item["jurisdiction"]:
                            if "value" in jur_info:
                                jurisdictions.append(jur_info["value"])
            
            return sorted(list(set(jurisdictions))) if jurisdictions else ["Saudi Arabia", "GCC", "International"]
            
        except Exception as e:
            logger.error(f"Error getting jurisdictions from Weaviate: {e}")
            return ["Saudi Arabia", "GCC", "International"]
    
    def get_available_practice_areas(self) -> List[str]:
        """Get available practice areas from Weaviate"""
        try:
            if not self.weaviate_client:
                return self._get_default_practice_areas()
            
            # Query to get unique practice areas from Weaviate
            result = self.weaviate_client.query.aggregate(self.legal_class).with_fields("practiceArea { count }").do()
            
            practice_areas = []
            if result and "data" in result and "Aggregate" in result["data"]:
                agg_data = result["data"]["Aggregate"].get(self.legal_class, [])
                for item in agg_data:
                    if "practiceArea" in item:
                        for area_info in item["practiceArea"]:
                            if "value" in area_info:
                                practice_areas.append(area_info["value"])
            
            return sorted(list(set(practice_areas))) if practice_areas else self._get_default_practice_areas()
            
        except Exception as e:
            logger.error(f"Error getting practice areas from Weaviate: {e}")
            return self._get_default_practice_areas()
    
    def _get_default_categories(self) -> List[str]:
        """Default legal categories when Weaviate is not available"""
        return [
            "Corporate Law", "Contract Law", "Regulatory Compliance", 
            "Employment Law", "Commercial Law", "Banking Law",
            "Real Estate Law", "Intellectual Property", "Tax Law",
            "International Trade", "General Legal Document"
        ]
    
    def _get_default_practice_areas(self) -> List[str]:
        """Default practice areas when Weaviate is not available"""
        return [
            "General Practice", "Corporate Law", "Healthcare Law",
            "Construction Law", "Employment Law", "Banking & Finance",
            "Real Estate", "Intellectual Property", "Tax Law"
        ]
    
    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        logger.info("Legal RAG engine cache cleared")
    
    def get_query_history(self) -> List[Dict]:
        """Get the history of legal queries for audit purposes"""
        return self.query_history
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Weaviate and get schema information"""
        try:
            if not self.weaviate_client:
                return {"status": "error", "message": "Weaviate client not available"}
            
            # Test basic connection
            is_ready = self.weaviate_client.is_ready()
            
            # Get schema information for LegalDocument class
            schema = self.weaviate_client.schema.get()
            legal_class_schema = None
            
            for class_def in schema.get("classes", []):
                if class_def["class"] == self.legal_class:
                    legal_class_schema = class_def
                    break
            
            # Get total document count
            total_docs = 0
            try:
                result = self.weaviate_client.query.aggregate(self.legal_class).with_meta_count().do()
                if result and "data" in result and "Aggregate" in result["data"]:
                    agg_data = result["data"]["Aggregate"].get(self.legal_class, [])
                    if agg_data and "meta" in agg_data[0]:
                        total_docs = agg_data[0]["meta"]["count"]
            except Exception:
                pass
            
            return {
                "status": "success",
                "is_ready": is_ready,
                "legal_class_exists": legal_class_schema is not None,
                "total_documents": total_docs,
                "schema_properties": [prop["name"] for prop in legal_class_schema.get("properties", [])] if legal_class_schema else [],
                "message": f"Connected to Weaviate with {total_docs} legal documents"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Connection test failed: {str(e)}"}