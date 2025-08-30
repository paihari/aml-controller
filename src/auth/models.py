"""
User and session models for AML Controller authentication
"""

from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class User:
    """User model for authenticated users"""
    id: Optional[int]
    provider: str  # 'google', 'microsoft', 'github', 'oracle' 
    provider_user_id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    role: str = 'analyst'  # 'analyst', 'admin', 'viewer', 'compliance_officer'
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        """Convert user to dictionary for session storage"""
        return {
            'id': self.id,
            'provider': self.provider,
            'provider_user_id': self.provider_user_id,
            'email': self.email,
            'name': self.name,
            'avatar_url': self.avatar_url,
            'role': self.role,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Create user from dictionary (from session)"""
        return cls(
            id=data.get('id'),
            provider=data['provider'],
            provider_user_id=data['provider_user_id'],
            email=data['email'],
            name=data['name'],
            avatar_url=data.get('avatar_url'),
            role=data.get('role', 'analyst'),
            last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            is_active=data.get('is_active', True)
        )
    
    def has_role(self, required_roles: List[str]) -> bool:
        """Check if user has any of the required roles"""
        return self.role in required_roles
    
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == 'admin'


@dataclass
class UserSession:
    """User session model"""
    user_id: int
    session_id: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def is_active(self, timeout_minutes: int = 1440) -> bool:  # 24 hours default
        """Check if session is active based on last activity"""
        if not self.last_activity:
            return False
        timeout_delta = datetime.now() - self.last_activity
        return timeout_delta.total_seconds() < (timeout_minutes * 60)