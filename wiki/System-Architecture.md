# 🏗️ System Architecture

Comprehensive architectural overview of the Dynamic AML Detection Platform using the C4 model.

## 🎯 Architecture Principles

- **Modular Design** - Loosely coupled components for maintainability
- **Real-time Processing** - Sub-second transaction analysis
- **Scalable Architecture** - Horizontal scaling capabilities
- **API-First** - RESTful design for external integrations
- **Security by Design** - Built-in security and compliance features

---

## 🌐 Level 1: System Context

```mermaid
graph TB
    subgraph "External Systems"
        User[👤 Compliance Officer]
        OpenSanctions[🌐 OpenSanctions API]
        OFAC[🏛️ OFAC SDN List]
    end
    
    subgraph "AML Platform Boundary"
        AMLSystem[🛡️ Dynamic AML Platform]
    end
    
    User -->|"Monitor alerts<br/>Review transactions<br/>Generate reports"| AMLSystem
    AMLSystem -->|"Fetch sanctions data<br/>Real-time updates"| OpenSanctions
    AMLSystem -->|"Download OFAC lists<br/>Compliance data"| OFAC
    AMLSystem -->|"Display alerts<br/>Risk analytics<br/>Audit reports"| User
    
    style AMLSystem fill:#e1f5fe
    style User fill:#f3e5f5
    style OpenSanctions fill:#e8f5e8
    style OFAC fill:#fff3e0
```

### Key External Interactions

| Entity | Interaction Type | Data Format | Frequency |
|--------|------------------|-------------|-----------|
| **Compliance Officer** | Web UI, API calls | HTML, JSON | Real-time |
| **OpenSanctions API** | HTTP REST | JSON | On-demand |
| **OFAC SDN List** | File download | CSV/JSON | Daily updates |

---

## 🏢 Level 2: Container Diagram

```mermaid
graph TB
    subgraph "Dynamic AML Platform"
        WebDashboard[🌐 Web Dashboard<br/>HTML/CSS/JavaScript<br/>Port: Static]
        FlaskAPI[⚡ Flask API Server<br/>Python Flask<br/>Port: 5000]
        Database[(🗄️ SQLite Database<br/>aml_database.db)]
        
        subgraph "Core Processing"
            AMLEngine[🔍 AML Detection Engine<br/>Python<br/>Rule-based processing]
            TransactionGen[🎲 Transaction Generator<br/>Python Faker<br/>Synthetic data]
            SanctionsLoader[📥 Sanctions Loader<br/>Python Requests<br/>API integration]
        end
    end
    
    subgraph "External"
        User[👤 Compliance Officer]
        ExtAPIs[🌐 External APIs<br/>OpenSanctions, OFAC]
    end
    
    User -->|HTTPS/HTTP| WebDashboard
    WebDashboard -->|REST API calls<br/>JSON| FlaskAPI
    FlaskAPI -->|SQL queries| Database
    FlaskAPI -->|Process transactions| AMLEngine
    FlaskAPI -->|Generate test data| TransactionGen
    FlaskAPI -->|Load sanctions| SanctionsLoader
    
    AMLEngine -->|Store alerts| Database
    TransactionGen -->|Store transactions| Database
    SanctionsLoader -->|Store sanctions| Database
    SanctionsLoader -->|HTTP requests<br/>JSON/CSV| ExtAPIs
    
    style WebDashboard fill:#e3f2fd
    style FlaskAPI fill:#f3e5f5
    style Database fill:#e8f5e8
    style AMLEngine fill:#fff3e0
    style TransactionGen fill:#fce4ec
    style SanctionsLoader fill:#e0f2f1
```

### Container Responsibilities

| Container | Technology | Purpose | Ports |
|-----------|------------|---------|-------|
| **Web Dashboard** | HTML5, JavaScript, Chart.js | User interface and visualizations | Static files |
| **Flask API** | Python Flask, CORS | REST API and request routing | 5000 |
| **SQLite Database** | SQLite3 | Data persistence and queries | File-based |
| **AML Engine** | Python | Transaction analysis and alerting | N/A |
| **Transaction Generator** | Python Faker | Test data generation | N/A |
| **Sanctions Loader** | Python Requests | External data integration | N/A |

---

## ⚙️ Level 3: Component Diagram - AML Engine

```mermaid
graph TB
    subgraph "AML Detection Engine"
        Processor[📊 Transaction Processor<br/>Input validation<br/>Data normalization]
        
        subgraph "Detection Rules"
            Rules[📋 Rules Engine<br/>Orchestrates all rules]
            Sanctions[🚫 Sanctions Screening<br/>OFAC/UN/EU lists<br/>Fuzzy matching]
            Geography[🌍 Geography Risk<br/>High-risk corridors<br/>Country analysis]
            Structuring[💰 Structuring Detection<br/>Multiple small amounts<br/>Pattern analysis]
            Velocity[⚡ Velocity Analysis<br/>Transaction frequency<br/>Time-based patterns]
            RoundTrip[🔄 Round-Trip Detection<br/>Circular flows<br/>Party matching]
        end
        
        AlertGenerator[🚨 Alert Generator<br/>Risk scoring<br/>Evidence compilation]
        AlertStorage[📁 Alert Storage<br/>Database persistence<br/>Status tracking]
    end
    
    subgraph "External"
        API[⚡ Flask API]
        DB[(🗄️ Database)]
    end
    
    API -->|Transaction data| Processor
    Processor -->|Validated data| Rules
    
    Rules -->|Check sanctions| Sanctions
    Rules -->|Analyze geography| Geography
    Rules -->|Detect structuring| Structuring
    Rules -->|Check velocity| Velocity
    Rules -->|Find round-trips| RoundTrip
    
    Sanctions -->|Alert data| AlertGenerator
    Geography -->|Alert data| AlertGenerator
    Structuring -->|Alert data| AlertGenerator
    Velocity -->|Alert data| AlertGenerator
    RoundTrip -->|Alert data| AlertGenerator
    
    AlertGenerator -->|Generated alerts| AlertStorage
    AlertStorage -->|Store alerts| DB
    
    style Processor fill:#e3f2fd
    style Rules fill:#fff3e0
    style Sanctions fill:#ffebee
    style Geography fill:#e8f5e8
    style Structuring fill:#e3f2fd
    style Velocity fill:#fce4ec
    style RoundTrip fill:#f3e5f5
    style AlertGenerator fill:#fff8e1
    style AlertStorage fill:#f1f8e9
```

### Detection Rule Details

| Rule | Algorithm | Threshold | Output |
|------|-----------|-----------|--------|
| **R1: Sanctions** | Fuzzy string matching | 90% similarity | Risk: 95% |
| **R2: Geography** | Country risk mapping | High-risk corridors | Risk: 60-85% |
| **R3: Structuring** | Pattern detection | 4+ transactions <$10K | Risk: 80% |
| **R4: Velocity** | Time-based analysis | 10+ transactions/24h | Risk: 70% |
| **R5: Round-Trip** | Graph analysis | Circular flows | Risk: 75% |

---

## 📁 Level 4: Code Structure

```
dynamic-aml-system/
├── 🌐 Presentation Layer
│   ├── app.py                      # Flask application entry point
│   └── dashboard/
│       └── dynamic.html            # Real-time web dashboard
│
├── 🔍 Business Logic Layer
│   ├── dynamic_aml_engine.py       # Core AML detection engine
│   │   ├── DynamicAMLEngine()      # Main engine class
│   │   ├── process_transaction()   # Single transaction processing
│   │   ├── process_batch()         # Batch processing
│   │   ├── _check_sanctions_screening()
│   │   ├── _check_high_risk_geography()
│   │   ├── _check_structuring_patterns()
│   │   ├── _check_velocity_anomalies()
│   │   └── _check_round_trip_transactions()
│   │
│   ├── transaction_generator.py    # Test data generation
│   │   ├── TransactionGenerator()  # Generator class
│   │   ├── generate_mixed_batch()  # Create diverse transactions
│   │   ├── generate_sanctions_risk_transaction()
│   │   ├── generate_structuring_pattern()
│   │   └── generate_geography_risk_transaction()
│   │
│   └── sanctions_loader.py         # External data integration
│       ├── SanctionsLoader()       # Loader class
│       ├── load_opensanctions_data()
│       ├── load_ofac_data()        # OFAC integration
│       └── _load_fallback_sanctions()
│
├── 🗄️ Data Access Layer
│   ├── database.py                 # Database operations
│   │   ├── AMLDatabase()           # Database class
│   │   ├── add_transaction()       # Transaction CRUD
│   │   ├── add_alert()            # Alert management
│   │   ├── get_active_alerts()    # Alert queries
│   │   └── get_statistics()       # System metrics
│   │
│   └── aml_database.db            # SQLite database file
│
├── 🚀 Infrastructure Layer
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Container configuration
│   ├── render.yaml                 # Render deployment
│   ├── fly.toml                    # Fly.io deployment
│   └── start.sh                    # Local startup script
│
└── 📚 Documentation
    ├── README.md                   # Project overview
    └── wiki/                       # Comprehensive documentation
        ├── Home.md
        ├── Quick-Start-Guide.md
        └── System-Architecture.md
```

---

## 🔄 Data Flow Architecture

### Request Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant Dashboard
    participant API
    participant Engine
    participant DB
    participant ExtAPI
    
    User->>Dashboard: Access dashboard
    Dashboard->>API: GET /api/dashboard/data
    API->>DB: Query statistics, alerts, transactions
    DB-->>API: Return data
    API-->>Dashboard: JSON response
    Dashboard-->>User: Render dashboard
    
    User->>API: POST /api/transactions (new transaction)
    API->>Engine: process_transaction()
    Engine->>Engine: Run 5 detection rules
    Engine->>DB: Store alerts
    DB-->>Engine: Confirm storage
    Engine-->>API: Return alert results
    API-->>User: JSON response with alerts
    
    Note over API,ExtAPI: Background process
    API->>ExtAPI: Fetch sanctions data
    ExtAPI-->>API: Return sanctions list
    API->>DB: Update sanctions table
```

### Data Persistence Layer

```mermaid
erDiagram
    SANCTIONS {
        int id PK
        string name
        string name_normalized
        string country
        string sanctions_type
        string program
        string source
        datetime date_added
    }
    
    TRANSACTIONS {
        int id PK
        string transaction_id UK
        float amount
        string currency
        string sender_name
        string receiver_name
        string sender_country
        string receiver_country
        datetime transaction_date
        datetime created_at
    }
    
    ALERTS {
        int id PK
        string alert_id UK
        string transaction_id FK
        string typology
        float risk_score
        string alert_reason
        string evidence
        string status
        datetime created_at
    }
    
    PARTIES {
        int id PK
        string party_name
        string party_type
        string country
        string risk_rating
        datetime created_at
    }
    
    ALERT_HISTORY {
        int id PK
        string alert_id FK
        string status_change
        string changed_by
        string notes
        datetime created_at
    }
    
    TRANSACTIONS ||--o{ ALERTS : generates
    ALERTS ||--o{ ALERT_HISTORY : tracks
```

---

## 🔧 Configuration Architecture

### Environment Variables
```bash
# Application settings
FLASK_ENV=production
PORT=5000
DEBUG=false

# Database configuration
DATABASE_PATH=/app/data/aml_database.db
DATABASE_POOL_SIZE=10

# External API settings
OPENSANCTIONS_API_BASE=https://api.opensanctions.org
OFAC_API_ENDPOINT=https://www.treasury.gov/ofac/downloads/sdn.csv
API_TIMEOUT=30

# Security settings
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT=100/hour
```

### Runtime Configuration
```python
# app.py configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-key'),
    DEBUG=os.environ.get('DEBUG', 'false').lower() == 'true',
    DATABASE_PATH=os.environ.get('DATABASE_PATH', 'aml_database.db'),
    API_TIMEOUT=int(os.environ.get('API_TIMEOUT', '30'))
)
```

---

## 📊 Performance Architecture

### Scaling Strategies

| Component | Scaling Method | Bottleneck | Solution |
|-----------|----------------|------------|----------|
| **Flask API** | Horizontal | Request volume | Load balancer + multiple instances |
| **Database** | Vertical | Query performance | PostgreSQL + connection pooling |
| **AML Engine** | Horizontal | Rule processing | Microservice + queue system |
| **Static Assets** | CDN | Global access | CloudFront/CloudFlare |

### Performance Targets

| Metric | Target | Current | Measurement |
|--------|--------|---------|-------------|
| **API Response** | <200ms | ~150ms | Average response time |
| **Transaction Processing** | <100ms | ~75ms | Per transaction through all rules |
| **Database Query** | <10ms | ~5ms | SQLite query performance |
| **Dashboard Load** | <2s | ~1.2s | Complete page with data |
| **Memory Usage** | <256MB | ~128MB | Runtime footprint |

---

## 🔐 Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "Security Layers"
        Network[🌐 Network Security<br/>HTTPS, CORS, Rate Limiting]
        Application[🔒 Application Security<br/>Input validation, SQL injection prevention]
        Data[🗄️ Data Security<br/>Encryption at rest, Audit logging]
        Identity[👤 Identity & Access<br/>API keys, Role-based access]
    end
    
    Internet[🌍 Internet] --> Network
    Network --> Application
    Application --> Data
    Application --> Identity
```

### Security Controls

| Layer | Control | Implementation |
|-------|---------|----------------|
| **Network** | HTTPS enforcement | Flask-Talisman |
| **Application** | Input validation | JSON schema validation |
| **Data** | SQL injection prevention | Parameterized queries |
| **Access** | Rate limiting | Flask-Limiter |
| **Monitoring** | Audit logging | Structured logging |

---

Next: **[Database Schema](Database-Schema)** - Detailed database design and relationships