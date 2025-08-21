#!/usr/bin/env python3
"""
Setup AML tables in Supabase
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_aml_tables():
    """Create AML tables in Supabase"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        return False
    
    try:
        print("🔗 Connecting to Supabase...")
        supabase = create_client(supabase_url, supabase_key)
        
        # Read the schema file
        with open('supabase_aml_schema.sql', 'r') as f:
            schema_sql = f.read()
        
        print("📝 Creating AML tables in Supabase...")
        print("⚠️  Note: You need to run the SQL in supabase_aml_schema.sql manually in the Supabase dashboard")
        print("🌐 Go to: https://app.supabase.com/project/[your-project]/sql")
        print(f"📋 Run the SQL from: {os.path.abspath('supabase_aml_schema.sql')}")
        
        # Test connection by trying to query existing tables
        try:
            result = supabase.table('aml_transactions').select('*').limit(1).execute()
            print("✅ aml_transactions table exists and is accessible")
        except Exception as e:
            print(f"⚠️  aml_transactions table not found: {e}")
        
        try:
            result = supabase.table('aml_alerts').select('*').limit(1).execute()
            print("✅ aml_alerts table exists and is accessible")
        except Exception as e:
            print(f"⚠️  aml_alerts table not found: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up AML tables: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Setting up AML tables in Supabase...")
    success = setup_aml_tables()
    
    if success:
        print("\n✅ Setup completed!")
        print("📝 Manual steps:")
        print("1. Go to https://app.supabase.com/project/[your-project]/sql")
        print("2. Copy and paste the SQL from supabase_aml_schema.sql")
        print("3. Run the SQL to create the tables")
        print("4. Test the connection by running this script again")
    else:
        print("❌ Setup failed!")