#!/usr/bin/env python3
"""
Setup script to create user authentication tables in Supabase
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_user_auth_tables():
    """Create user authentication tables in Supabase"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        return False
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # SQL to create user authentication tables
        sql_commands = [
            """
            -- Users table
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                provider TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                avatar_url TEXT,
                role TEXT DEFAULT 'user',
                last_login TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(provider, provider_user_id)
            );
            """,
            """
            -- User sessions table
            CREATE TABLE IF NOT EXISTS user_sessions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                session_id TEXT UNIQUE NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            -- Authentication audit log
            CREATE TABLE IF NOT EXISTS auth_audit_log (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
                event_type TEXT NOT NULL,
                provider TEXT,
                ip_address INET,
                user_agent TEXT,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            -- Create indexes for better performance
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_provider ON users(provider, provider_user_id);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
            CREATE INDEX IF NOT EXISTS idx_auth_audit_user_id ON auth_audit_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_auth_audit_event_type ON auth_audit_log(event_type);
            """,
            """
            -- Enable Row Level Security (RLS)
            ALTER TABLE users ENABLE ROW LEVEL SECURITY;
            ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
            ALTER TABLE auth_audit_log ENABLE ROW LEVEL SECURITY;
            """,
            """
            -- Create policies for Row Level Security
            CREATE POLICY IF NOT EXISTS "Allow all operations on users" ON users FOR ALL USING (true);
            CREATE POLICY IF NOT EXISTS "Allow all operations on user_sessions" ON user_sessions FOR ALL USING (true);
            CREATE POLICY IF NOT EXISTS "Allow all operations on auth_audit_log" ON auth_audit_log FOR ALL USING (true);
            """
        ]
        
        # Note: Supabase Python client doesn't support raw SQL execution for DDL
        # These commands need to be run via the Supabase SQL Editor or psql
        print("📝 SQL commands to run in Supabase SQL Editor:")
        print("=" * 60)
        for i, sql in enumerate(sql_commands, 1):
            print(f"-- Command {i}:")
            print(sql.strip())
            print()
        
        print("=" * 60)
        print("✅ Copy and paste these SQL commands into your Supabase SQL Editor")
        print("🌐 Go to: https://supabase.com/dashboard → Your Project → SQL Editor")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Supabase: {e}")
        return False

if __name__ == "__main__":
    print("🔐 Setting up user authentication tables in Supabase...")
    create_user_auth_tables()