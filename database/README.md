# RAG Database Documentation

This directory contains the PostgreSQL RAG (Retrieval-Augmented Generation) database infrastructure for the NAICS Industry Opportunity Finder.

## Overview

The RAG database stores three types of intelligence data that agents query to identify GenAI business opportunities:

1. **Voice of Customer** - Reddit posts, G2/Capterra reviews, forum discussions
2. **Competitive Intelligence** - Startup funding, VC activity, product launches
3. **Workflow Intelligence** - Job descriptions, process documentation, automation opportunities

All tables support **semantic search** using OpenAI ada-002 embeddings (1536 dimensions) via pgvector.

---

## Database Schema

### Table 1: `voice_of_customer`

Stores customer feedback from various sources to identify pain points and feature gaps.

**Key Fields**:
- `source_type` - reddit, g2, capterra, trustradius, linkedin, forum, other
- `industry_naics` - NAICS code for industry association
- `content` - Full text of review/post
- `software_mentioned` - Name of software being discussed
- `sentiment` - positive, negative, neutral, mixed
- `pain_point_category` - manual_process, integration, cost, ux, etc.
- `complaint_keywords` - Array of complaint signals (e.g., ['clunky', 'outdated'])
- `feature_gaps` - Array of missing features users want
- `embedding` - Vector embedding for semantic search

**Example Query**:
```sql
SELECT * FROM search_voice_of_customer(
    query_embedding := (SELECT embedding FROM some_query),
    naics_code := '541511',
    source_types := ARRAY['reddit', 'g2'],
    limit_count := 20
);
```

### Table 2: `competitive_intelligence`

Stores startup funding and competitive landscape data.

**Key Fields**:
- `company_name` - Startup/company name
- `industry_naics` - Target industry NAICS code
- `target_customer` - Who they sell to (e.g., 'insurance brokers')
- `funding_stage` - pre-seed, seed, series_a, series_b, etc.
- `funding_amount_usd` - Amount raised in this round
- `total_funding_usd` - Total funding to date
- `product_category` - workflow_automation, data_analytics, ai_platform, etc.
- `key_features` - Array of product features
- `technology_stack` - Array of technologies used (['ai', 'ml', 'nlp'])
- `embedding` - Vector embedding for semantic search

**Example Query**:
```sql
SELECT * FROM get_recent_funding(
    naics_code := '541511',
    since_date := '2023-01-01'::DATE
)
ORDER BY funding_amount_usd DESC;
```

### Table 3: `workflow_intelligence`

Stores workflow mapping and automation opportunity data.

**Key Fields**:
- `industry_naics` - Industry NAICS code
- `job_role` - Role performing workflow (e.g., 'insurance broker')
- `workflow_name` - Name of workflow (e.g., 'Quote generation')
- `manual_steps` - Array of manual steps in workflow
- `tools_used` - Array of current tools/software used
- `time_spent_hours` - Time per workflow execution
- `frequency` - hourly, daily, weekly, monthly
- `volume_per_period` - Number of executions per period
- `pain_point_description` - Detailed pain point description
- `automation_feasibility` - high, medium, low
- `genai_fit_score` - 0-100 score for GenAI automation suitability
- `data_types` - Array of data types involved (['pdf', 'email', 'excel'])
- `embedding` - Vector embedding for semantic search

**Example Query**:
```sql
SELECT * FROM find_automation_opportunities(
    naics_code := '541511',
    min_genai_score := 70
)
ORDER BY genai_fit_score DESC, time_spent_hours DESC;
```

---

## Helper Functions

### `search_voice_of_customer(query_embedding, naics_code, source_types, limit_count)`

Semantic similarity search on customer feedback.

**Parameters**:
- `query_embedding` - vector(1536) - Your query embedding
- `naics_code` - VARCHAR(10) - Filter by NAICS (NULL for all)
- `source_types` - TEXT[] - Filter by sources (NULL for all)
- `limit_count` - INTEGER - Max results (default 50)

**Returns**: Table with id, content, pain_point_category, complaint_keywords, similarity

### `aggregate_pain_points(naics_code)`

Aggregate and rank pain points by category for a NAICS code.

**Parameters**:
- `naics_code` - VARCHAR(10) - Target NAICS code

**Returns**: Table with pain_point_category, mention_count, all_keywords, negativity_score, example_content

### `get_recent_funding(naics_code, since_date)`

Get recent startup funding activity in an industry.

**Parameters**:
- `naics_code` - VARCHAR(10) - Target NAICS code
- `since_date` - DATE - Cutoff date (default 24 months ago)

**Returns**: Table with company_name, funding_stage, funding_amount_usd, funding_date, product_category, key_features

### `find_automation_opportunities(naics_code, min_genai_score)`

Find workflows with high GenAI automation potential.

**Parameters**:
- `naics_code` - VARCHAR(10) - Target NAICS code
- `min_genai_score` - INTEGER - Minimum GenAI fit score (default 60)

**Returns**: Table with workflow_name, job_role, genai_fit_score, automation_feasibility, time_spent_hours, frequency

---

## Views

### `industry_rag_summary`

Summary statistics across all RAG tables by NAICS code.

**Fields**:
- `naics_code` - Industry NAICS code
- `voice_of_customer_count` - Number of VOC entries
- `competitive_intel_count` - Number of competitive entries
- `workflow_intel_count` - Number of workflow entries
- `negative_sentiment_ratio` - Ratio of negative sentiment (0-1)
- `software_products_mentioned` - Count of distinct software products
- `total_recent_funding` - Total funding amount in industry
- `funded_startups_12mo` - Count of funded startups in last 12 months
- `avg_genai_fit_score` - Average GenAI fit score for workflows
- `high_automation_workflows` - Count of high-feasibility workflows

**Example Query**:
```sql
SELECT * FROM industry_rag_summary
WHERE voice_of_customer_count > 10
ORDER BY avg_genai_fit_score DESC, total_recent_funding DESC;
```

---

## Setup Instructions

### Prerequisites

1. PostgreSQL server running (version 12+)
2. Python 3.9+ with pip
3. Environment variables configured in `.env`

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `psycopg2-binary` - PostgreSQL adapter
- `openai` - For generating embeddings
- Other existing dependencies

### Step 2: Configure Environment

Add to your `.env` file:

```env
# PostgreSQL RAG Database
PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=meetup_events
PG_USER=meetup_app
PG_PASSWORD=your_password_here
```

### Step 3: Run Setup Script

```bash
python database/setup_database.py
```

**Expected Output**:
```
======================================================================
  PostgreSQL RAG Database Setup
======================================================================

[Step 1] Verifying Database Connection
----------------------------------------------------------------------
✅ Successfully connected to PostgreSQL
   Host: localhost:5432
   Database: meetup_events
   User: meetup_app
   Version: PostgreSQL 14.x

[Step 2] Executing 01_create_extension.sql
----------------------------------------------------------------------
✅ 01_create_extension.sql executed successfully

[Step 3] Executing 02_voice_of_customer.sql
----------------------------------------------------------------------
✅ 02_voice_of_customer.sql executed successfully

...

[Step 7] Verifying Database Setup
----------------------------------------------------------------------
✅ pgvector extension installed
✅ Table 'voice_of_customer' created (currently 0 rows)
✅ Table 'competitive_intelligence' created (currently 0 rows)
✅ Table 'workflow_intelligence' created (currently 0 rows)
✅ Function 'search_voice_of_customer()' created
✅ Function 'aggregate_pain_points()' created
✅ Function 'get_recent_funding()' created
✅ Function 'find_automation_opportunities()' created
✅ View 'industry_rag_summary' created

======================================================================
  Setup Complete!
======================================================================
✅ All database components created successfully
```

### Step 4: Verify Setup

```bash
# Connect to database
psql -h localhost -U meetup_app -d meetup_events

# List tables
\dt

# Describe voice_of_customer table
\d voice_of_customer

# List functions
\df

# Query summary view (will be empty initially)
SELECT * FROM industry_rag_summary;
```

---

## Data Population

**Important**: The user is responsible for populating the RAG database. The setup script only creates the schema.

### Populating `voice_of_customer`

**Data Sources**:
- Reddit posts from industry subreddits
- G2.com reviews for industry software
- Capterra reviews
- TrustRadius reviews
- LinkedIn discussions
- Industry forums

**Example Insert**:
```python
import openai
from psycopg2 import connect

# Generate embedding
content = "This insurance software is so clunky. Manual data entry everywhere..."
embedding = openai.Embedding.create(
    input=content,
    model="text-embedding-ada-002"
)['data'][0]['embedding']

# Insert
conn = connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO voice_of_customer (
        source_type, industry_naics, industry_keywords, title, content,
        software_mentioned, sentiment, pain_point_category,
        complaint_keywords, feature_gaps, url, embedding
    ) VALUES (
        'reddit', '524210', ARRAY['insurance', 'broker'],
        'Frustrated with our agency management system',
        %s, 'Applied Systems', 'negative', 'manual_process',
        ARRAY['clunky', 'manual', 'data entry'], ARRAY['automation', 'api'],
        'https://reddit.com/r/insurance/...', %s
    )
""", (content, embedding))

conn.commit()
```

### Populating `competitive_intelligence`

**Data Sources**:
- Crunchbase startup data
- Product Hunt launches
- VC firm portfolio pages
- TechCrunch funding announcements

**Example Insert**:
```python
company_desc = "AI-powered insurance workflow automation for brokers"
embedding = openai.Embedding.create(
    input=company_desc,
    model="text-embedding-ada-002"
)['data'][0]['embedding']

cursor.execute("""
    INSERT INTO competitive_intelligence (
        company_name, founded_year, employee_count_range, industry_naics,
        industry_vertical, target_customer, funding_stage,
        funding_amount_usd, funding_date, total_funding_usd,
        product_category, key_features, technology_stack,
        source_url, embedding
    ) VALUES (
        'InsureTech AI', 2022, '11-50', '524210', 'insurance tech',
        'insurance brokers', 'seed', 2500000, '2023-06-15', 2500000,
        'workflow_automation', ARRAY['quote_generation', 'document_processing'],
        ARRAY['ai', 'nlp', 'ocr'], 'https://crunchbase.com/...', %s
    )
""", (embedding,))
```

### Populating `workflow_intelligence`

**Data Sources**:
- Job descriptions (detailed responsibilities)
- Industry process documentation
- LinkedIn posts about daily workflows
- Industry blogs about operational challenges

**Example Insert**:
```python
workflow_desc = "Insurance brokers spend 3 hours daily generating quotes manually"
embedding = openai.Embedding.create(
    input=workflow_desc,
    model="text-embedding-ada-002"
)['data'][0]['embedding']

cursor.execute("""
    INSERT INTO workflow_intelligence (
        industry_naics, job_role, workflow_name, manual_steps, tools_used,
        time_spent_hours, frequency, volume_per_period,
        pain_point_description, automation_feasibility, genai_fit_score,
        data_types, data_volume_estimate, source_url, embedding
    ) VALUES (
        '524210', 'insurance broker', 'Quote Generation',
        ARRAY['Collect client info', 'Email carriers', 'Wait for responses', 'Manually compare'],
        ARRAY['Excel', 'Email', 'Applied Systems'],
        3.0, 'daily', 15,
        'Spend hours manually collecting and comparing quotes from multiple carriers',
        'high', 85,
        ARRAY['email', 'pdf', 'excel'], '100-500 quotes/month',
        'https://linkedin.com/...', %s
    )
""", (embedding,))
```

---

## Agent Integration

### Python Connection Module

See `src/rag_database.py` for the connection and query helper module.

**Example Usage**:
```python
from src.rag_database import RAGDatabase

# Initialize connection
rag_db = RAGDatabase()

# Generate query embedding
query_embedding = rag_db.generate_embedding(
    "What are the biggest complaints about insurance software?"
)

# Search voice of customer
results = rag_db.search_voice_of_customer(
    query_embedding=query_embedding,
    naics_code='524210',
    limit_count=10
)

for row in results:
    print(f"Similarity: {row['similarity']:.3f}")
    print(f"Content: {row['content'][:100]}...")
    print(f"Keywords: {row['complaint_keywords']}")
    print()
```

### Query Patterns for Agents

**Research Agent**:
- Before web search, query `search_voice_of_customer()` for known pain points
- Use top results to inform search query construction
- Cross-reference web findings with RAG data

**Technical Data Scientist Agent**:
- Query `find_automation_opportunities()` for high GenAI fit workflows
- Query `workflow_intelligence` for data type patterns
- Calculate total time savings potential across workflows

**Product Manager Agent**:
- Query `aggregate_pain_points()` for top pain point categories
- Query `voice_of_customer` for buyer persona patterns
- Analyze sentiment distribution by software/category

**Strategic Agent**:
- Query `get_recent_funding()` for competitive landscape
- Query `industry_rag_summary` for market activity signals
- Compare incumbent gaps with funded startup features

**Quantitative Agent**:
- Query `workflow_intelligence` for ROI calculations
- Calculate market size based on workflow volume × time savings × labor cost
- Use funding data to estimate competitive burn rates

---

## Performance Optimization

### Vector Search Performance

**IVFFlat Index**: All embedding columns have IVFFlat indexes with 100 lists
- Good for datasets up to 100K vectors
- For larger datasets, increase lists: `CREATE INDEX ... USING ivfflat ... WITH (lists = 200)`

**Query Optimization**:
```sql
-- Set probes for accuracy/speed tradeoff
SET ivfflat.probes = 10;  -- Default is 1 (faster but less accurate)

-- For production, tune based on dataset size
SET ivfflat.probes = 20;  -- More accurate but slower
```

### Array Search Performance

**GIN Indexes**: All TEXT[] columns have GIN indexes for fast array containment checks

**Efficient Query Patterns**:
```sql
-- Fast: Uses GIN index
WHERE complaint_keywords && ARRAY['clunky', 'slow'];

-- Fast: Uses GIN index
WHERE 'manual' = ANY(complaint_keywords);

-- Slower: Requires full scan
WHERE array_length(complaint_keywords, 1) > 3;
```

---

## Maintenance

### Rebuilding Indexes

If you add many rows, rebuild indexes for optimal performance:

```sql
-- Rebuild vector indexes
REINDEX INDEX idx_voc_embedding;
REINDEX INDEX idx_ci_embedding;
REINDEX INDEX idx_wi_embedding;

-- Vacuum analyze for statistics
VACUUM ANALYZE voice_of_customer;
VACUUM ANALYZE competitive_intelligence;
VACUUM ANALYZE workflow_intelligence;
```

### Backup

```bash
# Backup entire database
pg_dump -h localhost -U meetup_app meetup_events > backup.sql

# Backup only RAG tables
pg_dump -h localhost -U meetup_app -t voice_of_customer -t competitive_intelligence -t workflow_intelligence meetup_events > rag_backup.sql

# Restore
psql -h localhost -U meetup_app meetup_events < backup.sql
```

---

## Troubleshooting

### "pgvector extension not found"

```sql
-- Check if installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- If not, install (requires superuser)
CREATE EXTENSION vector;
```

### "Permission denied for table"

```sql
-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO meetup_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO meetup_app;
```

### "Slow vector search"

```sql
-- Increase probes (accuracy vs speed)
SET ivfflat.probes = 20;

-- Or rebuild index with more lists
DROP INDEX idx_voc_embedding;
CREATE INDEX idx_voc_embedding ON voice_of_customer
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 200);
```

### "Out of memory during indexing"

```sql
-- Increase maintenance_work_mem temporarily
SET maintenance_work_mem = '1GB';
CREATE INDEX ...;
RESET maintenance_work_mem;
```

---

## Schema Evolution

For schema changes, create migration files in `database/migrations/`:

**Example**: `database/migrations/001_add_confidence_score.sql`
```sql
-- Add confidence_score to voice_of_customer
ALTER TABLE voice_of_customer
ADD COLUMN confidence_score NUMERIC(3,2)
CHECK (confidence_score >= 0 AND confidence_score <= 1);

-- Add index
CREATE INDEX idx_voc_confidence ON voice_of_customer(confidence_score);

-- Update view
CREATE OR REPLACE VIEW industry_rag_summary AS
SELECT
    ...
    AVG(voc.confidence_score) as avg_confidence_score,
    ...
```

Run migrations manually:
```bash
psql -h localhost -U meetup_app meetup_events < database/migrations/001_add_confidence_score.sql
```

---

## Summary

**Database**: PostgreSQL with pgvector
**Tables**: 3 (voice_of_customer, competitive_intelligence, workflow_intelligence)
**Functions**: 4 helper functions
**Views**: 1 summary view
**Indexes**: 27 total (9 per table: B-tree, GIN, IVFFlat)

**Setup Time**: ~30 seconds
**Data Population**: Manual (user responsibility)
**Agent Integration**: Via `src/rag_database.py` module

For questions or issues, see main README.md or contact the development team.
