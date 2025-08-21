#!/usr/bin/env python3
"""
Populate Supabase sanctions table with OpenSanctions data
"""

import sys
import os
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        print("🚀 Starting Supabase sanctions data population...")
        print("=" * 60)
        
        # Test Supabase connection first
        print("🔄 Testing Supabase connection...")
        from supabase_sanctions import SupabaseSanctionsDB
        
        supabase_db = SupabaseSanctionsDB()
        initial_count = supabase_db.get_sanctions_count()
        print(f"✅ Connected to Supabase - Current records: {initial_count:,}")
        
        # Initialize sanctions loader
        print("\n🔄 Initializing sanctions loader...")
        from database import AMLDatabase
        from sanctions_loader import SanctionsLoader
        
        db = AMLDatabase()
        loader = SanctionsLoader(db)
        
        # Load fresh OpenSanctions data
        print("\n📥 Loading OpenSanctions daily datasets...")
        print("  This may take several minutes for large datasets...")
        
        result = loader.force_refresh_sanctions_data()
        
        if result.get('success'):
            total_count = result.get('total_count', 0)
            source = result.get('source', 'Unknown')
            
            print(f"\n✅ Successfully loaded {total_count:,} sanctions records")
            print(f"📊 Data source: {source}")
            
            # Show detailed breakdown
            datasets = result.get('datasets', {})
            if datasets:
                print("\n📋 Dataset breakdown:")
                for dataset_key, dataset_result in datasets.items():
                    if dataset_result.get('success'):
                        count = dataset_result.get('count', 0)
                        date = dataset_result.get('date', 'Unknown')
                        dataset_source = dataset_result.get('source', 'Unknown')
                        print(f"  • {dataset_key.upper()}: {count:,} records from {dataset_source} ({date})")
            
            # Verify final count in Supabase
            print("\n🔍 Verifying data in Supabase...")
            final_count = supabase_db.get_sanctions_count()
            print(f"📊 Final Supabase record count: {final_count:,}")
            
            # Test search functionality
            print("\n🔍 Testing search functionality...")
            test_searches = ['Vladimir Putin', 'Kim Jong Un', 'Iran', 'Russia']
            
            for search_term in test_searches:
                results = supabase_db.get_sanctions_by_name(search_term)
                if results:
                    print(f"  ✅ '{search_term}': {len(results)} matches found")
                    # Show first match details
                    first = results[0]
                    name = first.get('name', 'Unknown')
                    source = first.get('data_source', 'Unknown')
                    list_name = first.get('list_name', 'Unknown')
                    print(f"      → {name} ({list_name} - {source})")
                else:
                    print(f"  ⚠️ '{search_term}': No matches found")
            
            print(f"\n🎉 Supabase population completed successfully!")
            print(f"🌟 Your AML system now has {final_count:,} sanctions records in cloud storage")
            print(f"⚡ This resolves the Render database size issues")
            
            return True
            
        else:
            error = result.get('error', 'Unknown error')
            print(f"\n❌ Failed to load sanctions data: {error}")
            
            # Try to load fallback data if daily datasets fail
            print("\n🔄 Attempting to load fallback sanctions data...")
            fallback_result = loader._load_fallback_sanctions()
            
            if fallback_result.get('success'):
                fallback_count = fallback_result.get('count', 0)
                print(f"✅ Loaded {fallback_count} fallback sanctions records")
                return True
            else:
                print("❌ Fallback data loading also failed")
                return False
    
    except Exception as e:
        print(f"\n❌ Error during population: {e}")
        print(f"📋 Error details: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Population script completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Population script failed!")
        sys.exit(1)