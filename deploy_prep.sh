#!/bin/bash

# Dynamic AML System - Deployment Preparation Script

echo "🛡️  Dynamic AML System - Deployment Prep"
echo "========================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << EOF
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env.bak/
venv.bak/
*.db
*.log
.DS_Store
node_modules/
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache
.env
*.env
EOF
    echo "✅ .gitignore created"
fi

# Test the production app
echo "🔧 Testing production app..."
if command -v python3 &> /dev/null; then
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    python3 -c "
try:
    from app_production import app
    print('✅ Production app imports successfully')
except Exception as e:
    print(f'❌ Production app test failed: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo "✅ Production app test passed"
    else
        echo "❌ Production app test failed - check dependencies"
        exit 1
    fi
else
    echo "⚠️  Python3 not found, skipping app test"
fi

# Test Docker build (optional)
if command -v docker &> /dev/null; then
    echo "🐳 Testing Docker build..."
    if docker build -t aml-test . --quiet; then
        echo "✅ Docker build successful"
        docker rmi aml-test --force > /dev/null 2>&1
    else
        echo "⚠️  Docker build failed - check Dockerfile"
    fi
else
    echo "⚠️  Docker not found, skipping Docker test"
fi

# Stage files for Git
echo "📤 Staging files for Git..."
git add .
echo "✅ Files staged"

# Show git status
echo "📋 Git status:"
git status --short

echo ""
echo "🎯 Deployment Ready!"
echo "===================="
echo ""
echo "Next steps:"
echo "1. Commit changes:"
echo "   git commit -m 'Deploy: Dynamic AML System'"
echo ""
echo "2. Push to GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/aml-controller.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Choose deployment platform:"
echo "   🚄 Railway:      https://railway.app (recommended)"
echo "   🎨 Render:       https://render.com"
echo "   🟣 Heroku:       https://heroku.com"
echo "   ☁️  Google Cloud: https://cloud.google.com/run"
echo ""
echo "4. See DEPLOYMENT.md for detailed instructions"
echo ""
echo "✨ Your AML system is ready to go online!"