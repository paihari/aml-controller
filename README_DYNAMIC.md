# Dynamic AML Detection System

A real-time Anti-Money Laundering (AML) detection platform with live data processing, sanctions screening, and transaction monitoring.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Internet connection (for sanctions data)

### Installation & Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the complete system**:
   ```bash
   python run_dynamic_aml.py
   ```

This will:
- Initialize the SQLite database
- Load real sanctions data from OpenSanctions API
- Generate initial transaction data
- Start the Flask API server
- Open the dynamic dashboard

### Manual Setup (Alternative)

1. **Initialize database and load data**:
   ```bash
   python database.py           # Setup database
   python sanctions_loader.py   # Load sanctions data
   python transaction_generator.py  # Generate test transactions
   ```

2. **Start the API server**:
   ```bash
   python app.py
   ```

3. **Open the dashboard**:
   - Open `dashboard/dynamic.html` in your browser
   - Or visit the static version: `dashboard/index.html`

## 🌐 API Endpoints

### Core Endpoints
- `GET /api/health` - System health check
- `GET /api/statistics` - System statistics
- `GET /api/dashboard/data` - All dashboard data

### Data Management
- `GET /api/alerts` - Get active alerts
- `GET /api/transactions` - Get recent transactions
- `POST /api/transactions` - Process single transaction
- `POST /api/transactions/batch` - Process transaction batch

### Data Generation
- `POST /api/generate/transactions` - Generate sample transactions
- `POST /api/generate/process` - Generate and process transactions

### Sanctions Management
- `POST /api/sanctions/refresh` - Refresh sanctions data
- `GET /api/sanctions/search?name=<name>` - Search sanctions

## 🛡️ AML Detection Rules

The system implements 5 core AML detection typologies:

### R1: Sanctions Screening
- **Purpose**: Identify transactions involving sanctioned entities
- **Data Source**: OpenSanctions API + OFAC SDN List
- **Detection**: Fuzzy name matching with confidence scoring
- **Risk Score**: 0.95 (Critical)

### R2: Structuring Detection
- **Purpose**: Detect multiple transactions under reporting thresholds
- **Pattern**: 4+ transactions < $10,000 same day, same account
- **Risk Score**: 0.6-0.9 (based on count and amounts)

### R3: High-Risk Geography
- **Purpose**: Flag transactions to/from high-risk countries
- **Countries**: Iran, Russia, North Korea, Syria, etc.
- **Risk Score**: 0.5-0.95 (based on corridor risk)

### R4: Velocity Anomalies
- **Purpose**: Detect unusual transaction frequencies
- **Pattern**: High volume/frequency in short time periods
- **Risk Score**: 0.5-0.85 (based on volume and count)

### R5: Round-Trip Transactions
- **Purpose**: Identify money returning to origin
- **Pattern**: Account A → Account B → Account A (similar amounts)
- **Risk Score**: 0.70 (High)

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Flask API     │    │   Database      │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  AML Engine     │
                    │  - Rules Engine │
                    │  - Scoring      │
                    │  - Alerts       │
                    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │  Data Sources   │
                    │  - OpenSanctions│
                    │  - OFAC SDN     │
                    │  - Generated TX │
                    └─────────────────┘
```

## 📁 File Structure

```
aml-controller/
├── app.py                    # Flask API server
├── database.py               # Database setup and operations
├── dynamic_aml_engine.py     # AML detection engine
├── transaction_generator.py  # Transaction data generator
├── sanctions_loader.py       # Sanctions data loader
├── run_dynamic_aml.py       # System launcher
├── requirements.txt         # Python dependencies
├── dashboard/
│   ├── dynamic.html         # Real-time dashboard
│   └── index.html           # Static demo dashboard
└── README_DYNAMIC.md        # This file
```

## 🧪 Testing the System

### 1. Generate Test Data
```bash
curl -X POST http://localhost:5000/api/generate/process \
  -H "Content-Type: application/json" \
  -d '{"count": 20}'
```

### 2. Process Existing Transactions
```bash
curl -X POST http://localhost:5000/api/transactions/batch \
  -H "Content-Type: application/json" \
  -d '{"transactions": [...]}'
```

### 3. Search Sanctions
```bash
curl "http://localhost:5000/api/sanctions/search?name=Vladimir"
```

### 4. Check System Health
```bash
curl http://localhost:5000/api/health
```

## 📈 Sample API Response

### Dashboard Data
```json
{
  "success": true,
  "statistics": {
    "total_sanctions": 1247,
    "total_transactions": 156,
    "active_alerts": 23,
    "alerts_by_risk": {
      "Critical": 3,
      "High": 8,
      "Medium": 9,
      "Low": 3
    }
  },
  "alerts": [
    {
      "alert_id": "ALERT-A1B2C3D4",
      "subject_id": "TXN-12345",
      "typology": "R1_SANCTIONS_MATCH",
      "risk_score": 0.95,
      "evidence": {
        "party_name": "Vladimir Petrov",
        "watchlist_name": "Vladimir Vladimirovich PUTIN",
        "match_confidence": 0.87,
        "source": "OpenSanctions"
      },
      "created_at": "2025-08-19T15:30:45"
    }
  ]
}
```

## 🔧 Configuration

### Database
- **Default**: SQLite (`aml_database.db`)
- **Alternative**: PostgreSQL (modify `database.py`)

### API Server
- **Host**: `0.0.0.0` (all interfaces)
- **Port**: `5000`
- **Debug**: Enabled in development

### Sanctions Sources
1. **Primary**: OpenSanctions API
2. **Fallback**: OFAC SDN XML
3. **Emergency**: Hardcoded known entities

## 🚨 Production Considerations

### Security
- [ ] Add authentication/authorization
- [ ] Implement HTTPS/TLS
- [ ] Add rate limiting
- [ ] Sanitize inputs

### Performance
- [ ] Database indexing optimization
- [ ] Caching layer (Redis)
- [ ] Async processing (Celery)
- [ ] Load balancing

### Compliance
- [ ] Audit trail implementation
- [ ] Data retention policies
- [ ] Regulatory reporting
- [ ] Privacy controls

## 📞 Support

For issues, feature requests, or questions:
1. Check the API health endpoint: `/api/health`
2. Review application logs
3. Test individual components:
   - `python database.py` (database)
   - `python sanctions_loader.py` (sanctions)
   - `python transaction_generator.py` (transactions)
   - `python dynamic_aml_engine.py` (AML engine)

## 🎯 Next Steps

- [ ] Add more detection rules (trade-based ML, shell companies)
- [ ] Implement case management workflow
- [ ] Add ML-based risk scoring
- [ ] Create regulatory reporting templates
- [ ] Build investigation tools
- [ ] Add real-time streaming capabilities