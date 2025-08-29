"""
Authentication module for AML Controller
Provides OAuth2/OpenID Connect authentication with multiple providers using Authlib
"""

from .auth_manager import AuthManager
from .middleware import AuthMiddleware
from .decorators import require_auth, require_roles
from .models import User, UserSession

__all__ = [
    'AuthManager',
    'AuthMiddleware', 
    'require_auth',
    'require_roles', 
    'User',
    'UserSession'
]