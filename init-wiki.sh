#!/bin/bash

echo "🚀 Initializing GitHub Wiki for AML Controller"
echo "=============================================="

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "📁 Working directory: $TEMP_DIR"
cd "$TEMP_DIR"

# Try to clone the wiki repository
echo "📥 Attempting to clone wiki repository..."
if git clone https://github.com/paihari/aml-controller.wiki.git aml-wiki 2>/dev/null; then
    echo "✅ Wiki repository found!"
    cd aml-wiki
else
    echo "ℹ️  Wiki repository not found. Creating new wiki..."
    
    # Initialize a new git repository for the wiki
    mkdir aml-wiki
    cd aml-wiki
    git init
    git remote add origin https://github.com/paihari/aml-controller.wiki.git
    
    # Create initial README to initialize the wiki
    echo "# AML Controller Wiki" > Home.md
    git add Home.md
    git commit -m "Initialize wiki"
    
    # Try to push to create the wiki repository
    echo "📤 Creating wiki repository on GitHub..."
    git push -u origin main 2>/dev/null || git push -u origin master 2>/dev/null || {
        echo "❌ Unable to create wiki repository."
        echo "Please enable the wiki feature first:"
        echo "   1. Go to https://github.com/paihari/aml-controller/settings"
        echo "   2. Scroll to 'Features' section"  
        echo "   3. Check ✅ 'Wikis'"
        echo "   4. Save changes"
        echo "   5. Visit https://github.com/paihari/aml-controller/wiki"
        echo "   6. Create the first page manually, then run this script again"
        cd - > /dev/null
        rm -rf "$TEMP_DIR"
        exit 1
    }
fi

# Now copy our wiki content
echo "📄 Copying wiki documentation..."
cp "${OLDPWD}/wiki/Home.md" ./Home.md
cp "${OLDPWD}/wiki/Quick-Start-Guide.md" ./Quick-Start-Guide.md  
cp "${OLDPWD}/wiki/System-Architecture.md" ./System-Architecture.md
cp "${OLDPWD}/wiki/API-Reference.md" ./API-Reference.md
cp "${OLDPWD}/wiki/Detection-Rules.md" ./Detection-Rules.md

# Add and commit all files
git add .
git commit -m "Add comprehensive AML documentation

- Complete Home page with navigation
- Quick Start Guide (5-minute setup)
- System Architecture with C4 diagrams
- Complete API Reference with examples  
- Detection Rules for all AML algorithms"

# Push to GitHub
echo "🚀 Pushing to GitHub Wiki..."
if git push; then
    echo "🎉 SUCCESS! GitHub Wiki has been set up!"
    echo ""
    echo "📚 Your wiki is now available at:"
    echo "   https://github.com/paihari/aml-controller/wiki"
    echo ""
    echo "📖 Pages created:"
    echo "   • Home"
    echo "   • Quick-Start-Guide" 
    echo "   • System-Architecture"
    echo "   • API-Reference"
    echo "   • Detection-Rules"
else
    echo "❌ Failed to push to GitHub Wiki"
fi

# Cleanup
cd - > /dev/null
rm -rf "$TEMP_DIR"