"""
Authentication decorators for protecting Flask routes
"""

from functools import wraps
from typing import List, Optional
from flask import session, request, jsonify, redirect, url_for, g
from .models import User


def require_auth(f):
    """Decorator to require authentication for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is in session
        user_data = session.get('user')
        if not user_data:
            # If it's an API request, return JSON error
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            # For web requests, redirect to login
            return redirect(url_for('auth_login'))
        
        # Create user object and add to g
        try:
            g.current_user = User.from_dict(user_data)
            # Check if user is active
            if not g.current_user.is_active:
                session.clear()
                if request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': 'User account is inactive',
                        'code': 'USER_INACTIVE'
                    }), 403
                return redirect(url_for('auth_login'))
        except Exception as e:
            # Invalid user data in session
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({
                    'success': False,
                    'error': 'Invalid session data',
                    'code': 'INVALID_SESSION'
                }), 401
            return redirect(url_for('auth_login'))
        
        return f(*args, **kwargs)
    return decorated_function


def require_roles(allowed_roles: List[str]):
    """Decorator to require specific roles for a route"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check authentication
            user_data = session.get('user')
            if not user_data:
                if request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': 'Authentication required',
                        'code': 'AUTH_REQUIRED'
                    }), 401
                return redirect(url_for('auth_login'))
            
            # Create user object
            try:
                user = User.from_dict(user_data)
                g.current_user = user
            except Exception:
                session.clear()
                if request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': 'Invalid session data',
                        'code': 'INVALID_SESSION'
                    }), 401
                return redirect(url_for('auth_login'))
            
            # Check role
            if not user.has_role(allowed_roles):
                if request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': f'Access denied. Required roles: {", ".join(allowed_roles)}',
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'user_role': user.role,
                        'required_roles': allowed_roles
                    }), 403
                # For web requests, show access denied page
                return jsonify({
                    'error': 'Access Denied',
                    'message': f'You need one of these roles: {", ".join(allowed_roles)}',
                    'your_role': user.role
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin role"""
    return require_roles(['admin'])(f)


def get_current_user() -> Optional[User]:
    """Get current user from g object"""
    return getattr(g, 'current_user', None)