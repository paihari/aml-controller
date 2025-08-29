# AML Controller Authentication Strategy & Implementation Runbook

## Executive Summary

This document outlines the comprehensive authentication strategy for the AML Controller application, implementing OAuth2/OpenID Connect integration with multiple identity providers (Google, Azure, GitHub, Oracle OCI). The strategy leverages the existing Flask infrastructure while adding secure, enterprise-grade authentication.

## Current State Analysis

### Existing Infrastructure
✅ **Flask application with CORS enabled**
✅ **Middleware architecture already in place** (`LoggingMiddleware`)
✅ **Error handling for 401/403 responses** implemented
✅ **User context extraction** ready in middleware
✅ **Enterprise logging system** with security event logging
✅ **Environment variable support** via python-dotenv
✅ **Docker containerization** support

### Current Authentication Status
❌ **No authentication implementation**
❌ **No session management**
❌ **No OAuth2/OIDC providers configured**
❌ **All API endpoints are publicly accessible**

## Authentication Architecture Design

### 1. OAuth2/OpenID Connect Flow
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Browser  │◄──►│ AML Controller  │◄──►│ Identity Provider│
│                 │    │  (Flask App)    │    │ (Google/Azure/  │
│                 │    │                 │    │  GitHub/OCI)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Authentication Flow:**
1. User accesses protected resource
2. Redirect to identity provider login
3. User authenticates with IDP
4. IDP redirects back with authorization code
5. AML Controller exchanges code for tokens
6. User session established with JWT token
7. Subsequent requests validated via token

### 2. Technology Stack
- **OAuth2 Library**: `Authlib` (comprehensive OAuth2/OIDC support)
- **Session Management**: `Flask-Session` with Redis backend
- **JWT Handling**: `PyJWT` for token validation
- **Security Headers**: `Flask-Talisman` for security headers
- **Rate Limiting**: `Flask-Limiter` for brute force protection

### 3. Supported Identity Providers

#### Google Cloud Identity
- **OAuth2 Endpoint**: `https://accounts.google.com/o/oauth2/auth`
- **Token Endpoint**: `https://oauth2.googleapis.com/token`
- **Scopes**: `openid profile email`
- **User Info**: `https://www.googleapis.com/oauth2/v2/userinfo`

#### Azure Active Directory (Microsoft)
- **OAuth2 Endpoint**: `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize`
- **Token Endpoint**: `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`
- **Scopes**: `openid profile email`
- **User Info**: Microsoft Graph API

#### GitHub
- **OAuth2 Endpoint**: `https://github.com/login/oauth/authorize`
- **Token Endpoint**: `https://github.com/login/oauth/access_token`
- **Scopes**: `user:email`
- **User Info**: `https://api.github.com/user`

#### Oracle Cloud Infrastructure (OCI)
- **OAuth2 Endpoint**: `https://idcs-{instance}.identity.oraclecloud.com/oauth2/v1/authorize`
- **Token Endpoint**: `https://idcs-{instance}.identity.oraclecloud.com/oauth2/v1/token`
- **Scopes**: `openid profile email`
- **User Info**: IDCS API

## Implementation Plan

### Phase 1: Dependencies & Basic Setup
**Estimated Time**: 2-3 hours

1. **Install Required Dependencies**
   ```bash
   pip install authlib flask-session flask-talisman flask-limiter pyjwt redis
   ```

2. **Environment Variables Setup**
   ```env
   # Authentication Configuration
   SECRET_KEY=your-secret-key-here
   SESSION_TYPE=redis
   REDIS_URL=redis://localhost:6379
   
   # Google OAuth2
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   
   # Azure OAuth2
   AZURE_CLIENT_ID=your-azure-client-id
   AZURE_CLIENT_SECRET=your-azure-client-secret
   AZURE_TENANT_ID=your-azure-tenant-id
   
   # GitHub OAuth2
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   
   # Oracle OCI OAuth2
   OCI_CLIENT_ID=your-oci-client-id
   OCI_CLIENT_SECRET=your-oci-client-secret
   OCI_INSTANCE=your-oci-instance-id
   ```

3. **Create Authentication Module Structure**
   ```
   src/auth/
   ├── __init__.py
   ├── auth_manager.py      # Main authentication manager
   ├── providers/           # OAuth2 provider implementations
   │   ├── __init__.py
   │   ├── base.py         # Base provider class
   │   ├── google.py       # Google OAuth2 implementation
   │   ├── azure.py        # Azure AD implementation
   │   ├── github.py       # GitHub OAuth2 implementation
   │   └── oci.py          # Oracle OCI implementation
   ├── middleware.py       # Authentication middleware
   ├── decorators.py       # Route protection decorators
   └── models.py          # User/session models
   ```

### Phase 2: Core Authentication Implementation
**Estimated Time**: 4-5 hours

1. **Base OAuth2 Provider Class** (`src/auth/providers/base.py`)
   - Abstract base class for all OAuth2 providers
   - Common OAuth2 flow implementation
   - Token validation and refresh logic

2. **Authentication Manager** (`src/auth/auth_manager.py`)
   - Multi-provider management
   - Session handling
   - User profile normalization

3. **Authentication Middleware** (`src/auth/middleware.py`)
   - Integrate with existing `LoggingMiddleware`
   - JWT token validation
   - Session management
   - Route protection

4. **Protection Decorators** (`src/auth/decorators.py`)
   - `@require_auth` decorator for protected routes
   - `@require_roles` decorator for role-based access
   - `@rate_limit` decorator for API endpoints

### Phase 3: Provider-Specific Implementations
**Estimated Time**: 3-4 hours

1. **Google OAuth2 Provider** (`src/auth/providers/google.py`)
2. **Azure AD Provider** (`src/auth/providers/azure.py`)
3. **GitHub Provider** (`src/auth/providers/github.py`)
4. **Oracle OCI Provider** (`src/auth/providers/oci.py`)

### Phase 4: Route Integration
**Estimated Time**: 2-3 hours

1. **Authentication Routes** (add to `src/api/app.py`)
   - `/auth/login` - Provider selection page
   - `/auth/login/<provider>` - Initiate OAuth2 flow
   - `/auth/callback/<provider>` - OAuth2 callback handling
   - `/auth/logout` - Session termination
   - `/auth/profile` - User profile information

2. **Protected Route Implementation**
   - Apply `@require_auth` to sensitive endpoints
   - Update existing routes with proper protection

### Phase 5: Frontend Integration
**Estimated Time**: 2-3 hours

1. **Login Page** (`dashboard/login.html`)
   - Provider selection interface
   - Consistent branding with existing dashboard

2. **Dashboard Integration**
   - User profile display
   - Logout functionality
   - Session timeout handling

### Phase 6: Testing & Security Hardening
**Estimated Time**: 3-4 hours

1. **Security Testing**
   - CSRF protection
   - Session security
   - Token validation
   - Brute force protection

2. **Integration Testing**
   - Test each OAuth2 provider
   - End-to-end authentication flows
   - Session management
   - Error handling

## Security Considerations

### 1. Token Security
- **JWT Signing**: Use strong secret keys (256-bit minimum)
- **Token Expiration**: Short-lived access tokens (15 minutes)
- **Refresh Tokens**: Secure refresh token rotation
- **Token Storage**: HttpOnly cookies for web sessions

### 2. Session Management
- **Session Encryption**: Redis with encryption at rest
- **Session Timeout**: Configurable timeout (default: 24 hours)
- **Session Invalidation**: Proper logout handling
- **Concurrent Sessions**: Limit active sessions per user

### 3. CSRF Protection
- **CSRF Tokens**: Implementation in forms
- **SameSite Cookies**: Strict SameSite policy
- **Origin Validation**: Validate request origins

### 4. Rate Limiting
- **Authentication Endpoints**: 5 attempts per minute
- **API Endpoints**: 100 requests per minute per user
- **IP-based Limits**: Backup IP-based rate limiting

### 5. Security Headers
```python
TALISMAN_CONFIG = {
    'force_https': True,
    'strict_transport_security': True,
    'content_security_policy': {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
    }
}
```

## Configuration Management

### 1. Environment-Specific Configuration
```python
# config/auth_config.py
class AuthConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_TYPE = os.environ.get('SESSION_TYPE', 'redis')
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    # OAuth2 Providers
    OAUTH2_PROVIDERS = {
        'google': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
            'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
            'enabled': bool(os.environ.get('GOOGLE_CLIENT_ID'))
        },
        # ... other providers
    }
```

### 2. Provider Registration
```python
# Provider auto-discovery based on environment variables
enabled_providers = []
for provider_name, config in OAUTH2_PROVIDERS.items():
    if config.get('enabled'):
        enabled_providers.append(provider_name)
```

## Database Schema Extensions

### 1. User Management Tables
```sql
-- Users table for authenticated users
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
);

-- User sessions table
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
);

-- Audit log for authentication events
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
);
```

## Monitoring & Logging

### 1. Authentication Events
- Login attempts (success/failure)
- Provider-specific authentication
- Session creation/destruction
- Token refresh events
- Permission violations

### 2. Security Monitoring
- Failed login attempts
- Brute force detection
- Suspicious IP activity
- Token validation failures
- Session hijacking attempts

### 3. Metrics Collection
- Authentication success rates by provider
- Average session duration
- Active user counts
- API usage by authenticated users

## Error Handling & User Experience

### 1. Authentication Errors
```python
AUTH_ERROR_MESSAGES = {
    'provider_error': 'Authentication provider error. Please try again.',
    'invalid_token': 'Your session has expired. Please log in again.',
    'insufficient_permissions': 'You do not have permission to access this resource.',
    'rate_limited': 'Too many requests. Please try again later.',
    'provider_unavailable': 'Authentication service temporarily unavailable.'
}
```

### 2. Graceful Degradation
- Fallback authentication methods
- Offline capability where appropriate
- Clear error messaging
- Automatic retry mechanisms

## Deployment Considerations

### 1. Docker Integration
```dockerfile
# Add authentication dependencies to Dockerfile
RUN pip install authlib flask-session flask-talisman flask-limiter pyjwt redis

# Ensure Redis is available in docker-compose.yml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 2. Environment Variables
- Secure secret management (use Docker secrets or cloud key vaults)
- Provider-specific configuration
- Redis connection settings

### 3. HTTPS Requirements
- Force HTTPS in production
- Proper SSL certificate handling
- Secure cookie settings

## Testing Strategy

### 1. Unit Tests
- OAuth2 provider implementations
- Token validation logic
- Session management
- Middleware functionality

### 2. Integration Tests
- End-to-end authentication flows
- Provider callback handling
- Session persistence
- Error scenarios

### 3. Security Tests
- CSRF protection validation
- Session hijacking prevention
- Token tampering detection
- Rate limiting effectiveness

## Success Metrics

### 1. Technical Metrics
- Authentication success rate > 99%
- Session timeout < 100ms
- Token validation < 50ms
- Zero unauthorized access events

### 2. User Experience Metrics
- Login completion rate > 95%
- Average login time < 10 seconds
- User satisfaction with provider choice
- Support ticket reduction

## Implementation Checklist

### Phase 1: Setup ✅
- [ ] Install dependencies
- [ ] Create authentication module structure  
- [ ] Configure environment variables
- [ ] Set up Redis session store

### Phase 2: Core Implementation ✅
- [ ] Implement base OAuth2 provider
- [ ] Create authentication manager
- [ ] Build authentication middleware
- [ ] Develop protection decorators

### Phase 3: Provider Integration ✅
- [ ] Google OAuth2 implementation
- [ ] Azure AD implementation
- [ ] GitHub implementation
- [ ] Oracle OCI implementation

### Phase 4: Route Protection ✅
- [ ] Add authentication routes
- [ ] Protect existing API endpoints
- [ ] Implement role-based access
- [ ] Add logout functionality

### Phase 5: Frontend ✅
- [ ] Create login page
- [ ] Update dashboard with user info
- [ ] Add logout button
- [ ] Handle session timeouts

### Phase 6: Testing & Security ✅
- [ ] Security testing
- [ ] Provider integration tests
- [ ] Performance testing
- [ ] Documentation updates

## Next Steps

1. **Review and approve this strategy**
2. **Set up development environment with required dependencies**
3. **Register OAuth2 applications with each provider**
4. **Begin Phase 1 implementation**
5. **Test with one provider before scaling to all**

---

**Document Version**: 1.0  
**Last Updated**: $(date)  
**Author**: Claude Code Assistant  
**Review Status**: Pending