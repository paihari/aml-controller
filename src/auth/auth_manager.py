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

# Import Supabase client
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class AuthManager:
    """Manages OAuth2 authentication and user sessions"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.oauth = OAuth()
        self.db_path = os.getenv('LOCAL_DB_PATH', 'aml_database.db')
        
        # Initialize Supabase client for user data
        self.use_supabase = SUPABASE_AVAILABLE and os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY')
        self.supabase = None
        
        if self.use_supabase:
            try:
                self.supabase = create_client(
                    os.getenv('SUPABASE_URL'),
                    os.getenv('SUPABASE_ANON_KEY')
                )
                print("✅ Using Supabase for user authentication storage")
            except Exception as e:
                print(f"⚠️ Failed to initialize Supabase for auth, falling back to SQLite: {e}")
                self.use_supabase = False
        
        if not self.use_supabase:
            print("✅ Using SQLite for user authentication storage")
        
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
        """Initialize user management tables"""
        if self.use_supabase and self.supabase:
            # For Supabase, check if tables exist
            try:
                result = self.supabase.table('users').select('id').limit(1).execute()
                print("✅ Supabase user authentication tables verified")
                return
            except Exception as e:
                print(f"⚠️ Supabase user tables may not exist: {e}")
                print("📝 Creating user tables in Supabase...")
                # Note: In practice, these tables should be created via Supabase dashboard or SQL
                # For now, we'll fall back to SQLite if Supabase tables don't exist
                self.use_supabase = False
        
        # Use SQLite as fallback
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
        # Normalize user info based on provider
        normalized_info = self._normalize_user_info(provider, user_info)
        
        if self.use_supabase and self.supabase:
            return self._create_or_update_user_supabase(provider, normalized_info)
        else:
            return self._create_or_update_user_sqlite(provider, normalized_info)
    
    def _create_or_update_user_supabase(self, provider: str, normalized_info: Dict) -> User:
        """Create or update user in Supabase"""
        try:
            # Check if user exists
            existing_user = self.supabase.table('users').select('*').eq(
                'provider', provider
            ).eq('provider_user_id', normalized_info['provider_user_id']).execute()
            
            current_time = datetime.now().isoformat()
            
            if existing_user.data:
                # Update existing user
                user_data = {
                    'email': normalized_info['email'],
                    'name': normalized_info['name'],
                    'avatar_url': normalized_info.get('avatar_url'),
                    'last_login': current_time,
                    'updated_at': current_time
                }
                
                result = self.supabase.table('users').update(user_data).eq(
                    'id', existing_user.data[0]['id']
                ).execute()
                
                user_record = result.data[0]
            else:
                # Create new user
                user_data = {
                    'provider': provider,
                    'provider_user_id': normalized_info['provider_user_id'],
                    'email': normalized_info['email'],
                    'name': normalized_info['name'],
                    'avatar_url': normalized_info.get('avatar_url'),
                    'role': 'analyst',
                    'is_active': True,
                    'created_at': current_time,
                    'updated_at': current_time,
                    'last_login': current_time
                }
                
                result = self.supabase.table('users').insert(user_data).execute()
                user_record = result.data[0]
            
            # Convert to User object
            return User(
                id=user_record['id'],
                provider=user_record['provider'],
                provider_user_id=user_record['provider_user_id'],
                email=user_record['email'],
                name=user_record['name'],
                avatar_url=user_record['avatar_url'],
                role=user_record['role'],
                last_login=datetime.fromisoformat(user_record['last_login'].replace('Z', '+00:00')) if user_record['last_login'] else None,
                created_at=datetime.fromisoformat(user_record['created_at'].replace('Z', '+00:00')) if user_record['created_at'] else None,
                is_active=user_record['is_active']
            )
            
        except Exception as e:
            print(f"❌ Error creating/updating user in Supabase: {e}")
            raise
    
    def _create_or_update_user_sqlite(self, provider: str, normalized_info: Dict) -> User:
        """Create or update user in SQLite (fallback)"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
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
                    'analyst'  # Default role
                ))
                user_id = cursor.lastrowid
                role = 'analyst'
            
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
            print(f"❌ Error creating/updating user in SQLite: {e}")
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
    
    def create_user_session(self, user: User, session_id: str, access_token: str = None, 
                           ip_address: str = None, user_agent: str = None) -> UserSession:
        """Create user session in Supabase database"""
        return self._create_user_session_supabase(user, session_id, access_token, ip_address, user_agent)
    
    def _create_user_session_supabase(self, user: User, session_id: str, access_token: str = None,
                                     ip_address: str = None, user_agent: str = None) -> UserSession:
        """Create user session in Supabase"""
        try:
            # Set session expiration (24 hours default)
            expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
            current_time = datetime.now().isoformat()
            
            session_data = {
                'user_id': user.id,
                'session_id': session_id,
                'access_token': access_token,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'expires_at': expires_at,
                'created_at': current_time,
                'last_activity': current_time,
                'is_active': True
            }
            
            result = self.supabase.table('user_sessions').insert(session_data).execute()
            session_record = result.data[0]
            
            return UserSession(
                user_id=session_record['user_id'],
                session_id=session_record['session_id'],
                access_token=session_record['access_token'],
                ip_address=session_record['ip_address'],
                user_agent=session_record['user_agent'],
                expires_at=datetime.fromisoformat(session_record['expires_at'].replace('Z', '+00:00')),
                created_at=datetime.fromisoformat(session_record['created_at'].replace('Z', '+00:00')),
                last_activity=datetime.fromisoformat(session_record['last_activity'].replace('Z', '+00:00'))
            )
            
        except Exception as e:
            print(f"❌ Error creating user session in Supabase: {e}")
            raise
    
    
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
    
    def get_user_statistics(self) -> dict:
        """Get user authentication statistics"""
        if self.use_supabase and self.supabase:
            return self._get_user_statistics_supabase()
        else:
            return self._get_user_statistics_sqlite()
    
    def _get_user_statistics_supabase(self) -> dict:
        """Get user statistics from Supabase"""
        try:
            # Get total users
            total_users_result = self.supabase.table('users').select('id', count='exact').execute()
            total_users = total_users_result.count or 0
            
            # Get active users
            active_users_result = self.supabase.table('users').select('id', count='exact').eq('is_active', True).execute()
            active_users = active_users_result.count or 0
            
            # Get users by provider
            provider_stats_result = self.supabase.rpc('get_users_by_provider').execute()
            users_by_provider = {}
            if provider_stats_result.data:
                for row in provider_stats_result.data:
                    users_by_provider[row['provider']] = row['count']
            
            # If RPC doesn't exist, fall back to regular query
            if not users_by_provider:
                all_users = self.supabase.table('users').select('provider').execute()
                from collections import Counter
                provider_counts = Counter([user['provider'] for user in all_users.data])
                users_by_provider = dict(provider_counts)
            
            # Get recent logins (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            recent_logins_result = self.supabase.table('users').select('id', count='exact').gte('last_login', thirty_days_ago).execute()
            recent_logins = recent_logins_result.count or 0
            
            # Get login events from audit log (last 30 days)
            login_events_result = self.supabase.table('auth_audit_log').select('id', count='exact').eq(
                'event_type', 'USER_LOGIN'
            ).eq('success', True).gte('created_at', thirty_days_ago).execute()
            login_events = login_events_result.count or 0
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'recent_logins_30d': recent_logins,
                'login_events_30d': login_events,
                'users_by_provider': users_by_provider
            }
            
        except Exception as e:
            print(f"Error getting user statistics from Supabase: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'recent_logins_30d': 0,
                'login_events_30d': 0,
                'users_by_provider': {}
            }
    
    def _get_user_statistics_sqlite(self) -> dict:
        """Get user statistics from SQLite (fallback)"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get total users
            total_users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            
            # Get active users
            active_users = conn.execute('SELECT COUNT(*) FROM users WHERE is_active = 1').fetchone()[0]
            
            # Get users by provider
            provider_stats = conn.execute('''
                SELECT provider, COUNT(*) as count 
                FROM users 
                GROUP BY provider
            ''').fetchall()
            
            # Get recent logins (last 30 days)
            recent_logins = conn.execute('''
                SELECT COUNT(*) 
                FROM users 
                WHERE last_login >= datetime('now', '-30 days')
            ''').fetchone()[0]
            
            # Get login events from audit log (last 30 days)
            login_events = conn.execute('''
                SELECT COUNT(*) 
                FROM auth_audit_log 
                WHERE event_type = 'USER_LOGIN' 
                AND success = 1 
                AND created_at >= datetime('now', '-30 days')
            ''').fetchone()[0]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'recent_logins_30d': recent_logins,
                'login_events_30d': login_events,
                'users_by_provider': {row[0]: row[1] for row in provider_stats}
            }
            
        except Exception as e:
            print(f"Error getting user statistics from SQLite: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'recent_logins_30d': 0,
                'login_events_30d': 0,
                'users_by_provider': {}
            }