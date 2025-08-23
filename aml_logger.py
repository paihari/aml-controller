#!/usr/bin/env python3
"""
Centralized logging configuration for AML Controller
Organizes logs by use cases for better debugging and monitoring
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Log file organization by use case
LOG_FILES = {
    'sanctions': 'sanctions_processing.log',
    'supabase': 'supabase_operations.log', 
    'api': 'api_requests.log',
    'statistics': 'statistics_calculations.log',
    'batch_processing': 'batch_operations.log',
    'general': 'general.log'
}

class AMLLogger:
    """Centralized logger factory for AML Controller"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, use_case: str = 'general') -> logging.Logger:
        """
        Get or create a logger for a specific use case
        
        Args:
            name: Logger name (usually module name)
            use_case: Use case category (sanctions, supabase, api, statistics, batch_processing, general)
        """
        logger_key = f"{use_case}_{name}"
        
        if logger_key in cls._loggers:
            return cls._loggers[logger_key]
        
        # Create logger
        logger = logging.getLogger(logger_key)
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler - organized by use case
        log_file = LOG_FILES.get(use_case, LOG_FILES['general'])
        file_handler = RotatingFileHandler(
            filename=os.path.join(LOGS_DIR, log_file),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler for errors and important info
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter('%(levelname)s | %(name)s | %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        cls._loggers[logger_key] = logger
        return logger
    
    @classmethod
    def log_api_request(cls, endpoint: str, method: str, params: dict = None, response_code: int = None):
        """Log API request details"""
        logger = cls.get_logger('api_requests', 'api')
        logger.info(f"{method} {endpoint} | params={params} | response_code={response_code}")
    
    @classmethod
    def log_supabase_operation(cls, operation: str, table: str, success: bool, details: str = ""):
        """Log Supabase database operations"""
        logger = cls.get_logger('supabase_ops', 'supabase')
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"{operation} | table={table} | {status} | {details}")
    
    @classmethod
    def log_sanctions_processing(cls, stage: str, count: int = 0, details: str = ""):
        """Log sanctions processing stages"""
        logger = cls.get_logger('sanctions_processing', 'sanctions')
        logger.info(f"{stage} | count={count} | {details}")
    
    @classmethod
    def log_batch_processing(cls, operation: str, batch_size: int, processed: int, success: bool):
        """Log batch processing operations"""
        logger = cls.get_logger('batch_processing', 'batch_processing')
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"{operation} | batch_size={batch_size} | processed={processed} | {status}")
    
    @classmethod
    def log_statistics(cls, component: str, key: str, value, details: str = ""):
        """Log statistics calculations"""
        logger = cls.get_logger('statistics', 'statistics')
        logger.info(f"{component} | {key}={value} | {details}")

# Convenience functions for common logging patterns
def log_function_entry(logger, func_name: str, **kwargs):
    """Log function entry with parameters"""
    params = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"ENTRY {func_name}({params})")

def log_function_exit(logger, func_name: str, result=None, **kwargs):
    """Log function exit with result"""
    details = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"EXIT {func_name} | result={result} | {details}")

def log_error_with_context(logger, error: Exception, context: str, **kwargs):
    """Log error with contextual information"""
    details = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
    logger.error(f"ERROR {context} | {type(error).__name__}: {str(error)} | {details}")

# Initialize logging on import
logger = AMLLogger.get_logger('aml_logger', 'general')
logger.info("AML Logging System Initialized")
logger.info(f"Logs directory: {LOGS_DIR}")
logger.info(f"Log files: {list(LOG_FILES.values())}")