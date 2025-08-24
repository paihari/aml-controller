-- Supabase schema for sanctions data
-- Run this in Supabase SQL Editor to create the sanctions table

CREATE TABLE IF NOT EXISTS sanctions (
    id BIGSERIAL PRIMARY KEY,
    entity_id TEXT NOT NULL,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    schema_type TEXT DEFAULT 'Person',
    countries JSONB DEFAULT '[]',
    topics JSONB DEFAULT '[]',
    datasets JSONB DEFAULT '[]',
    first_seen DATE,
    last_seen DATE,
    properties JSONB DEFAULT '{}',
    data_source TEXT DEFAULT 'OpenSanctions',
    list_name TEXT DEFAULT 'unknown',
    program TEXT DEFAULT 'unknown',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sanctions_name ON sanctions(name);
CREATE INDEX IF NOT EXISTS idx_sanctions_name_normalized ON sanctions(name_normalized);
CREATE INDEX IF NOT EXISTS idx_sanctions_entity_id ON sanctions(entity_id);
CREATE INDEX IF NOT EXISTS idx_sanctions_list_name ON sanctions(list_name);
CREATE INDEX IF NOT EXISTS idx_sanctions_data_source ON sanctions(data_source);

-- Create text search index for name searching
CREATE INDEX IF NOT EXISTS idx_sanctions_name_search ON sanctions USING gin(to_tsvector('english', name));

-- Enable Row Level Security (RLS)
ALTER TABLE sanctions ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for anon/authenticated users
-- Note: In production, you should create more restrictive policies
CREATE POLICY "Allow all operations on sanctions" ON sanctions
    FOR ALL USING (true);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sanctions_updated_at BEFORE UPDATE ON sanctions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();