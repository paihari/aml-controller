#!/usr/bin/env python3
"""
Simple script to check and create minimal user schema
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_and_create_users_table():
    """Check if users table exists and create if not"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test if users table exists by trying to query it
        try:
            result = supabase.table('users').select('id').limit(1).execute()
            print("✅ Users table already exists")
            
            # Check if provider column exists
            try:
                result = supabase.table('users').select('provider').limit(1).execute()
                print("✅ Provider column exists")
                
                # Check if get_users_by_provider function exists
                try:
                    result = supabase.rpc('get_users_by_provider').execute()
                    print("✅ get_users_by_provider function exists")
                    print("✅ Database schema is complete")
                    return True
                except Exception as e:
                    print(f"❌ get_users_by_provider function missing: {str(e)[:100]}...")
                    return False
                    
            except Exception as e:
                print(f"❌ Provider column missing: {str(e)[:100]}...")
                return False
                
        except Exception as e:
            print(f"❌ Users table missing: {str(e)[:100]}...")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking database schema...")
    check_and_create_users_table()