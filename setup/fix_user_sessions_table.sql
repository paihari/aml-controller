-- Fix user_sessions table by adding missing columns
-- Run this in Supabase SQL Editor

-- Add missing columns to user_sessions table if they don't exist
DO $$ 
BEGIN
    -- Add access_token column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_sessions' AND column_name = 'access_token'
    ) THEN
        ALTER TABLE user_sessions ADD COLUMN access_token TEXT;
        RAISE NOTICE 'Added access_token column to user_sessions';
    END IF;

    -- Add refresh_token column if it doesn't exist  
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_sessions' AND column_name = 'refresh_token'
    ) THEN
        ALTER TABLE user_sessions ADD COLUMN refresh_token TEXT;
        RAISE NOTICE 'Added refresh_token column to user_sessions';
    END IF;

    RAISE NOTICE 'user_sessions table structure updated';
END $$;