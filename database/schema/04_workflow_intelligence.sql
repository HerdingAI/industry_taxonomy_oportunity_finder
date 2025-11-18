-- ================================================================
-- STEP 4: Create workflow_intelligence table
-- Stores workflow mapping, job descriptions, process documentation
-- ================================================================

CREATE TABLE IF NOT EXISTS workflow_intelligence (
    id SERIAL PRIMARY KEY,

    -- Industry and role context
    industry_naics VARCHAR(10) NOT NULL,
    industry_name VARCHAR(255),
    job_role VARCHAR(255),              -- 'insurance broker', 'construction PM', 'legal paralegal'
    company_size VARCHAR(50) CHECK (company_size IN ('solo', 'small', 'medium', 'large', 'enterprise')), -- 1, 2-10, 11-50, 51-200, 200+

    -- Workflow identification
    workflow_name VARCHAR(255),         -- 'Quote generation', 'Invoice processing', 'Contract review'
    workflow_description TEXT,
    workflow_category VARCHAR(100),     -- 'sales', 'operations', 'compliance', 'finance', 'customer_service'

    -- Process details
    manual_steps TEXT[],                -- Array of manual process descriptions
    tools_used TEXT[],                  -- Current software/tools in this workflow
    time_spent_hours DECIMAL(5,2),     -- Average time spent per execution
    frequency VARCHAR(50) CHECK (frequency IN ('hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'annually')),
    volume_per_period INTEGER,          -- How many times executed per frequency period

    -- Pain points
    inefficiency_type VARCHAR(100),     -- 'data_entry', 'manual_calculation', 'reconciliation', 'document_processing'
    pain_point_description TEXT,
    error_rate_estimate DECIMAL(5,2),  -- Percentage (0-100)
    cost_of_error TEXT,                 -- Description of what errors cost

    -- Automation potential
    automation_feasibility VARCHAR(20) CHECK (automation_feasibility IN ('high', 'medium', 'low', 'none')),
    genai_fit_score INTEGER CHECK (genai_fit_score >= 0 AND genai_fit_score <= 100),
    automation_complexity VARCHAR(50),  -- 'simple', 'moderate', 'complex', 'very_complex'

    -- Data characteristics
    data_types TEXT[],                  -- ['pdf', 'email', 'excel', 'images', 'text', 'structured']
    data_volume_estimate VARCHAR(50),   -- 'low (<100/month)', 'medium (100-1000)', 'high (1000+)'
    data_quality VARCHAR(50),           -- 'clean', 'messy', 'unstructured', 'mixed'

    -- Business impact
    revenue_impact VARCHAR(50),         -- 'high', 'medium', 'low', 'none'
    compliance_criticality VARCHAR(50), -- 'critical', 'important', 'nice_to_have', 'not_applicable'

    -- Data source
    source_type VARCHAR(50) CHECK (source_type IN ('job_description', 'process_doc', 'interview', 'forum', 'reddit', 'linkedin', 'survey', 'case_study', 'other')),
    source_url TEXT,
    source_date DATE,

    -- Vector embedding
    embedding vector(1536),

    -- Housekeeping
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_wi_naics ON workflow_intelligence(industry_naics);
CREATE INDEX IF NOT EXISTS idx_wi_role ON workflow_intelligence(job_role);
CREATE INDEX IF NOT EXISTS idx_wi_category ON workflow_intelligence(workflow_category);
CREATE INDEX IF NOT EXISTS idx_wi_automation_feasibility ON workflow_intelligence(automation_feasibility);
CREATE INDEX IF NOT EXISTS idx_wi_genai_score ON workflow_intelligence(genai_fit_score DESC);
CREATE INDEX IF NOT EXISTS idx_wi_company_size ON workflow_intelligence(company_size);

-- GIN indexes for arrays
CREATE INDEX IF NOT EXISTS idx_wi_tools_used ON workflow_intelligence USING GIN(tools_used);
CREATE INDEX IF NOT EXISTS idx_wi_data_types ON workflow_intelligence USING GIN(data_types);
CREATE INDEX IF NOT EXISTS idx_wi_manual_steps ON workflow_intelligence USING GIN(manual_steps);

-- Vector similarity index
CREATE INDEX IF NOT EXISTS idx_wi_embedding ON workflow_intelligence
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_wi_naics_automation ON workflow_intelligence(industry_naics, automation_feasibility, genai_fit_score DESC);

-- Comments
COMMENT ON TABLE workflow_intelligence IS 'Workflow mapping and automation opportunity data';
COMMENT ON COLUMN workflow_intelligence.genai_fit_score IS 'Score 0-100 indicating suitability for GenAI automation';
COMMENT ON COLUMN workflow_intelligence.time_spent_hours IS 'Average hours per workflow execution';
COMMENT ON COLUMN workflow_intelligence.volume_per_period IS 'Number of executions per frequency period';
