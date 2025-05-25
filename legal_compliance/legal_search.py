#!/usr/bin/env python3
# legal_compliance/legal_search.py - Legal Search Engine for web-based legal research

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger("legal_compliance")

class LegalSearchEngine:
    """Legal search engine for web-based legal research and compliance checking"""
    
    def __init__(self, web_search_engine=None):
        self.web_search_engine = web_search_engine
        self.cache = {}
        self.cache_duration = 3600  # 1 hour cache
        
        # Legal search configuration
        self.legal_domains = [
            "gov.sa", "moj.gov.sa", "mci.gov.sa", "sagia.gov.sa",
            "saudilaw.org", "legal-database.sa"
        ]
        
        self.search_categories = {
            "Corporate Law": ["company formation", "corporate governance", "shareholders"],
            "Contract Law": ["contract terms", "agreement enforcement", "breach of contract"],
            "Employment Law": ["labor regulations", "employee rights", "workplace compliance"],
            "Regulatory Compliance": ["regulatory requirements", "compliance standards", "regulatory updates"],
            "Commercial Law": ["commercial transactions", "business regulations", "trade law"],
            "Banking Law": ["banking regulations", "financial services", "monetary policy"],
            "Real Estate Law": ["property law", "real estate transactions", "land regulations"],
            "Tax Law": ["tax regulations", "tax compliance", "tax procedures"],
            "International Trade": ["import regulations", "export compliance", "trade agreements"]
        }
        
        logger.info("Legal Search Engine initialized")
    
    def search_legal_web_content(self, query: str, legal_category: str = None, 
                                jurisdiction: str = "Saudi Arabia", max_results: int = 5) -> Dict[str, Any]:
        """
        Search for legal content on the web with legal-specific filtering
        
        Args:
            query: Search query
            legal_category: Legal category to focus on
            jurisdiction: Legal jurisdiction to search within
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results and legal analysis
        """
        try:
            # Check cache first
            cache_key = f"{query}_{legal_category}_{jurisdiction}_{max_results}"
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if datetime.now() - datetime.fromisoformat(cached_result['timestamp']) < timedelta(seconds=self.cache_duration):
                    logger.info("Returning cached legal search results")
                    return cached_result
            
            logger.info(f"Searching legal web content for: {query}")
            
            # Enhance query with legal terms
            enhanced_query = self._enhance_legal_query(query, legal_category, jurisdiction)
            
            if self.web_search_engine:
                # Use real web search if available
                results = self.web_search_engine.research_topic(
                    query=enhanced_query,
                    context="legal compliance regulation",
                    market=jurisdiction,
                    top_n=max_results
                )
                
                # Filter and enhance results for legal relevance
                legal_results = self._filter_legal_results(results, legal_category)
                
            else:
                # Generate mock legal search results
                legal_results = self._generate_mock_legal_results(query, legal_category, jurisdiction, max_results)
            
            # Add timestamp and cache
            legal_results['timestamp'] = datetime.now().isoformat()
            self.cache[cache_key] = legal_results
            
            return legal_results
            
        except Exception as e:
            logger.error(f"Error in legal web search: {e}")
            return {
                'query': query,
                'legal_category': legal_category,
                'jurisdiction': jurisdiction,
                'sources': [],
                'summary': f'Error occurred during legal search: {str(e)}',
                'key_findings': [],
                'error': str(e)
            }
    
    def search_legal_precedents(self, case_type: str, jurisdiction: str = "Saudi Arabia") -> List[Dict]:
        """
        Search for legal precedents and case law
        
        Args:
            case_type: Type of legal case to search for
            jurisdiction: Jurisdiction to search within
            
        Returns:
            List of legal precedents
        """
        try:
            logger.info(f"Searching legal precedents for: {case_type}")
            
            # Check cache
            cache_key = f"precedents_{case_type}_{jurisdiction}"
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if datetime.now() - datetime.fromisoformat(cached_result['timestamp']) < timedelta(seconds=self.cache_duration):
                    return cached_result['precedents']
            
            if self.web_search_engine:
                # Search for case law and precedents
                precedent_query = f"{case_type} case law precedent {jurisdiction} court decision"
                results = self.web_search_engine.research_topic(
                    query=precedent_query,
                    context="legal case law precedent",
                    market=jurisdiction,
                    top_n=3
                )
                
                precedents = self._extract_precedents_from_results(results, case_type, jurisdiction)
            else:
                precedents = self._generate_mock_precedents(case_type, jurisdiction)
            
            # Cache results
            cache_data = {
                'precedents': precedents,
                'timestamp': datetime.now().isoformat()
            }
            self.cache[cache_key] = cache_data
            
            return precedents
            
        except Exception as e:
            logger.error(f"Error searching legal precedents: {e}")
            return []
    
    def search_regulatory_updates(self, sector: str = None, days_back: int = 90) -> List[Dict]:
        """
        Search for recent regulatory updates and changes
        
        Args:
            sector: Specific sector to search for updates
            days_back: Number of days to look back for updates
            
        Returns:
            List of regulatory updates
        """
        try:
            logger.info(f"Searching regulatory updates for sector: {sector}")
            
            # Check cache
            cache_key = f"regulatory_updates_{sector}_{days_back}"
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if datetime.now() - datetime.fromisoformat(cached_result['timestamp']) < timedelta(seconds=self.cache_duration):
                    return cached_result['updates']
            
            if self.web_search_engine:
                # Search for regulatory updates
                update_query = f"regulatory update {sector or ''} Saudi Arabia new regulation recent"
                results = self.web_search_engine.research_topic(
                    query=update_query,
                    context="regulatory compliance update",
                    market="Saudi Arabia",
                    top_n=5
                )
                
                updates = self._extract_regulatory_updates(results, sector, days_back)
            else:
                updates = self._generate_mock_regulatory_updates(sector, days_back)
            
            # Cache results
            cache_data = {
                'updates': updates,
                'timestamp': datetime.now().isoformat()
            }
            self.cache[cache_key] = cache_data
            
            return updates
            
        except Exception as e:
            logger.error(f"Error searching regulatory updates: {e}")
            return []
    
    def search_compliance_requirements(self, business_type: str, jurisdiction: str = "Saudi Arabia") -> Dict[str, Any]:
        """
        Search for compliance requirements for a specific business type
        
        Args:
            business_type: Type of business to search requirements for
            jurisdiction: Jurisdiction to search within
            
        Returns:
            Dictionary with compliance requirements
        """
        try:
            logger.info(f"Searching compliance requirements for: {business_type}")
            
            # Check cache
            cache_key = f"compliance_{business_type}_{jurisdiction}"
            if cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if datetime.now() - datetime.fromisoformat(cached_result['timestamp']) < timedelta(seconds=self.cache_duration):
                    return cached_result
            
            if self.web_search_engine:
                # Search for compliance requirements
                compliance_query = f"{business_type} compliance requirements regulations {jurisdiction} license permit"
                results = self.web_search_engine.research_topic(
                    query=compliance_query,
                    context="business compliance regulatory requirements",
                    market=jurisdiction,
                    top_n=5
                )
                
                compliance_info = self._extract_compliance_requirements(results, business_type, jurisdiction)
            else:
                compliance_info = self._generate_mock_compliance_requirements(business_type, jurisdiction)
            
            # Add timestamp and cache
            compliance_info['timestamp'] = datetime.now().isoformat()
            self.cache[cache_key] = compliance_info
            
            return compliance_info
            
        except Exception as e:
            logger.error(f"Error searching compliance requirements: {e}")
            return {
                'business_type': business_type,
                'jurisdiction': jurisdiction,
                'requirements': [],
                'licenses_needed': [],
                'regulatory_bodies': [],
                'sources': [],
                'error': str(e)
            }
    
    def _enhance_legal_query(self, query: str, legal_category: str, jurisdiction: str) -> str:
        """Enhance search query with legal-specific terms"""
        enhanced_query = query
        
        # Add jurisdiction-specific terms
        if jurisdiction == "Saudi Arabia":
            enhanced_query += " Saudi Arabia law regulation royal decree"
        elif jurisdiction == "GCC":
            enhanced_query += " GCC Gulf Cooperation Council regulation"
        
        # Add category-specific terms
        if legal_category and legal_category in self.search_categories:
            category_terms = " ".join(self.search_categories[legal_category])
            enhanced_query += f" {category_terms}"
        
        # Add general legal terms
        enhanced_query += " legal compliance regulatory framework"
        
        return enhanced_query
    
    def _filter_legal_results(self, results: Dict, legal_category: str) -> Dict:
        """Filter and enhance search results for legal relevance"""
        if not results or 'data' not in results:
            return self._generate_empty_legal_results()
        
        filtered_sources = []
        key_findings = []
        
        for source in results['data']:
            # Check if source is from a legal domain or contains legal keywords
            url = source.get('url', '').lower()
            title = source.get('title', '').lower()
            summary = source.get('summary', '').lower()
            
            legal_keywords = ['law', 'regulation', 'legal', 'compliance', 'regulatory', 'statute', 'decree']
            
            if any(domain in url for domain in self.legal_domains) or \
               any(keyword in title or keyword in summary for keyword in legal_keywords):
                
                # Enhance source with legal metadata
                legal_source = {
                    'title': source.get('title', 'Legal Document'),
                    'url': source.get('url', ''),
                    'summary': source.get('summary', ''),
                    'retrieved_date': datetime.now().isoformat(),
                    'legal_relevance': 'high' if any(domain in url for domain in self.legal_domains) else 'medium',
                    'source_type': self._determine_legal_source_type(source)
                }
                filtered_sources.append(legal_source)
                
                # Extract key findings
                if legal_source['legal_relevance'] == 'high':
                    key_findings.append(f"Key legal principle from {legal_source['title']}")
        
        return {
            'query': results.get('query', ''),
            'legal_category': legal_category,
            'jurisdiction': results.get('market', 'Unknown'),
            'sources': filtered_sources,
            'summary': self._generate_legal_summary(filtered_sources, legal_category),
            'key_findings': key_findings,
            'total_sources': len(filtered_sources)
        }
    
    def _determine_legal_source_type(self, source: Dict) -> str:
        """Determine the type of legal source"""
        url = source.get('url', '').lower()
        title = source.get('title', '').lower()
        
        if 'gov.sa' in url:
            return 'government_official'
        elif 'court' in url or 'court' in title:
            return 'court_decision'
        elif 'law' in url or 'legal' in url:
            return 'legal_database'
        elif 'regulation' in title or 'decree' in title:
            return 'regulatory_document'
        else:
            return 'legal_commentary'
    
    def _generate_legal_summary(self, sources: List[Dict], legal_category: str) -> str:
        """Generate a summary of legal search results"""
        if not sources:
            return f"No specific legal sources found for {legal_category or 'the requested topic'}."
        
        official_sources = [s for s in sources if s['source_type'] == 'government_official']
        
        summary = f"Found {len(sources)} legal sources"
        if official_sources:
            summary += f", including {len(official_sources)} official government sources"
        
        summary += f" related to {legal_category or 'legal matters'} in Saudi Arabia."
        
        if legal_category:
            summary += f" The sources cover key aspects of {legal_category.lower()} including regulatory requirements and compliance procedures."
        
        return summary
    
    def _extract_precedents_from_results(self, results: Dict, case_type: str, jurisdiction: str) -> List[Dict]:
        """Extract legal precedents from search results"""
        precedents = []
        
        if results and 'data' in results:
            for source in results['data'][:3]:  # Limit to top 3 results
                precedent = {
                    'case_title': source.get('title', f"Legal Precedent for {case_type}"),
                    'case_type': case_type,
                    'jurisdiction': jurisdiction,
                    'summary': source.get('summary', f"Important precedent case regarding {case_type} in {jurisdiction}"),
                    'source_url': source.get('url', ''),
                    'retrieved_date': datetime.now().isoformat(),
                    'relevance_score': 0.8  # Mock relevance score
                }
                precedents.append(precedent)
        
        return precedents
    
    def _extract_regulatory_updates(self, results: Dict, sector: str, days_back: int) -> List[Dict]:
        """Extract regulatory updates from search results"""
        updates = []
        
        if results and 'data' in results:
            for source in results['data'][:5]:  # Limit to top 5 results
                update = {
                    'title': source.get('title', f"Regulatory Update - {sector or 'General'}"),
                    'sector': sector,
                    'update_date': datetime.now().isoformat(),
                    'summary': source.get('summary', f"Recent regulatory changes affecting {sector or 'various sectors'}"),
                    'source': source.get('url', 'Saudi Arabian Regulatory Authority'),
                    'impact_level': self._assess_regulatory_impact(source),
                    'retrieved_date': datetime.now().isoformat()
                }
                updates.append(update)
        
        return updates
    
    def _assess_regulatory_impact(self, source: Dict) -> str:
        """Assess the impact level of a regulatory update"""
        title = source.get('title', '').lower()
        summary = source.get('summary', '').lower()
        
        high_impact_terms = ['mandatory', 'required', 'penalty', 'fine', 'compliance deadline']
        medium_impact_terms = ['guideline', 'recommendation', 'update', 'clarification']
        
        if any(term in title or term in summary for term in high_impact_terms):
            return 'high'
        elif any(term in title or term in summary for term in medium_impact_terms):
            return 'medium'
        else:
            return 'low'
    
    def _extract_compliance_requirements(self, results: Dict, business_type: str, jurisdiction: str) -> Dict[str, Any]:
        """Extract compliance requirements from search results"""
        requirements = []
        licenses_needed = []
        regulatory_bodies = []
        sources = []
        
        if results and 'data' in results:
            for source in results['data']:
                sources.append({
                    'title': source.get('title', ''),
                    'url': source.get('url', ''),
                    'summary': source.get('summary', ''),
                    'retrieved_date': datetime.now().isoformat()
                })
                
                # Extract requirements from source content
                content = source.get('summary', '').lower()
                if 'license' in content or 'permit' in content:
                    licenses_needed.append(f"Business license for {business_type}")
                if 'registration' in content:
                    requirements.append(f"Business registration for {business_type}")
                if 'ministry' in content or 'authority' in content:
                    regulatory_bodies.append("Relevant Regulatory Authority")
        
        # Add default requirements if none found
        if not requirements:
            requirements = [
                f"Commercial registration for {business_type}",
                f"Regulatory compliance for {business_type} operations",
                "Tax registration and compliance"
            ]
        
        if not licenses_needed:
            licenses_needed = [
                f"Primary business license for {business_type}",
                "Municipal permits",
                "Industry-specific certifications"
            ]
        
        if not regulatory_bodies:
            regulatory_bodies = [
                "Ministry of Commerce and Investment",
                "Saudi Arabian General Investment Authority",
                "Relevant sector regulatory body"
            ]
        
        return {
            'business_type': business_type,
            'jurisdiction': jurisdiction,
            'requirements': requirements,
            'licenses_needed': licenses_needed,
            'regulatory_bodies': regulatory_bodies,
            'sources': sources,
            'compliance_complexity': self._assess_compliance_complexity(requirements, licenses_needed)
        }
    
    def _assess_compliance_complexity(self, requirements: List[str], licenses: List[str]) -> str:
        """Assess the complexity of compliance requirements"""
        total_items = len(requirements) + len(licenses)
        
        if total_items > 10:
            return 'high'
        elif total_items > 5:
            return 'medium'
        else:
            return 'low'
    
    # Mock data generation methods
    def _generate_mock_legal_results(self, query: str, legal_category: str, jurisdiction: str, max_results: int) -> Dict:
        """Generate mock legal search results"""
        mock_sources = []
        
        for i in range(min(max_results, 3)):
            mock_sources.append({
                'title': f"Legal Document {i+1}: {query} in {jurisdiction}",
                'url': f'https://example-legal-source-{i+1}.gov.sa',
                'summary': f"Official legal guidance regarding {query} in {jurisdiction}. This document outlines key requirements and compliance procedures.",
                'retrieved_date': datetime.now().isoformat(),
                'legal_relevance': 'high',
                'source_type': 'government_official'
            })
        
        return {
            'query': query,
            'legal_category': legal_category,
            'jurisdiction': jurisdiction,
            'sources': mock_sources,
            'summary': f'Found {len(mock_sources)} official legal sources regarding {query} in {jurisdiction}',
            'key_findings': [f"Key legal principle related to {query}"],
            'is_mock_data': True
        }
    
    def _generate_mock_precedents(self, case_type: str, jurisdiction: str) -> List[Dict]:
        """Generate mock legal precedents"""
        return [
            {
                'case_title': f"Important Precedent Case for {case_type}",
                'case_type': case_type,
                'jurisdiction': jurisdiction,
                'summary': f"Landmark legal precedent regarding {case_type} in {jurisdiction} that established key legal principles",
                'source_url': 'https://example-legal-database.gov.sa/case-123',
                'retrieved_date': datetime.now().isoformat(),
                'relevance_score': 0.9
            }
        ]
    
    def _generate_mock_regulatory_updates(self, sector: str, days_back: int) -> List[Dict]:
        """Generate mock regulatory updates"""
        return [
            {
                'title': f"Recent Regulatory Update - {sector or 'General Business'}",
                'sector': sector,
                'update_date': (datetime.now() - timedelta(days=30)).isoformat(),
                'summary': f"Important regulatory changes affecting {sector or 'various business sectors'} in Saudi Arabia",
                'source': 'Saudi Arabian Regulatory Authority',
                'impact_level': 'medium',
                'retrieved_date': datetime.now().isoformat()
            }
        ]
    
    def _generate_mock_compliance_requirements(self, business_type: str, jurisdiction: str) -> Dict[str, Any]:
        """Generate mock compliance requirements"""
        return {
            'business_type': business_type,
            'jurisdiction': jurisdiction,
            'requirements': [
                f"Commercial registration for {business_type}",
                f"Regulatory compliance for {business_type} operations",
                "Tax registration and compliance",
                "Health and safety compliance",
                "Environmental compliance (if applicable)"
            ],
            'licenses_needed': [
                f"Primary business license for {business_type}",
                "Municipal permits",
                "Industry-specific certifications",
                "Import/export licenses (if applicable)"
            ],
            'regulatory_bodies': [
                "Ministry of Commerce and Investment",
                "Saudi Arabian General Investment Authority",
                "Relevant sector regulatory body",
                "Municipal authorities",
                "Tax authorities"
            ],
            'sources': [
                {
                    'title': f"Official Guide to {business_type} Compliance",
                    'url': 'https://example-gov-portal.gov.sa',
                    'summary': f"Complete guide to regulatory requirements for {business_type}",
                    'retrieved_date': datetime.now().isoformat()
                }
            ],
            'compliance_complexity': 'medium',
            'is_mock_data': True
        }
    
    def _generate_empty_legal_results(self) -> Dict:
        """Generate empty legal search results"""
        return {
            'query': '',
            'legal_category': None,
            'jurisdiction': 'Unknown',
            'sources': [],
            'summary': 'No legal sources found',
            'key_findings': [],
            'total_sources': 0
        }
    
    def clear_cache(self):
        """Clear the search cache"""
        self.cache.clear()
        logger.info("Legal search engine cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'total_cached_items': len(self.cache),
            'cache_duration_seconds': self.cache_duration,
            'oldest_cached_item': min([item.get('timestamp', '') for item in self.cache.values()]) if self.cache else None,
            'newest_cached_item': max([item.get('timestamp', '') for item in self.cache.values()]) if self.cache else None
        }