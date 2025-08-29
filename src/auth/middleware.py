"""
Authentication Middleware for AML Controller
Integrates with existing LoggingMiddleware and provides session management
"""

import time
import uuid
from typing import Optional, Dict
from flask import Flask, request, g, session, jsonify
from datetime import datetime

from .auth_manager import AuthManager
from .models import User
from ..utils.enterprise_logger import enterprise_logger


class AuthMiddleware:
    """Authentication middleware that works alongside LoggingMiddleware"""
    
    def __init__(self, app: Optional[Flask] = None, auth_manager: Optional[AuthManager] = None):
        self.app = app
        self.auth_manager = auth_manager
        
        if app is not None:
            self.init_app(app, auth_manager)
    
    def init_app(self, app: Flask, auth_manager: Optional[AuthManager] = None):
        """Initialize authentication middleware with Flask app"""
        self.app = app
        self.auth_manager = auth_manager or AuthManager(app)
        
        # Register middleware functions
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Add auth-specific error handlers
        app.errorhandler(401)(self._handle_auth_error)
        app.errorhandler(403)(self._handle_permission_error)
    
    def _before_request(self):
        """Execute before each request - handle authentication"""
        # Skip authentication for public endpoints
        if self._is_public_endpoint():
            return
        
        # Initialize user context
        g.current_user = None
        g.is_authenticated = False
        
        # Check for existing user session
        user_data = session.get('user')
        if user_data:
            try:
                # Recreate user from session data
                user = User.from_dict(user_data)
                
                # Validate user is still active
                if user.is_active:
                    g.current_user = user
                    g.is_authenticated = True
                    
                    # Update last activity
                    self._update_session_activity(user)
                    
                    # Log successful session validation
                    self._log_auth_event('SESSION_VALIDATED', True, user=user)
                else:
                    # User account is inactive - clear session
                    session.clear()
                    self._log_auth_event('SESSION_CLEARED', True, reason='inactive_user')
                    
            except Exception as e:
                # Invalid session data - clear it
                session.clear()
                self._log_auth_event('SESSION_CLEARED', False, error=str(e))
    
    def _after_request(self, response):
        """Execute after each request - cleanup and logging"""
        # Add authentication headers if user is authenticated
        if g.get('is_authenticated'):
            response.headers['X-Auth-Status'] = 'authenticated'
            response.headers['X-Auth-Provider'] = g.current_user.provider if g.current_user else 'unknown'
        else:
            response.headers['X-Auth-Status'] = 'anonymous'
        
        return response
    
    def _is_public_endpoint(self) -> bool:
        """Check if current endpoint is public (doesn't require authentication)"""
        public_endpoints = [
            '/',                          # Home page
            '/api/health',               # Health check
            '/api/statistics',           # Public statistics
            '/images/',                  # Static images
            '/auth/',                    # Authentication endpoints
        ]
        
        # Check if current path matches any public endpoint
        current_path = request.path
        
        # Exact matches
        if current_path in public_endpoints:
            return True
        
        # Prefix matches
        public_prefixes = ['/images/', '/auth/']
        for prefix in public_prefixes:
            if current_path.startswith(prefix):
                return True
        
        return False
    
    def _update_session_activity(self, user: User):
        """Update user session activity timestamp"""
        try:
            session_id = session.get('session_id')
            if session_id and hasattr(self.auth_manager, 'update_session_activity'):
                # This would be implemented in auth_manager if needed
                pass
        except Exception as e:
            print(f"Warning: Could not update session activity: {e}")
    
    def _log_auth_event(self, event_type: str, success: bool, user: Optional[User] = None, 
                       error: Optional[str] = None, **kwargs):
        """Log authentication events"""
        try:
            if self.auth_manager:
                self.auth_manager.log_auth_event(
                    event_type=event_type,
                    success=success,
                    user_id=user.id if user else None,
                    provider=user.provider if user else None,
                    error_message=error,
                    ip_address=self._get_client_ip(),
                    user_agent=request.headers.get('User-Agent', 'Unknown'),
                    **kwargs
                )
        except Exception as e:
            print(f"Warning: Could not log auth event: {e}")
    
    def _get_client_ip(self) -> str:
        """Get client IP address, handling proxies"""
        # Check for common proxy headers
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'Unknown'
    
    def _handle_auth_error(self, error):
        """Handle 401 authentication errors"""
        # Log authentication failure
        self._log_auth_event(
            'AUTHENTICATION_REQUIRED', 
            False, 
            error='Authentication required'
        )
        
        # Return appropriate response based on request type
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED',
                'login_url': '/auth/login'
            }), 401
        else:
            # For web requests, redirect to login
            return jsonify({
                'error': 'Authentication Required',
                'message': 'Please log in to access this resource',
                'login_url': '/auth/login'
            }), 401
    
    def _handle_permission_error(self, error):
        """Handle 403 permission errors"""
        user = g.get('current_user')
        
        # Log permission denial
        self._log_auth_event(
            'ACCESS_DENIED', 
            False, 
            user=user,
            error='Insufficient permissions'
        )
        
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'code': 'INSUFFICIENT_PERMISSIONS',
                'user_role': user.role if user else 'anonymous',
                'required_permissions': 'See endpoint documentation'
            }), 403
        else:
            return jsonify({
                'error': 'Access Denied', 
                'message': 'You do not have permission to access this resource',
                'user_role': user.role if user else 'anonymous'
            }), 403
    
    def require_authentication(self):
        """Check if current user is authenticated, raise 401 if not"""
        if not g.get('is_authenticated'):
            self._log_auth_event('AUTH_CHECK_FAILED', False)
            
            if request.path.startswith('/api/'):
                response = jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                })
                response.status_code = 401
                return response
            else:
                response = jsonify({
                    'error': 'Authentication Required',
                    'login_url': '/auth/login'
                })
                response.status_code = 401
                return response
        
        return None
    
    def require_roles(self, required_roles: list):
        """Check if current user has required roles, raise 403 if not"""
        # First check authentication
        auth_check = self.require_authentication()
        if auth_check:
            return auth_check
        
        user = g.get('current_user')
        if not user or not user.has_role(required_roles):
            self._log_auth_event(
                'ROLE_CHECK_FAILED', 
                False, 
                user=user,
                error=f'Required roles: {required_roles}, user role: {user.role if user else "none"}'
            )
            
            if request.path.startswith('/api/'):
                response = jsonify({
                    'success': False,
                    'error': f'Access denied. Required roles: {", ".join(required_roles)}',
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'user_role': user.role if user else 'none',
                    'required_roles': required_roles
                })
                response.status_code = 403
                return response
            else:
                response = jsonify({
                    'error': 'Access Denied',
                    'message': f'Required roles: {", ".join(required_roles)}',
                    'user_role': user.role if user else 'none'
                })
                response.status_code = 403
                return response
        
        return None
    
    def login_user(self, user: User, remember: bool = False):
        """Log in a user and create session"""
        try:
            # Store user data in session
            session['user'] = user.to_dict()
            session['session_id'] = str(uuid.uuid4())
            session['login_time'] = datetime.now().isoformat()
            
            if remember:
                session.permanent = True
            
            # Create session record in database
            if self.auth_manager:
                self.auth_manager.create_user_session(
                    user=user,
                    session_id=session['session_id']
                )
            
            # Log successful login
            self._log_auth_event('USER_LOGIN', True, user=user)
            
            # Set global context
            g.current_user = user
            g.is_authenticated = True
            
            return True
            
        except Exception as e:
            self._log_auth_event('USER_LOGIN', False, user=user, error=str(e))
            return False
    
    def logout_user(self):
        """Log out current user and clear session"""
        user = g.get('current_user')
        
        try:
            # Clear session
            session.clear()
            
            # Clear global context
            g.current_user = None
            g.is_authenticated = False
            
            # Log successful logout
            self._log_auth_event('USER_LOGOUT', True, user=user)
            
            return True
            
        except Exception as e:
            self._log_auth_event('USER_LOGOUT', False, user=user, error=str(e))
            return False
    
    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user"""
        return g.get('current_user')
    
    def is_authenticated(self) -> bool:
        """Check if current request is authenticated"""
        return g.get('is_authenticated', False)