-- AML System Tables for Supabase
-- Alerts and Transactions tables to replace SQLite

-- Drop existing tables if they exist
DROP TABLE IF EXISTS aml_alerts CASCADE;
DROP TABLE IF EXISTS aml_transactions CASCADE;

-- AML Transactions Table
CREATE TABLE aml_transactions (
    id BIGSERIAL PRIMARY KEY,
    transaction_id TEXT UNIQUE NOT NULL,
    account_id TEXT,
    amount DECIMAL(15,2),
    currency TEXT DEFAULT 'USD',
    transaction_type TEXT,
    transaction_date DATE,
    beneficiary_account TEXT,
    beneficiary_name TEXT,
    beneficiary_bank TEXT,
    beneficiary_country TEXT,
    origin_country TEXT,
    purpose TEXT,
    status TEXT DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AML Alerts Table  
CREATE TABLE aml_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_id TEXT UNIQUE NOT NULL,
    subject_id TEXT,
    subject_type TEXT DEFAULT 'TRANSACTION', -- PARTY, ACCOUNT, TRANSACTION
    typology TEXT,
    risk_score DECIMAL(3,2),
    evidence JSONB, -- JSON for structured evidence
    status TEXT DEFAULT 'ACTIVE',
    assigned_to TEXT,
    resolution TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_aml_transactions_date ON aml_transactions(transaction_date);
CREATE INDEX idx_aml_transactions_status ON aml_transactions(status);
CREATE INDEX idx_aml_transactions_beneficiary ON aml_transactions(beneficiary_name);
CREATE INDEX idx_aml_transactions_country ON aml_transactions(beneficiary_country);

CREATE INDEX idx_aml_alerts_status ON aml_alerts(status);
CREATE INDEX idx_aml_alerts_typology ON aml_alerts(typology);
CREATE INDEX idx_aml_alerts_subject ON aml_alerts(subject_id);
CREATE INDEX idx_aml_alerts_risk_score ON aml_alerts(risk_score);

-- Enable Row Level Security (RLS)
ALTER TABLE aml_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE aml_alerts ENABLE ROW LEVEL SECURITY;

-- Create policies to allow all operations for anon/authenticated users
CREATE POLICY "Allow all operations on aml_transactions" ON aml_transactions
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on aml_alerts" ON aml_alerts  
    FOR ALL USING (true);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_aml_transactions_updated_at ON aml_transactions;
CREATE TRIGGER update_aml_transactions_updated_at BEFORE UPDATE ON aml_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_aml_alerts_updated_at ON aml_alerts;
CREATE TRIGGER update_aml_alerts_updated_at BEFORE UPDATE ON aml_alerts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();