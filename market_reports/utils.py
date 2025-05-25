import os
import json
import time
import requests
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
import logging
from functools import wraps
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("market_intelligence.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("market_intelligence")

# -----------------------------
# File & Encoding Utilities
# -----------------------------

def detect_file_encoding(filename: str) -> str:
    """Detect the encoding of a file with robust error handling"""
    try:
        from chardet.universaldetector import UniversalDetector
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
            logger.warning(f"Error detecting encoding for {filename}: {e}")
            return 'utf-8'  # Default to UTF-8 on error
    except ImportError:
        logger.warning("chardet not installed. Defaulting to utf-8.")
        return 'utf-8'

def read_file_with_encoding(filename: str) -> Optional[str]:
    """Read a file with automatic encoding detection and fallbacks"""
    try:
        # Try to detect encoding
        encoding = detect_file_encoding(filename)
        logger.debug(f"Detected encoding {encoding} for file {filename}")
        
        # Try to read with detected encoding
        try:
            with open(filename, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            logger.debug(f"Failed to decode with {encoding}, trying utf-8")
            # If that fails, try UTF-8
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode with utf-8, using latin-1")
                # If UTF-8 fails, fall back to latin-1 which should always work
                with open(filename, 'r', encoding='latin-1') as f:
                    return f.read()
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        return None

def write_file_with_encoding(filename: str, content: str) -> bool:
    """Write content to a file with UTF-8 encoding, ensuring directory exists"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Write with UTF-8 encoding
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"Successfully wrote to file {filename}")
        return True
    except Exception as e:
        logger.error(f"Error writing file {filename}: {e}")
        return False

def load_json_with_encoding(filename: str) -> Optional[Any]:
    """Load JSON data with proper encoding handling"""
    content = read_file_with_encoding(filename)
    if content is None:
        return None
        
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for file {filename}: {e}")
        return None

def save_json_with_encoding(filename: str, data: Any, indent: int = 2) -> bool:
    """Save JSON data with proper encoding handling"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Write with UTF-8 encoding and ensure_ascii=False
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        
        logger.debug(f"Successfully saved JSON to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file {filename}: {e}")
        return False

# -----------------------------
# HTTP & Web Utilities
# -----------------------------

def extract_html_content(html_content: str) -> str:
    """Extract clean text from HTML content with proper encoding handling"""
    try:
        from bs4 import BeautifulSoup
        
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

def http_request_with_retry(url: str, method: str = "GET", headers: Dict = None, 
                           data: Any = None, max_retries: int = 3, 
                           base_delay: float = 2.0, timeout: int = 15) -> requests.Response:
    """Make HTTP request with exponential backoff retry logic"""
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; MarketIntelligencePlatform/1.0; +https://linksaudi.com/bot)'}
    
    for attempt in range(max_retries):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                timeout=timeout
            )
            response.raise_for_status()
            return response
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError) as e:
            if attempt < max_retries - 1:
                # Exponential backoff
                sleep_time = base_delay * (2 ** attempt)
                logger.warning(f"Request attempt {attempt+1} failed: {e}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                # Final attempt failed
                logger.error(f"All {max_retries} request attempts failed for {url}: {e}")
                raise

# -----------------------------
# Error Handling Utilities
# -----------------------------

def format_error_for_display(error, user_friendly_message=None):
    """Format error message for UI display"""
    try:
        if isinstance(error, requests.exceptions.ConnectionError):
            return {
                "type": "connection_error",
                "user_message": user_friendly_message or "Unable to connect to the server. Please check your internet connection.",
                "technical_details": str(error),
                "suggestions": [
                    "Check your internet connection",
                    "Try again in a few moments",
                    "Contact support if the problem persists"
                ]
            }
        elif isinstance(error, requests.exceptions.Timeout):
            return {
                "type": "timeout_error",
                "user_message": user_friendly_message or "The request timed out. The server might be busy.",
                "technical_details": str(error),
                "suggestions": [
                    "Try again with a simpler query",
                    "Try again later when the server might be less busy",
                    "Check if your connection is stable"
                ]
            }
        elif isinstance(error, ValueError):
            return {
                "type": "value_error",
                "user_message": user_friendly_message or "There was a problem with your input.",
                "technical_details": str(error),
                "suggestions": [
                    "Check your input for any special characters or formatting issues",
                    "Try a different query",
                    "Refer to the documentation for proper input format"
                ]
            }
        else:
            return {
                "type": "unknown_error",
                "user_message": user_friendly_message or "An unexpected error occurred.",
                "technical_details": str(error),
                "suggestions": [
                    "Try again",
                    "Refresh the page",
                    "Contact support if the problem persists"
                ]
            }
    except Exception as e:
        logger.error(f"Error in format_error_for_display: {e}")
        # Fallback error response
        return {
            "type": "error_handling_error",
            "user_message": "An error occurred while processing another error.",
            "technical_details": f"Original error: {str(error)}, Error handling error: {str(e)}",
            "suggestions": ["Contact support"]
        }

def safe_execute(func: Callable, *args, default_return=None, error_message="Function execution failed", **kwargs):
    """Execute a function safely, returning a default value on error"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{error_message}: {e}")
        logger.debug(traceback.format_exc())
        return default_return

# -----------------------------
# AI Output Cleanup Utilities
# -----------------------------

def clean_ai_language(content: str) -> str:
    """Clean AI/LLM-specific language to make the content more executive-friendly"""
    import re
    
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

# -----------------------------
# Logging Decorators
# -----------------------------

def log_function_call(func):
    """Decorator to log function calls with timing"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        logger.debug(f"Calling {func_name}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.debug(f"{func_name} completed in {elapsed_time:.2f}s")
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"{func_name} failed after {elapsed_time:.2f}s: {e}")
            logger.debug(traceback.format_exc())
            raise
    
    return wrapper

def retry_on_exception(max_retries=3, base_delay=1.0, backoff_factor=2.0, 
                      exceptions=(Exception,), logger=logger):
    """Decorator to retry a function on exception with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (backoff_factor ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} for {func.__name__} "
                            f"failed: {e}. Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} attempts for {func.__name__} failed. "
                            f"Last error: {e}"
                        )
                        raise
        return wrapper
    return decorator

# -----------------------------
# Config Management
# -----------------------------

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file with fallback to defaults"""
        config = load_json_with_encoding(self.config_file)
        
        if config is None:
            logger.warning(f"Could not load config from {self.config_file}, using defaults")
            config = self._default_config()
            # Try to save the default config
            save_json_with_encoding(self.config_file, config)
        
        return config
    
    def _default_config(self):
        """Default configuration settings"""
        return {
            "api_keys": {
                "openai": os.getenv("OPENAI_API_KEY", ""),
                "weaviate": {
                    "url": os.getenv("WEAVIATE_URL", ""),
                    "api_key": os.getenv("WEAVIATE_API_KEY", "")
                }
            },
            "embedding": {
                "model": "text-embedding-3-small",
                "dimensions": 1536,
                "use_local_fallback": True
            },
            "reports": {
                "default_sections": [
                    "Executive Summary",
                    "Market Overview",
                    "Sector Analysis",
                    "Market Trends",
                    "Future Outlook",
                    "Conclusion"
                ]
            },
            "system": {
                "min_search_interval": 5,
                "max_retries": 3,
                "chart_dir": "report_charts",
                "report_dir": "market_reports",
                "log_level": "INFO"
            }
        }
    
    def get(self, key, default=None):
        """Get a configuration value with dot notation support"""
        parts = key.split('.')
        value = self.config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def update(self, key, value):
        """Update a configuration value with dot notation support"""
        parts = key.split('.')
        config = self.config
        
        # Navigate to the correct level
        for i, part in enumerate(parts[:-1]):
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # Update the value
        config[parts[-1]] = value
        
        # Save the updated config
        saved = save_json_with_encoding(self.config_file, self.config)
        if not saved:
            logger.error(f"Failed to save updated configuration to {self.config_file}")
        
        return saved

# Create a singleton instance
config_manager = ConfigManager()

# -----------------------------
# State Management
# -----------------------------

class SystemState:
    """Centralized system state management"""
    
    def __init__(self):
        self.states = {
            'online': 'System is fully operational with all services available',
            'degraded': 'System is operational with some services unavailable',
            'offline': 'System is operating in offline mode with limited functionality'
        }
        self.current_state = 'unknown'
        self.components = {}
    
    def set_component_status(self, component: str, available: bool, description: str = ""):
        """Set the status of a system component"""
        self.components[component] = {
            'available': available,
            'description': description,
            'last_updated': datetime.now().isoformat()
        }
        self._update_system_state()
    
    def _update_system_state(self):
        """Update overall system state based on component statuses"""
        if not self.components:
            self.current_state = 'unknown'
            return
        
        # Check if all critical components are available
        critical_components = ['rag_engine', 'web_search']
        all_critical_available = all(
            self.components.get(comp, {}).get('available', False) 
            for comp in critical_components 
            if comp in self.components
        )
        
        some_available = any(comp.get('available', False) for comp in self.components.values())
        
        if all_critical_available:
            self.current_state = 'online'
        elif some_available:
            self.current_state = 'degraded'
        else:
            self.current_state = 'offline'
    
    def get_state(self):
        """Get the current system state"""
        return {
            'state': self.current_state,
            'description': self.states.get(self.current_state, 'Unknown state'),
            'components': self.components,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_component_status(self, component: str):
        """Get the status of a specific component"""
        return self.components.get(component, {
            'available': False,
            'description': 'Component not registered',
            'last_updated': None
        })

# Create a singleton instance
system_state = SystemState()

# Initialization function to be called at application startup
def initialize_utils(log_level=None):
    """Initialize the utilities module with proper logging"""
    if log_level:
        logger.setLevel(getattr(logging, log_level.upper()))
    
    # Set component directories
    os.makedirs(config_manager.get('system.chart_dir', 'report_charts'), exist_ok=True)
    os.makedirs(config_manager.get('system.report_dir', 'market_reports'), exist_ok=True)
    
    logger.info("Utilities module initialized")
    return True

if __name__ == "__main__":
    # Self-test
    initialize_utils("DEBUG")
    logger.info("Running utils.py self-test")
    
    # Test config manager
    test_value = config_manager.get("system.log_level")
    logger.info(f"Config test: system.log_level = {test_value}")
    
    # Test system state
    system_state.set_component_status("utils", True, "Utilities module is available")
    logger.info(f"System state: {system_state.get_state()}")
    
    logger.info("Self-test complete")