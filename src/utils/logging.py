"""
Logging utilities for M-Pesa STK Push application.
Provides structured logging and performance monitoring.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable


class LoggerSetup:
    """Centralized logger setup."""
    
    @staticmethod
    def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
        """Setup and configure logger."""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Avoid duplicate handlers
        if not logger.handlers:
            # Create console handler
            handler = logging.StreamHandler()
            handler.setLevel(level)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            
            # Add handler to logger
            logger.addHandler(handler)
        
        return logger


def timing_decorator(logger: logging.Logger) -> Callable:
    """
    Decorator to measure and log function execution time.
    
    Args:
        logger: Logger instance to use for timing logs
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{func.__name__} executed successfully in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {str(e)}")
                raise
        return wrapper
    return decorator


class SecurityLogger:
    """Security-focused logging utility."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(self, phone_number: str, amount: float, masked: bool = True) -> None:
        """Log STK push request with optional phone number masking."""
        if masked and len(phone_number) >= 6:
            masked_phone = f"{phone_number[:3]}***{phone_number[-3:]}"
        else:
            masked_phone = phone_number
        
        self.logger.info(f"STK push request: Phone={masked_phone}, Amount=KES {amount}")
    
    def log_response(self, success: bool, response_code: str = None, error_message: str = None) -> None:
        """Log STK push response."""
        if success:
            self.logger.info(f"STK push successful: ResponseCode={response_code}")
        else:
            self.logger.warning(f"STK push failed: {error_message}")
    
    def log_token_generation(self, from_cache: bool = False) -> None:
        """Log access token generation."""
        if from_cache:
            self.logger.info("Using cached access token")
        else:
            self.logger.info("Generated new access token")
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """Log errors with context."""
        if context:
            self.logger.error(f"Error in {context}: {str(error)}")
        else:
            self.logger.error(f"Error: {str(error)}")


# Create application loggers
app_logger = LoggerSetup.setup_logger("mpesa_app")
security_logger = SecurityLogger(LoggerSetup.setup_logger("mpesa_security"))
performance_logger = LoggerSetup.setup_logger("mpesa_performance")