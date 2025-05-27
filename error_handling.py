#!/usr/bin/env python3
# error_handling.py - Lightweight exception handling

import logging
import functools
import time
from typing import Dict, Any, Optional, Callable, Union, Type, List

logger = logging.getLogger("market_intelligence")

class ApplicationError(Exception):
    """Base application error"""
    
    def __init__(self, message: str, error_code: str = "app_error", user_message: str = None):
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or "An application error occurred."
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {"error_code": self.error_code, "message": self.message, "user_message": self.user_message}

class ConnectionError(ApplicationError):
    """Connection error"""
    def __init__(self, message: str, service_name: str = "external service"):
        super().__init__(message, "connection_error", f"Unable to connect to {service_name}.")
        self.service_name = service_name

class ServiceUnavailableError(ApplicationError):
    """Service unavailable error"""
    def __init__(self, service_name: str):
        super().__init__(f"Service {service_name} unavailable", "service_unavailable", 
                        f"{service_name} is currently unavailable.")
        self.service_name = service_name

def handle_exception(func: Callable) -> Callable:
    """Exception handling decorator"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApplicationError as e:
            logger.error(f"{e.error_code}: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise
    return wrapper

def retry_on_exception(max_retries: int = 3, base_delay: float = 1.0, 
                      retry_exceptions: Union[Type[Exception], List[Type[Exception]]] = (Exception,)) -> Callable:
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.1f}s")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed: {e}")
            
            if isinstance(last_exception, ApplicationError):
                raise last_exception
            else:
                raise ServiceUnavailableError(func.__name__) from last_exception
        return wrapper
    return decorator

def format_error_for_display(error: Exception, user_message: Optional[str] = None) -> Dict[str, Any]:
    """Format error for UI display"""
    if isinstance(error, ApplicationError):
        error_data = error.to_dict()
        error_data["user_message"] = user_message or error_data["user_message"]
        
        # Add suggestions based on error type
        if isinstance(error, ConnectionError):
            error_data["suggestions"] = ["Check internet connection", "Try again later", "Contact support"]
        elif isinstance(error, ServiceUnavailableError):
            error_data["suggestions"] = ["Try offline mode", "Try again later", "Check system status"]
        else:
            error_data["suggestions"] = ["Try again", "Refresh application", "Contact support"]
        return error_data
    
    # Handle common exceptions
    error_type = type(error).__name__
    suggestions = ["Try again", "Check input", "Contact support"]
    
    if "requests" in str(type(error)):
        if "ConnectionError" in error_type:
            return {"type": "connection_error", "user_message": "Connection failed", 
                   "technical_details": str(error), "suggestions": ["Check internet", "Try again"]}
        elif "Timeout" in error_type:
            return {"type": "timeout_error", "user_message": "Request timed out", 
                   "technical_details": str(error), "suggestions": ["Try again", "Check connection"]}
    
    return {"type": error_type.lower(), "user_message": user_message or "An error occurred",
           "technical_details": str(error), "suggestions": suggestions}

def safe_execute(func: Callable, *args, default_return=None, error_message="Execution failed", 
                log_error=True, **kwargs):
    """Safely execute function with fallback"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(f"{error_message}: {e}")
        return default_return

class ErrorHandler:
    """Context manager for error handling"""
    
    def __init__(self, operation_name: str, default_value=None, reraise=False):
        self.operation_name = operation_name
        self.default_value = default_value
        self.reraise = reraise
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Error during {self.operation_name}: {exc_val}")
            if not self.reraise:
                return True  # Suppress exception
        return False