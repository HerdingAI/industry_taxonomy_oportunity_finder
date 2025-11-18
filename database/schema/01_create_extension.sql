-- ================================================================
-- STEP 1: Install pgvector extension for vector embeddings
-- ================================================================

-- Check if pgvector is installed
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        CREATE EXTENSION vector;
        RAISE NOTICE 'pgvector extension created successfully';
    ELSE
        RAISE NOTICE 'pgvector extension already exists';
    END IF;
END
$$;

-- Verify installation
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
