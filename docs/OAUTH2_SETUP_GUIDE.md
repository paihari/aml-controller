# OAuth2 Provider Setup Guide

This guide will help you obtain OAuth2 credentials for each authentication provider.

## ⚠️ Important Notes

- Keep all client secrets secure and never commit them to version control
- For production, use environment variables or secret management systems
- Each provider requires a different setup process
- You'll need to set redirect URIs for each provider

## Standard Redirect URIs

For your AML Controller application, use these redirect URIs:
- **Development**: `http://localhost:5000/auth/callback/{provider}`
- **Production**: `https://your-domain.com/auth/callback/{provider}`

Replace `{provider}` with: `google`, `microsoft`, `github`, or `oracle`

---

## 1️⃣ Google OAuth2 Setup

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google+ API or Identity API

### Step 2: Create OAuth2 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Choose **Web application**
4. Set **Authorized redirect URIs**:
   - `http://localhost:5000/auth/callback/google` (development)
   - `https://your-domain.com/auth/callback/google` (production)

### Step 3: Update .env file
```env
GOOGLE_CLIENT_ID=your-actual-google-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-google-client-secret
```

---

## 2️⃣ Microsoft Azure OAuth2 Setup

### Step 1: Register Application in Azure AD
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Set **Redirect URI** (Web): 
   - `http://localhost:5000/auth/callback/microsoft` (development)
   - `https://your-domain.com/auth/callback/microsoft` (production)

### Step 2: Get Application Details
1. Note the **Application (client) ID**
2. Note the **Directory (tenant) ID**
3. Go to **Certificates & secrets** → **New client secret**
4. Copy the secret value (you won't see it again!)

### Step 3: Update .env file
```env
AZURE_CLIENT_ID=your-actual-azure-application-id
AZURE_CLIENT_SECRET=your-actual-azure-client-secret
AZURE_TENANT_ID=your-actual-azure-tenant-id
```

---

## 3️⃣ GitHub OAuth2 Setup

### Step 1: Create GitHub OAuth App
1. Go to [GitHub Settings](https://github.com/settings/developers)
2. Click **OAuth Apps** → **New OAuth App**
3. Fill in details:
   - **Application name**: AML Controller
   - **Homepage URL**: `http://localhost:5000` (or your domain)
   - **Authorization callback URL**: 
     - `http://localhost:5000/auth/callback/github` (development)
     - `https://your-domain.com/auth/callback/github` (production)

### Step 2: Get Credentials
1. Note the **Client ID**
2. Generate a **Client Secret**

### Step 3: Update .env file
```env
GITHUB_CLIENT_ID=your-actual-github-client-id
GITHUB_CLIENT_SECRET=your-actual-github-client-secret
```

---

## 4️⃣ Oracle Cloud Infrastructure (OCI) OAuth2 Setup

### Step 1: Access OCI Console
1. Go to [Oracle Cloud Console](https://cloud.oracle.com/)
2. Navigate to **Identity & Security** → **Identity** → **Applications**

### Step 2: Create Confidential Application
1. Click **Add Application**
2. Choose **Confidential Application**
3. Set **Redirect URL**:
   - `http://localhost:5000/auth/callback/oracle` (development)
   - `https://your-domain.com/auth/callback/oracle` (production)

### Step 3: Configure OAuth2 Settings
1. Enable **Authorization Code** grant type
2. Set scopes: `openid`, `email`, `profile`
3. Note the **Client ID** and **Client Secret**
4. Note your **IDCS Instance ID** (from the URL)

### Step 4: Update .env file
```env
OCI_CLIENT_ID=your-actual-oci-client-id
OCI_CLIENT_SECRET=your-actual-oci-client-secret
OCI_INSTANCE_ID=your-oci-instance-id
```

---

## 🔧 Testing Your Configuration

After setting up all providers, test the configuration:

```bash
# Check if environment variables are loaded
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

providers = ['GOOGLE', 'AZURE', 'GITHUB', 'OCI']
for provider in providers:
    client_id = os.getenv(f'{provider}_CLIENT_ID')
    client_secret = os.getenv(f'{provider}_CLIENT_SECRET')
    
    if client_id and client_id != f'your-{provider.lower()}-client-id':
        print(f'✅ {provider}: Configured')
    else:
        print(f'❌ {provider}: Not configured')
"
```

## 🛡️ Security Best Practices

1. **Never commit secrets**: Add `.env` to `.gitignore`
2. **Use different credentials**: Separate dev/prod credentials
3. **Rotate secrets regularly**: Change secrets periodically
4. **Limit scopes**: Only request necessary permissions
5. **Monitor usage**: Track OAuth2 usage in each provider's console

## 🚀 Next Steps

After configuring OAuth2 providers:
1. Test each provider individually
2. Implement the authentication manager
3. Add authentication routes to your Flask app
4. Test the complete authentication flow

---

**Need Help?**
- Check each provider's documentation for the latest instructions
- Test with one provider first before adding others
- Use development URLs for initial testing