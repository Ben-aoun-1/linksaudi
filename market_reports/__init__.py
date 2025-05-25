#!/usr/bin/env python3
# market_reports/__init__.py - Market Reports Package Initialization

"""
LinkSaudi Market Intelligence Platform - Market Reports Package

This package contains all market analysis and reporting components including:
- RAG-enhanced market analysis
- Web search and research capabilities  
- Report generation and export
- PDF export functionality
- Text processing utilities
"""

__version__ = "1.0.0"
__author__ = "LinkSaudi"

# Import key components for easier access
try:
    from .utils import logger, config_manager, system_state
except ImportError:
    pass

try:
    from .rag_enhanced import generate_rag_response, semantic_search
except ImportError:
    pass

try:
    from .web_search import WebResearchEngine
except ImportError:
    pass

try:
    from .report_generator_enhanced import ReportGenerator
except ImportError:
    pass

try:
    from .market_report_system import MarketReportSystem
except ImportError:
    pass