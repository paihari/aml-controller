#!/usr/bin/env python3
"""
Apply user authentication schema to Supabase database
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_user_schema():
    """Apply user authentication schema to Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url:
        print("❌ Missing SUPABASE_URL environment variable")
        return False
        
    if not supabase_service_key:
        print("❌ Missing SUPABASE_SERVICE_ROLE_KEY environment variable")
        print("   Using SUPABASE_ANON_KEY instead (limited permissions)")
        supabase_service_key = os.getenv('SUPABASE_ANON_KEY')
        
    if not supabase_service_key:
        print("❌ Missing both SUPABASE_SERVICE_ROLE_KEY and SUPABASE_ANON_KEY")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_service_key)
        print("✅ Connected to Supabase")
        
        # Read the schema file
        schema_file = os.path.join(os.path.dirname(__file__), 'supabase_user_schema.sql')
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Split into individual commands (split by semicolon and newline)
        commands = []
        current_command = []
        
        for line in schema_sql.split('\n'):
            line = line.strip()
            if line.startswith('--') or not line:
                continue
            
            current_command.append(line)
            if line.endswith(';'):
                command = ' '.join(current_command).strip()
                if command:
                    commands.append(command)
                current_command = []
        
        # Add any remaining command
        if current_command:
            command = ' '.join(current_command).strip()
            if command:
                commands.append(command)
        
        print(f"📝 Applying {len(commands)} database commands...")
        
        success_count = 0
        for i, command in enumerate(commands, 1):
            try:
                # Use rpc to execute raw SQL
                result = supabase.rpc('exec_sql', {'sql': command}).execute()
                print(f"✅ Command {i} executed successfully")
                success_count += 1
            except Exception as e:
                # Try alternative method for DDL commands
                try:
                    # For some DDL commands, we might need to use the REST API differently
                    print(f"⚠️ Command {i} failed with rpc, trying alternative method: {str(e)[:100]}...")
                    # This is a fallback - in practice, you might need to run these manually
                    print(f"Manual command: {command[:100]}...")
                except Exception as e2:
                    print(f"❌ Command {i} failed: {str(e2)[:100]}...")
        
        print(f"✅ Applied {success_count}/{len(commands)} commands successfully")
        
        if success_count < len(commands):
            print("\n📋 For commands that failed, you may need to run them manually in Supabase SQL Editor:")
            print(f"🌐 Go to: {supabase_url.replace('/rest/v1', '')}/dashboard → SQL Editor")
            print("\nFailed commands:")
            for i, command in enumerate(commands[success_count:], success_count + 1):
                print(f"-- Command {i}:")
                print(command)
                print()
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        
        # Fallback: print instructions for manual execution
        print("\n📋 Please run these commands manually in Supabase SQL Editor:")
        print(f"🌐 Go to: https://supabase.com/dashboard → Your Project → SQL Editor")
        print("\nSQL to execute:")
        print("=" * 60)
        schema_file = os.path.join(os.path.dirname(__file__), 'supabase_user_schema.sql')
        with open(schema_file, 'r') as f:
            print(f.read())
        print("=" * 60)
        
        return False

if __name__ == "__main__":
    print("🔐 Applying user authentication schema to Supabase...")
    success = apply_user_schema()
    sys.exit(0 if success else 1)