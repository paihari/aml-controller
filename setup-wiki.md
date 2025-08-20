# 📚 GitHub Wiki Setup Instructions

## Step 1: Enable Wiki
1. Go to https://github.com/paihari/aml-controller/settings
2. Scroll to "Features" section
3. Check ✅ "Wikis"
4. Save changes

## Step 2: Create Wiki Pages

Go to https://github.com/paihari/aml-controller/wiki and create these pages:

### Page 1: Home
**Title**: `Home`
**Content**: Copy entire content from `wiki/Home.md`

### Page 2: Quick Start Guide  
**Title**: `Quick-Start-Guide`
**Content**: Copy entire content from `wiki/Quick-Start-Guide.md`

### Page 3: System Architecture
**Title**: `System-Architecture` 
**Content**: Copy entire content from `wiki/System-Architecture.md`

### Page 4: API Reference
**Title**: `API-Reference`
**Content**: Copy entire content from `wiki/API-Reference.md`

### Page 5: Detection Rules
**Title**: `Detection-Rules`
**Content**: Copy entire content from `wiki/Detection-Rules.md`

## Step 3: Verify Links
After creating all pages, check that internal links work properly.

## Alternative: Use GitHub CLI
If you have GitHub CLI installed:

```bash
# Clone wiki repository
git clone https://github.com/paihari/aml-controller.wiki.git

# Copy wiki files
cp wiki/*.md aml-controller.wiki/

# Push to wiki
cd aml-controller.wiki
git add .
git commit -m "Add comprehensive wiki documentation"
git push
```

## Quick Links to Copy From:
- [Home.md](https://github.com/paihari/aml-controller/blob/main/wiki/Home.md)
- [Quick-Start-Guide.md](https://github.com/paihari/aml-controller/blob/main/wiki/Quick-Start-Guide.md)
- [System-Architecture.md](https://github.com/paihari/aml-controller/blob/main/wiki/System-Architecture.md)
- [API-Reference.md](https://github.com/paihari/aml-controller/blob/main/wiki/API-Reference.md)
- [Detection-Rules.md](https://github.com/paihari/aml-controller/blob/main/wiki/Detection-Rules.md)

Just click each link above, copy the raw content, and paste into the corresponding wiki page!