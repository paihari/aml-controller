# OpenSanctions Consolidated Sanctions - AML System Design

## Overview

This document outlines the design for integrating OpenSanctions Consolidated Sanctions dataset as the primary source for AML (Anti-Money Laundering) screening in our system.

## Data Source Details

### Primary Dataset
- **Name**: OpenSanctions Consolidated Sanctions
- **URL Pattern**: `https://data.opensanctions.org/datasets/{DATE}/sanctions/senzing.json`
- **Current URL**: `https://data.opensanctions.org/datasets/20250822/sanctions/senzing.json`
- **Last Processed**: 2025-08-22 13:47:01
- **Update Frequency**: Daily
- **Format**: Senzing JSON format

### Data Scale
- **Total Entities**: 264,518
- **Searchable Entities**: 91,381
- **Core Targets**: 64,662
- **Data Sources**: 84 global sanctions authorities

### Entity Distribution
| Entity Type | Count | Description |
|-------------|-------|-------------|
| People | 36,828 | Natural persons under sanctions |
| Addresses | 20,227 | Locations associated with sanctioned entities |
| Organizations | 16,330 | Non-profit and government organizations |
| Legal Entities | 8,457 | General legal entities |
| Securities | 2,833 | Financial instruments and bonds |
| Cryptocurrency Wallets | 2,022 | Digital asset addresses |
| Companies | - | For-profit corporations |
| Vessels | - | Ships and maritime assets |
| Airplanes | - | Aircraft assets |
| Public Bodies | - | Government institutions |

## Data Sources (84 Authorities)

The consolidated dataset combines sanctions from 84 global authorities including:

### Primary Sources
- **UN Security Council** - Global sanctions framework
- **US OFAC** - Office of Foreign Assets Control
- **EU Sanctions** - European Union consolidated list
- **UK Sanctions** - HM Treasury sanctions
- **Canada Sanctions** - Global Affairs Canada
- **Australia Sanctions** - Department of Foreign Affairs

### Regional Sources
- **OFSI** (UK Office of Financial Sanctions Implementation)
- **SECO** (Switzerland State Secretariat for Economic Affairs)
- **BIS** (US Bureau of Industry and Security)
- **And 75+ additional authorities worldwide**

## Entity Schema Structure

### Base Entity Properties
All entities inherit from the base schema with common properties:

```json
{
  "id": "entity-identifier",
  "schema": "Person|Organization|Address|etc",
  "caption": "Primary display name",
  "countries": ["country-codes"],
  "topics": ["sanction", "crime", "poi"],
  "datasets": ["source-dataset-names"],
  "first_seen": "YYYY-MM-DD",
  "last_seen": "YYYY-MM-DD",
  "properties": {
    // Entity-specific properties
  }
}
```

### Person Entity
```json
{
  "schema": "Person",
  "properties": {
    "name": ["Full Name"],
    "firstName": ["Given Name"],
    "lastName": ["Family Name"],
    "birthDate": ["1970-01-01"],
    "birthPlace": ["City, Country"],
    "nationality": ["country-code"],
    "passportNumber": ["document-numbers"],
    "idNumber": ["identification-numbers"]
  }
}
```

### Organization Entity
```json
{
  "schema": "Organization",
  "properties": {
    "name": ["Organization Name"],
    "incorporationDate": ["1990-01-01"],
    "registrationNumber": ["reg-numbers"],
    "taxNumber": ["tax-identifiers"],
    "address": ["Full Address"],
    "country": ["country-code"]
  }
}
```

### Address Entity
```json
{
  "schema": "Address",
  "properties": {
    "full": ["Complete Address"],
    "street": ["Street Address"],
    "city": ["City Name"],
    "region": ["State/Province"],
    "postalCode": ["ZIP/Postal Code"],
    "country": ["country-code"]
  }
}
```

### Company Entity
```json
{
  "schema": "Company",
  "properties": {
    "name": ["Company Name"],
    "legalForm": ["Corporation Type"],
    "registrationNumber": ["Business Registration"],
    "taxNumber": ["Tax ID"],
    "sector": ["Industry Sector"],
    "employees": ["Employee Count Range"]
  }
}
```

### Cryptocurrency Wallet Entity
```json
{
  "schema": "CryptoWallet",
  "properties": {
    "address": ["wallet-address"],
    "currency": ["BTC", "ETH", "etc"],
    "holder": ["entity-reference"]
  }
}
```

### Vessel Entity
```json
{
  "schema": "Vessel",
  "properties": {
    "name": ["Ship Name"],
    "imoNumber": ["IMO-identifier"],
    "flag": ["Flag Country"],
    "tonnage": ["Gross Tonnage"],
    "owner": ["entity-reference"]
  }
}
```

### Aircraft Entity
```json
{
  "schema": "Aircraft",
  "properties": {
    "name": ["Aircraft Name"],
    "registrationNumber": ["tail-number"],
    "model": ["Aircraft Model"],
    "owner": ["entity-reference"]
  }
}
```

## System Architecture

### Data Flow
```
OpenSanctions API → Daily Fetch → Entity Processing → Supabase Storage → AML Screening
```

### Processing Pipeline
1. **Daily Fetch**: Download latest sanctions data
2. **Entity Parsing**: Parse Senzing JSON format
3. **Schema Validation**: Validate against entity schemas
4. **Data Transformation**: Convert to internal format
5. **Supabase Storage**: Store in normalized tables
6. **Index Building**: Create search indices
7. **AML Integration**: Enable real-time screening

### Database Schema Design

#### Primary Tables
```sql
-- Main sanctions entities table
CREATE TABLE sanctions_entities (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(200) UNIQUE NOT NULL,
    schema_type VARCHAR(50) NOT NULL,
    name VARCHAR(1000) NOT NULL,
    name_normalized VARCHAR(1000),
    countries JSONB,
    topics JSONB,
    datasets JSONB,
    first_seen DATE,
    last_seen DATE,
    properties JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Entity relationships table
CREATE TABLE sanctions_relationships (
    id BIGSERIAL PRIMARY KEY,
    source_entity_id VARCHAR(200) REFERENCES sanctions_entities(entity_id),
    target_entity_id VARCHAR(200) REFERENCES sanctions_entities(entity_id),
    relationship_type VARCHAR(100),
    properties JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Search optimization table
CREATE TABLE sanctions_search_index (
    id BIGSERIAL PRIMARY KEY,
    entity_id VARCHAR(200) REFERENCES sanctions_entities(entity_id),
    search_text TEXT,
    entity_type VARCHAR(50),
    is_primary_target BOOLEAN DEFAULT FALSE,
    risk_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Indices for Performance
```sql
-- Search indices
CREATE INDEX idx_sanctions_entities_name ON sanctions_entities USING GIN (to_tsvector('english', name));
CREATE INDEX idx_sanctions_entities_schema ON sanctions_entities (schema_type);
CREATE INDEX idx_sanctions_entities_countries ON sanctions_entities USING GIN (countries);
CREATE INDEX idx_sanctions_search_text ON sanctions_search_index USING GIN (to_tsvector('english', search_text));

-- Performance indices
CREATE INDEX idx_sanctions_entities_entity_id ON sanctions_entities (entity_id);
CREATE INDEX idx_sanctions_entities_updated ON sanctions_entities (updated_at);
```

## API Integration

### Endpoints
- `GET /api/sanctions/entities` - List all sanctions entities
- `GET /api/sanctions/search?q={query}` - Search sanctions by name/identifier
- `GET /api/sanctions/entity/{id}` - Get specific entity details
- `POST /api/sanctions/screen` - Screen transaction parties against sanctions
- `POST /api/sanctions/refresh` - Force refresh from OpenSanctions

### Screening Logic
```python
def screen_transaction(transaction_data):
    """Screen transaction parties against sanctions"""
    parties = extract_parties(transaction_data)
    matches = []
    
    for party in parties:
        # Search by name
        name_matches = search_sanctions_by_name(party.name)
        
        # Search by identifiers
        id_matches = search_sanctions_by_identifiers(party.identifiers)
        
        # Fuzzy matching for variations
        fuzzy_matches = fuzzy_search_sanctions(party.name)
        
        matches.extend(name_matches + id_matches + fuzzy_matches)
    
    return {
        'transaction_id': transaction_data.id,
        'risk_level': calculate_risk_level(matches),
        'matches': matches,
        'requires_review': len(matches) > 0
    }
```

## Benefits of This Design

### Accuracy
- ✅ **Authoritative Source**: 84 global sanctions authorities
- ✅ **Daily Updates**: Fresh sanctions data every day
- ✅ **Comprehensive Coverage**: All entity types included
- ✅ **Standardized Format**: Consistent data structure

### Performance
- ✅ **Focused Dataset**: 264K entities vs 1.2M irrelevant data
- ✅ **Optimized Storage**: Entity-specific schemas
- ✅ **Fast Search**: Indexed text search and identifiers
- ✅ **Real-time Screening**: Sub-second response times

### Compliance
- ✅ **Global Coverage**: UN, US, EU, UK, Canada, Australia
- ✅ **Asset Types**: People, companies, crypto, vessels, aircraft
- ✅ **Audit Trail**: Complete data lineage and updates
- ✅ **Risk Assessment**: Multi-level risk scoring

## Implementation Phases

### Phase 1: Data Integration
- [ ] Implement daily fetch from OpenSanctions
- [ ] Build Senzing JSON parser
- [ ] Create entity processors for all 10 types
- [ ] Design and implement Supabase schema

### Phase 2: Search & Screening
- [ ] Build search indices and algorithms
- [ ] Implement fuzzy matching for name variations
- [ ] Create transaction screening logic
- [ ] Add risk scoring algorithms

### Phase 3: API & UI
- [ ] Develop REST API endpoints
- [ ] Create admin dashboard for sanctions management
- [ ] Build screening workflow UI
- [ ] Add reporting and analytics

### Phase 4: Optimization
- [ ] Performance tuning and caching
- [ ] Advanced matching algorithms
- [ ] Real-time update webhooks
- [ ] Compliance reporting automation

---

**Document Version**: 1.0  
**Last Updated**: 2025-08-22  
**Status**: Design Phase