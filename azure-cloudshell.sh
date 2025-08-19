#!/bin/bash

# Azure Cloud Shell Deployment Script
# Run this directly in Azure Cloud Shell (shell.azure.com)

echo "🌐 Dynamic AML System - Azure Cloud Shell Deployment"
echo "==================================================="

# Configuration
RESOURCE_GROUP="aml-system-rg-$(date +%s)"
LOCATION="eastus"
CONTAINER_NAME="dynamic-aml-system"
DNS_LABEL="aml-system-$(date +%s)"

echo "📋 Deployment Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   Container Name: $CONTAINER_NAME"
echo "   DNS Label: $DNS_LABEL"
echo ""

# Create resource group
echo "🏗️  Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

echo "✅ Resource group created"

# Deploy using pre-built Docker image from Docker Hub
echo "🚀 Deploying container instance..."

DEPLOYMENT_OUTPUT=$(az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image python:3.11-slim \
    --dns-name-label $DNS_LABEL \
    --ports 5000 \
    --environment-variables FLASK_ENV=production PORT=5000 \
    --memory 1 \
    --cpu 0.5 \
    --restart-policy Always \
    --command-line "/bin/bash -c '
        apt-get update && apt-get install -y git curl && 
        git clone https://github.com/YOUR_USERNAME/aml-controller.git /app &&
        cd /app && 
        pip install -r requirements.txt && 
        python app_production.py
    '" \
    --output json)

# Extract public IP and FQDN
PUBLIC_IP=$(echo $DEPLOYMENT_OUTPUT | jq -r '.ipAddress.ip')
FQDN=$(echo $DEPLOYMENT_OUTPUT | jq -r '.ipAddress.fqdn')

echo ""
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "========================"
echo ""
echo "📍 PUBLIC IP ADDRESS: $PUBLIC_IP"
echo "🌐 FULL DOMAIN NAME:   $FQDN"
echo ""
echo "🔗 Access URLs:"
echo "   🏠 Dashboard:  http://$FQDN:5000/dashboard"
echo "   ❤️  Health:    http://$FQDN:5000/api/health"  
echo "   🔧 API Base:   http://$FQDN:5000/api"
echo ""
echo "⏳ Container is starting... (may take 2-3 minutes)"
echo ""
echo "🧪 Test when ready:"
echo "   curl http://$FQDN:5000/api/health"
echo ""

# Save deployment info to Azure Cloud Shell storage
cat > ~/aml-deployment-info.txt << EOF
Dynamic AML System - Azure Deployment
====================================
Deployed: $(date)
Resource Group: $RESOURCE_GROUP
Location: $LOCATION

📍 PUBLIC IP: $PUBLIC_IP
🌐 FQDN: $FQDN

URLs:
🏠 Dashboard: http://$FQDN:5000/dashboard
❤️ Health: http://$FQDN:5000/api/health
🔧 API: http://$FQDN:5000/api

Management Commands:
- View logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow
- Restart: az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME  
- Status: az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME
- Delete: az group delete --name $RESOURCE_GROUP --yes --no-wait
EOF

echo "💾 Deployment info saved to ~/aml-deployment-info.txt"
echo ""
echo "🎯 Management:"
echo "   View logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow"
echo "   Restart:   az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
echo "   Delete:    az group delete --name $RESOURCE_GROUP --yes"
echo ""
echo "✨ Your AML system will be online shortly!"