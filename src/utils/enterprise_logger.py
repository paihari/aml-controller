#!/usr/bin/env python3
"""
Enterprise-grade logging system for AML Controller
Features:
- Structured JSON logging
- Correlation IDs for request tracing
- Security and audit logging
- Performance monitoring
- Centralized configuration
- Multi-format output support
"""

import json
import logging
import os
import sys
import uuid
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from contextlib import contextmanager
from functools import wraps
import traceback

# Thread-local storage for correlation IDs
_local = threading.local()

class EnterpriseFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record):
        # Base log structure
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread_id': record.thread,
            'process_id': record.process
        }
        
        # Add correlation ID if available
        correlation_id = getattr(_local, 'correlation_id', None)
        if correlation_id:
            log_entry['correlation_id'] = correlation_id
            
        # Add user context if available
        user_context = getattr(_local, 'user_context', None)
        if user_context:
            log_entry['user'] = user_context
            
        # Add custom fields from record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        # Add exception information
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
            
        return json.dumps(log_entry, default=str)

class SecurityLogFilter(logging.Filter):
    """Filter for security-sensitive log records"""
    
    SENSITIVE_FIELDS = {
        'password', 'token', 'key', 'secret', 'auth', 
        'credential', 'api_key', 'session_id'
    }
    
    def filter(self, record):
        # Mask sensitive information in log messages
        if hasattr(record, 'extra_fields'):
            for field, value in record.extra_fields.items():
                if any(sensitive in field.lower() for sensitive in self.SENSITIVE_FIELDS):
                    record.extra_fields[field] = self._mask_sensitive(value)
        
        # Mask sensitive information in log message
        msg = record.getMessage()
        for sensitive in self.SENSITIVE_FIELDS:
            if sensitive in msg.lower():
                # Simple masking - in production, use more sophisticated methods
                record.msg = msg.replace(str(value), '***MASKED***')
        
        return True
    
    def _mask_sensitive(self, value: Any) -> str:
        """Mask sensitive values"""
        value_str = str(value)
        if len(value_str) <= 4:
            return '***'
        return f"{value_str[:2]}***{value_str[-2:]}"

class StructuredLogger:
    """Wrapper for standard logger with structured logging support"""
    
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    
    def _log(self, level: int, msg: str, extra_fields: dict = None, **kwargs):
        """Internal logging method that handles extra fields"""
        if extra_fields:
            # Create a custom LogRecord with extra fields
            record = self._logger.makeRecord(
                self._logger.name, level, "", 0, msg, (), None
            )
            record.extra_fields = extra_fields
            self._logger.handle(record)
        else:
            self._logger.log(level, msg, **kwargs)
    
    def debug(self, msg: str, extra_fields: dict = None, **kwargs):
        self._log(logging.DEBUG, msg, extra_fields, **kwargs)
    
    def info(self, msg: str, extra_fields: dict = None, **kwargs):
        self._log(logging.INFO, msg, extra_fields, **kwargs)
    
    def warning(self, msg: str, extra_fields: dict = None, **kwargs):
        self._log(logging.WARNING, msg, extra_fields, **kwargs)
    
    def error(self, msg: str, extra_fields: dict = None, **kwargs):
        self._log(logging.ERROR, msg, extra_fields, **kwargs)
    
    def critical(self, msg: str, extra_fields: dict = None, **kwargs):
        self._log(logging.CRITICAL, msg, extra_fields, **kwargs)
    
    def log(self, level: int, msg: str, extra_fields: dict = None, **kwargs):
        self._log(level, msg, extra_fields, **kwargs)
    
    # Delegate other attributes to the underlying logger
    def __getattr__(self, name):
        return getattr(self._logger, name)

class EnterpriseLogger:
    """Enterprise logging system with advanced features"""
    
    _instance = None
    _loggers = {}
    _handlers = {}
    
    # Log levels and categories
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    LOG_CATEGORIES = {
        'APPLICATION': 'app',
        'API': 'api',
        'DATABASE': 'database', 
        'SECURITY': 'security',
        'AUDIT': 'audit',
        'PERFORMANCE': 'performance',
        'SANCTIONS': 'sanctions',
        'TRANSACTIONS': 'transactions',
        'CACHE': 'cache',
        'SYSTEM': 'system'
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.config = self._load_config()
        self.logs_dir = self._ensure_logs_directory()
        self._setup_root_logger()
        self._initialized = True
        
        # Log system initialization
        self.get_logger('system').info(
            "Enterprise logging system initialized",
            extra_fields={
                'event_type': 'system_startup',
                'logs_directory': str(self.logs_dir),
                'log_level': self.config['log_level']
            }
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load logging configuration"""
        return {
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_format': os.getenv('LOG_FORMAT', 'json'),  # json or text
            'log_to_console': os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true',
            'log_to_file': os.getenv('LOG_TO_FILE', 'true').lower() == 'true',
            'log_rotation': os.getenv('LOG_ROTATION', 'size'),  # size or time
            'max_log_size': int(os.getenv('MAX_LOG_SIZE_MB', '50')) * 1024 * 1024,
            'max_log_files': int(os.getenv('MAX_LOG_FILES', '10')),
            'log_retention_days': int(os.getenv('LOG_RETENTION_DAYS', '30')),
            'enable_audit_logging': os.getenv('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true',
            'enable_security_logging': os.getenv('ENABLE_SECURITY_LOGGING', 'true').lower() == 'true',
            'enable_performance_logging': os.getenv('ENABLE_PERFORMANCE_LOGGING', 'true').lower() == 'true'
        }
    
    def _ensure_logs_directory(self) -> str:
        """Create and return logs directory path"""
        logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir
    
    def _setup_root_logger(self):
        """Configure root logger"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.LOG_LEVELS[self.config['log_level']])
        
        # Clear existing handlers
        root_logger.handlers.clear()
    
    def get_logger(self, category: str = 'APPLICATION', component: str = None) -> StructuredLogger:
        """
        Get or create a logger for specific category and component
        
        Args:
            category: Log category (APPLICATION, API, DATABASE, etc.)
            component: Optional component name
        """
        category_key = self.LOG_CATEGORIES.get(category.upper(), category.lower())
        logger_name = f"{category_key}.{component}" if component else category_key
        
        if logger_name in self._loggers:
            return self._loggers[logger_name]
        
        logger = logging.getLogger(logger_name)
        logger.setLevel(self.LOG_LEVELS[self.config['log_level']])
        logger.propagate = False
        
        # Add handlers
        handlers = self._get_handlers(category_key)
        for handler in handlers:
            logger.addHandler(handler)
        
        # Wrap in StructuredLogger
        structured_logger = StructuredLogger(logger)
        self._loggers[logger_name] = structured_logger
        return structured_logger
    
    def _get_handlers(self, category: str) -> list:
        """Get handlers for a specific category"""
        handlers = []
        
        # File handler
        if self.config['log_to_file']:
            if category not in self._handlers:
                self._handlers[category] = self._create_file_handler(category)
            handlers.append(self._handlers[category])
        
        # Console handler
        if self.config['log_to_console']:
            if 'console' not in self._handlers:
                self._handlers['console'] = self._create_console_handler()
            handlers.append(self._handlers['console'])
            
        return handlers
    
    def _create_file_handler(self, category: str) -> logging.Handler:
        """Create file handler with rotation"""
        log_file = os.path.join(self.logs_dir, f"{category}.log")
        
        if self.config['log_rotation'] == 'time':
            handler = TimedRotatingFileHandler(
                log_file,
                when='D',  # Daily rotation
                interval=1,
                backupCount=self.config['log_retention_days']
            )
        else:
            handler = RotatingFileHandler(
                log_file,
                maxBytes=self.config['max_log_size'],
                backupCount=self.config['max_log_files']
            )
        
        handler.setLevel(self.LOG_LEVELS[self.config['log_level']])
        
        # Set formatter
        if self.config['log_format'] == 'json':
            handler.setFormatter(EnterpriseFormatter())
        else:
            formatter = logging.Formatter(
                fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
        
        # Add security filter for sensitive categories
        if category in ['security', 'audit', 'api']:
            handler.addFilter(SecurityLogFilter())
            
        return handler
    
    def _create_console_handler(self) -> logging.Handler:
        """Create console handler"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.WARNING)  # Only warnings and errors to console
        
        # Simple format for console
        formatter = logging.Formatter('%(levelname)s | %(name)s | %(message)s')
        handler.setFormatter(formatter)
        
        return handler
    
    @contextmanager
    def correlation_context(self, correlation_id: str = None, user_context: Dict = None):
        """Context manager for correlation ID and user context"""
        correlation_id = correlation_id or str(uuid.uuid4())
        
        # Store in thread-local storage
        old_correlation_id = getattr(_local, 'correlation_id', None)
        old_user_context = getattr(_local, 'user_context', None)
        
        _local.correlation_id = correlation_id
        if user_context:
            _local.user_context = user_context
            
        try:
            yield correlation_id
        finally:
            _local.correlation_id = old_correlation_id
            _local.user_context = old_user_context
    
    def log_api_request(self, method: str, endpoint: str, **kwargs):
        """Log API request with structured data"""
        logger = self.get_logger('API', 'requests')
        logger.info(
            f"API Request: {method} {endpoint}",
            extra_fields={
                'event_type': 'api_request',
                'http_method': method,
                'endpoint': endpoint,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_api_response(self, method: str, endpoint: str, status_code: int, 
                        duration_ms: float, **kwargs):
        """Log API response with metrics"""
        logger = self.get_logger('API', 'responses')
        level = logging.ERROR if status_code >= 400 else logging.INFO
        
        logger.log(
            level,
            f"API Response: {method} {endpoint} - {status_code} ({duration_ms:.2f}ms)",
            extra_fields={
                'event_type': 'api_response',
                'http_method': method,
                'endpoint': endpoint,
                'status_code': status_code,
                'duration_ms': duration_ms,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_database_operation(self, operation: str, table: str, success: bool, 
                             duration_ms: float = None, **kwargs):
        """Log database operations"""
        logger = self.get_logger('DATABASE', 'operations')
        level = logging.INFO if success else logging.ERROR
        
        logger.log(
            level,
            f"Database {operation}: {table} - {'SUCCESS' if success else 'FAILED'}",
            extra_fields={
                'event_type': 'database_operation',
                'operation': operation,
                'table': table,
                'success': success,
                'duration_ms': duration_ms,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_security_event(self, event_type: str, severity: str, description: str, **kwargs):
        """Log security events"""
        if not self.config['enable_security_logging']:
            return
            
        logger = self.get_logger('SECURITY', event_type)
        level = logging.CRITICAL if severity == 'HIGH' else logging.WARNING
        
        logger.log(
            level,
            f"Security Event: {event_type} - {description}",
            extra_fields={
                'event_type': 'security_event',
                'security_event_type': event_type,
                'severity': severity,
                'description': description,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_audit_event(self, action: str, resource: str, user_id: str = None, **kwargs):
        """Log audit events for compliance"""
        if not self.config['enable_audit_logging']:
            return
            
        logger = self.get_logger('AUDIT', 'compliance')
        logger.info(
            f"Audit: {action} on {resource}",
            extra_fields={
                'event_type': 'audit_event',
                'action': action,
                'resource': resource,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str, **kwargs):
        """Log performance metrics"""
        if not self.config['enable_performance_logging']:
            return
            
        logger = self.get_logger('PERFORMANCE', 'metrics')
        logger.info(
            f"Performance: {metric_name} = {value} {unit}",
            extra_fields={
                'event_type': 'performance_metric',
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
        )

# Decorators for automatic logging
def log_function_calls(category: str = 'APPLICATION', component: str = None):
    """Decorator to automatically log function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = EnterpriseLogger().get_logger(category, component)
            
            start_time = time.time()
            function_name = f"{func.__module__}.{func.__name__}"
            
            logger.info(
                f"Function call: {function_name}",
                extra_fields={
                    'event_type': 'function_call',
                    'function': function_name,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs)
                }
            )
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"Function completed: {function_name} ({duration_ms:.2f}ms)",
                    extra_fields={
                        'event_type': 'function_complete',
                        'function': function_name,
                        'duration_ms': duration_ms,
                        'success': True
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Function failed: {function_name} - {str(e)}",
                    extra_fields={
                        'event_type': 'function_error',
                        'function': function_name,
                        'duration_ms': duration_ms,
                        'success': False,
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    },
                    exc_info=True
                )
                
                raise
        
        return wrapper
    return decorator

def log_performance(metric_name: str = None):
    """Decorator to log performance metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                name = metric_name or f"{func.__module__}.{func.__name__}"
                EnterpriseLogger().log_performance_metric(
                    metric_name=name,
                    value=duration_ms,
                    unit='ms',
                    function=f"{func.__module__}.{func.__name__}"
                )
                
                return result
                
            except Exception:
                duration_ms = (time.time() - start_time) * 1000
                name = metric_name or f"{func.__module__}.{func.__name__}"
                EnterpriseLogger().log_performance_metric(
                    metric_name=f"{name}_error",
                    value=duration_ms,
                    unit='ms',
                    function=f"{func.__module__}.{func.__name__}",
                    success=False
                )
                raise
        
        return wrapper
    return decorator

# Global logger instance
enterprise_logger = EnterpriseLogger()

# Convenience functions
def get_logger(category: str = 'APPLICATION', component: str = None) -> logging.Logger:
    """Get a logger instance"""
    return enterprise_logger.get_logger(category, component)

def correlation_context(correlation_id: str = None, user_context: Dict = None):
    """Get correlation context manager"""
    return enterprise_logger.correlation_context(correlation_id, user_context)