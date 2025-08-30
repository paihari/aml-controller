-- Check what roles are allowed by the constraint
-- Run this in Supabase SQL Editor to see the constraint definition

SELECT 
    conname as constraint_name,
    pg_get_constraintdef(oid) as constraint_definition
FROM pg_constraint 
WHERE conname LIKE '%role%' 
  AND conrelid = (
    SELECT oid FROM pg_class WHERE relname = 'users'
  );