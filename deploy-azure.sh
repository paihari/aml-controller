#!/bin/bash

# Azure Deployment Script for Dynamic AML System

set -e

echo "🌐 Dynamic AML System - Azure Deployment"
echo "========================================"

# Configuration
RESOURCE_GROUP="aml-system-rg"
LOCATION="eastus"
CONTAINER_NAME="dynamic-aml-system"
ACR_NAME="amlsystemregistry$(date +%s)"
IMAGE_NAME="dynamic-aml"
APP_NAME="aml-system-$(date +%s)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first:"
    echo "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first:"
    echo "https://docs.docker.com/get-docker/"
    exit 1
fi

print_status "Checking Azure login status..."
if ! az account show &> /dev/null; then
    print_warning "Not logged in to Azure. Please log in:"
    az login
fi

print_success "Azure CLI ready"

# Create resource group
print_status "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

print_success "Resource group created"

# Method 1: Azure Container Instances (Fastest with Public IP)
echo ""
echo "🚀 Option 1: Azure Container Instances (Recommended)"
echo "=================================================="

read -p "Deploy using Container Instances? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    
    # Create Azure Container Registry
    print_status "Creating Azure Container Registry: $ACR_NAME"
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --admin-enabled true \
        --output table
    
    print_success "Container Registry created"
    
    # Get ACR login server
    ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
    
    # Build and tag Docker image
    print_status "Building Docker image..."
    docker build -t $IMAGE_NAME .
    docker tag $IMAGE_NAME $ACR_LOGIN_SERVER/$IMAGE_NAME:latest
    
    print_success "Docker image built and tagged"
    
    # Login to ACR and push image
    print_status "Pushing image to Azure Container Registry..."
    az acr login --name $ACR_NAME
    docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:latest
    
    print_success "Image pushed to registry"
    
    # Get ACR credentials
    ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)
    
    # Deploy container instance
    print_status "Deploying container instance..."
    DEPLOYMENT_OUTPUT=$(az container create \
        --resource-group $RESOURCE_GROUP \
        --name $CONTAINER_NAME \
        --image $ACR_LOGIN_SERVER/$IMAGE_NAME:latest \
        --registry-login-server $ACR_LOGIN_SERVER \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --dns-name-label "aml-system-$(date +%s)" \
        --ports 5000 \
        --environment-variables FLASK_ENV=production PORT=5000 DATABASE_PATH=/app/data/aml_database.db \
        --memory 1 \
        --cpu 0.5 \
        --restart-policy Always \
        --output json)
    
    # Extract public IP and FQDN
    PUBLIC_IP=$(echo $DEPLOYMENT_OUTPUT | jq -r '.ipAddress.ip')
    FQDN=$(echo $DEPLOYMENT_OUTPUT | jq -r '.ipAddress.fqdn')
    
    print_success "Container deployed successfully!"
    
    echo ""
    echo "🎉 DEPLOYMENT SUCCESSFUL!"
    echo "========================"
    echo ""
    echo "📍 PUBLIC IP ADDRESS: $PUBLIC_IP"
    echo "🌐 FULL DOMAIN NAME:   $FQDN"
    echo ""
    echo "🔗 URLs:"
    echo "   Dashboard: http://$FQDN:5000/dashboard"
    echo "   API Health: http://$FQDN:5000/api/health"
    echo "   API Base: http://$FQDN:5000/api"
    echo ""
    echo "📊 Test your deployment:"
    echo "   curl http://$FQDN:5000/api/health"
    echo ""
    
    # Save deployment info
    cat > azure-deployment-info.txt << EOF
Dynamic AML System - Azure Deployment Info
==========================================
Deployed: $(date)
Resource Group: $RESOURCE_GROUP
Container Name: $CONTAINER_NAME
Container Registry: $ACR_NAME

PUBLIC IP: $PUBLIC_IP
FQDN: $FQDN

URLs:
- Dashboard: http://$FQDN:5000/dashboard
- API Health: http://$FQDN:5000/api/health
- API Base: http://$FQDN:5000/api

Management:
- View logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME
- Restart: az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME
- Delete: az group delete --name $RESOURCE_GROUP --yes
EOF
    
    print_success "Deployment info saved to azure-deployment-info.txt"
    
    # Test the deployment
    print_status "Testing deployment..."
    sleep 30  # Wait for container to start
    
    if curl -f http://$FQDN:5000/api/health > /dev/null 2>&1; then
        print_success "✅ Health check passed!"
        print_success "✅ Your AML system is live and accessible!"
    else
        print_warning "⚠️  Health check failed. Container may still be starting..."
        print_status "Check status with: az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
    fi
    
else
    echo ""
    echo "🌐 Option 2: Azure App Service"
    echo "============================="
    
    print_warning "Azure App Service requires a container registry URL."
    print_warning "Please build and push your image to Docker Hub or Azure Container Registry first."
    
    echo "Manual steps:"
    echo "1. Build: docker build -t yourusername/dynamic-aml ."
    echo "2. Push: docker push yourusername/dynamic-aml"
    echo "3. Deploy using the ARM template:"
    echo "   az deployment group create --resource-group $RESOURCE_GROUP --template-file azure-webapp.json --parameters dockerImage=yourusername/dynamic-aml"
fi

echo ""
print_success "🎯 Deployment script completed!"
print_status "Your Dynamic AML System is now running on Microsoft Azure"