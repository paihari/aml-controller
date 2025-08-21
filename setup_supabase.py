#!/usr/bin/env python3
"""
Setup Supabase database with sanctions table and data
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from sanctions_loader import SanctionsLoader
from database import AMLDatabase

# Load environment variables
load_dotenv()

def create_sanctions_table():
    """Create the sanctions table in Supabase"""
    try:
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found in .env")
            return False
            
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # Create table using SQL
        sql_schema = """
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
        DROP POLICY IF EXISTS "Allow all operations on sanctions" ON sanctions;
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
        
        DROP TRIGGER IF EXISTS update_sanctions_updated_at ON sanctions;
        CREATE TRIGGER update_sanctions_updated_at BEFORE UPDATE ON sanctions
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        # Execute schema creation
        print("🔧 Creating sanctions table and indexes...")
        result = supabase.rpc('exec_sql', {'sql': sql_schema}).execute()
        print("✅ Sanctions table created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating sanctions table: {e}")
        return False

def populate_sanctions_data():
    """Load sanctions data into Supabase"""
    try:
        print("🔄 Starting sanctions data population...")
        
        # Initialize components
        db = AMLDatabase()
        sanctions_loader = SanctionsLoader(db)
        
        # Force refresh to load fresh data
        print("📥 Loading OpenSanctions daily datasets...")
        result = sanctions_loader.force_refresh_sanctions_data()
        
        if result.get('success'):
            print(f"✅ Successfully loaded {result.get('total_count', 0)} sanctions records")
            print(f"📊 Data source: {result.get('source', 'Unknown')}")
            
            # Show breakdown by dataset
            datasets = result.get('datasets', {})
            for dataset_name, dataset_result in datasets.items():
                if dataset_result.get('success'):
                    count = dataset_result.get('count', 0)
                    date = dataset_result.get('date', 'Unknown')
                    print(f"  • {dataset_name}: {count:,} records ({date})")
            
            return True
        else:
            print(f"❌ Failed to load sanctions data: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error populating sanctions data: {e}")
        return False

def verify_supabase_setup():
    """Verify that Supabase setup is working"""
    try:
        from supabase_sanctions import SupabaseSanctionsDB
        
        print("🔍 Verifying Supabase setup...")
        supabase_db = SupabaseSanctionsDB()
        
        # Test connection and get statistics
        stats = supabase_db.get_sanctions_statistics()
        print(f"✅ Supabase verification successful")
        print(f"📊 Total sanctions in Supabase: {stats.get('total_sanctions', 0):,}")
        
        # Test search functionality
        test_names = ['Vladimir Putin', 'Kim Jong Un', 'Hassan']
        for test_name in test_names:
            results = supabase_db.get_sanctions_by_name(test_name)
            if results:
                print(f"🔍 Search test '{test_name}': Found {len(results)} matches")
                # Show first match
                first_match = results[0]
                print(f"  → {first_match.get('name', 'Unknown')} ({first_match.get('data_source', 'Unknown')})")
            else:
                print(f"🔍 Search test '{test_name}': No matches found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying Supabase setup: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up Supabase sanctions database...")
    
    # Step 1: Create table
    if create_sanctions_table():
        print("\n" + "="*50)
        
        # Step 2: Populate data
        if populate_sanctions_data():
            print("\n" + "="*50)
            
            # Step 3: Verify setup
            verify_supabase_setup()
            print("\n✅ Supabase setup complete!")
        else:
            print("\n❌ Failed to populate sanctions data")
    else:
        print("\n❌ Failed to create sanctions table")