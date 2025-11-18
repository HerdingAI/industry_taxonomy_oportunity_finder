-- ================================================================
-- STEP 2: Create voice_of_customer table
-- Stores Reddit, G2, Capterra reviews, LinkedIn posts
-- ================================================================

CREATE TABLE IF NOT EXISTS voice_of_customer (
    id SERIAL PRIMARY KEY,

    -- Source identification
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('reddit', 'g2', 'capterra', 'trustradius', 'linkedin', 'forum', 'other')),

    -- Industry categorization
    industry_naics VARCHAR(10),  -- NAICS code (e.g., '541511')
    industry_keywords TEXT[],    -- Array of keywords for flexible search

    -- Content
    title TEXT,
    content TEXT NOT NULL,
    author VARCHAR(255),
    post_date TIMESTAMP,
    url TEXT,

    -- Metadata
    software_mentioned VARCHAR(255),     -- Which software is being discussed
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'negative', 'neutral', 'mixed')),
    pain_point_category VARCHAR(100),    -- 'manual_process', 'integration', 'cost', 'ux', 'performance', 'support'

    -- Extracted insights (arrays for flexibility)
    complaint_keywords TEXT[],           -- ['clunky', 'outdated', 'slow', 'expensive']
    feature_gaps TEXT[],                 -- Missing features mentioned

    -- Vector embedding for semantic search (1536 dimensions for OpenAI ada-002)
    embedding vector(1536),

    -- Housekeeping
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT voice_of_customer_url_unique UNIQUE(url)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_voc_naics ON voice_of_customer(industry_naics);
CREATE INDEX IF NOT EXISTS idx_voc_source ON voice_of_customer(source_type);
CREATE INDEX IF NOT EXISTS idx_voc_software ON voice_of_customer(software_mentioned);
CREATE INDEX IF NOT EXISTS idx_voc_sentiment ON voice_of_customer(sentiment);
CREATE INDEX IF NOT EXISTS idx_voc_pain_category ON voice_of_customer(pain_point_category);
CREATE INDEX IF NOT EXISTS idx_voc_post_date ON voice_of_customer(post_date DESC);

-- GIN indexes for array searches
CREATE INDEX IF NOT EXISTS idx_voc_keywords ON voice_of_customer USING GIN(complaint_keywords);
CREATE INDEX IF NOT EXISTS idx_voc_feature_gaps ON voice_of_customer USING GIN(feature_gaps);
CREATE INDEX IF NOT EXISTS idx_voc_industry_keywords ON voice_of_customer USING GIN(industry_keywords);

-- Vector similarity index (IVFFlat - faster for large datasets)
CREATE INDEX IF NOT EXISTS idx_voc_embedding ON voice_of_customer
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Comments for documentation
COMMENT ON TABLE voice_of_customer IS 'Stores user reviews, complaints, and feedback from various sources (Reddit, G2, forums, etc.)';
COMMENT ON COLUMN voice_of_customer.embedding IS 'Vector embedding (1536 dims) for semantic similarity search using OpenAI ada-002';
COMMENT ON COLUMN voice_of_customer.complaint_keywords IS 'Extracted complaint keywords for quick filtering';
COMMENT ON COLUMN voice_of_customer.pain_point_category IS 'Categorized pain point type for aggregation';
