#!/usr/bin/env python3
# error_handling.py - Centralized exception handling for the application

import logging
import traceback
import functools
import time
import requests
from typing import Dict, Any, Optional, Callable, List, Union, Type

logger = logging.getLogger("market_intelligence")

class ApplicationError(Exception):
    """Base exception class for application-specific errors"""
    
    def __init__(self, message: str, error_code: str = "app_error", user_message: str = None):
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or "An application error occurred."
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary for easy formatting"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_message": self.user_message
        }

class ConnectionError(ApplicationError):
    """Error when connecting to external services"""
    
    def __init__(self, message: str, service_name: str = "external service"):
        super().__init__(
            message=message,
            error_code="connection_error",
            user_message=f"Unable to connect to {service_name}. Please check your internet connection."
        )
        self.service_name = service_name

class ServiceUnavailableError(ApplicationError):
    """Error when a required service is unavailable"""
    
    def __init__(self, service_name: str):
        super().__init__(
            message=f"Service {service_name} is unavailable",
            error_code="service_unavailable",
            user_message=f"The {service_name} service is currently unavailable. Please try again later."
        )
        self.service_name = service_name

class DataProcessingError(ApplicationError):
    """Error when processing data"""
    
    def __init__(self, message: str, data_type: str = "data"):
        super().__init__(
            message=message,
            error_code="data_processing_error",
            user_message=f"An error occurred while processing {data_type}."
        )
        self.data_type = data_type

class FileOperationError(ApplicationError):
    """Error during file operations"""
    
    def __init__(self, message: str, filename: str, operation: str = "access"):
        super().__init__(
            message=message,
            error_code="file_operation_error",
            user_message=f"Unable to {operation} the file: {filename}"
        )
        self.filename = filename
        self.operation = operation

def handle_exception(func: Callable) -> Callable:
    """Decorator to handle exceptions in a standardized way"""
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApplicationError as e:
            # Log application-specific errors
            logger.error(f"{e.error_code}: {e.message}")
            raise
        except requests.exceptions.ConnectionError as e:
            # Handle connection errors
            error = ConnectionError(
                message=str(e),
                service_name=kwargs.get('service_name', 'remote service')
            )
            logger.error(f"{error.error_code}: {error.message}")
            raise error from e
        except requests.exceptions.Timeout as e:
            # Handle timeout errors
            error = ConnectionError(
                message=f"Request timed out: {str(e)}",
                service_name=kwargs.get('service_name', 'remote service')
            )
            logger.error(f"{error.error_code}: {error.message}")
            raise error from e
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            raise
    
    return wrapper

def retry_on_exception(
    max_retries: int = 3, 
    base_delay: float = 1.0, 
    backoff_factor: float = 2.0,
    retry_exceptions: Union[Type[Exception], List[Type[Exception]]] = (Exception,),
    log_level: str = "WARNING"
) -> Callable:
    """
    Decorator that retries a function on specified exceptions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        backoff_factor: Factor by which to increase the delay after each retry
        retry_exceptions: Exception type(s) that should trigger a retry
        log_level: Logging level for retry messages ("DEBUG", "INFO", "WARNING", "ERROR")
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            log_func = getattr(logger, log_level.lower())
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        delay = base_delay * (backoff_factor ** attempt)
                        log_func(
                            f"Attempt {attempt + 1}/{max_retries} for {func.__name__} "
                            f"failed: {e}. Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} attempts for {func.__name__} failed. "
                            f"Last error: {e}"
                        )
            
            # If we get here, all retries failed
            if isinstance(last_exception, ApplicationError):
                raise last_exception
            else:
                # Convert to ApplicationError for better handling
                raise ServiceUnavailableError(func.__name__) from last_exception
        
        return wrapper
    
    return decorator

def format_error_for_display(error: Exception, user_friendly_message: Optional[str] = None) -> Dict[str, Any]:
    """
    Format error for display in the UI with user-friendly messages and suggestions
    
    Args:
        error: The exception object
        user_friendly_message: Optional custom message to display
    
    Returns:
        Dictionary with formatted error information
    """
    try:
        # If it's our ApplicationError, use its built-in formatting
        if isinstance(error, ApplicationError):
            error_data = error.to_dict()
            error_data["user_message"] = user_friendly_message or error_data["user_message"]
            
            # Add appropriate suggestions based on error type
            if isinstance(error, ConnectionError):
                error_data["suggestions"] = [
                    "Check your internet connection",
                    "Verify that the service is online",
                    "Try again in a few moments",
                    "Contact support if the problem persists"
                ]
            elif isinstance(error, ServiceUnavailableError):
                error_data["suggestions"] = [
                    "Try using the system in offline mode",
                    "Try again later when services may be back online",
                    "Check system status for maintenance notifications"
                ]
            elif isinstance(error, FileOperationError):
                error_data["suggestions"] = [
                    "Verify that the file exists and is not open in another program",
                    "Check if you have sufficient permissions",
                    "Try a different file location"
                ]
            else:
                error_data["suggestions"] = [
                    "Try again with a different input",
                    "Refresh the application",
                    "Contact support if the problem persists"
                ]
            
            return error_data
        
        # Handle specific external exceptions
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
            # Generic error handling
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
        # Meta error handling (error during error handling)
        logger.error(f"Error in format_error_for_display: {e}")
        return {
            "type": "error_handling_error",
            "user_message": "An error occurred while processing another error.",
            "technical_details": f"Original error: {str(error)}, Error handling error: {str(e)}",
            "suggestions": ["Contact support"]
        }

def safe_execute(
    func: Callable, 
    *args, 
    default_return=None, 
    error_message="Function execution failed", 
    log_error=True,
    **kwargs
):
    """
    Safely execute a function, returning a default value on error
    
    Args:
        func: Function to execute
        *args: Arguments to pass to the function
        default_return: Value to return if the function raises an exception
        error_message: Message to log if an error occurs
        log_error: Whether to log the error
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            logger.error(f"{error_message}: {e}")
            logger.debug(traceback.format_exc())
        return default_return

def check_service_availability(service_name: str, check_func: Callable, *args, **kwargs) -> bool:
    """
    Check if a service is available
    
    Args:
        service_name: Name of the service for logging
        check_func: Function to call to check availability
        *args: Arguments to pass to check_func
        **kwargs: Keyword arguments to pass to check_func
    
    Returns:
        True if service is available, False otherwise
    """
    try:
        logger.debug(f"Checking availability of {service_name}...")
        result = check_func(*args, **kwargs)
        logger.debug(f"{service_name} availability check result: {result}")
        return bool(result)
    except Exception as e:
        logger.warning(f"{service_name} is unavailable: {str(e)}")
        return False

class ErrorHandler:
    """
    Context manager for error handling
    
    Example:
        with ErrorHandler("Processing data", default_value=[]):
            result = process_data(data)
            return result
    """
    
    def __init__(self, operation_name: str, default_value=None, reraise=False, log_level="ERROR"):
        self.operation_name = operation_name
        self.default_value = default_value
        self.reraise = reraise
        self.log_level = log_level.lower()
        self.log_func = getattr(logger, self.log_level)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.log_func(f"Error during {self.operation_name}: {exc_val}")
            
            if self.log_level in ['error', 'critical']:
                logger.debug(traceback.format_exc())
            
            if not self.reraise:
                return True  # Suppress the exception
        
        return False  # Allow the exception to propagate

# Register common error handlers for modules

def register_error_handlers_for_module(module_name: str):
    """
    Register error handlers for a module
    
    This function can be used to patch external modules with our error handling,
    helping to standardize error responses across the application.
    
    Args:
        module_name: The name of the module to patch
    """
    try:
        module = __import__(module_name)
        
        # Example: Patch specific functions with retry behavior
        if module_name == 'requests':
            original_get = module.get
            
            @functools.wraps(original_get)
            def get_with_retry(*args, **kwargs):
                return retry_on_exception(
                    max_retries=3,
                    retry_exceptions=(
                        module.exceptions.ConnectionError,
                        module.exceptions.Timeout
                    )
                )(original_get)(*args, **kwargs)
            
            module.get = get_with_retry
        
        logger.debug(f"Registered error handlers for module: {module_name}")
    except ImportError:
        logger.warning(f"Could not import module {module_name} to register error handlers")
    except Exception as e:
        logger.error(f"Error registering error handlers for {module_name}: {e}")

if __name__ == "__main__":
    # Self-test
    logging.basicConfig(level=logging.DEBUG)
    
    # Test the retry decorator
    @retry_on_exception(max_retries=3, base_delay=0.1, log_level="DEBUG")
    def test_retry(should_fail=True):
        if should_fail:
            raise ValueError("Test error")
        return "Success"
    
    try:
        result = test_retry(should_fail=False)
        logger.info(f"Success result: {result}")
        
        result = test_retry(should_fail=True)
    except Exception as e:
        logger.info(f"Expected error: {e}")
    
    # Test error formatting
    try:
        raise ConnectionError("Test connection error", "TestAPI")
    except Exception as e:
        error_data = format_error_for_display(e)
        logger.info(f"Formatted error: {error_data}")
    
    logger.info("Error handling module self-test complete")