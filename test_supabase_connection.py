#!/usr/bin/env python3
"""
Test Supabase connection and populate with sanctions data
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test basic connection
def test_connection():
    try:
        from supabase_sanctions import SupabaseSanctionsDB
        
        print("🔄 Testing Supabase connection...")
        db = SupabaseSanctionsDB()
        print("✅ Supabase connection successful")
        
        # Try to get count (this will tell us if table exists)
        count = db.get_sanctions_count()
        print(f"📊 Current sanctions count: {count}")
        
        if count == 0:
            print("🔄 Table exists but is empty - proceeding with data population...")
            return True
        else:
            print("✅ Table already has data")
            return True
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        print("💡 Please ensure the 'sanctions' table exists in your Supabase database")
        print("💡 Run the SQL from supabase_schema.sql in your Supabase dashboard")
        return False

def populate_sanctions():
    """Populate Supabase with sanctions data"""
    try:
        from sanctions_loader import SanctionsLoader
        from database import AMLDatabase
        
        print("🔄 Initializing sanctions loader...")
        db = AMLDatabase()
        loader = SanctionsLoader(db)
        
        print("📥 Loading OpenSanctions daily datasets...")
        result = loader.force_refresh_sanctions_data()
        
        if result.get('success'):
            total_count = result.get('total_count', 0)
            print(f"✅ Successfully loaded {total_count:,} sanctions records")
            
            # Show dataset breakdown
            datasets = result.get('datasets', {})
            for dataset_key, dataset_result in datasets.items():
                if dataset_result.get('success'):
                    count = dataset_result.get('count', 0)
                    date = dataset_result.get('date', 'Unknown')
                    source = dataset_result.get('source', 'Unknown')
                    print(f"  • {dataset_key}: {count:,} records from {source} ({date})")
            
            return True
        else:
            print(f"❌ Failed to load sanctions: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during sanctions population: {e}")
        return False

def verify_data():
    """Verify the populated data"""
    try:
        from supabase_sanctions import SupabaseSanctionsDB
        
        print("🔍 Verifying populated data...")
        db = SupabaseSanctionsDB()
        
        # Get final statistics
        stats = db.get_sanctions_statistics()
        total = stats.get('total_sanctions', 0)
        print(f"✅ Final verification: {total:,} sanctions records in Supabase")
        
        # Test search with known entities
        test_searches = [
            'Vladimir Putin',
            'Kim Jong Un', 
            'Iran',
            'Russia'
        ]
        
        for search_term in test_searches:
            results = db.get_sanctions_by_name(search_term)
            if results:
                print(f"🔍 Search '{search_term}': {len(results)} matches")
                # Show first result
                first = results[0]
                print(f"  → {first.get('name', 'Unknown')} ({first.get('list_name', 'Unknown')})")
            else:
                print(f"🔍 Search '{search_term}': No matches")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Supabase setup and population...")
    print("="*60)
    
    # Step 1: Test connection
    if test_connection():
        print("\n" + "="*60)
        
        # Step 2: Populate data
        if populate_sanctions():
            print("\n" + "="*60)
            
            # Step 3: Verify
            if verify_data():
                print("\n✅ Supabase setup and population completed successfully!")
                print("🌟 Your AML system is now using cloud-based sanctions storage")
            else:
                print("\n⚠️ Data populated but verification had issues")
        else:
            print("\n❌ Failed to populate sanctions data")
    else:
        print("\n❌ Connection test failed - please create the table first")
        print("\n📋 Manual Steps Required:")
        print("1. Go to your Supabase project dashboard")
        print("2. Navigate to SQL Editor")  
        print("3. Copy the SQL from supabase_schema.sql")
        print("4. Run the SQL to create the sanctions table")
        print("5. Run this script again")