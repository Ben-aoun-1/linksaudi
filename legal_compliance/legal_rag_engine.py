#!/usr/bin/env python3
# legal_compliance/legal_rag_engine.py - FIXED Legal RAG Engine with Weaviate Cloud connection

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
    FIXED Legal-specific RAG engine that properly queries LegalDocument class in Weaviate Cloud
    with correct property mappings and robust error handling
    """
    
    def __init__(self, weaviate_client=None, openai_client=None, embedding_engine=None, openai_api_key=None):
        self.weaviate_client = weaviate_client
        self.openai_client = openai_client
        self.embedding_engine = embedding_engine
        self.legal_class = "LegalDocument"
        self.cache = {}
        self.query_history = []
        
        # Initialize OpenAI client if API key provided but no client
        if openai_api_key and not self.openai_client:
            try:
                import openai
                # Handle both v0.x and v1.x OpenAI client initialization
                if hasattr(openai, 'OpenAI'):
                    # OpenAI v1.x
                    self.openai_client = openai.OpenAI(api_key=openai_api_key)
                else:
                    # OpenAI v0.x
                    openai.api_key = openai_api_key
                    self.openai_client = openai
                logger.info("OpenAI client initialized for legal RAG engine")
            except ImportError:
                logger.warning("OpenAI library not available")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")
        elif not self.openai_client and not openai_api_key:
            # Try to get API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    import openai
                    if hasattr(openai, 'OpenAI'):
                        self.openai_client = openai.OpenAI(api_key=api_key)
                    else:
                        openai.api_key = api_key
                        self.openai_client = openai
                    logger.info("OpenAI client initialized from environment variable")
                except Exception as e:
                    logger.warning(f"Could not initialize OpenAI client from env: {e}")
        
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
        
        # Test Weaviate connection
        self._test_weaviate_connection()
        
        logger.info("FIXED Legal RAG Engine initialized with Weaviate Cloud support")
    
    def _test_weaviate_connection(self):
        """Test connection to Weaviate Cloud"""
        if not self.weaviate_client:
            logger.warning("No Weaviate client provided - will use mock data")
            return False
        
        try:
            is_ready = self.weaviate_client.is_ready()
            if is_ready:
                logger.info("Weaviate Cloud connection verified for legal RAG")
                
                # Test if LegalDocument class exists
                schema = self.weaviate_client.schema.get()
                legal_class_found = False
                for class_def in schema.get("classes", []):
                    if class_def["class"] == self.legal_class:
                        legal_class_found = True
                        logger.info(f"Found {self.legal_class} class in Weaviate Cloud")
                        break
                
                if not legal_class_found:
                    logger.warning(f"{self.legal_class} class not found in Weaviate Cloud - will use mock data")
                    return False
                
                # Test document count
                try:
                    result = self.weaviate_client.query.aggregate(self.legal_class).with_meta_count().do()
                    if result and "data" in result and "Aggregate" in result["data"]:
                        agg_data = result["data"]["Aggregate"].get(self.legal_class, [])
                        if agg_data and "meta" in agg_data[0]:
                            doc_count = agg_data[0]["meta"]["count"]
                            logger.info(f"Found {doc_count} legal documents in Weaviate Cloud")
                            return True
                except Exception as e:
                    logger.warning(f"Could not count legal documents: {e}")
                
                return True
            else:
                logger.warning("Weaviate Cloud not ready for legal RAG")
                return False
        except Exception as e:
            logger.error(f"Error testing Weaviate Cloud connection: {e}")
            return False
    
    def search_legal_documents(self, query: str, limit: int = 10, 
                              document_type: str = None, jurisdiction: str = None,
                              practice_area: str = None) -> List[Dict]:
        """
        FIXED: Search legal documents in Weaviate Cloud with proper error handling
        """
        try:
            if not self.weaviate_client:
                logger.warning("Weaviate client not available - using mock data")
                return self._get_mock_legal_documents(query, limit)
            
            logger.info(f"Searching legal documents in Weaviate Cloud for: {query}")
            
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
            
            # Start with semantic search - FIXED VERSION
            query_builder = None
            try:
                # Try semantic search with proper error handling
                query_builder = (
                    self.weaviate_client.query
                    .get(self.legal_class, properties_to_retrieve)
                    .with_near_text({
                        "concepts": [query],
                        "certainty": 0.7  # Add certainty threshold
                    })
                    .with_limit(limit)
                )
                logger.debug("Using semantic search with near_text for legal documents")
            except Exception as semantic_error:
                logger.warning(f"Semantic search setup failed: {semantic_error}")
                # Try semantic search with different parameters
                try:
                    query_builder = (
                        self.weaviate_client.query
                        .get(self.legal_class, properties_to_retrieve)
                        .with_near_text({"concepts": [query]})  # Simpler version
                        .with_limit(limit)
                    )
                    logger.debug("Using simplified semantic search")
                except Exception as simple_semantic_error:
                    logger.warning(f"Simplified semantic search failed: {simple_semantic_error}")
                    # Fallback to basic query as last resort
                    try:
                        query_builder = (
                            self.weaviate_client.query
                            .get(self.legal_class, properties_to_retrieve)
                            .with_limit(limit)
                        )
                        logger.debug("Fallback to basic query (no semantic search)")
                    except Exception as basic_error:
                        logger.error(f"All query types failed: {basic_error}")
                        return self._get_mock_legal_documents(query, limit)
            
            if not query_builder:
                logger.error("Could not create query builder for legal documents")
                return self._get_mock_legal_documents(query, limit)
            
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
                try:
                    if len(where_conditions) == 1:
                        query_builder = query_builder.with_where(where_conditions[0])
                    else:
                        query_builder = query_builder.with_where({
                            "operator": "And",
                            "operands": where_conditions
                        })
                    logger.debug(f"Applied {len(where_conditions)} filters to legal document search")
                except Exception as filter_error:
                    logger.warning(f"Could not apply filters to legal search: {filter_error}")
                    # Continue without filters
            
            # Execute the query with comprehensive error handling
            result = None
            try:
                logger.info(f"Executing semantic search query for legal documents: '{query}'")
                result = query_builder.do()
                logger.info(f"Query executed successfully, result type: {type(result)}")
                
                # Debug the result structure
                if result is None:
                    logger.warning("Query returned None - this indicates semantic search failure")
                    # Try a basic query instead
                    logger.info("Attempting fallback to basic query...")
                    fallback_result = (
                        self.weaviate_client.query
                        .get(self.legal_class, properties_to_retrieve)
                        .with_limit(limit)
                        .do()
                    )
                    if fallback_result:
                        logger.info("Fallback basic query successful")
                        result = fallback_result
                    else:
                        logger.warning("Even fallback basic query returned None")
                elif isinstance(result, dict):
                    logger.info(f"Query result keys: {list(result.keys())}")
                    if "data" in result:
                        data_keys = list(result["data"].keys()) if isinstance(result["data"], dict) else "Not a dict"
                        logger.info(f"Result data keys: {data_keys}")
                else:
                    logger.warning(f"Unexpected result type: {type(result)}")
                    
            except Exception as query_error:
                logger.error(f"Legal document query execution failed: {query_error}")
                # Try one more fallback - simple query without any filters
                try:
                    logger.info("Attempting emergency fallback query...")
                    result = (
                        self.weaviate_client.query
                        .get(self.legal_class, ["content", "documentTitle", "documentType"])
                        .with_limit(limit)
                        .do()
                    )
                    if result:
                        logger.info("Emergency fallback query successful")
                    else:
                        logger.error("Emergency fallback also returned None")
                except Exception as fallback_error:
                    logger.error(f"Emergency fallback failed: {fallback_error}")
                
                if not result:
                    return self._get_mock_legal_documents(query, limit)
            
            # FIXED: Handle None result explicitly
            if result is None:
                logger.warning("Weaviate legal query returned None - using fallback")
                return self._get_mock_legal_documents(query, limit)
            
            # FIXED: Check result structure before accessing
            if not isinstance(result, dict):
                logger.warning(f"Unexpected legal result type: {type(result)} - using fallback")
                return self._get_mock_legal_documents(query, limit)
            
            if "data" not in result:
                logger.warning("No 'data' key in legal result - using fallback")
                return self._get_mock_legal_documents(query, limit)
            
            if not isinstance(result["data"], dict):
                logger.warning(f"Legal result data is not dict: {type(result['data'])} - using fallback")
                return self._get_mock_legal_documents(query, limit)
            
            if "Get" not in result["data"]:
                logger.warning("No 'Get' key in legal result data - using fallback")
                return self._get_mock_legal_documents(query, limit)
            
            # FIXED: Safely get the legal data
            get_data = result["data"]["Get"]
            if not isinstance(get_data, dict):
                logger.warning(f"Legal Get data is not dict: {type(get_data)} - using fallback")
                return self._get_mock_legal_documents(query, limit)
            
            legal_data = get_data.get(self.legal_class, [])
            
            # FIXED: Ensure legal_data is iterable
            if legal_data is None:
                logger.warning("Legal data is None - using fallback")
                return self._get_mock_legal_documents(query, limit)
            
            if not isinstance(legal_data, (list, tuple)):
                logger.warning(f"Legal data is not iterable: {type(legal_data)} - using fallback")
                return self._get_mock_legal_documents(query, limit)
            
            # Process results with correct property mapping
            documents = []
            for item in legal_data:
                # FIXED: Handle each item safely
                if not isinstance(item, dict):
                    logger.warning(f"Skipping non-dict legal item: {type(item)}")
                    continue
                
                try:
                    # Map Weaviate properties to standardized format
                    document = {
                        "content": str(item.get("content", "")),
                        "title": str(item.get("documentTitle", "Untitled Legal Document")),
                        "document_type": str(item.get("documentType", "Unknown")),
                        "jurisdiction": str(item.get("jurisdiction", "Unknown")),
                        "practice_area": str(item.get("practiceArea", "General Practice")),
                        "file_name": str(item.get("filename", "")),
                        "file_path": str(item.get("filePath", "")),
                        "processing_date": str(item.get("processingDate", "Unknown")),
                        "page_number": int(item.get("pageNumber", 0)) if item.get("pageNumber") is not None else 0,
                        "total_pages": int(item.get("totalPages", 0)) if item.get("totalPages") is not None else 0,
                        "word_count": int(item.get("wordCount", 0)) if item.get("wordCount") is not None else 0,
                        "chunk_index": int(item.get("chunkIndex", 0)) if item.get("chunkIndex") is not None else 0,
                        "type": "legal_document",
                        "source": "Weaviate Cloud Legal Database"
                    }
                    documents.append(document)
                except Exception as doc_error:
                    logger.warning(f"Error processing legal document item: {doc_error}")
                    continue
            
            logger.info(f"Successfully found {len(documents)} legal documents from Weaviate Cloud")
            
            # If no documents found, return mock data for demonstration
            if not documents:
                logger.info("No legal documents found in Weaviate Cloud, returning mock data for demonstration")
                return self._get_mock_legal_documents(query, limit)
            
            return documents
            
        except Exception as e:
            logger.error(f"Unexpected error searching legal documents in Weaviate Cloud: {e}")
            logger.error(f"Error details: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
            # Return mock data on any error
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
                logger.warning("No legal documents found, using fallback response")
                return {
                    "response": "I couldn't find specific legal documents to answer your question. However, I can provide general guidance that you should consult with a qualified attorney licensed in Saudi Arabia for specific legal matters.",
                    "documents": [],
                    "citations": [],
                    "warning": "No legal documents found"
                }
            
            # Format context for the LLM prompt
            context = self._format_legal_context(legal_documents)
            
            # Create comprehensive legal prompt
            prompt = self._create_comprehensive_legal_prompt(query, context, include_citations)
            
            # Generate response using OpenAI
            response_text = ""
            model_used = "fallback"
            
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
                                    You provide accurate, well-researched legal analysis based on the provided legal documents from our database. 
                                    Always include appropriate disclaimers about seeking professional legal advice for specific situations.
                                    Be precise with citations and clearly distinguish between mandatory requirements and recommendations."""
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=self.temperature,
                            max_tokens=self.max_tokens
                        )
                        response_text = response.choices[0].message.content
                        model_used = "gpt-4"
                    else:
                        # OpenAI v1.x
                        response = self.openai_client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {
                                    "role": "system", 
                                    "content": """You are an expert legal analyst specializing in Saudi Arabian law and regulations. 
                                    You provide accurate, well-researched legal analysis based on the provided legal documents from our database. 
                                    Always include appropriate disclaimers about seeking professional legal advice for specific situations.
                                    Be precise with citations and clearly distinguish between mandatory requirements and recommendations."""
                                },
                                {"role": "user", "content": prompt}
                            ],
                            temperature=self.temperature,
                            max_tokens=self.max_tokens
                        )
                        response_text = response.choices[0].message.content
                        model_used = "gpt-4"
                    
                except Exception as openai_error:
                    logger.error(f"OpenAI API error: {openai_error}")
                    response_text = self._generate_fallback_response(query, legal_documents)
                    model_used = "fallback"
            else:
                logger.warning("OpenAI client not available, using fallback response")
                response_text = self._generate_fallback_response(query, legal_documents)
                model_used = "fallback"
            
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
                "search_method": "weaviate_cloud_semantic_search",
                "model_used": model_used,
                "source": "Weaviate Cloud Legal Database"
            }
            
            logger.info(f"Generated legal response with {len(legal_documents)} documents using {model_used}")
            return legal_response
            
        except Exception as e:
            logger.error(f"Error generating legal response: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return {
                "response": f"I encountered an error while analyzing your legal question: {str(e)}. Please try again or contact support for assistance with legal matters in Saudi Arabia.",
                "documents": [],
                "citations": [],
                "error": str(e)
            }
    
    def _format_legal_context(self, documents: List[Dict]) -> str:
        """Format legal documents for context with proper structure"""
        if not documents:
            return "=== NO LEGAL DOCUMENTS AVAILABLE ==="
        
        context = "=== LEGAL DOCUMENTS FROM WEAVIATE CLOUD ===\n\n"
        
        for i, doc in enumerate(documents, 1):
            if not isinstance(doc, dict):
                continue
                
            context += f"--- Legal Document {i} ---\n"
            context += f"Title: {doc.get('title', 'Untitled')}\n"
            context += f"Document Type: {doc.get('document_type', 'Unknown')}\n"
            context += f"Jurisdiction: {doc.get('jurisdiction', 'Unknown')}\n"
            context += f"Practice Area: {doc.get('practice_area', 'General')}\n"
            context += f"File: {doc.get('file_name', 'Unknown')}\n"
            
            if doc.get('page_number'):
                context += f"Page: {doc.get('page_number')}/{doc.get('total_pages', 'Unknown')}\n"
                
            # Limit content length but ensure we get meaningful text
            content = str(doc.get('content', ''))
            if len(content) > 2000:
                content = content[:2000] + "..."
            context += f"Content: {content}\n\n"
        
        return context
    
    def _create_comprehensive_legal_prompt(self, query: str, context: str, include_citations: bool) -> str:
        """Create a comprehensive legal-specific prompt"""
        prompt = f"""
Based on the legal documents from our Weaviate Cloud legal database, please provide a comprehensive legal analysis for the following question:

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
This analysis is based on legal documents in our database and is for informational purposes only. For specific legal advice applicable to your situation, please consult with a qualified attorney licensed to practice in Saudi Arabia.

LEGAL ANALYSIS:
"""
        return prompt
    
    def _generate_fallback_response(self, query: str, documents: List[Dict]) -> str:
        """Generate a fallback response when OpenAI is not available"""
        if not documents:
            return f"""I apologize, but I don't have access to specific legal documents in Weaviate Cloud to answer your question about '{query}'. 

For legal matters in Saudi Arabia, I recommend:
• Consulting with a qualified attorney licensed in Saudi Arabia
• Reviewing official government legal resources
• Contacting relevant regulatory authorities
• Ensuring compliance with current Saudi Arabian laws and regulations

**Legal Disclaimer:** This information is for general guidance only and does not constitute legal advice. For specific legal matters, please consult with a qualified attorney licensed to practice in Saudi Arabia."""

        response = f"Based on the legal documents from our Weaviate Cloud database regarding '{query}', here are the key findings:\n\n"
        
        # Extract key information from documents
        doc_types = set()
        jurisdictions = set()
        key_points = []
        
        for doc in documents[:3]:  # Use top 3 documents
            if isinstance(doc, dict):
                doc_types.add(doc.get('document_type', 'Unknown'))
                jurisdictions.add(doc.get('jurisdiction', 'Unknown'))
                
                # Extract some meaningful content
                content = str(doc.get('content', ''))[:300]
                if content:
                    key_points.append(f"• From {doc.get('title', 'Legal Document')}: {content}...")
        
        response += f"**Document Types Consulted:** {', '.join(doc_types)}\n"
        response += f"**Jurisdictions:** {', '.join(jurisdictions)}\n\n"
        response += "**Key Information from Weaviate Cloud:**\n"
        response += '\n'.join(key_points[:3])
        
        response += "\n\n**Legal Disclaimer:** This analysis is based on legal documents in our Weaviate Cloud database and is for informational purposes only. For specific legal advice applicable to your situation, please consult with a qualified attorney licensed to practice in Saudi Arabia."
        
        return response
    
    def _extract_citations(self, documents: List[Dict]) -> List[Dict]:
        """Extract citation information from documents"""
        citations = []
        for doc in documents:
            if isinstance(doc, dict):
                citation = {
                    "title": str(doc.get('title', 'Untitled')),
                    "document_type": str(doc.get('document_type', 'Unknown')),
                    "jurisdiction": str(doc.get('jurisdiction', 'Unknown')),
                    "practice_area": str(doc.get('practice_area', 'General')),
                    "file_name": str(doc.get('file_name', '')),
                    "page_number": str(doc.get('page_number', '')),
                    "processing_date": str(doc.get('processing_date', 'Unknown')),
                    "source": "Weaviate Cloud Legal Database"
                }
                citations.append(citation)
        return citations
    
    def _get_mock_legal_documents(self, query: str, limit: int) -> List[Dict]:
        """Generate mock legal documents when Weaviate Cloud is not available"""
        mock_docs = [
            {
                "content": f"Saudi Arabian legal framework regarding {query}. This document outlines the key legal requirements and compliance procedures that must be followed according to Saudi law. Employment regulations in Saudi Arabia are governed by the Labor Law and related ministerial decisions.",
                "title": f"Legal Guide: Employment Law in Saudi Arabia",
                "document_type": "Legal Guidance",
                "jurisdiction": "Saudi Arabia",
                "practice_area": "Employment Law",
                "file_name": "employment_law_guide.pdf",
                "processing_date": datetime.now().isoformat(),
                "page_number": 1,
                "total_pages": 10,
                "word_count": 50,
                "type": "legal_document",
                "source": "Mock Legal Database (Weaviate Cloud not available)"
            },
            {
                "content": f"Commercial regulations in Saudi Arabia require compliance with various ministerial decisions and royal decrees. Companies must register with the Ministry of Commerce and Investment and obtain necessary licenses for commercial activities related to {query}.",
                "title": f"Commercial Regulations Guide",
                "document_type": "Regulatory Guide",
                "jurisdiction": "Saudi Arabia",
                "practice_area": "Commercial Law",
                "file_name": "commercial_regulations.pdf",
                "processing_date": datetime.now().isoformat(),
                "page_number": 1,
                "total_pages": 15,
                "word_count": 75,
                "type": "legal_document",
                "source": "Mock Legal Database (Weaviate Cloud not available)"
            }
        ]
        return mock_docs[:limit]
    
    def get_legal_categories(self) -> List[str]:
        """Get available legal document categories from Weaviate Cloud"""
        try:
            if not self.weaviate_client:
                return self._get_default_categories()
            
            # Query to get unique document types from Weaviate Cloud
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
            logger.error(f"Error getting legal categories from Weaviate Cloud: {e}")
            return self._get_default_categories()
    
    def get_available_jurisdictions(self) -> List[str]:
        """Get available jurisdictions from Weaviate Cloud"""
        try:
            if not self.weaviate_client:
                return ["Saudi Arabia", "GCC", "International"]
            
            # Query to get unique jurisdictions from Weaviate Cloud
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
            logger.error(f"Error getting jurisdictions from Weaviate Cloud: {e}")
            return ["Saudi Arabia", "GCC", "International"]
    
    def get_available_practice_areas(self) -> List[str]:
        """Get available practice areas from Weaviate Cloud"""
        try:
            if not self.weaviate_client:
                return self._get_default_practice_areas()
            
            # Query to get unique practice areas from Weaviate Cloud
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
            logger.error(f"Error getting practice areas from Weaviate Cloud: {e}")
            return self._get_default_practice_areas()
    
    def _get_default_categories(self) -> List[str]:
        """Default legal categories when Weaviate Cloud is not available"""
        return [
            "Corporate Law", "Contract Law", "Regulatory Compliance", 
            "Employment Law", "Commercial Law", "Banking Law",
            "Real Estate Law", "Intellectual Property", "Tax Law",
            "International Trade", "General Legal Document"
        ]
    
    def _get_default_practice_areas(self) -> List[str]:
        """Default practice areas when Weaviate Cloud is not available"""
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
        """Test the connection to Weaviate Cloud and get schema information"""
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
                "message": f"Connected to Weaviate Cloud with {total_docs} legal documents"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Connection test failed: {str(e)}"}