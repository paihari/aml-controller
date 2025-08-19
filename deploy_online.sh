#!/bin/bash

echo "🚀 Deploying AML Dashboard Online..."
echo "=" * 50

# Create deployment packages
echo "📦 Creating deployment packages..."
mkdir -p online_deploy

# Copy main files
cp docs/enhanced.html online_deploy/index.html
cp docs/index.html online_deploy/standard.html

# Create a simple index with both versions
cat > online_deploy/README.md << EOF
# AML Alert Dashboard - Online Demo

## 🌐 Available Dashboards

1. **Enhanced Dashboard**: [index.html](./index.html) - Full featured with 10 alerts
2. **Standard Dashboard**: [standard.html](./standard.html) - Original 3 alerts

## 📊 Features

- Real-time AML alert visualization
- Interactive risk distribution charts
- OFAC sanctions screening results
- High-risk geography detection
- Structuring pattern analysis

## 🔍 Sample Data

- 20 transactions processed
- 15 parties analyzed
- 25 watchlist entries checked
- 5 detection rules applied

Generated $(date) by AML Agentic Platform
EOF

echo "📁 Created deployment package in: online_deploy/"
ls -la online_deploy/

echo ""
echo "🌐 Deployment Options:"
echo ""

echo "1. 📎 Netlify Drop (Instant):"
echo "   - Visit: https://app.netlify.com/drop"
echo "   - Drag 'online_deploy' folder"
echo "   - Get instant URL"
echo ""

echo "2. 🚀 Vercel (GitHub):"
echo "   - Visit: https://vercel.com/new"
echo "   - Import this repository"
echo "   - Auto-deploy from GitHub"
echo ""

echo "3. 📡 GitHub Pages:"
echo "   - Repository settings > Pages"
echo "   - Source: Deploy from branch 'main'"
echo "   - Folder: /docs"
echo ""

echo "4. ☁️ Azure Static Web Apps:"
echo "   - Create Static Web App resource"
echo "   - Connect to this GitHub repo"
echo "   - Build settings: Root folder '/'"
echo ""

echo "5. 🔗 Surge.sh (Command Line):"
echo "   cd online_deploy && surge . aml-demo-$(date +%s).surge.sh"
echo ""

echo "✅ All deployment packages ready!"
echo "📂 Location: $(pwd)/online_deploy/"

# Try surge deployment if available
if command -v surge &> /dev/null; then
    echo ""
    read -p "🚀 Deploy to Surge.sh now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🌐 Deploying to Surge.sh..."
        cd online_deploy
        DOMAIN="aml-demo-$(date +%s).surge.sh"
        surge . $DOMAIN
        echo ""
        echo "🎉 Deployed successfully!"
        echo "📊 Enhanced Dashboard: https://$DOMAIN"
        echo "📋 Standard Dashboard: https://$DOMAIN/standard.html"
    fi
else
    echo ""
    echo "💡 Install surge for instant deployment:"
    echo "   npm install -g surge"
fi