-- Minimalist AML Schema for Supabase PostgreSQL
-- Drop existing tables if they exist
DROP TABLE IF EXISTS entity_relationships CASCADE;
DROP TABLE IF EXISTS sanctions_entities CASCADE;

-- Create sanctions_entities table
CREATE TABLE sanctions_entities (
    -- Primary Key
    id BIGSERIAL PRIMARY KEY,
    
    -- Core Identity
    entity_id VARCHAR(100) UNIQUE NOT NULL,
    entity_type VARCHAR(20) NOT NULL, -- person|organization|company|address|crypto|vessel|aircraft
    
    -- Names (Critical for Screening)
    primary_name VARCHAR(500) NOT NULL,
    normalized_name VARCHAR(500) NOT NULL,
    search_names TEXT[], -- Array of name variations
    
    -- Identifiers (High-value for AML)
    passport_numbers TEXT[],
    national_ids TEXT[],
    tax_numbers TEXT[],
    registration_numbers TEXT[],
    crypto_addresses TEXT[],
    vessel_imo VARCHAR(20),
    aircraft_tail VARCHAR(20),
    
    -- Geographic & Risk
    countries VARCHAR(10)[], -- ISO country codes
    risk_level VARCHAR(10) NOT NULL DEFAULT 'HIGH', -- CRITICAL|HIGH|MEDIUM|LOW
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Source Tracking
    data_sources VARCHAR(50)[],
    last_updated DATE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create entity_relationships table
CREATE TABLE entity_relationships (
    id BIGSERIAL PRIMARY KEY,
    parent_entity_id BIGINT REFERENCES sanctions_entities(id),
    child_entity_id BIGINT REFERENCES sanctions_entities(id),
    relationship_type VARCHAR(30), -- owned_by|controlled_by|associated_with|same_as
    created_at TIMESTAMP DEFAULT NOW()
);

-- Core screening indexes
CREATE INDEX idx_sanctions_normalized_name ON sanctions_entities (normalized_name);
CREATE INDEX idx_sanctions_search_names ON sanctions_entities USING gin (search_names);
CREATE INDEX idx_sanctions_entity_type ON sanctions_entities (entity_type) WHERE is_active = true;

-- Identifier matching indexes
CREATE INDEX idx_sanctions_passports ON sanctions_entities USING gin (passport_numbers);
CREATE INDEX idx_sanctions_national_ids ON sanctions_entities USING gin (national_ids);
CREATE INDEX idx_sanctions_tax_numbers ON sanctions_entities USING gin (tax_numbers);
CREATE INDEX idx_sanctions_crypto ON sanctions_entities USING gin (crypto_addresses);

-- Risk and geographic indexes
CREATE INDEX idx_sanctions_countries ON sanctions_entities USING gin (countries);
CREATE INDEX idx_sanctions_risk_active ON sanctions_entities (risk_level, is_active);

-- Full-text search index
CREATE INDEX idx_sanctions_fulltext ON sanctions_entities USING gin (to_tsvector('english', primary_name));

-- Relationship indexes
CREATE INDEX idx_relationships_parent ON entity_relationships (parent_entity_id);
CREATE INDEX idx_relationships_child ON entity_relationships (child_entity_id);

-- Verify table creation
SELECT 'sanctions_entities table created' as status;
SELECT 'entity_relationships table created' as status;