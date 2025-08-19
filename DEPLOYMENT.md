# 🚀 Dynamic AML System - Online Deployment Guide

Deploy your Dynamic AML Detection System online using various cloud platforms. Choose the method that best fits your needs.

## 📋 Quick Summary

**Ready-to-deploy files created:**
- ✅ `app_production.py` - Production Flask app
- ✅ `Dockerfile` - Docker containerization  
- ✅ `requirements.txt` - Python dependencies
- ✅ Platform-specific configs (Railway, Render, Heroku, etc.)
- ✅ Dynamic dashboard with auto-API detection

## 🎯 Deployment Options

### Option 1: Railway (Recommended - Free & Easy)

**Why Railway?** Free tier, automatic HTTPS, simple deployment from GitHub.

1. **Push to GitHub** (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Dynamic AML System"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/aml-controller.git
   git push -u origin main
   ```

2. **Deploy on Railway**:
   - Visit [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Connect your GitHub repo: `aml-controller`
   - Railway auto-detects the Dockerfile and deploys
   - Get your URL: `https://YOUR_APP.railway.app`

3. **Access your system**:
   - Dashboard: `https://YOUR_APP.railway.app/dashboard`
   - API: `https://YOUR_APP.railway.app/api/health`

### Option 2: Render (Free Tier Available)

**Why Render?** Reliable, free SSL, good for production apps.

1. **Push to GitHub** (same as above)

2. **Deploy on Render**:
   - Visit [render.com](https://render.com)
   - Create "New Web Service"
   - Connect GitHub repo: `aml-controller`
   - Use these settings:
     - **Runtime:** Docker
     - **Build Command:** (auto-detected)
     - **Start Command:** `python app_production.py`
   - Deploy and get URL: `https://YOUR_APP.onrender.com`

### Option 3: Heroku (Classic Choice)

**Why Heroku?** Battle-tested platform, extensive documentation.

1. **Install Heroku CLI**:
   ```bash
   brew install heroku/brew/heroku  # Mac
   # or download from heroku.com
   ```

2. **Deploy**:
   ```bash
   heroku login
   heroku create your-aml-app-name
   git push heroku main
   heroku open
   ```

3. **Your URL**: `https://your-aml-app-name.herokuapp.com`

### Option 4: Google Cloud Run (Scalable)

**Why Cloud Run?** Pay-per-use, highly scalable, Google infrastructure.

1. **Install gcloud CLI**:
   ```bash
   # Follow instructions at cloud.google.com/sdk
   ```

2. **Deploy**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud run deploy aml-system --source . --region us-central1 --allow-unauthenticated
   ```

### Option 5: DigitalOcean App Platform

**Why DigitalOcean?** Simple pricing, good performance, developer-friendly.

1. **Push to GitHub**
2. **Create App** on DigitalOcean App Platform
3. **Connect GitHub repo** and deploy
4. **URL**: `https://YOUR_APP.ondigitalocean.app`

### Option 6: Local Docker (Testing)

Test the Docker container locally:

```bash
# Build image
docker build -t dynamic-aml .

# Run container
docker run -p 8080:5000 dynamic-aml

# Access at http://localhost:8080
```

## 🔧 Environment Configuration

Most platforms will auto-detect these settings from the config files:

| Platform | Config File | Port | Health Check |
|----------|-------------|------|--------------|
| Railway | `railway.toml` | Auto | `/api/health` |
| Render | `render.yaml` | Auto | `/api/health` |
| Heroku | `Procfile` | Auto | `/api/health` |
| Vercel | `vercel.json` | Auto | `/api/health` |
| Google App Engine | `app.yaml` | Auto | `/api/health` |

## 📱 Post-Deployment Testing

Once deployed, test your system:

1. **Health Check**: `https://YOUR_URL/api/health`
2. **Dashboard**: `https://YOUR_URL/dashboard`
3. **Generate Data**: Click "🎲 Generate Test Data" in dashboard
4. **API Test**:
   ```bash
   curl https://YOUR_URL/api/statistics
   ```

## 🛡️ Security Features Included

- ✅ **CORS configured** for production domains
- ✅ **Error handling** with proper HTTP status codes  
- ✅ **Request logging** for monitoring
- ✅ **Health checks** for uptime monitoring
- ✅ **Rate limiting** on data generation endpoints
- ✅ **Secure headers** and production settings

## 🎨 Customization

### Custom Domain
Most platforms support custom domains:
- Railway: Project Settings → Networking
- Render: Service Settings → Custom Domains
- Heroku: App Settings → Domains

### Environment Variables
Set these if needed:
- `DATABASE_PATH`: Custom database location
- `FLASK_ENV`: `production` (already set)
- `PORT`: Custom port (auto-detected)

### API Limits
Production limits are set in `app_production.py`:
- Max transactions per generation: 100
- Max batch processing: 50
- Alert history: 20 recent alerts

## 📊 Monitoring & Maintenance

### View Logs
- **Railway**: Project → Deployments → View Logs
- **Render**: Service → Logs tab
- **Heroku**: `heroku logs --tail`

### Database Persistence
- **Railway/Render**: Files persist across deployments
- **Heroku**: Use PostgreSQL add-on for persistence
- **Cloud Run**: Use Cloud SQL for production

### Scaling
- **Railway**: Automatic scaling included
- **Render**: Upgrade plan for auto-scaling  
- **Heroku**: `heroku ps:scale web=2`

## 🚨 Troubleshooting

### Common Issues

1. **"Application Error" on startup**:
   - Check logs for Python dependency issues
   - Ensure `requirements.txt` is complete

2. **Database errors**:
   - Check write permissions for database directory
   - Verify `DATABASE_PATH` environment variable

3. **API CORS errors**:
   - Verify your domain is in CORS origins list
   - Check browser developer console for errors

4. **Slow initial load**:
   - First request initializes the system (normal)
   - Subsequent requests will be faster

### Getting Help

- **Railway**: [railway.app/help](https://railway.app/help)
- **Render**: [render.com/docs](https://render.com/docs)  
- **Heroku**: [devcenter.heroku.com](https://devcenter.heroku.com)

## 🎉 Success! 

Once deployed, your Dynamic AML System will be available online with:

- 🌐 **Public URL** accessible worldwide
- 🔒 **HTTPS encryption** automatically configured
- 📊 **Real-time dashboard** with live data
- 🚀 **Production-ready API** with proper logging
- 🛡️ **AML detection engine** processing transactions
- 📥 **Live sanctions data** integration

**Next Steps:**
1. Share your URL: `https://YOUR_APP.PLATFORM.app/dashboard`
2. Generate demo data using the dashboard controls
3. Explore the API endpoints at `/api/health`
4. Monitor system performance through platform dashboards

---

**🎯 Recommended:** Start with **Railway** for the easiest deployment experience, then consider other platforms based on your scaling needs.