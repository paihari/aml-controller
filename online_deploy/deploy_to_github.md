# Deploy AML Dashboard to GitHub Pages

## Quick Steps:

1. **Push to GitHub** (if not already done):
```bash
git remote add origin https://github.com/[username]/aml-controller.git
git branch -M main
git push -u origin main
```

2. **Enable GitHub Pages**:
   - Go to repository Settings
   - Scroll to Pages section
   - Source: "Deploy from a branch"
   - Branch: `main`
   - Folder: `/docs`
   - Save

3. **Access URLs**:
   - Enhanced: `https://[username].github.io/aml-controller/enhanced.html`
   - Standard: `https://[username].github.io/aml-controller/index.html`

## Alternative: Netlify Drop

1. Visit: https://app.netlify.com/drop
2. Drag the entire `online_deploy` folder
3. Get instant URL like: `https://amazing-name-123456.netlify.app`

The dashboard will be immediately available with all 10 alerts and interactive features!