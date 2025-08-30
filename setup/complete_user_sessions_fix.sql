-- Complete fix for user_sessions table structure
-- Run this in Supabase SQL Editor

DO $$ 
BEGIN
    -- Check if user_sessions table exists, if not create it
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_sessions') THEN
        CREATE TABLE user_sessions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_id TEXT UNIQUE NOT NULL,
            access_token TEXT,
            refresh_token TEXT,
            expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        RAISE NOTICE 'Created user_sessions table';
    ELSE
        -- Table exists, add missing columns
        
        -- Add access_token column if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_sessions' AND column_name = 'access_token'
        ) THEN
            ALTER TABLE user_sessions ADD COLUMN access_token TEXT;
            RAISE NOTICE 'Added access_token column';
        END IF;

        -- Add refresh_token column if it doesn't exist  
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_sessions' AND column_name = 'refresh_token'
        ) THEN
            ALTER TABLE user_sessions ADD COLUMN refresh_token TEXT;
            RAISE NOTICE 'Added refresh_token column';
        END IF;

        -- Add expires_at column if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_sessions' AND column_name = 'expires_at'
        ) THEN
            ALTER TABLE user_sessions ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE;
            RAISE NOTICE 'Added expires_at column';
        END IF;

        -- Add created_at column if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_sessions' AND column_name = 'created_at'
        ) THEN
            ALTER TABLE user_sessions ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            RAISE NOTICE 'Added created_at column';
        END IF;

        -- Add last_activity column if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'user_sessions' AND column_name = 'last_activity'
        ) THEN
            ALTER TABLE user_sessions ADD COLUMN last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            RAISE NOTICE 'Added last_activity column';
        END IF;

        RAISE NOTICE 'user_sessions table structure updated';
    END IF;

    -- Create indexes for better performance if they don't exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_user_sessions_user_id') THEN
        CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
        RAISE NOTICE 'Created index on user_id';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_user_sessions_session_id') THEN
        CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
        RAISE NOTICE 'Created index on session_id';
    END IF;

    -- Enable Row Level Security if not enabled
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE tablename = 'user_sessions' AND rowsecurity = true
    ) THEN
        ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE 'Enabled RLS on user_sessions';
    END IF;

    -- Create policy if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'user_sessions' AND policyname = 'Allow all operations on user_sessions'
    ) THEN
        CREATE POLICY "Allow all operations on user_sessions" ON user_sessions FOR ALL USING (true);
        RAISE NOTICE 'Created RLS policy';
    END IF;

END $$;