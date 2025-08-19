# AML Alert Dashboard

🛡️ **Real-time Anti-Money Laundering Detection Platform**

## 🌐 Live Demo
**Enhanced Dashboard**: https://willowy-chebakia-75fee1.netlify.app/

## 🎯 Features

- **Real-time AML Detection** - 5 comprehensive detection rules
- **Interactive Dashboard** - Modern web-based visualization
- **Multiple Typologies** - Sanctions, structuring, geography, velocity, round-trip
- **Comprehensive Coverage** - 20 transactions, 15 parties, 25 watchlist entries
- **Professional Analytics** - Interactive charts and risk scoring

## 📊 Detection Results

The platform currently detects:
- **4 OFAC Sanctions Matches** (95% risk) - Vladimir Petrov, Dmitri Kozlov, Hassan Bin Rashid, Anna Volkov
- **5 High-Risk Geography Transactions** (60-85% risk) - US→Iran, DE→Russia, offshore
- **1 Structuring Pattern** (80% risk) - 4 transactions under $10K threshold

## 🚀 Quick Start

### Run AML Detection
```bash
python3 test_data_flow_extended.py
```

### Start Dashboard Locally
```bash
cd dashboard
python3 start_dashboard.sh
```

### Deploy Online
```bash
./deploy_online.sh
```

## 📁 Project Structure

```
├── dashboard/              # Web dashboard and visualization
├── sample_data/           # AML test data (transactions, parties, watchlists)  
├── test_data_flow_extended.py  # Main AML detection engine
├── test_results_alerts_extended.json  # Generated alerts
└── online_deploy/         # Deployment package for hosting
```

## 🔍 AML Detection Engine

The core detection engine (`test_data_flow_extended.py`) implements:

### Detection Rules
1. **R1_SANCTIONS_MATCH** - OFAC watchlist screening
2. **R2_STRUCTURING** - Multiple small transactions pattern
3. **R3_HIGH_RISK_CORRIDOR** - Geographic risk assessment  
4. **R4_VELOCITY_ANOMALY** - Transaction velocity analysis
5. **R5_ROUND_TRIP** - Circular transaction detection

### Data Processing
- **Silver Layer** - Data normalization and cleansing
- **Gold Layer** - Alert generation and risk scoring
- **Evidence Tracking** - Comprehensive audit trail

## 📈 Sample Data

- **Transactions**: 20 diverse transaction patterns
- **Parties**: 15 entities from various jurisdictions
- **Watchlists**: 25 entries from OFAC, DEA, Treasury sources
- **Risk Scenarios**: Sanctions evasion, structuring, money laundering

## 🌐 Deployment Options

1. **Netlify Drop** - Drag `online_deploy` folder to https://app.netlify.com/drop
2. **GitHub Pages** - Push to GitHub, enable Pages from `/docs` folder
3. **Vercel** - Import repository at https://vercel.com/new
4. **Local Server** - Run `dashboard/start_dashboard.sh`

## 📊 Dashboard Features

- **Real-time Alerts** - Live alert monitoring
- **Risk Distribution** - Interactive doughnut charts
- **Typology Analysis** - Detection method breakdown  
- **Evidence Details** - Complete alert context
- **Mobile Responsive** - Works on all devices

## 🛠️ Technology Stack

- **Backend**: Python 3.x with CSV/JSON processing
- **Frontend**: HTML5, CSS3, JavaScript with Chart.js
- **Hosting**: Static deployment (Netlify, GitHub Pages, Vercel)
- **Data**: File-based processing with in-memory analytics

## 📄 License

This project is licensed under the MIT License.