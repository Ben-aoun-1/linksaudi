#!/usr/bin/env python3
# legal_compliance/legal_rag_engine.py - Legal-specific RAG engine

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from parent modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import logger, safe_execute
from error_handling import format_error_for_display, ApplicationError

# Legal compliance specific logger
legal_logger = logging.getLogger("legal_compliance")
legal_handler = logging.FileHandler("logs/legal_compliance.log")
legal_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
legal_logger.addHandler(legal_handler)
legal_logger.setLevel(logging.INFO)

class LegalRAGEngine:
    """Legal-specific RAG engine that queries LegalDocument class in Weaviate"""
    
    def __init__(self, weaviate_client=None, openai_client=None, embedding_engine=None):
        self.weaviate_client = weaviate_client
        self.openai_client = openai_client
        self.embedding_engine = embedding_engine
        self.legal_class = "LegalDocument"
        self.cache = {}
        self.query_history = []
        
        # Legal-specific configuration
        self.temperature = 0.2  # Lower temperature for legal accuracy
        self.max_tokens = 1500  # More tokens for detailed legal responses
        self.context_limit = 10  # More context for comprehensive legal analysis
        
        legal_logger.info("Legal RAG Engine initialized")
    
    def search_legal_documents(self, query: str, limit: int = 10, 
                              document_type: str = None, jurisdiction: str = None) -> List[Dict]:
        """
        Search legal documents in Weaviate with filters
        
        Args:
            query: Search query
            limit: Maximum number of results
            document_type: Filter by document type (law, regulation, contract, etc.)
            jurisdiction: Filter by jurisdiction (saudi, gcc, international, etc.)
        
        Returns:
            List of legal documents with metadata
        """
        try:
            if not self.weaviate_client:
                legal_logger.error("Weaviate client not available")
                return []
            
            legal_logger.info(f"Searching legal documents for: {query}")
            
            # Generate embedding for semantic search
            query_embedding = None
            if self.embedding_engine:
                query_embedding = self.embedding_engine.encode(query)
            
            # Build the query with filters
            query_builder = (
                self.weaviate_client.query
                .get(self.legal_class, [
                    "content", 
                    "title", 
                    "documentType", 
                    "jurisdiction", 
                    "datePublished",
                    "source",
                    "lawNumber",
                    "category",
                    "summary",
                    "keyTerms"
                ])
                .with_limit(limit)
            )
            
            # Add semantic search if embedding is available
            if query_embedding:
                query_builder = query_builder.with_near_vector({"vector": query_embedding})
            else:
                # Fallback to BM25 search
                query_builder = query_builder.with_bm25(query=query)
            
            # Add filters if specified
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
            
            # Process results
            documents = []
            if result and "data" in result:
                legal_data = result["data"].get("Get", {}).get(self.legal_class, [])
                
                for item in legal_data:
                    documents.append({
                        "content": item.get("content", ""),
                        "title": item.get("title", "Untitled Legal Document"),
                        "document_type": item.get("documentType", "Unknown"),
                        "jurisdiction": item.get("jurisdiction", "Unknown"),
                        "date_published": item.get("datePublished", "Unknown"),
                        "source": item.get("source", "Unknown"),
                        "law_number": item.get("lawNumber", ""),
                        "category": item.get("category", ""),
                        "summary": item.get("summary", ""),
                        "key_terms": item.get("keyTerms", []),
                        "type": "legal_document"
                    })
            
            legal_logger.info(f"Found {len(documents)} legal documents")
            return documents
            
        except Exception as e:
            legal_logger.error(f"Error searching legal documents: {e}")
            return []
    
    def generate_legal_response(self, query: str, context_limit: int = None, 
                               include_citations: bool = True,
                               document_type: str = None, 
                               jurisdiction: str = None) -> Dict[str, Any]:
        """
        Generate a legal response using RAG
        
        Args:
            query: Legal question
            context_limit: Number of documents to use as context
            include_citations: Whether to include document citations
            document_type: Filter by document type
            jurisdiction: Filter by jurisdiction
        
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Log the query for compliance tracking
            legal_logger.info(f"Legal query: {query}")
            self.query_history.append({
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "document_type": document_type,
                "jurisdiction": jurisdiction
            })
            
            # Check cache first
            cache_key = f"{query}_{document_type}_{jurisdiction}_{context_limit}"
            if cache_key in self.cache:
                cached_response = self.cache[cache_key]
                # Check if cache is still valid (24 hours)
                cache_time = datetime.fromisoformat(cached_response.get("timestamp", "2000-01-01"))
                if (datetime.now() - cache_time).total_seconds() < 86400:  # 24 hours
                    legal_logger.info("Returning cached legal response")
                    return cached_response
            
            if not self.openai_client:
                return {
                    "response": "Legal analysis service is currently unavailable. Please ensure OpenAI client is properly configured.",
                    "documents": [],
                    "citations": [],
                    "error": "OpenAI client not available"
                }
            
            # Search for relevant legal documents
            context_limit = context_limit or self.context_limit
            legal_documents = self.search_legal_documents(
                query, 
                limit=context_limit,
                document_type=document_type,
                jurisdiction=jurisdiction
            )
            
            if not legal_documents:
                return {
                    "response": "I couldn't find relevant legal documents to answer your question. Please try rephrasing your query or contact a legal professional for specific advice.",
                    "documents": [],
                    "citations": [],
                    "warning": "No legal documents found"
                }
            
            # Format context for the prompt
            context = self._format_legal_context(legal_documents)
            
            # Create the legal-specific prompt
            prompt = self._create_legal_prompt(query, context, include_citations)
            
            # Generate response using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert legal analyst specializing in Saudi Arabian law and regulations. Provide accurate, well-cited legal analysis based on the provided legal documents. Always include appropriate disclaimers about seeking professional legal advice for specific situations."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            response_text = response.choices[0].message.content
            
            # Extract citations if requested
            citations = []
            if include_citations:
                citations = self._extract_citations(legal_documents)
            
            # Create response object
            legal_response = {
                "response": response_text,
                "documents": legal_documents,
                "citations": citations,
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "document_count": len(legal_documents),
                "filters_applied": {
                    "document_type": document_type,
                    "jurisdiction": jurisdiction
                }
            }
            
            # Cache the response
            self.cache[cache_key] = legal_response
            
            legal_logger.info(f"Generated legal response with {len(legal_documents)} documents")
            return legal_response
            
        except Exception as e:
            legal_logger.error(f"Error generating legal response: {e}")
            return {
                "response": f"I encountered an error while analyzing your legal question: {str(e)}. Please try again or contact support.",
                "documents": [],
                "citations": [],
                "error": str(e)
            }
    
    def _format_legal_context(self, documents: List[Dict]) -> str:
        """Format legal documents for context"""
        context = ""
        for i, doc in enumerate(documents):
            context += f"\n--- Legal Document {i+1} ---\n"
            context += f"Title: {doc.get('title', 'Untitled')}\n"
            context += f"Type: {doc.get('document_type', 'Unknown')}\n"
            context += f"Jurisdiction: {doc.get('jurisdiction', 'Unknown')}\n"
            context += f"Law Number: {doc.get('law_number', 'N/A')}\n"
            
            if doc.get('summary'):
                context += f"Summary: {doc.get('summary')}\n"
            
            content = doc.get('content', '')
            # Limit content length to prevent token overflow
            if len(content) > 1500:
                content = content[:1500] + "..."
            context += f"Content: {content}\n"
            
            if doc.get('key_terms'):
                context += f"Key Terms: {', '.join(doc.get('key_terms', []))}\n"
        
        return context
    
    def _create_legal_prompt(self, query: str, context: str, include_citations: bool) -> str:
        """Create a legal-specific prompt"""
        prompt = f"""
Based on the provided legal documents, please answer the following legal question:

Question: {query}

Legal Documents Context:
{context}

Please provide a comprehensive legal analysis that:
1. Directly addresses the question asked
2. References specific legal provisions and documents
3. Explains the relevant legal principles
4. Provides practical implications
5. Includes appropriate legal disclaimers

{"6. Includes citations to the specific legal documents referenced" if include_citations else ""}

Important Guidelines:
- Be precise and accurate in your legal analysis
- Cite specific article numbers, sections, or provisions when available
- Distinguish between mandatory requirements and recommendations
- Always include a disclaimer about seeking professional legal counsel
- Focus on Saudi Arabian law and regulations when applicable
- If the answer requires interpretation, acknowledge any ambiguity

Legal Analysis:
"""
        return prompt
    
    def _extract_citations(self, documents: List[Dict]) -> List[Dict]:
        """Extract citation information from documents"""
        citations = []
        for doc in documents:
            citation = {
                "title": doc.get('title', 'Untitled'),
                "document_type": doc.get('document_type', 'Unknown'),
                "law_number": doc.get('law_number', ''),
                "jurisdiction": doc.get('jurisdiction', 'Unknown'),
                "source": doc.get('source', 'Unknown'),
                "date_published": doc.get('date_published', 'Unknown')
            }
            citations.append(citation)
        return citations
    
    def get_query_history(self) -> List[Dict]:
        """Get the history of legal queries for audit purposes"""
        return self.query_history
    
    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        legal_logger.info("Legal RAG engine cache cleared")
    
    def get_legal_categories(self) -> List[str]:
        """Get available legal document categories"""
        try:
            if not self.weaviate_client:
                return []
            
            # Query to get unique categories
            result = self.weaviate_client.query.aggregate(self.legal_class).with_fields("category { count }").do()
            
            categories = []
            if result and "data" in result:
                agg_data = result["data"].get("Aggregate", {}).get(self.legal_class, [])
                for item in agg_data:
                    if "category" in item:
                        categories.extend([cat["value"] for cat in item["category"]])
            
            return sorted(list(set(categories)))
            
        except Exception as e:
            legal_logger.error(f"Error getting legal categories: {e}")
            return ["Corporate Law", "Contract Law", "Regulatory Compliance", "Employment Law", "Commercial Law"]  # Fallback
    
    def get_available_jurisdictions(self) -> List[str]:
        """Get available jurisdictions"""
        try:
            if not self.weaviate_client:
                return []
            
            # Query to get unique jurisdictions
            result = self.weaviate_client.query.aggregate(self.legal_class).with_fields("jurisdiction { count }").do()
            
            jurisdictions = []
            if result and "data" in result:
                agg_data = result["data"].get("Aggregate", {}).get(self.legal_class, [])
                for item in agg_data:
                    if "jurisdiction" in item:
                        jurisdictions.extend([jur["value"] for jur in item["jurisdiction"]])
            
            return sorted(list(set(jurisdictions)))
            
        except Exception as e:
            legal_logger.error(f"Error getting jurisdictions: {e}")
            return ["Saudi Arabia", "GCC", "International"]  # Fallback