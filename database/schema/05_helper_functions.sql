-- ================================================================
-- STEP 5: Create helper functions and views
-- ================================================================

-- Function: Semantic search on voice of customer
CREATE OR REPLACE FUNCTION search_voice_of_customer(
    query_embedding vector(1536),
    naics_code VARCHAR(10) DEFAULT NULL,
    source_types TEXT[] DEFAULT NULL,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
    id INTEGER,
    content TEXT,
    pain_point_category VARCHAR(100),
    complaint_keywords TEXT[],
    feature_gaps TEXT[],
    url TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        voc.id,
        voc.content,
        voc.pain_point_category,
        voc.complaint_keywords,
        voc.feature_gaps,
        voc.url,
        1 - (voc.embedding <=> query_embedding) as similarity
    FROM voice_of_customer voc
    WHERE
        (naics_code IS NULL OR voc.industry_naics = naics_code)
        AND (source_types IS NULL OR voc.source_type = ANY(source_types))
    ORDER BY voc.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function: Aggregate pain points by category
CREATE OR REPLACE FUNCTION aggregate_pain_points(
    naics_code VARCHAR(10)
)
RETURNS TABLE (
    pain_point_category VARCHAR(100),
    mention_count BIGINT,
    all_keywords TEXT[],
    negativity_score NUMERIC,
    example_content TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        voc.pain_point_category,
        COUNT(*) as mention_count,
        ARRAY_AGG(DISTINCT unnest) as all_keywords,
        AVG(CASE
            WHEN voc.sentiment = 'negative' THEN 1.0
            WHEN voc.sentiment = 'mixed' THEN 0.5
            ELSE 0.0
        END) as negativity_score,
        (ARRAY_AGG(voc.content ORDER BY voc.post_date DESC))[1] as example_content
    FROM voice_of_customer voc,
         LATERAL unnest(voc.complaint_keywords) unnest
    WHERE voc.industry_naics = naics_code
      AND voc.pain_point_category IS NOT NULL
    GROUP BY voc.pain_point_category
    ORDER BY mention_count DESC, negativity_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function: Get recent competitive activity
CREATE OR REPLACE FUNCTION get_recent_funding(
    naics_code VARCHAR(10),
    since_date DATE DEFAULT CURRENT_DATE - INTERVAL '24 months'
)
RETURNS TABLE (
    company_name VARCHAR(255),
    funding_stage VARCHAR(50),
    funding_amount_usd BIGINT,
    funding_date DATE,
    product_category VARCHAR(100),
    key_features TEXT[],
    total_funding_usd BIGINT,
    source_url TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ci.company_name,
        ci.funding_stage,
        ci.funding_amount_usd,
        ci.funding_date,
        ci.product_category,
        ci.key_features,
        ci.total_funding_usd,
        ci.source_url
    FROM competitive_intelligence ci
    WHERE ci.industry_naics = naics_code
      AND ci.funding_date >= since_date
    ORDER BY ci.funding_date DESC, ci.funding_amount_usd DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

-- Function: Find high-automation-potential workflows
CREATE OR REPLACE FUNCTION find_automation_opportunities(
    naics_code VARCHAR(10),
    min_genai_score INTEGER DEFAULT 60
)
RETURNS TABLE (
    workflow_name VARCHAR(255),
    job_role VARCHAR(255),
    genai_fit_score INTEGER,
    automation_feasibility VARCHAR(20),
    time_spent_hours DECIMAL(5,2),
    frequency VARCHAR(50),
    pain_point_description TEXT,
    data_types TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        wi.workflow_name,
        wi.job_role,
        wi.genai_fit_score,
        wi.automation_feasibility,
        wi.time_spent_hours,
        wi.frequency,
        wi.pain_point_description,
        wi.data_types
    FROM workflow_intelligence wi
    WHERE wi.industry_naics = naics_code
      AND wi.genai_fit_score >= min_genai_score
      AND wi.automation_feasibility IN ('high', 'medium')
    ORDER BY wi.genai_fit_score DESC, wi.time_spent_hours DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

-- View: Industry summary statistics
CREATE OR REPLACE VIEW industry_rag_summary AS
SELECT
    COALESCE(voc.industry_naics, ci.industry_naics, wi.industry_naics) as naics_code,
    COUNT(DISTINCT voc.id) as voice_of_customer_count,
    COUNT(DISTINCT ci.id) as competitive_intel_count,
    COUNT(DISTINCT wi.id) as workflow_intel_count,
    -- Voice of customer metrics
    AVG(CASE WHEN voc.sentiment = 'negative' THEN 1.0 ELSE 0.0 END) as negative_sentiment_ratio,
    COUNT(DISTINCT voc.software_mentioned) as software_products_mentioned,
    -- Competitive metrics
    SUM(ci.funding_amount_usd) as total_recent_funding,
    COUNT(DISTINCT CASE WHEN ci.funding_date >= CURRENT_DATE - INTERVAL '12 months' THEN ci.company_name END) as funded_startups_12mo,
    -- Workflow metrics
    AVG(wi.genai_fit_score) as avg_genai_fit_score,
    COUNT(CASE WHEN wi.automation_feasibility = 'high' THEN 1 END) as high_automation_workflows
FROM voice_of_customer voc
FULL OUTER JOIN competitive_intelligence ci ON voc.industry_naics = ci.industry_naics
FULL OUTER JOIN workflow_intelligence wi ON COALESCE(voc.industry_naics, ci.industry_naics) = wi.industry_naics
GROUP BY COALESCE(voc.industry_naics, ci.industry_naics, wi.industry_naics);

-- Comments on functions
COMMENT ON FUNCTION search_voice_of_customer IS 'Semantic similarity search on customer feedback using vector embeddings';
COMMENT ON FUNCTION aggregate_pain_points IS 'Aggregate and rank pain points by category for a given NAICS code';
COMMENT ON FUNCTION get_recent_funding IS 'Get recent startup funding activity in an industry';
COMMENT ON FUNCTION find_automation_opportunities IS 'Find workflows with high GenAI automation potential';
COMMENT ON VIEW industry_rag_summary IS 'Summary statistics across all RAG tables by NAICS code';
