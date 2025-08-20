# 🚀 Quick Start Guide

Get your Dynamic AML Detection Platform running in just 5 minutes!

## 🎯 Prerequisites

- **Python 3.11+** installed
- **Git** for cloning the repository
- **Web browser** for accessing the dashboard

## ⚡ 5-Minute Setup

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone https://github.com/paihari/aml-controller.git
cd aml-controller

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start the System
```bash
# Launch the AML platform
python app.py
```

The system will automatically:
- ✅ Initialize SQLite database
- ✅ Load live sanctions data from OpenSanctions API
- ✅ Generate sample transactions
- ✅ Create AML alerts
- ✅ Start the web server

### Step 3: Access the Dashboard
Open your browser and navigate to:
- **Dashboard**: http://localhost:5000/dashboard/dynamic.html
- **API Health**: http://localhost:5000/api/health
- **Statistics**: http://localhost:5000/api/statistics

## 🎲 Generate More Data

If you want more test data, visit:
```
http://localhost:5000/api/initialize
```

This will generate additional transactions and alerts for testing.

## 🌐 Try the Live Demo

Don't want to install locally? Try our live demo:
**[https://aml-controller.onrender.com/](https://aml-controller.onrender.com/)**

## 📊 What You'll See

### Dashboard Features
- **Real-time Alerts** - Live AML detection results
- **Risk Analytics** - Transaction risk distribution
- **Interactive Charts** - Visual data representation
- **Transaction History** - Complete audit trail

### Sample Alerts
The system will generate alerts for:
- 🚫 **Sanctions Matches** - OFAC watchlist hits
- 🌍 **Geography Risk** - High-risk country transactions
- 💰 **Structuring** - Multiple small transactions
- ⚡ **Velocity Anomalies** - Unusual transaction frequency
- 🔄 **Round-Trip** - Circular money flows

## 🔧 Next Steps

- **[System Architecture](System-Architecture)** - Understand the system design
- **[API Reference](API-Reference)** - Explore the REST API
- **[Detection Rules](Detection-Rules)** - Learn about AML algorithms
- **[Development Setup](Development-Setup)** - Set up for development

## ❓ Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Check what's using port 5000
lsof -i :5000

# Kill the process or use a different port
PORT=8000 python app.py
```

**Missing dependencies:**
```bash
# Upgrade pip and retry
pip install --upgrade pip
pip install -r requirements.txt
```

**Database issues:**
```bash
# Remove existing database to reset
rm aml_database.db
python app.py
```

## 💡 Pro Tips

1. **Monitor Logs** - Watch the console output for system status
2. **Check Health** - Visit `/api/health` to verify system status
3. **Generate Data** - Use `/api/initialize` for more test scenarios
4. **API Explorer** - Try different API endpoints to understand the system

---

Ready to dive deeper? Check out the **[System Architecture](System-Architecture)** to understand how everything works!