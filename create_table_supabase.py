#!/usr/bin/env python3
"""
Create Supabase sanctions table using direct table operations
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_table_via_insert():
    """Create table by attempting an insert operation"""
    try:
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found in .env")
            return False
            
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # Test if table exists by trying to query it
        try:
            result = supabase.table('sanctions_entities').select('id').limit(1).execute()
            print("✅ Sanctions entities table already exists")
            return True
        except Exception as e:
            print(f"⚠️ Table doesn't exist yet: {e}")
            print("❌ Please create the table manually in Supabase dashboard using supabase_schema.sql")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return False

if __name__ == "__main__":
    create_table_via_insert()