# Phase 2 User Guide: Data-Vendor Opportunity Analysis

**Version**: 1.0
**Last Updated**: November 19, 2024
**Status**: Ready for Testing

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Understanding the Output](#understanding-the-output)
7. [Cost and Performance](#cost-and-performance)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Usage](#advanced-usage)

---

## Overview

Phase 2 analyzes 8-digit NAICS segments to discover **data-vendor business opportunities**. Unlike Phase 1 (which focused on GenAI automation), Phase 2 identifies opportunities to build data products and sell them to businesses.

### What Does Phase 2 Do?

For each 8-digit NAICS segment, the system:

1. **Discovers Data Needs**: What data do businesses in this segment need to operate?
2. **Maps Vendor Landscape**: Who currently provides this data? What are the gaps?
3. **Identifies Data Sources**: Where does the data originate? How accessible is it?
4. **Sizes the Market**: What's the TAM/SAM/SOM? Unit economics?
5. **Analyzes Moat**: How defensible is this opportunity?
6. **Designs Products**: What should the product look like?
7. **Ranks Opportunities**: Which opportunities are TIER_1 (pursue immediately)?

### Example Output

```
NAICS: 52411001 - Direct Property & Casualty Insurance Carriers

Top Opportunity: Real-time Worker's Compensation Rate Data
- Tier: TIER_1 (Pursue Immediately)
- Composite Score: 87.3/100
- TAM: $450M
- Opportunity Type: Aggregation (fragmented market)
- Key Moat: Exclusive data partnerships with state agencies
```

---

## Quick Start

### 1. Analyze a Single NAICS Code

```bash
python run_data_vendor_analysis.py \
  --naics 52411001 \
  --description "Direct Property and Casualty Insurance Carriers"
```

**Output:**
- Markdown report: `output/phase2/52411001_data_vendor_report.md`
- JSON results: `output/phase2/52411001_data_vendor_results.json`
- Database record: `data/opportunities.db`

**Time**: 6-10 minutes
**Cost**: $1.20-$1.80

### 2. Batch Process Multiple NAICS Codes

```bash
python run_data_vendor_analysis.py \
  --csv data/naics_8digit_codes.csv
```

**CSV Format:**
```csv
naics_8_digit,description
52411001,Direct Property and Casualty Insurance Carriers
52411002,Reinsurance Carriers
54151001,Computer Systems Design Services
```

**Output:**
- Individual reports for each NAICS
- Batch summary: `output/phase2/batch_summary_YYYYMMDD_HHMMSS.md`

---

## System Requirements

### Dependencies

```bash
# Python 3.8+
pip install langchain-openai langgraph duckduckgo-search tqdm chromadb
```

### API Keys

```bash
# Required
export OPENAI_API_KEY="sk-..."
```

### System Resources

- **RAM**: 2GB minimum (4GB recommended for large batches)
- **Disk**: 100MB per 1,000 segments analyzed
- **Network**: Stable internet for web searches

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/HerdingAI/industry_taxonomy_oportunity_finder.git
cd industry_taxonomy_oportunity_finder
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 4. Verify Installation

```bash
python run_data_vendor_analysis.py --help
```

---

## Usage

### Command-Line Options

```
python run_data_vendor_analysis.py [OPTIONS]

Options:
  --naics TEXT              Single 8-digit NAICS code
  --description TEXT        Segment description (required with --naics)
  --csv PATH                CSV file with NAICS codes
  --start INT               Start index for batch (default: 0)
  --end INT                 End index for batch (optional)
  --resume                  Skip already-analyzed NAICS
  --output PATH             Output directory (default: output/phase2)
```

### Common Use Cases

#### Single Analysis (Testing)

```bash
python run_data_vendor_analysis.py \
  --naics 52411001 \
  --description "Insurance Carriers"
```

**Use When**: Testing the system, analyzing a specific segment

#### Batch Processing (Production)

```bash
python run_data_vendor_analysis.py \
  --csv data/all_naics_codes.csv
```

**Use When**: Analyzing your full list of ~5,000 NAICS codes

#### Resume Interrupted Batch

```bash
python run_data_vendor_analysis.py \
  --csv data/all_naics_codes.csv \
  --resume
```

**Use When**: A batch run was interrupted and you want to skip already-analyzed segments

#### Process Specific Range

```bash
python run_data_vendor_analysis.py \
  --csv data/all_naics_codes.csv \
  --start 0 \
  --end 100
```

**Use When**: Processing in chunks (e.g., 100 segments at a time)

---

## Understanding the Output

### Markdown Report Structure

Each NAICS gets a comprehensive markdown report:

```markdown
# Data-Vendor Opportunity Report

## Executive Summary
- Total Opportunities: 12
- TIER_1 (Pursue Immediately): 3
- TIER_2 (Validate First): 5
- TIER_3 (Monitor): 4

### Top Opportunity
**Data Type**: Real-time Claims Pricing Data
**Composite Score**: 87.3/100
**TAM**: $450M
**Opportunity Type**: Aggregation

## Ranked Opportunities

### 1. Real-time Claims Pricing Data
**Tier**: TIER_1 | **Score**: 87.3/100 | **TAM**: $450M

**Key Strengths**:
- Fragmented market with no dominant player
- High willingness to pay ($15K-50K ARPU)
- Exclusive data source access possible

**Key Risks**:
- Regulatory compliance requirements
- Long sales cycles (6-12 months)

### 2. Historical Loss Ratio Benchmarks
**Tier**: TIER_1 | **Score**: 82.1/100 | **TAM**: $180M
...
```

### JSON Output Structure

```json
{
  "ranked_opportunities": [
    {
      "data_type": "Real-time Claims Pricing Data",
      "tier": "TIER_1",
      "composite_score": 87.3,
      "opportunity_type": "aggregation",
      "market_size_score": {
        "tam": 450000000,
        "sam": 180000000,
        "som_y3": 27000000
      },
      "moat_score": {
        "composite": 8.2,
        "exclusivity": 9,
        "network_effects": 7,
        "switching_costs": 8
      },
      "key_strengths": [...],
      "key_risks": [...]
    }
  ],
  "metadata": {
    "naics_8_digit": "52411001",
    "run_id": "phase2_52411001_a1b2c3d4",
    "total_execution_time_seconds": 456.2,
    "agent_execution_times": {
      "discover_needs": 78.3,
      "analyze_vendors": 92.1,
      ...
    }
  }
}
```

### Tier Classification

| Tier | Score | Meaning | Action |
|------|-------|---------|--------|
| **TIER_1** | 80-100 | Strong opportunity | Pursue immediately |
| **TIER_2** | 60-79 | Promising but needs validation | Validate assumptions first |
| **TIER_3** | 40-59 | Potential but challenging | Monitor for market changes |
| **PASS** | 0-39 | Not recommended | Deprioritize |

### Opportunity Types

- **White-Space**: No vendors exist, greenfield opportunity
- **Disruption**: Weak/expensive incumbents, ripe for disruption
- **Aggregation**: Fragmented market, opportunity to consolidate

### Composite Score Breakdown

The composite score (0-100) is weighted across 5 dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Market Size | 30% | TAM, growth rate, addressable market |
| Moat | 25% | Defensibility, exclusivity, barriers |
| Accessibility | 20% | Data source access, acquisition costs |
| Competition | 15% | Incumbent strength, market concentration |
| Unit Economics | 10% | ARPU, margins, LTV/CAC, payback period |

---

## Cost and Performance

### Per-Segment Metrics

| Metric | Estimate | Notes |
|--------|----------|-------|
| **Processing Time** | 6-10 minutes | Depends on web search latency |
| **Cost** | $1.20-$1.80 | OpenAI API calls (gpt-4o-mini) |
| **Web Searches** | 145-155 | DuckDuckGo (free) |
| **LLM Calls** | 7 main + parsing | One per agent |
| **Output Size** | 5-10 KB | Per NAICS |

### Batch Processing (5,000 segments)

| Metric | Estimate | Notes |
|--------|----------|-------|
| **Total Time** | 500-833 hours | 20-35 days if sequential |
| **Total Cost** | $6,000-$9,000 | Can be optimized |
| **Success Rate** | ~95% | Some may fail due to search limits |

**Recommendations:**
- Process in batches of 100-500 segments
- Use `--resume` to handle interruptions
- Monitor costs in first batch before scaling
- Consider parallel processing (future enhancement)

---

## Troubleshooting

### Common Issues

#### 1. "OPENAI_API_KEY environment variable not set"

**Solution:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Make it permanent:
```bash
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### 2. "CSV must have columns: naics_8_digit, description"

**Solution:**
Ensure your CSV has exactly these column names:
```csv
naics_8_digit,description
52411001,Insurance Carriers
```

#### 3. "DuckDuckGo rate limit exceeded"

**Cause**: Too many searches too quickly

**Solution**: The system has exponential backoff built-in. If this persists:
- Increase delays in agent code
- Process smaller batches
- Wait 1 hour and resume

#### 4. "Module not found" errors

**Solution:**
```bash
pip install langchain-openai langgraph duckduckgo-search tqdm chromadb
```

#### 5. Analysis fails with "timeout" errors

**Cause**: Network issues or slow LLM responses

**Solution**:
- Check internet connection
- Use `--resume` to skip already-analyzed segments
- Increase timeout in code if needed

---

## Advanced Usage

### Programmatic Access

```python
from langchain_openai import ChatOpenAI
from src.data_vendor_analyzer import DataVendorAnalyzer
from src.audit_database import AuditDatabase

# Initialize
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
audit_db = AuditDatabase("data/audit.db")
analyzer = DataVendorAnalyzer(llm, audit_db)

# Analyze single NAICS
result = analyzer.analyze(
    naics_8_digit="52411001",
    segment_description="Insurance Carriers"
)

# Access results
opportunities = result['ranked_opportunities']
tier1 = [opp for opp in opportunities if opp['tier'] == 'TIER_1']

print(f"Found {len(tier1)} TIER_1 opportunities")
for opp in tier1:
    print(f"- {opp['data_type']}: ${opp['market_size_score']['tam']:,.0f} TAM")
```

### Database Queries

```python
from src.database import DatabaseManager

db = DatabaseManager("data/opportunities.db")

# Get all TIER_1 opportunities across all NAICS
tier1_opps = db.get_all_tier1_opportunities()

# Compare multiple NAICS
comparison = db.compare_naics_opportunities([
    "52411001",
    "52411002",
    "54151001"
])

# Get Phase 2 summary statistics
summary = db.get_phase2_summary()
print(f"Total analyzed: {summary['total_analyzed']}")
print(f"TIER_1 opportunities: {summary['total_tier1_opps']}")
print(f"Cumulative TAM: ${summary['cumulative_tam']:,.0f}")
```

### Custom Output Directory

```bash
python run_data_vendor_analysis.py \
  --csv data/naics.csv \
  --output ~/my_analysis_results
```

### Processing Specific NAICS Subsets

```python
# Create a filtered CSV
import pandas as pd

# Load full list
df = pd.read_csv('data/all_naics.csv')

# Filter to specific sector (e.g., Finance = 52*)
finance = df[df['naics_8_digit'].str.startswith('52')]
finance.to_csv('data/finance_naics.csv', index=False)

# Process just finance sector
```

```bash
python run_data_vendor_analysis.py --csv data/finance_naics.csv
```

---

## Best Practices

### For Testing
1. Start with 1-3 NAICS codes you understand well
2. Review output quality before scaling
3. Validate cost estimates match expectations
4. Check that tier classifications make sense

### For Production
1. Process in batches of 100-500 segments
2. Use `--resume` to handle interruptions gracefully
3. Monitor first batch closely for issues
4. Review aggregate results for patterns
5. Keep original analysis reports for audit trail

### For Cost Optimization
1. Use gpt-4o-mini (current default) not gpt-4
2. Process during off-peak hours if possible
3. Consider caching search results (future enhancement)
4. Monitor per-segment costs and adjust if needed

### For Quality
1. Review TIER_1 opportunities manually
2. Validate market size estimates with external data
3. Cross-reference competitor analysis with your knowledge
4. Use confidence scores to filter low-quality results

---

## Support and Feedback

### Getting Help

1. Check this user guide first
2. Review `PHASE_2_CHECKPOINT_REVIEW.md` for technical details
3. Check `PHASE_2_IMPLEMENTATION_PLAN.md` for architecture
4. Open GitHub issue with details

### Reporting Issues

When reporting issues, include:
- Command you ran
- Error message (full stack trace)
- NAICS code that failed
- Contents of run log if available

### Feature Requests

Future enhancements under consideration:
- Parallel processing for faster batches
- Cost optimization options
- Custom scoring weights
- Export to Excel/CSV
- Comparison dashboard
- Real-time progress monitoring

---

## Appendix

### File Locations

```
project/
├── run_data_vendor_analysis.py      # Main entry point
├── src/
│   ├── data_vendor_analyzer.py      # Orchestrator
│   ├── data_needs_researcher.py     # Agent 1
│   ├── vendor_intelligence_agent.py # Agent 2
│   ├── data_source_mapper.py        # Agent 3
│   ├── data_market_sizer.py         # Agent 4
│   ├── data_moat_analyzer.py        # Agent 5
│   ├── data_product_designer.py     # Agent 6
│   ├── data_opportunity_synthesizer.py # Agent 7
│   ├── database.py                  # Database layer
│   └── audit_database.py            # Audit tracking
├── data/
│   ├── opportunities.db             # Results database
│   ├── audit.db                     # Audit logs
│   └── naics_8digit_codes.csv       # Your input CSV
└── output/
    └── phase2/
        ├── {naics}_data_vendor_report.md
        ├── {naics}_data_vendor_results.json
        └── batch_summary_*.md
```

### Version History

- **v1.0** (Nov 19, 2024): Initial release, Phase 2A complete

---

**Ready to start?** Try analyzing your first NAICS code:

```bash
python run_data_vendor_analysis.py \
  --naics 52411001 \
  --description "Direct Property and Casualty Insurance Carriers"
```

Good luck discovering data-vendor opportunities! 🚀
