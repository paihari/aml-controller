# 📡 API Reference

Complete REST API documentation for the Dynamic AML Detection Platform.

## 🌐 Base URL

- **Production**: `https://aml-controller.onrender.com/api`
- **Local Development**: `http://localhost:5000/api`

## 🔐 Authentication

Currently, the API uses no authentication for demo purposes. In production, implement:
- API key authentication
- OAuth 2.0 / JWT tokens
- Rate limiting per user/key

---

## 📋 API Endpoints Overview

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **System** | `/health` | GET | Health check |
| **System** | `/statistics` | GET | System metrics |
| **System** | `/initialize` | GET | Initialize with sample data |
| **Transactions** | `/transactions` | GET | List transactions |
| **Transactions** | `/transactions` | POST | Process single transaction |
| **Transactions** | `/transactions/batch` | POST | Process batch |
| **Alerts** | `/alerts` | GET | List active alerts |
| **Alerts** | `/alerts/{id}/update` | PUT | Update alert status |
| **Sanctions** | `/sanctions/search` | GET | Search sanctions |
| **Sanctions** | `/sanctions/refresh` | POST | Refresh sanctions data |
| **Data Generation** | `/generate/transactions` | POST | Generate test transactions |
| **Data Generation** | `/generate/process` | GET/POST | Generate and process |
| **Dashboard** | `/dashboard/data` | GET | Complete dashboard data |

---

## 🏥 System Endpoints

### GET `/api/health`

Health check endpoint for monitoring system status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-20T05:12:20.966176",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200` - System is healthy
- `503` - System is unavailable

---

### GET `/api/statistics`

Get comprehensive system statistics and metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_transactions": 25,
    "active_alerts": 8,
    "total_sanctions": 1247,
    "total_parties": 15,
    "high_risk_alerts": 5,
    "medium_risk_alerts": 3,
    "processing_time_avg": 0.075
  },
  "timestamp": "2025-08-20T05:12:31.073954"
}
```

**Status Codes:**
- `200` - Success
- `503` - Database not initialized
- `500` - Internal server error

---

### GET `/api/initialize`

Initialize the system with sample data for demonstration purposes.

**Response:**
```json
{
  "success": true,
  "message": "System initialized with sample data",
  "transactions_generated": 15,
  "transactions_stored": 15,
  "alerts_generated": 8,
  "timestamp": "2025-08-20T05:15:42.123456"
}
```

**Status Codes:**
- `200` - Success
- `503` - System components not initialized
- `500` - Initialization failed

---

## 💳 Transaction Endpoints

### GET `/api/transactions`

Retrieve recent transactions with optional pagination.

**Query Parameters:**
- `limit` (integer, optional): Number of transactions to return (default: 100, max: 1000)

**Example Request:**
```bash
curl "https://aml-controller.onrender.com/api/transactions?limit=10"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "transaction_id": "TXN_001_20250820",
      "amount": 75000.0,
      "currency": "USD",
      "sender_name": "John Smith",
      "receiver_name": "Vladimir Petrov",
      "sender_country": "US",
      "receiver_country": "RU",
      "transaction_date": "2025-08-20",
      "created_at": "2025-08-20T05:12:30.123456"
    }
  ],
  "count": 1,
  "timestamp": "2025-08-20T05:12:31.073954"
}
```

---

### POST `/api/transactions`

Process a single transaction through the AML detection engine.

**Request Body:**
```json
{
  "transaction_id": "TXN_USER_001",
  "amount": 50000,
  "currency": "USD",
  "sender_name": "Alice Johnson",
  "receiver_name": "Bob Wilson",
  "sender_country": "US",
  "receiver_country": "UK",
  "transaction_date": "2025-08-20"
}
```

**Response:**
```json
{
  "success": true,
  "transaction_id": "TXN_USER_001",
  "alerts_generated": 2,
  "alerts": [
    {
      "alert_id": "ALT_001_20250820",
      "typology": "HIGH_RISK_GEOGRAPHY",
      "risk_score": 0.65,
      "alert_reason": "Transaction from high-risk geography corridor",
      "evidence": {
        "sender_country": "US",
        "receiver_country": "UK",
        "risk_corridor": "US→UK",
        "corridor_risk": 0.65
      }
    }
  ],
  "timestamp": "2025-08-20T05:15:42.123456"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid transaction data
- `503` - AML engine not available
- `500` - Processing error

---

### POST `/api/transactions/batch`

Process multiple transactions in a single batch operation.

**Request Body:**
```json
{
  "transactions": [
    {
      "transaction_id": "BATCH_001",
      "amount": 25000,
      "currency": "USD",
      "sender_name": "Corp A",
      "receiver_name": "Corp B",
      "sender_country": "US",
      "receiver_country": "DE"
    },
    {
      "transaction_id": "BATCH_002",
      "amount": 8500,
      "currency": "EUR",
      "sender_name": "Corp B",
      "receiver_name": "Corp C",
      "sender_country": "DE",
      "receiver_country": "FR"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "processed_count": 2,
  "alert_count": 1,
  "alerts": [
    {
      "alert_id": "ALT_BATCH_001",
      "transaction_id": "BATCH_001",
      "typology": "STRUCTURING",
      "risk_score": 0.8,
      "alert_reason": "Multiple transactions under reporting threshold"
    }
  ],
  "processing_time": "2025-08-20T05:15:42.123456",
  "timestamp": "2025-08-20T05:15:42.987654"
}
```

---

## 🚨 Alert Endpoints

### GET `/api/alerts`

Retrieve active alerts with optional filtering and pagination.

**Query Parameters:**
- `limit` (integer, optional): Number of alerts to return (default: 50, max: 500)
- `status` (string, optional): Filter by status (`OPEN`, `INVESTIGATING`, `CLOSED`)
- `typology` (string, optional): Filter by alert type

**Example Request:**
```bash
curl "https://aml-controller.onrender.com/api/alerts?limit=20&status=OPEN"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "alert_id": "ALT_001_20250820",
      "transaction_id": "TXN_001_20250820",
      "typology": "SANCTIONS_MATCH",
      "risk_score": 0.95,
      "alert_reason": "Sender name matches OFAC sanctions list",
      "evidence": {
        "matched_name": "Vladimir Petrov",
        "sanctions_entry": "Vladimir Petrov (Russia - OFAC SDN)",
        "match_confidence": 0.98,
        "sanctions_program": "UKRAINE-EO13662"
      },
      "status": "OPEN",
      "created_at": "2025-08-20T05:12:30.123456"
    }
  ],
  "count": 1,
  "timestamp": "2025-08-20T05:12:31.073954"
}
```

---

### PUT `/api/alerts/{alert_id}/update`

Update the status or assignment of a specific alert.

**Path Parameters:**
- `alert_id` (string): The unique alert identifier

**Request Body:**
```json
{
  "status": "INVESTIGATING",
  "assigned_to": "analyst@bank.com",
  "notes": "Under investigation - additional documentation requested"
}
```

**Response:**
```json
{
  "success": true,
  "alert_id": "ALT_001_20250820",
  "updated_fields": ["status", "assigned_to", "notes"],
  "timestamp": "2025-08-20T05:15:42.123456"
}
```

---

## 🚫 Sanctions Endpoints

### GET `/api/sanctions/search`

Search sanctions lists by name with fuzzy matching.

**Query Parameters:**
- `name` (string, required): Name to search for
- `limit` (integer, optional): Number of results (default: 10, max: 100)

**Example Request:**
```bash
curl "https://aml-controller.onrender.com/api/sanctions/search?name=Vladimir&limit=5"
```

**Response:**
```json
{
  "success": true,
  "query": "Vladimir",
  "results": [
    {
      "id": 1,
      "name": "Vladimir Petrov",
      "name_normalized": "vladimir petrov",
      "country": "Russia",
      "sanctions_type": "SDN",
      "program": "UKRAINE-EO13662",
      "source": "OFAC",
      "date_added": "2022-03-15"
    }
  ],
  "count": 1,
  "timestamp": "2025-08-20T05:12:31.073954"
}
```

**Status Codes:**
- `200` - Success
- `400` - Missing name parameter
- `500` - Search error

---

### POST `/api/sanctions/refresh`

Refresh sanctions data from external sources (OpenSanctions API, OFAC).

**Response:**
```json
{
  "success": true,
  "results": {
    "opensanctions_loaded": 1247,
    "ofac_loaded": 532,
    "total_sanctions": 1779,
    "update_time": "2025-08-20T05:15:42.123456"
  },
  "timestamp": "2025-08-20T05:15:42.987654"
}
```

**Status Codes:**
- `200` - Success
- `503` - External APIs unavailable
- `500` - Refresh failed

---

## 🎲 Data Generation Endpoints

### POST `/api/generate/transactions`

Generate sample transactions for testing purposes.

**Request Body:**
```json
{
  "count": 20
}
```

**Response:**
```json
{
  "success": true,
  "generated_count": 20,
  "stored_count": 20,
  "transactions": [
    {
      "transaction_id": "GEN_001_20250820",
      "amount": 45000,
      "currency": "USD",
      "sender_name": "Test Corp A",
      "receiver_name": "Test Corp B",
      "sender_country": "US",
      "receiver_country": "CA"
    }
  ],
  "timestamp": "2025-08-20T05:15:42.123456"
}
```

---

### GET/POST `/api/generate/process`

Generate transactions and immediately process them through the AML engine.

**GET Query Parameters:**
- `count` (integer, optional): Number of transactions to generate (default: 20)

**POST Request Body:**
```json
{
  "count": 15
}
```

**Response:**
```json
{
  "success": true,
  "generated_count": 15,
  "processed_count": 15,
  "alert_count": 6,
  "alerts": [
    {
      "alert_id": "ALT_GEN_001",
      "typology": "SANCTIONS_MATCH",
      "risk_score": 0.95
    }
  ],
  "processing_time": "2025-08-20T05:15:42.123456",
  "timestamp": "2025-08-20T05:15:42.987654"
}
```

---

## 📊 Dashboard Endpoints

### GET `/api/dashboard/data`

Get all data needed for the dashboard in a single request.

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_transactions": 25,
    "active_alerts": 8,
    "total_sanctions": 1247
  },
  "alerts": [
    {
      "alert_id": "ALT_001",
      "typology": "SANCTIONS_MATCH",
      "risk_score": 0.95
    }
  ],
  "transactions": [
    {
      "transaction_id": "TXN_001",
      "amount": 75000,
      "sender_name": "John Smith"
    }
  ],
  "alert_typologies": {
    "SANCTIONS_MATCH": 4,
    "HIGH_RISK_GEOGRAPHY": 3,
    "STRUCTURING": 1
  },
  "timestamp": "2025-08-20T05:12:31.073954"
}
```

---

## 🔧 Error Handling

### Standard Error Response

```json
{
  "success": false,
  "error": "Detailed error message",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-08-20T05:15:42.123456"
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| `400` | `VALIDATION_ERROR` | Invalid request data |
| `404` | `NOT_FOUND` | Resource not found |
| `503` | `SERVICE_UNAVAILABLE` | System components not initialized |
| `500` | `INTERNAL_ERROR` | Unexpected server error |
| `429` | `RATE_LIMIT_EXCEEDED` | Too many requests |

---

## 📚 SDK Examples

### Python Example

```python
import requests
import json

# Base configuration
base_url = "https://aml-controller.onrender.com/api"
headers = {"Content-Type": "application/json"}

# Health check
response = requests.get(f"{base_url}/health")
print(f"System status: {response.json()['status']}")

# Process a transaction
transaction = {
    "transaction_id": "PYTHON_001",
    "amount": 50000,
    "currency": "USD",
    "sender_name": "Alice Smith",
    "receiver_name": "Bob Jones",
    "sender_country": "US",
    "receiver_country": "UK"
}

response = requests.post(
    f"{base_url}/transactions",
    headers=headers,
    data=json.dumps(transaction)
)

result = response.json()
print(f"Generated {result['alerts_generated']} alerts")
```

### JavaScript Example

```javascript
// Base configuration
const baseUrl = 'https://aml-controller.onrender.com/api';

// Health check
async function checkHealth() {
    const response = await fetch(`${baseUrl}/health`);
    const data = await response.json();
    console.log(`System status: ${data.status}`);
}

// Process transaction
async function processTransaction() {
    const transaction = {
        transaction_id: 'JS_001',
        amount: 75000,
        currency: 'USD',
        sender_name: 'Charlie Brown',
        receiver_name: 'Diana Prince',
        sender_country: 'US',
        receiver_country: 'CA'
    };
    
    const response = await fetch(`${baseUrl}/transactions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(transaction)
    });
    
    const result = await response.json();
    console.log(`Generated ${result.alerts_generated} alerts`);
}
```

### cURL Examples

```bash
# Health check
curl https://aml-controller.onrender.com/api/health

# Get statistics
curl https://aml-controller.onrender.com/api/statistics

# Process transaction
curl -X POST https://aml-controller.onrender.com/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "CURL_001",
    "amount": 60000,
    "currency": "USD",
    "sender_name": "Test User",
    "receiver_name": "Test Recipient",
    "sender_country": "US",
    "receiver_country": "DE"
  }'

# Search sanctions
curl "https://aml-controller.onrender.com/api/sanctions/search?name=Vladimir&limit=5"
```

---

## 🚀 Rate Limits

| Endpoint Category | Rate Limit | Window |
|------------------|------------|---------|
| **Health/Statistics** | 100 requests | 1 minute |
| **Transaction Processing** | 50 requests | 1 minute |
| **Data Generation** | 10 requests | 1 minute |
| **Sanctions Search** | 30 requests | 1 minute |

---

## 📝 Response Headers

All API responses include these headers:

```http
Content-Type: application/json
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
X-Response-Time: 0.045s
```

---

Next: **[Detection Rules](Detection-Rules)** - Detailed explanation of all AML detection algorithms