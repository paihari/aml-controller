# 🌐 Azure Deployment - Get Public IP in 5 Minutes

Deploy your Dynamic AML System to **Microsoft Azure** and get a **public IP address**.

## 🚀 Fastest Method (No Docker Build Required)

```bash
# One command - complete deployment
chmod +x azure-simple-deploy.sh
./azure-simple-deploy.sh
```

**Output:** You'll get a public IP and FQDN like:
```
📍 PUBLIC IP ADDRESS: 20.123.456.789
🌐 FULL DOMAIN NAME:   aml-system-12345.eastus.azurecontainer.io

🔗 Access URLs:
   🏠 Home:      http://aml-system-12345.eastus.azurecontainer.io:5000/
   🛡️  Dashboard: http://aml-system-12345.eastus.azurecontainer.io:5000/dashboard  
   ❤️  Health:   http://aml-system-12345.eastus.azurecontainer.io:5000/api/health
```

## 🎯 Alternative Methods

### Option 1: Full Docker Build
```bash
./deploy-azure.sh
```
- Builds complete Docker image
- Uses Azure Container Registry
- Full production deployment

### Option 2: Azure Cloud Shell
1. Go to [shell.azure.com](https://shell.azure.com)
2. Upload `azure-cloudshell.sh`
3. Run: `chmod +x azure-cloudshell.sh && ./azure-cloudshell.sh`

## 📋 Prerequisites

- **Azure CLI**: `brew install azure-cli` (or visit [docs.microsoft.com](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- **Azure Account**: Free tier works ([azure.microsoft.com/free](https://azure.microsoft.com/free))
- **5 minutes**: That's all it takes!

## 💰 Cost

**Azure Container Instances** (0.5 vCPU, 1GB RAM):
- ~$0.25/day continuous operation  
- **Free**: $200 Azure credit for new accounts = 800+ days free
- **Pay-as-you-go**: Only charged when running

## 🎉 What You Get

### ✅ Public Access
- **Public IP address** accessible worldwide
- **Custom domain name** (*.azurecontainer.io)
- **HTTP access** on port 5000

### ✅ AML System Features
- Real-time transaction monitoring
- Sanctions screening (OFAC data)
- 5 AML detection rules
- Interactive dashboard
- REST API endpoints

### ✅ Azure Benefits
- **99.9% uptime SLA**
- **Global availability** (15+ regions)
- **Auto-scaling** capabilities
- **Integration** with Azure services

## 🔧 Management Commands

After deployment, manage your system:

```bash
# View logs
az container logs --resource-group aml-system-rg --name dynamic-aml-system --follow

# Restart container
az container restart --resource-group aml-system-rg --name dynamic-aml-system

# Get public IP
az container show --resource-group aml-system-rg --name dynamic-aml-system --query ipAddress.ip

# Delete everything
az group delete --name aml-system-rg --yes
```

## 🧪 Test Your Deployment

Once deployed, test these URLs:

```bash
# Health check
curl http://YOUR_FQDN:5000/api/health

# Statistics  
curl http://YOUR_FQDN:5000/api/statistics

# Dashboard (in browser)
open http://YOUR_FQDN:5000/dashboard
```

## 🚨 Troubleshooting

**Container not starting?**
```bash
az container logs --resource-group aml-system-rg --name dynamic-aml-system
```

**Can't access public IP?**
- Wait 2-3 minutes for container startup
- Verify port 5000 is included in the URL
- Check container state: `az container show --resource-group aml-system-rg --name dynamic-aml-system --query instanceView.state`

## 🎯 Ready to Deploy?

**Quickest path:**
```bash
# Login to Azure (one time)
az login

# Deploy your AML system
./azure-simple-deploy.sh

# Wait 3 minutes, then access your public IP!
```

**Your Dynamic AML System will be live on Azure with a public IP in under 5 minutes!** 🚀

---

📍 **Need the IP immediately?** The script outputs the public IP as soon as deployment starts!