#!/usr/bin/env python3
"""
Centralized logging configuration for AML Controller
Integrates enterprise logging with existing systems
"""

import os
import sys
from typing import Dict, Any
from .enterprise_logger import EnterpriseLogger, get_logger

# Environment variables for logging configuration
LOGGING_CONFIG = {
    # Log Levels
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    
    # Output Formats
    'LOG_FORMAT': os.getenv('LOG_FORMAT', 'json'),  # json or text
    'LOG_TO_CONSOLE': os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true',
    'LOG_TO_FILE': os.getenv('LOG_TO_FILE', 'true').lower() == 'true',
    
    # File Rotation
    'LOG_ROTATION': os.getenv('LOG_ROTATION', 'size'),  # size or time
    'MAX_LOG_SIZE_MB': int(os.getenv('MAX_LOG_SIZE_MB', '50')),
    'MAX_LOG_FILES': int(os.getenv('MAX_LOG_FILES', '10')),
    'LOG_RETENTION_DAYS': int(os.getenv('LOG_RETENTION_DAYS', '30')),
    
    # Feature Toggles
    'ENABLE_AUDIT_LOGGING': os.getenv('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true',
    'ENABLE_SECURITY_LOGGING': os.getenv('ENABLE_SECURITY_LOGGING', 'true').lower() == 'true',
    'ENABLE_PERFORMANCE_LOGGING': os.getenv('ENABLE_PERFORMANCE_LOGGING', 'true').lower() == 'true',
    'ENABLE_CORRELATION_TRACKING': os.getenv('ENABLE_CORRELATION_TRACKING', 'true').lower() == 'true',
    
    # External Integrations
    'LOG_AGGREGATION_ENDPOINT': os.getenv('LOG_AGGREGATION_ENDPOINT'),  # ELK, Splunk, etc.
    'LOG_AGGREGATION_API_KEY': os.getenv('LOG_AGGREGATION_API_KEY'),
    
    # Development/Debug
    'DEBUG_SQL_QUERIES': os.getenv('DEBUG_SQL_QUERIES', 'false').lower() == 'true',
    'DEBUG_API_REQUESTS': os.getenv('DEBUG_API_REQUESTS', 'false').lower() == 'true',
    'DEBUG_CACHE_OPERATIONS': os.getenv('DEBUG_CACHE_OPERATIONS', 'false').lower() == 'true',
}

def configure_logging():
    """Initialize enterprise logging system"""
    logger = get_logger('SYSTEM', 'logging')
    logger.info(
        "Initializing enterprise logging system",
        extra_fields={
            'event_type': 'logging_init',
            'config': {k: v for k, v in LOGGING_CONFIG.items() if 'API_KEY' not in k}
        }
    )
    
    # Log configuration summary
    logger.info(
        "Logging configuration applied",
        extra_fields={
            'log_level': LOGGING_CONFIG['LOG_LEVEL'],
            'log_format': LOGGING_CONFIG['LOG_FORMAT'],
            'audit_logging': LOGGING_CONFIG['ENABLE_AUDIT_LOGGING'],
            'security_logging': LOGGING_CONFIG['ENABLE_SECURITY_LOGGING'],
            'performance_logging': LOGGING_CONFIG['ENABLE_PERFORMANCE_LOGGING']
        }
    )

def get_aml_logger(component: str) -> Any:
    """Get logger for specific AML component"""
    return get_logger('APPLICATION', component)

def get_api_logger(component: str = 'general') -> Any:
    """Get logger for API components"""
    return get_logger('API', component)

def get_database_logger(component: str = 'general') -> Any:
    """Get logger for database components"""
    return get_logger('DATABASE', component)

def get_security_logger(component: str = 'general') -> Any:
    """Get logger for security components"""
    return get_logger('SECURITY', component)

def get_audit_logger() -> Any:
    """Get logger for audit events"""
    return get_logger('AUDIT', 'compliance')

def get_performance_logger() -> Any:
    """Get logger for performance metrics"""
    return get_logger('PERFORMANCE', 'metrics')

def get_cache_logger() -> Any:
    """Get logger for cache operations"""
    return get_logger('CACHE', 'operations')

def get_sanctions_logger() -> Any:
    """Get logger for sanctions processing"""
    return get_logger('SANCTIONS', 'processing')

def get_transactions_logger() -> Any:
    """Get logger for transaction processing"""
    return get_logger('TRANSACTIONS', 'processing')

# Initialize logging on import
configure_logging()