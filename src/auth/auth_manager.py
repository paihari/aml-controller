"""
Authentication Manager for AML Controller
Handles OAuth2 setup and user management using Authlib built-in providers
"""

import os
import sqlite3
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from flask import Flask, session
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

from .models import User, UserSession

# Load environment variables
load_dotenv()


class AuthManager:
    """Manages OAuth2 authentication and user sessions"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.oauth = OAuth()
        self.db_path = os.getenv('LOCAL_DB_PATH', 'aml_database.db')
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the authentication manager with Flask app"""
        self.app = app
        
        # Configure Flask-Session for server-side sessions
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
        app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE', 'filesystem')
        app.config['SESSION_PERMANENT'] = False
        app.config['SESSION_USE_SIGNER'] = True
        
        # Configure Redis if specified
        if os.getenv('SESSION_TYPE') == 'redis':
            app.config['SESSION_REDIS'] = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # Initialize OAuth with app
        self.oauth.init_app(app)
        
        # Register OAuth providers
        self._register_providers()
        
        # Initialize user database tables
        self._init_user_tables()
        
    def _register_providers(self):
        """Register OAuth2 providers with their configurations"""
        
        # Debug: Print all environment variables related to auth
        print("🔍 Debug: All environment variables:")
        import os
        for key in sorted(os.environ.keys()):
            if any(x in key.upper() for x in ['GOOGLE', 'SECRET', 'SESSION', 'FLASK']):
                value = os.environ[key]
                # Mask secrets but show first few chars
                if 'SECRET' in key.upper():
                    display_value = f"{value[:8]}..." if len(value) > 8 else "SET"
                else:
                    display_value = value
                print(f"  {key} = {display_value}")
        
        # Debug: Print environment variable status
        print(f"🔍 Debug: GOOGLE_CLIENT_ID = {os.getenv('GOOGLE_CLIENT_ID', 'NOT SET')}")
        print(f"🔍 Debug: GOOGLE_CLIENT_SECRET = {'SET' if os.getenv('GOOGLE_CLIENT_SECRET') else 'NOT SET'}")
        
        # Google OAuth2
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if google_client_id and not google_client_id.startswith('your-'):
            self.oauth.register(
                name='google',
                client_id=google_client_id,
                client_secret=google_client_secret,
                authorize_url='https://accounts.google.com/o/oauth2/auth',
                access_token_url='https://oauth2.googleapis.com/token',
                api_base_url='https://www.googleapis.com/',
                client_kwargs={
                    'scope': 'email profile'  # Remove openid to avoid JWT/JWKS issues
                }
            )
            print("✅ Google OAuth2 provider registered")
        else:
            print("❌ Google OAuth2 provider NOT registered - missing or invalid credentials")
        
        # GitHub OAuth2
        github_client_id = os.getenv('GITHUB_CLIENT_ID')
        github_client_secret = os.getenv('GITHUB_CLIENT_SECRET')
        
        if github_client_id and not github_client_id.startswith('your-'):
            self.oauth.register(
                name='github',
                client_id=github_client_id,
                client_secret=github_client_secret,
                access_token_url='https://github.com/login/oauth/access_token',
                authorize_url='https://github.com/login/oauth/authorize',
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'user:email'}
            )
            print("✅ GitHub OAuth2 provider registered")
            
        # Microsoft/Azure OAuth2
        azure_client_id = os.getenv('AZURE_CLIENT_ID')
        azure_client_secret = os.getenv('AZURE_CLIENT_SECRET')
        azure_tenant_id = os.getenv('AZURE_TENANT_ID')
        
        if azure_client_id and not azure_client_id.startswith('your-'):
            self.oauth.register(
                name='microsoft',
                client_id=azure_client_id,
                client_secret=azure_client_secret,
                server_metadata_url=f'https://login.microsoftonline.com/{azure_tenant_id}/v2.0/.well-known/openid_configuration',
                client_kwargs={'scope': 'openid email profile'}
            )
            print("✅ Microsoft/Azure OAuth2 provider registered")
            
        # Oracle OCI OAuth2
        oci_client_id = os.getenv('OCI_CLIENT_ID')
        oci_client_secret = os.getenv('OCI_CLIENT_SECRET')
        oci_instance = os.getenv('OCI_INSTANCE_ID')
        
        if oci_client_id and not oci_client_id.startswith('your-'):
            self.oauth.register(
                name='oracle',
                client_id=oci_client_id,
                client_secret=oci_client_secret,
                authorize_url=f'https://idcs-{oci_instance}.identity.oraclecloud.com/oauth2/v1/authorize',
                access_token_url=f'https://idcs-{oci_instance}.identity.oraclecloud.com/oauth2/v1/token',
                api_base_url=f'https://idcs-{oci_instance}.identity.oraclecloud.com/',
                client_kwargs={'scope': 'openid email profile'}
            )
            print("✅ Oracle OCI OAuth2 provider registered")
    
    def get_provider(self, provider_name: str):
        """Get OAuth provider client by name"""
        return getattr(self.oauth, provider_name, None)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available OAuth providers"""
        providers = []
        
        # Check which providers are configured
        provider_configs = [
            ('google', 'GOOGLE_CLIENT_ID'),
            ('github', 'GITHUB_CLIENT_ID'), 
            ('microsoft', 'AZURE_CLIENT_ID'),
            ('oracle', 'OCI_CLIENT_ID')
        ]
        
        for provider_name, env_var in provider_configs:
            client_id = os.getenv(env_var)
            if client_id and not client_id.startswith('your-'):
                providers.append(provider_name)
        
        return providers
    
    def _init_user_tables(self):
        """Initialize user management tables in SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Users table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider VARCHAR(50) NOT NULL,
                    provider_user_id VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    avatar_url VARCHAR(500),
                    role VARCHAR(50) DEFAULT 'user',
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    UNIQUE(provider, provider_user_id)
                )
            ''')
            
            # User sessions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_id VARCHAR(255) UNIQUE NOT NULL,
                    access_token TEXT,
                    refresh_token TEXT,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            
            # Auth audit log
            conn.execute('''
                CREATE TABLE IF NOT EXISTS auth_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    event_type VARCHAR(50) NOT NULL,
                    provider VARCHAR(50),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )
            ''')
            
            conn.commit()
            print("✅ User authentication tables initialized")
            
        except Exception as e:
            print(f"❌ Error initializing user tables: {e}")
        finally:
            if conn:
                conn.close()
    
    def create_or_update_user(self, provider: str, user_info: Dict) -> User:
        """Create or update user from OAuth provider info"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Normalize user info based on provider
            normalized_info = self._normalize_user_info(provider, user_info)
            
            # Check if user exists
            existing_user = conn.execute('''
                SELECT * FROM users 
                WHERE provider = ? AND provider_user_id = ?
            ''', (provider, normalized_info['provider_user_id'])).fetchone()
            
            if existing_user:
                # Update existing user
                conn.execute('''
                    UPDATE users SET 
                        email = ?, name = ?, avatar_url = ?, 
                        last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    normalized_info['email'],
                    normalized_info['name'],
                    normalized_info.get('avatar_url'),
                    existing_user['id']
                ))
                user_id = existing_user['id']
                role = existing_user['role']
            else:
                # Create new user
                cursor = conn.execute('''
                    INSERT INTO users 
                    (provider, provider_user_id, email, name, avatar_url, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    provider,
                    normalized_info['provider_user_id'],
                    normalized_info['email'],
                    normalized_info['name'],
                    normalized_info.get('avatar_url'),
                    'user'  # Default role
                ))
                user_id = cursor.lastrowid
                role = 'user'
            
            conn.commit()
            
            # Create User object
            user = User(
                id=user_id,
                provider=provider,
                provider_user_id=normalized_info['provider_user_id'],
                email=normalized_info['email'],
                name=normalized_info['name'],
                avatar_url=normalized_info.get('avatar_url'),
                role=role,
                last_login=datetime.now(),
                is_active=True
            )
            
            return user
            
        except Exception as e:
            print(f"❌ Error creating/updating user: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _normalize_user_info(self, provider: str, user_info: Dict) -> Dict:
        """Normalize user info from different OAuth providers"""
        if provider == 'google':
            return {
                'provider_user_id': str(user_info.get('id', user_info.get('sub'))),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'avatar_url': user_info.get('picture')
            }
        elif provider == 'github':
            return {
                'provider_user_id': str(user_info.get('id')),
                'email': user_info.get('email'),
                'name': user_info.get('name') or user_info.get('login'),
                'avatar_url': user_info.get('avatar_url')
            }
        elif provider == 'microsoft':
            return {
                'provider_user_id': str(user_info.get('oid', user_info.get('sub'))),
                'email': user_info.get('email', user_info.get('preferred_username')),
                'name': user_info.get('name'),
                'avatar_url': None  # Microsoft doesn't provide avatar URL in token
            }
        elif provider == 'oracle':
            return {
                'provider_user_id': str(user_info.get('sub')),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'avatar_url': None
            }
        else:
            # Fallback for unknown providers
            return {
                'provider_user_id': str(user_info.get('id', user_info.get('sub'))),
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'avatar_url': user_info.get('avatar_url', user_info.get('picture'))
            }
    
    def create_user_session(self, user: User, session_id: str, access_token: str = None) -> UserSession:
        """Create user session in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Set session expiration (24 hours default)
            expires_at = datetime.now() + timedelta(hours=24)
            
            conn.execute('''
                INSERT INTO user_sessions 
                (user_id, session_id, access_token, expires_at, last_activity)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user.id, session_id, access_token, expires_at))
            
            conn.commit()
            
            return UserSession(
                user_id=user.id,
                session_id=session_id,
                access_token=access_token,
                expires_at=expires_at,
                created_at=datetime.now(),
                last_activity=datetime.now()
            )
            
        except Exception as e:
            print(f"❌ Error creating user session: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def log_auth_event(self, event_type: str, success: bool, provider: str = None, 
                      user_id: int = None, error_message: str = None, **kwargs):
        """Log authentication events for audit trail"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            conn.execute('''
                INSERT INTO auth_audit_log 
                (user_id, event_type, provider, ip_address, user_agent, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                event_type,
                provider,
                kwargs.get('ip_address'),
                kwargs.get('user_agent'),
                success,
                error_message
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ Error logging auth event: {e}")
        finally:
            if conn:
                conn.close()