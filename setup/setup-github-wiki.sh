#!/bin/bash

echo "🚀 Setting up GitHub Wiki for AML Controller"
echo "============================================"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Create temporary directory for wiki setup
TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: $TEMP_DIR"

# Clone the wiki repository
echo "📥 Cloning wiki repository..."
cd "$TEMP_DIR"
git clone https://github.com/paihari/aml-controller.wiki.git

# Check if clone was successful
if [ ! -d "aml-controller.wiki" ]; then
    echo "❌ Failed to clone wiki repository."
    echo "Make sure the wiki is enabled in your GitHub repository settings:"
    echo "   1. Go to https://github.com/paihari/aml-controller/settings"
    echo "   2. Scroll to 'Features' section"
    echo "   3. Check ✅ 'Wikis'"
    echo "   4. Save changes"
    echo "   5. Then run this script again"
    exit 1
fi

cd aml-controller.wiki

# Copy wiki files from the original repository
echo "📄 Copying wiki content..."
cp "$(dirname "$0")/wiki/Home.md" ./Home.md
cp "$(dirname "$0")/wiki/Quick-Start-Guide.md" ./Quick-Start-Guide.md
cp "$(dirname "$0")/wiki/System-Architecture.md" ./System-Architecture.md
cp "$(dirname "$0")/wiki/API-Reference.md" ./API-Reference.md
cp "$(dirname "$0")/wiki/Detection-Rules.md" ./Detection-Rules.md

# Add all files to git
echo "📤 Adding files to wiki..."
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit. Wiki might already be up to date."
else
    # Commit the changes
    echo "💾 Committing wiki pages..."
    git commit -m "Add comprehensive AML project documentation

- Home page with complete navigation structure
- Quick Start Guide with 5-minute setup instructions  
- System Architecture with C4 model diagrams
- Complete API Reference with examples
- Detailed Detection Rules for all AML algorithms

Features professional documentation with:
- Mermaid architecture diagrams
- Code examples in Python, JavaScript, cURL
- Performance metrics and benchmarks
- Security and compliance guidelines"

    # Push to GitHub wiki
    echo "🚀 Pushing to GitHub Wiki..."
    if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
        echo "✅ Successfully updated GitHub Wiki!"
        echo ""
        echo "🎉 Your wiki is now available at:"
        echo "   https://github.com/paihari/aml-controller/wiki"
        echo ""
        echo "📚 Wiki pages created:"
        echo "   • Home: https://github.com/paihari/aml-controller/wiki/Home"
        echo "   • Quick Start: https://github.com/paihari/aml-controller/wiki/Quick-Start-Guide"
        echo "   • Architecture: https://github.com/paihari/aml-controller/wiki/System-Architecture"
        echo "   • API Reference: https://github.com/paihari/aml-controller/wiki/API-Reference"
        echo "   • Detection Rules: https://github.com/paihari/aml-controller/wiki/Detection-Rules"
    else
        echo "❌ Failed to push to GitHub Wiki."
        echo "Please check your GitHub authentication and permissions."
    fi
fi

# Cleanup
echo "🧹 Cleaning up..."
cd - > /dev/null
rm -rf "$TEMP_DIR"

echo "🏁 Wiki setup complete!"