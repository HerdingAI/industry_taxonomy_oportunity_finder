# Strategic Market Intelligence System
## AI-Powered Industry Analysis for Business Opportunity Discovery

**Think like an MBA. Analyze like a data scientist. Write like Hemingway.**

---

## Overview

A multi-agent research system that systematically analyzes U.S. industries (6-digit NAICS codes) to identify high-value AI and automation opportunities.

**Current Focus**: Professional Services (54xxxx) - 43 industries from legal to veterinary services

### What Makes This Different

**Depth ≠ Length**
- Every sentence earns its place
- Numbers over adjectives
- Insights over descriptions
- "Why" and "So what?" over "What"

**MBA + Data Science**
- Porter's Five Forces (scored 0-100)
- Value chain analysis
- Quantitative opportunity scoring
- Unit economics modeling
- Risk-adjusted valuations

**Real Data, Not Hallucinations**
- DuckDuckGo web search
- Census Bureau data
- BLS employment statistics
- Confidence intervals on all estimates

**Learning System**
- Vector database (ChromaDB) for semantic search
- SQLite for structured queries
- Each analysis improves the next

---

## Architecture

### 4-Agent Pipeline

```
Research Agent → Strategic Analyst → Quantitative Analyst → Synthesizer
      ↓                ↓                     ↓                  ↓
  Web search     Porter's Forces      Opportunity           Concise
  Census data    Value chain          scoring              report
  BLS stats      Positioning          Unit economics       (<3 pages)
```

### Agent Breakdown

**1. Research Agent** (Facts, not opinions)
- DuckDuckGo search for market data
- Extracts: market size, growth, establishments, employment
- Identifies: pain points, tech stack, competitive dynamics
- Output: Structured JSON with confidence scores

**2. Strategic Analyst** (MBA frameworks)
- Porter's Five Forces (scored 0-100 per force)
- Strategic positioning analysis
- Value chain opportunity identification
- Output: Insight-dense strategic assessment

**3. Quantitative Analyst** (Data science)
- TAM/SAM/SOM market sizing
- Unit economics (ARPU, LTV, CAC, margins)
- Multi-criteria opportunity scoring (0-100)
- Risk-adjusted valuations
- Output: Numbers with assumptions and confidence intervals

**4. Synthesizer** (Concise reporting)
- Combines all analysis
- Max 2-3 pages per industry
- Every sentence must add value
- Output: Actionable markdown report

### Data Storage

**SQLite**: Industries, opportunities, Porter's scores, metrics
**ChromaDB**: Vector search across research, insights, opportunities

---

## Installation

### 1. Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenRouter API key
```

Your `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
OPENROUTER_MODEL=openrouter/sherlock-think-alpha
```

**Get API key**: https://openrouter.ai/

### 3. Verify Setup

```bash
python test_setup.py
```

---

## Usage

### Analyze Single Industry

```bash
python analyze.py 541511
```

**Output**:
```markdown
## NAICS 541511: Custom Computer Programming Services

**Score**: 67/100 | **Confidence**: 76% | **Verdict**: MODERATE OPPORTUNITY

### Market Reality
- $185.1B market, 8.2% CAGR
- 89,400 firms (HHI=182: hyper-fragmented)
- Avg firm revenue: $2.1M
- Key trends: AI code generation, offshore competition, cloud migration
- Digital maturity: high

### Strategic Insight
**Porter's Analysis**: Unattractive for generalists; attractive for vertical specialists with moats

**Winning strategy**: Vertical specialization with proprietary data moats
**Avoid**: Generalist hourly billing

### Top Opportunity: Healthcare-Specific AI Code Generator (Score: 85/100)

**The Play**: HL7/FHIR-native code assistant with built-in HIPAA compliance

**Numbers**:
- TAM $8.2B, SAM $2.1B, SOM Y3 $105M
- $7,188 ARPU, 87% margin, 7.0:1 LTV:CAC

**Why Now**: GenAI crossed quality threshold; HIPAA-compliant code gen unsolved
**Why Unsolved**: Requires rare combo of healthcare domain + AI expertise
**Moat**: Compliance library + health system partnerships (data flywheel)

**Key Risk**: Epic bundles competing feature (35% probability)
```

### Analyze Entire Sector

```bash
python analyze.py --sector 54
```

Analyzes all 43 Professional Services industries:
- Law firms, CPAs, engineers, architects
- Software development, consulting
- Advertising, marketing, design
- R&D, testing labs, veterinary

**Duration**: ~3-5 minutes per industry (~3 hours total)

### List Analyzed Industries

```bash
python analyze.py --list
```

```
NAICS    Name                                     Score   Opps
----------------------------------------------------------------
541511   Custom Computer Programming Services     67      3
541211   Offices of Certified Public Accountants  72      4
541110   Offices of Lawyers                       58      2
...
```

### Show Top Opportunities

```bash
python analyze.py --top 20
```

### Search Opportunities

```bash
python analyze.py --search "healthcare AI automation"
```

Semantic search across all identified opportunities using vector database.

---

## Example Output

See `MVP_DESIGN.md` for detailed example of a complete industry analysis.

**Key metrics provided**:
- Market size (TAM/SAM/SOM with assumptions)
- Growth rates and trends
- Porter's Five Forces scores
- HHI concentration index
- Digital maturity assessment
- Opportunity scores (0-100 with confidence)
- Unit economics (ARPU, LTV:CAC, margins, payback)
- Risk-adjusted valuations

---

## Professional Services Industries

43 industries in NAICS sector 54:

**Legal & Accounting** (541110-541219)
- Lawyers, CPAs, tax preparers, payroll services

**Architecture & Engineering** (541310-541380)
- Architects, engineers, surveyors, testing labs

**Specialized Design** (541410-541490)
- Interior, industrial, graphic design

**Computer Services** (541511-541519)
- Programming, systems design, IT consulting

**Management Consulting** (541611-541690)
- Strategy, HR, marketing, environmental

**R&D** (541713-541720)
- Nanotech, biotech, physical sciences, social sciences

**Advertising & Marketing** (541810-541910)
- Ad agencies, PR, media buying, market research

**Other Professional** (541920-541990)
- Photography, translation, veterinary

---

## Output Files

### Markdown Reports (`outputs/`)
- Concise analysis (<3 pages)
- All signal, no noise
- Numbers with sources
- Saved as: `naics_<code>_<timestamp>.md`

### SQLite Database (`data/intelligence.db`)
- Industries table (market data, scores)
- Opportunities table (sized, scored, ranked)
- Porter's forces table
- Pain points, tech usage

### Vector Database (`data/chromadb/`)
- Research findings
- Strategic insights
- Opportunity descriptions
- Enables semantic search

---

## Technical Details

**Tech Stack**:
- LangGraph: Agent orchestration
- OpenRouter: LLM inference (Sherlock-Think-Alpha)
- DuckDuckGo Search: Free web research (no API key!)
- ChromaDB: Vector storage & semantic search
- SQLite: Structured data storage
- Pandas/NumPy: Data analysis

**Cost**: ~$0.10-0.50 per industry analysis

**Speed**: ~3-5 minutes per industry

**Data Sources**:
- U.S. Census Bureau (NAICS definitions, establishment counts)
- Bureau of Labor Statistics (employment, wages)
- Web search results (market reports, news, trends)
- Industry publications (via search)

---

## Design Philosophy

### Depth ≠ Length

**Bad**: "This is a large and growing market with many opportunities for innovation and disruption through the application of artificial intelligence and machine learning technologies."

**Good**: "$185B, 8.2% CAGR. Fragmented (HHI=182) but commoditizing. Opportunity: Vertical AI with compliance moats."

### Every Number Needs Context

**Bad**: "TAM is $8.2B"

**Good**: "$185B industry × 4.4% applicable to this workflow = $8.2B TAM"

### Strategic Insight Over Description

**Bad**: "There is high competition in this market"

**Good**: "Fragmented (HHI=182) but commoditizing. Price war at low-end; specialization wins high-end."

---

## Database Schema

### Key Tables

```sql
-- Analyzed industries
industries(naics_code, name, market_size_usd, growth_rate,
           hhi_index, overall_score, confidence, ...)

-- Scored opportunities
opportunities(naics_code, title, opportunity_score, confidence,
              tam_usd, sam_usd, arpu, ltv_cac_ratio, key_moat, ...)

-- Porter's Five Forces
porters_forces(naics_code, competitive_rivalry_score,
               new_entrant_threat_score, ...)

-- Pre-built views
top_opportunities  -- Ranked by risk-adjusted score
industry_summary   -- Aggregated metrics
```

### Vector Collections

```python
# Semantic search across:
research_collection      # Market research findings
opportunities_collection # Business opportunities
insights_collection      # Strategic insights
```

---

## Extensibility

### Add New Data Sources

```python
# In research_agent.py
def _gather_census_data(self, naics_code):
    # Add Census Bureau API integration
    pass
```

### Customize Scoring Weights

```python
# In quantitative_agent.py
scoring_weights = {
    'market_size': 0.30,      # Adjust these
    'growth': 0.15,
    'margin': 0.20,
    'defensibility': 0.20,
    'competition': 0.15
}
```

### Add New MBA Frameworks

```python
# In strategic_agent.py
def _analyze_business_model_canvas(self, data):
    # Add new strategic framework
    pass
```

---

## Roadmap

**Phase 2** (expand scope):
- [ ] Healthcare sector (62xxxx)
- [ ] Construction (23xxxx)
- [ ] Manufacturing (31-33)

**Phase 3** (deeper analysis):
- [ ] Real-time Census/BLS API integration
- [ ] Funding data (Crunchbase API)
- [ ] Competitive intelligence (web scraping)
- [ ] Trend detection across industries

**Phase 4** (tooling):
- [ ] Web dashboard for exploration
- [ ] Automated sector reports
- [ ] Opportunity comparison matrix
- [ ] Investment thesis generator

---

## Documentation

- `MVP_DESIGN.md` - Complete system design and philosophy
- `ARCHITECTURE_PROPOSAL.md` - Full v2 system architecture
- `COMPARISON.md` - v1 vs v2 comparison
- `QUICKSTART.md` - 5-minute getting started guide

---

## Contributing

Contributions welcome! Focus areas:
- Additional data source integrations
- New strategic frameworks
- Improved scoring models
- Industry-specific analysis templates

---

## License

[Add your license]

---

## Support

**Issues**: Open a GitHub issue
**API Status**: https://status.openrouter.ai/
**NAICS Codes**: https://www.census.gov/naics/

---

**Built with**: LangGraph · OpenRouter · ChromaDB · DuckDuckGo Search

**Philosophy**: Insight density > word count. Numbers > adjectives. Why > what.

**Goal**: Systematically discover AI opportunities across every U.S. industry.

---

**Ready to discover opportunities?**

```bash
python analyze.py 541511
```
