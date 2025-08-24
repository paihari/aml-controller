#!/usr/bin/env python3
"""
Logging middleware for Flask applications
Provides automatic API request/response logging with correlation tracking
"""

import time
import uuid
from typing import Optional
from flask import Flask, request, g, Response
from functools import wraps

from ..utils.enterprise_logger import enterprise_logger, correlation_context
from ..utils.log_config import get_api_logger, get_security_logger, get_performance_logger

class LoggingMiddleware:
    """Flask middleware for comprehensive API logging"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.api_logger = get_api_logger('middleware')
        self.security_logger = get_security_logger('api')
        self.performance_logger = get_performance_logger()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)
        
        # Add custom error handlers
        app.errorhandler(500)(self._handle_500_error)
        app.errorhandler(404)(self._handle_404_error)
        app.errorhandler(403)(self._handle_403_error)
        app.errorhandler(401)(self._handle_401_error)
    
    def _before_request(self):
        """Execute before each request"""
        # Generate correlation ID
        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        g.correlation_id = correlation_id
        g.start_time = time.time()
        
        # Extract user context if available
        user_context = self._extract_user_context()
        
        # Set correlation context
        g.correlation_context = enterprise_logger.correlation_context(
            correlation_id=correlation_id,
            user_context=user_context
        ).__enter__()
        
        # Log request
        self._log_api_request()
        
        # Security logging for sensitive endpoints
        if self._is_sensitive_endpoint():
            self._log_security_event('API_ACCESS', 'INFO', 'Access to sensitive endpoint')
    
    def _after_request(self, response: Response) -> Response:
        """Execute after each request"""
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            
            # Add correlation ID to response headers
            response.headers['X-Correlation-ID'] = g.correlation_id
            
            # Log response
            self._log_api_response(response.status_code, duration_ms)
            
            # Log performance metrics
            self._log_performance_metrics(duration_ms, response.status_code)
            
            # Log slow requests
            if duration_ms > 1000:  # Log requests slower than 1 second
                self.performance_logger.warning(
                    f"Slow API request detected: {request.method} {request.path}",
                    extra_fields={
                        'event_type': 'slow_request',
                        'duration_ms': duration_ms,
                        'endpoint': request.path,
                        'method': request.method,
                        'status_code': response.status_code
                    }
                )
        
        return response
    
    def _teardown_request(self, exception=None):
        """Clean up after request"""
        # Exit correlation context
        if hasattr(g, 'correlation_context'):
            try:
                g.correlation_context.__exit__(None, None, None)
            except Exception:
                pass
        
        # Log any unhandled exceptions
        if exception is not None:
            self.api_logger.error(
                f"Unhandled exception in request: {str(exception)}",
                extra_fields={
                    'event_type': 'unhandled_exception',
                    'exception_type': type(exception).__name__,
                    'exception_message': str(exception),
                    'endpoint': request.path,
                    'method': request.method
                },
                exc_info=True
            )
    
    def _extract_user_context(self) -> Optional[dict]:
        """Extract user context from request"""
        user_context = {}
        
        # Extract from headers
        if request.headers.get('X-User-ID'):
            user_context['user_id'] = request.headers.get('X-User-ID')
        
        if request.headers.get('X-User-Role'):
            user_context['role'] = request.headers.get('X-User-Role')
        
        # Extract IP address
        user_context['client_ip'] = self._get_client_ip()
        
        # Extract User-Agent
        user_context['user_agent'] = request.headers.get('User-Agent', 'Unknown')
        
        return user_context if user_context else None
    
    def _get_client_ip(self) -> str:
        """Get client IP address, handling proxies"""
        # Check for common proxy headers
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'Unknown'
    
    def _log_api_request(self):
        """Log API request details"""
        request_data = {
            'method': request.method,
            'endpoint': request.path,
            'full_url': request.url,
            'client_ip': self._get_client_ip(),
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'content_type': request.content_type,
            'content_length': request.content_length
        }
        
        # Add query parameters (be careful with sensitive data)
        if request.args:
            request_data['query_params'] = dict(request.args)
        
        # Add request body for POST/PUT (limit size and exclude sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            try:
                json_data = request.get_json()
                if json_data and isinstance(json_data, dict):
                    # Filter out sensitive fields
                    filtered_data = self._filter_sensitive_data(json_data)
                    request_data['request_body'] = filtered_data
            except Exception:
                pass
        
        self.api_logger.info(
            f"API Request: {request.method} {request.path}",
            extra_fields={
                'event_type': 'api_request',
                **request_data
            }
        )
    
    def _log_api_response(self, status_code: int, duration_ms: float):
        """Log API response details"""
        response_data = {
            'status_code': status_code,
            'duration_ms': duration_ms,
            'method': request.method,
            'endpoint': request.path
        }
        
        # Determine log level based on status code
        if status_code >= 500:
            level = 'error'
        elif status_code >= 400:
            level = 'warning'
        else:
            level = 'info'
        
        getattr(self.api_logger, level)(
            f"API Response: {request.method} {request.path} - {status_code} ({duration_ms:.2f}ms)",
            extra_fields={
                'event_type': 'api_response',
                **response_data
            }
        )
    
    def _log_performance_metrics(self, duration_ms: float, status_code: int):
        """Log performance metrics"""
        enterprise_logger.log_performance_metric(
            metric_name=f"api_response_time_{request.method.lower()}",
            value=duration_ms,
            unit='ms',
            endpoint=request.path,
            status_code=status_code,
            method=request.method
        )
    
    def _log_security_event(self, event_type: str, severity: str, description: str, **kwargs):
        """Log security events"""
        enterprise_logger.log_security_event(
            event_type=event_type,
            severity=severity,
            description=description,
            client_ip=self._get_client_ip(),
            endpoint=request.path,
            method=request.method,
            user_agent=request.headers.get('User-Agent', 'Unknown'),
            **kwargs
        )
    
    def _is_sensitive_endpoint(self) -> bool:
        """Check if endpoint is security-sensitive"""
        sensitive_patterns = [
            '/api/auth',
            '/api/admin',
            '/api/user',
            '/api/config',
            '/api/sanctions/refresh',
            '/api/transactions/delete'
        ]
        
        return any(pattern in request.path for pattern in sensitive_patterns)
    
    def _filter_sensitive_data(self, data: dict) -> dict:
        """Filter out sensitive data from request body"""
        sensitive_keys = {
            'password', 'token', 'key', 'secret', 'auth', 
            'credential', 'api_key', 'session_id'
        }
        
        filtered = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                filtered[key] = '***FILTERED***'
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
            else:
                filtered[key] = value
        
        return filtered
    
    def _handle_500_error(self, error):
        """Handle 500 errors"""
        self.api_logger.error(
            f"Internal Server Error: {request.method} {request.path}",
            extra_fields={
                'event_type': 'internal_server_error',
                'error_message': str(error),
                'method': request.method,
                'endpoint': request.path,
                'client_ip': self._get_client_ip()
            },
            exc_info=True
        )
        
        self._log_security_event(
            'SERVER_ERROR', 
            'MEDIUM', 
            f'Internal server error occurred: {str(error)}'
        )
        
        return {'error': 'Internal server error', 'correlation_id': g.get('correlation_id')}, 500
    
    def _handle_404_error(self, error):
        """Handle 404 errors"""
        self.api_logger.warning(
            f"Not Found: {request.method} {request.path}",
            extra_fields={
                'event_type': 'not_found_error',
                'method': request.method,
                'endpoint': request.path,
                'client_ip': self._get_client_ip()
            }
        )
        
        return {'error': 'Resource not found', 'correlation_id': g.get('correlation_id')}, 404
    
    def _handle_403_error(self, error):
        """Handle 403 errors"""
        self.api_logger.warning(
            f"Forbidden: {request.method} {request.path}",
            extra_fields={
                'event_type': 'forbidden_error',
                'method': request.method,
                'endpoint': request.path,
                'client_ip': self._get_client_ip()
            }
        )
        
        self._log_security_event(
            'ACCESS_DENIED', 
            'MEDIUM', 
            f'Forbidden access attempt to {request.path}'
        )
        
        return {'error': 'Access forbidden', 'correlation_id': g.get('correlation_id')}, 403
    
    def _handle_401_error(self, error):
        """Handle 401 errors"""
        self.api_logger.warning(
            f"Unauthorized: {request.method} {request.path}",
            extra_fields={
                'event_type': 'unauthorized_error',
                'method': request.method,
                'endpoint': request.path,
                'client_ip': self._get_client_ip()
            }
        )
        
        self._log_security_event(
            'AUTHENTICATION_FAILED', 
            'MEDIUM', 
            f'Unauthorized access attempt to {request.path}'
        )
        
        return {'error': 'Authentication required', 'correlation_id': g.get('correlation_id')}, 401

def log_business_operation(operation_type: str, resource: str, success: bool = True, **kwargs):
    """Log business operations for audit trail"""
    enterprise_logger.log_audit_event(
        action=operation_type,
        resource=resource,
        user_id=kwargs.get('user_id'),
        success=success,
        **{k: v for k, v in kwargs.items() if k != 'user_id'}
    )