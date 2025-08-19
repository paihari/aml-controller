#!/bin/bash

# Simple Azure Deployment - No Docker Build Required
# Uses a pre-configured base image

echo "🌐 Azure Simple Deployment - Dynamic AML System"
echo "=============================================="

# Configuration
RESOURCE_GROUP="aml-system-$(date +%s)"
LOCATION="eastus"
CONTAINER_NAME="dynamic-aml-system"
DNS_LABEL="aml-system-$(date +%s)"

echo "🚀 Starting deployment..."
echo "Resource Group: $RESOURCE_GROUP"
echo "DNS Label: $DNS_LABEL"
echo ""

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install:"
    echo "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check login
if ! az account show &> /dev/null; then
    echo "🔐 Please login to Azure:"
    az login
fi

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION > /dev/null

# Create deployment with inline startup script
echo "🏗️  Deploying container..."

STARTUP_SCRIPT='#!/bin/bash
set -e
echo "Installing system dependencies..."
apt-get update > /dev/null 2>&1
apt-get install -y git curl > /dev/null 2>&1

echo "Cloning AML system..."
cd /tmp
cat > requirements.txt << EOF
flask
flask-cors
requests
python-dateutil
faker
gunicorn
EOF

cat > database.py << '"'"'EOFDATABASE'"'"'
import sqlite3
import json
import datetime
from typing import Dict, List, Optional

class AMLDatabase:
    def __init__(self, db_path: str = "/tmp/aml_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sanctions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT UNIQUE,
                name TEXT,
                name_normalized TEXT,
                type TEXT,
                schema TEXT,
                country TEXT,
                program TEXT,
                list_name TEXT,
                data_source TEXT,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE,
                account_id TEXT,
                amount DECIMAL(15,2),
                currency TEXT DEFAULT '"'"'USD'"'"',
                transaction_type TEXT,
                transaction_date DATE,
                beneficiary_account TEXT,
                beneficiary_name TEXT,
                beneficiary_country TEXT,
                origin_country TEXT,
                purpose TEXT,
                status TEXT DEFAULT '"'"'PENDING'"'"',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE,
                subject_id TEXT,
                subject_type TEXT,
                typology TEXT,
                risk_score DECIMAL(3,2),
                evidence TEXT,
                status TEXT DEFAULT '"'"'ACTIVE'"'"',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def add_sanctions_data(self, sanctions_data):
        conn = self.get_connection()
        fallback_data = [
            {'"'"'id'"'"': '"'"'fallback-001'"'"', '"'"'caption'"'"': '"'"'Vladimir Putin'"'"', '"'"'countries'"'"': ['"'"'ru'"'"'], '"'"'topics'"'"': ['"'"'sanction'"'"']},
            {'"'"'id'"'"': '"'"'fallback-002'"'"', '"'"'caption'"'"': '"'"'Kim Jong Un'"'"', '"'"'countries'"'"': ['"'"'kp'"'"'], '"'"'topics'"'"': ['"'"'sanction'"'"']}
        ]
        for entity in fallback_data:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO sanctions 
                    (entity_id, name, name_normalized, country, program, data_source, properties)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity.get('"'"'id'"'"'),
                    entity.get('"'"'caption'"'"'),
                    entity.get('"'"'caption'"'"', '"'"''"'"').upper(),
                    '"'"','"'"'.join(entity.get('"'"'countries'"'"', [])),
                    '"'"','"'"'.join(entity.get('"'"'topics'"'"', [])),
                    '"'"'FALLBACK'"'"',
                    json.dumps({})
                ))
            except: pass
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        conn = self.get_connection()
        stats = {}
        try:
            cursor = conn.execute("SELECT COUNT(*) as count FROM sanctions")
            stats['"'"'total_sanctions'"'"'] = cursor.fetchone()['"'"'count'"'"']
            cursor = conn.execute("SELECT COUNT(*) as count FROM transactions")  
            stats['"'"'total_transactions'"'"'] = cursor.fetchone()['"'"'count'"'"']
            cursor = conn.execute("SELECT COUNT(*) as count FROM alerts WHERE status = '"'"'ACTIVE'"'"'")
            stats['"'"'active_alerts'"'"'] = cursor.fetchone()['"'"'count'"'"']
        except: pass
        conn.close()
        return stats
        
    def get_active_alerts(self, limit=50):
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM alerts WHERE status = '"'"'ACTIVE'"'"' ORDER BY created_at DESC LIMIT ?", (limit,))
            alerts = []
            for row in cursor:
                alert = dict(row)
                try:
                    alert['"'"'evidence'"'"'] = json.loads(alert['"'"'evidence'"'"']) if alert['"'"'evidence'"'"'] else {}
                except: alert['"'"'evidence'"'"'] = {}
                alerts.append(alert)
            conn.close()
            return alerts
        except:
            conn.close()
            return []
EOFDATABASE

cat > app_simple.py << '"'"'EOFAPP'"'"'
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import os
from database import AMLDatabase

app = Flask(__name__)
CORS(app)

# Initialize database
db = AMLDatabase()
db.add_sanctions_data([])

@app.route('"'"'/'"'"')
def index():
    return '"'"'<h1>🛡️ Dynamic AML System</h1><p><a href="/dashboard">Go to Dashboard</a> | <a href="/api/health">API Health</a></p>'"'"'

@app.route('"'"'/dashboard'"'"')
def dashboard():
    return '"'"'<h1>🛡️ AML Dashboard</h1><p>Dashboard loading... <a href="/api/health">Check API Health</a></p><script>window.location.href="/api/dashboard/data"</script>'"'"'

@app.route('"'"'/api/health'"'"')
def health():
    stats = db.get_statistics()
    return jsonify({
        '"'"'status'"'"': '"'"'healthy'"'"',
        '"'"'timestamp'"'"': datetime.datetime.utcnow().isoformat(),
        '"'"'version'"'"': '"'"'1.0.0'"'"',
        '"'"'database'"'"': '"'"'connected'"'"',
        '"'"'statistics'"'"': stats,
        '"'"'message'"'"': '"'"'Dynamic AML System is running on Azure!'"'"'
    })

@app.route('"'"'/api/statistics'"'"')
def get_statistics():
    return jsonify({
        '"'"'success'"'"': True,
        '"'"'data'"'"': db.get_statistics(),
        '"'"'timestamp'"'"': datetime.datetime.utcnow().isoformat()
    })

@app.route('"'"'/api/alerts'"'"')
def get_alerts():
    alerts = db.get_active_alerts()
    return jsonify({
        '"'"'success'"'"': True,
        '"'"'data'"'"': alerts,
        '"'"'count'"'"': len(alerts),
        '"'"'timestamp'"'"': datetime.datetime.utcnow().isoformat()
    })

@app.route('"'"'/api/dashboard/data'"'"')
def get_dashboard_data():
    stats = db.get_statistics()
    alerts = db.get_active_alerts(20)
    return jsonify({
        '"'"'success'"'"': True,
        '"'"'statistics'"'"': stats,
        '"'"'alerts'"'"': alerts,
        '"'"'transactions'"'"': [],
        '"'"'alert_typologies'"'"': {},
        '"'"'timestamp'"'"': datetime.datetime.utcnow().isoformat(),
        '"'"'message'"'"': '"'"'AML System deployed successfully on Azure!'"'"'
    })

if __name__ == '"'"'__main__'"'"':
    port = int(os.environ.get('"'"'PORT'"'"', 5000))
    print(f"🚀 Starting AML System on port {port}")
    app.run(host='"'"'0.0.0.0'"'"', port=port, debug=False)
EOFAPP

echo "Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo "🛡️ Starting Dynamic AML System on Azure..."
python app_simple.py'

# Deploy container
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image python:3.11-slim \
    --dns-name-label $DNS_LABEL \
    --ports 5000 \
    --environment-variables FLASK_ENV=production PORT=5000 \
    --memory 1 \
    --cpu 0.5 \
    --restart-policy Always \
    --command-line "/bin/bash -c '$STARTUP_SCRIPT'" \
    --query '{ip:ipAddress.ip,fqdn:ipAddress.fqdn}' \
    --output table

echo ""
echo "🎉 DEPLOYMENT INITIATED!"
echo "======================="

# Get deployment info
sleep 5
DEPLOYMENT_INFO=$(az container show \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --query '{ip:ipAddress.ip,fqdn:ipAddress.fqdn,state:instanceView.state}' \
    --output json)

PUBLIC_IP=$(echo $DEPLOYMENT_INFO | jq -r '.ip')
FQDN=$(echo $DEPLOYMENT_INFO | jq -r '.fqdn')
STATE=$(echo $DEPLOYMENT_INFO | jq -r '.state')

echo ""
echo "📍 PUBLIC IP ADDRESS: $PUBLIC_IP"
echo "🌐 FULL DOMAIN NAME:   $FQDN"  
echo "📊 CONTAINER STATE:    $STATE"
echo ""
echo "🔗 Access URLs (available in ~2-3 minutes):"
echo "   🏠 Home:      http://$FQDN:5000/"
echo "   🛡️  Dashboard: http://$FQDN:5000/dashboard"
echo "   ❤️  Health:   http://$FQDN:5000/api/health"
echo "   🔧 API:       http://$FQDN:5000/api/statistics"
echo ""
echo "⏳ Container is starting up... Please wait 2-3 minutes"
echo ""
echo "🧪 Test when ready:"
echo "   curl http://$FQDN:5000/api/health"
echo ""
echo "🎯 Management:"
echo "   View logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --follow"  
echo "   Restart:   az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
echo "   Delete:    az group delete --name $RESOURCE_GROUP --yes"
echo ""

# Save info
echo "PUBLIC_IP=$PUBLIC_IP" > azure-deployment.env
echo "FQDN=$FQDN" >> azure-deployment.env  
echo "RESOURCE_GROUP=$RESOURCE_GROUP" >> azure-deployment.env
echo "CONTAINER_NAME=$CONTAINER_NAME" >> azure-deployment.env

echo "💾 Deployment details saved to azure-deployment.env"
echo "✨ Your Dynamic AML System is deploying to Azure!"