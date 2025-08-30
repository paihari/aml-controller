-- Add missing provider column to users table
-- Run this in Supabase SQL Editor

-- Add provider column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'provider'
    ) THEN
        ALTER TABLE users ADD COLUMN provider TEXT NOT NULL DEFAULT 'google';
        ALTER TABLE users ADD COLUMN provider_user_id TEXT;
        
        -- Add unique constraint
        ALTER TABLE users ADD CONSTRAINT unique_provider_user UNIQUE(provider, provider_user_id);
        
        -- Create index for performance
        CREATE INDEX IF NOT EXISTS idx_users_provider ON users(provider, provider_user_id);
        
        -- Update existing users to have provider info
        UPDATE users SET provider = 'google', provider_user_id = COALESCE(email, id::text);
        
        RAISE NOTICE 'Added provider column and updated existing users';
    ELSE
        RAISE NOTICE 'Provider column already exists';
    END IF;
END $$;

-- Create the get_users_by_provider function
CREATE OR REPLACE FUNCTION get_users_by_provider()
RETURNS TABLE(provider TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.provider,
        COUNT(*)::BIGINT as count
    FROM users u
    GROUP BY u.provider
    ORDER BY u.provider;
END;
$$ LANGUAGE plpgsql;