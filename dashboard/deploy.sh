#!/bin/bash

echo "🚀 Deploying AML Dashboard..."

# Create a simple deployment package
mkdir -p deploy
cp index.html deploy/
cp -r ../sample_data deploy/ 2>/dev/null || true

echo "📦 Dashboard package created in deploy/"
echo "📁 Files ready for hosting:"
ls -la deploy/

echo ""
echo "🌐 Manual Deployment Options:"
echo ""
echo "1. 📎 Netlify Drop: https://app.netlify.com/drop"
echo "   - Drag and drop the 'deploy' folder"
echo ""
echo "2. 🚀 Vercel: https://vercel.com/new"
echo "   - Import from GitHub or drag files"
echo ""
echo "3. 📡 GitHub Pages:"
echo "   - Push to GitHub and enable Pages"
echo ""
echo "4. ☁️ Azure Static Web Apps:"
echo "   - Create resource and deploy files"

echo ""
echo "✅ Deployment package ready!"
echo "📂 Location: $(pwd)/deploy/"