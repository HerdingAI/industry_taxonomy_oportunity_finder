-- ================================================================
-- STEP 3: Create competitive_intelligence table
-- Stores startup funding, VC activity, product launches
-- ================================================================

CREATE TABLE IF NOT EXISTS competitive_intelligence (
    id SERIAL PRIMARY KEY,

    -- Company identification
    company_name VARCHAR(255) NOT NULL,
    company_url TEXT,
    founded_year INTEGER CHECK (founded_year >= 1900 AND founded_year <= 2100),
    employee_count_range VARCHAR(50),   -- '1-10', '11-50', '51-200', '201-500', '501-1000', '1000+'
    headquarters_location VARCHAR(255), -- City, State/Country

    -- Industry categorization
    industry_naics VARCHAR(10),
    industry_vertical VARCHAR(100),     -- 'insurance tech', 'construction software', 'legal tech', etc.
    target_customer VARCHAR(255),       -- 'insurance brokers', 'general contractors', 'solo law practitioners'

    -- Funding data
    funding_stage VARCHAR(50) CHECK (funding_stage IN ('pre-seed', 'seed', 'series_a', 'series_b', 'series_c', 'series_d', 'growth', 'ipo', 'acquired', 'unknown')),
    funding_amount_usd BIGINT,          -- In USD
    funding_date DATE,
    lead_investor VARCHAR(255),
    total_funding_usd BIGINT,           -- Cumulative funding

    -- Product information
    product_category VARCHAR(100),      -- 'workflow_automation', 'data_analytics', 'ai_platform', 'saas', etc.
    key_features TEXT[],                -- Array of main features
    technology_stack TEXT[],            -- ['ai', 'ml', 'nlp', 'computer_vision', 'blockchain']
    pricing_model VARCHAR(100),         -- 'per_user', 'usage_based', 'flat_rate', 'freemium', 'enterprise'

    -- Market positioning
    competitors TEXT[],                 -- List of competitor company names
    unique_value_prop TEXT,             -- Their claimed differentiation
    customer_count_estimate INTEGER,    -- Estimated number of customers

    -- Data sources
    source_type VARCHAR(50) CHECK (source_type IN ('crunchbase', 'pitchbook', 'techcrunch', 'producthunt', 'ycombinator', 'linkedin', 'company_website', 'press_release', 'other')),
    source_url TEXT,
    source_date DATE,                   -- When this data was collected

    -- Vector embedding for similarity search
    embedding vector(1536),

    -- Housekeeping
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),

    -- Constraints (allow multiple funding rounds for same company)
    CONSTRAINT competitive_intelligence_unique UNIQUE(company_name, funding_date)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ci_naics ON competitive_intelligence(industry_naics);
CREATE INDEX IF NOT EXISTS idx_ci_vertical ON competitive_intelligence(industry_vertical);
CREATE INDEX IF NOT EXISTS idx_ci_stage ON competitive_intelligence(funding_stage);
CREATE INDEX IF NOT EXISTS idx_ci_funding_date ON competitive_intelligence(funding_date DESC);
CREATE INDEX IF NOT EXISTS idx_ci_company_name ON competitive_intelligence(company_name);
CREATE INDEX IF NOT EXISTS idx_ci_founded_year ON competitive_intelligence(founded_year DESC);

-- GIN indexes for arrays
CREATE INDEX IF NOT EXISTS idx_ci_tech_stack ON competitive_intelligence USING GIN(technology_stack);
CREATE INDEX IF NOT EXISTS idx_ci_competitors ON competitive_intelligence USING GIN(competitors);
CREATE INDEX IF NOT EXISTS idx_ci_key_features ON competitive_intelligence USING GIN(key_features);

-- Vector similarity index
CREATE INDEX IF NOT EXISTS idx_ci_embedding ON competitive_intelligence
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Comments
COMMENT ON TABLE competitive_intelligence IS 'Tracks startups, funding rounds, and competitive landscape';
COMMENT ON COLUMN competitive_intelligence.total_funding_usd IS 'Cumulative total funding raised by company';
COMMENT ON COLUMN competitive_intelligence.technology_stack IS 'Tech keywords for filtering (ai, ml, nlp, etc.)';
