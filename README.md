# NAICS Industry Taxonomy & AI Opportunity Finder

An AI-powered agent system that systematically analyzes U.S. industries (at the 6-digit NAICS level) to discover hidden automation and GenAI opportunities.

## Overview

This tool uses **LangGraph** and **OpenRouter's Sherlock-Think-Alpha** model to perform deep industry analysis, identifying:

- Industry hierarchies and operational workflows
- Technology gaps and manual processes
- Specific AI/automation opportunities
- Hidden niche markets and underserved segments
- Top 5 ranked startup opportunities per industry

Perfect for entrepreneurs, investors, and researchers seeking to discover "unknown unknowns" in unfamiliar industries.

## Features

- 🔍 **Comprehensive Industry Research**: Deep analysis of industry structure, value chains, and market dynamics
- 📋 **Workflow Mapping**: Detailed breakdown of operational processes and pain points
- 💻 **Technology Landscape Analysis**: Current software, vendors, and adoption gaps
- 🤖 **AI Opportunity Identification**: Specific automation opportunities with implementation details
- 🎯 **Niche Discovery**: Uncover hidden segments and overlooked markets
- 🏆 **Ranked Opportunities**: Top 5 viable startup ideas with competitive analysis
- 📊 **Structured Outputs**: JSON and Markdown reports for each analysis

## Architecture

The system uses a **LangGraph workflow** with 7 sequential nodes:

1. **Research Industry** → Gather foundational information
2. **Map Workflows** → Identify operational processes and pain points
3. **Analyze Technology** → Assess current tech landscape and gaps
4. **Identify Opportunities** → Find specific AI/automation use cases
5. **Find Niches** → Discover hidden markets and segments
6. **Rank Opportunities** → Select and rank top 5 opportunities
7. **Generate Report** → Produce comprehensive output

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd industry_taxonomy_oportunity_finder
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here  # Optional but recommended
```

**Get API Keys:**
- OpenRouter: https://openrouter.ai/
- Tavily (optional, for web research): https://tavily.com/

## Usage

### Single NAICS Code Analysis

**Interactive mode:**
```bash
python run_analysis.py
```

**Command-line mode:**
```bash
python run_analysis.py 541511
```

Example NAICS codes:
- `541511` - Custom Computer Programming Services
- `541512` - Computer Systems Design Services
- `621111` - Offices of Physicians (except Mental Health)
- `236220` - Commercial and Institutional Building Construction
- `311811` - Retail Bakeries

### Batch Analysis

Create a file with one NAICS code per line (e.g., `naics_codes.txt`):

```
541511
541512
541513
```

Run batch analysis:

```bash
python batch_analyze.py naics_codes.txt
```

### Direct Python Usage

```python
from naics_analyzer import NAICSAnalyzer

# Initialize analyzer
analyzer = NAICSAnalyzer()

# Analyze a NAICS code
result = analyzer.analyze("541511")

# Save reports
json_file, md_file = analyzer.save_report(result)

# Access results
print(result['industry_overview'])
print(result['top_opportunities'])
```

## Output

Analysis results are saved in the `outputs/` directory:

- **JSON file**: `naics_<code>_<timestamp>.json` - Full structured data
- **Markdown file**: `naics_<code>_<timestamp>.md` - Human-readable report

### Report Structure

Each report includes:

1. **Industry Overview**
   - Definition
   - Sub-segments
   - Value chain
   - Market size
   - Major players

2. **Operational Workflow Mapping**
   - End-to-end processes
   - Daily tasks and jobs
   - Pain points and bottlenecks
   - Tools and systems used

3. **Technology Landscape**
   - Current software categories
   - Major vendors
   - Adoption levels
   - Technology gaps
   - Barriers to adoption

4. **AI & Automation Opportunities**
   - Workflow step to automate
   - Current vs. automated state
   - Technology solution
   - Expected value
   - Target customers
   - Why unsolved
   - Implementation difficulty
   - Competitive advantages

5. **Hidden Niches**
   - Specialized sub-segments
   - Manual micro-workflows
   - Underserved technology segments
   - Low-tech maturity pockets

6. **Top 5 Startup Opportunities**
   - Detailed descriptions
   - Target markets
   - Value propositions
   - Competitive moats
   - Go-to-market strategies
   - Risk factors

## Configuration

### Model Configuration

Default model: `openrouter/sherlock-think-alpha`

To use a different model, update `.env`:

```env
OPENROUTER_MODEL=openrouter/anthropic/claude-3.5-sonnet
```

### Customizing Analysis Depth

Edit `naics_analyzer.py` to modify:

- Temperature (creativity): `temperature=0.7`
- Max tokens (response length): `max_tokens=4000`
- Prompt templates in each node method

## NAICS Code Reference

Find NAICS codes at: https://www.census.gov/naics/

**Popular industries for AI opportunities:**

- **Professional Services**: 541xxx
- **Healthcare**: 621xxx, 622xxx
- **Construction**: 236xxx, 237xxx
- **Manufacturing**: 311xxx - 339xxx
- **Finance & Insurance**: 522xxx, 524xxx
- **Real Estate**: 531xxx
- **Legal Services**: 541110
- **Accounting**: 541211

## Troubleshooting

### API Key Errors

```
ValueError: OPENROUTER_API_KEY not found in environment variables
```

**Solution**: Ensure `.env` file exists and contains valid API key

### JSON Parsing Errors

The analyzer includes robust JSON extraction that handles markdown code blocks. If you still encounter parsing errors, check the model's output format.

### Rate Limiting

For batch analysis, the script includes 10-second delays between requests. Adjust in `batch_analyze.py` if needed.

### Timeout Issues

Large industries may take longer to analyze. Increase timeout in OpenAI client initialization if needed.

## Advanced Usage

### Custom Workflow Modifications

The LangGraph workflow is modular. To add custom analysis steps:

1. Add a new method in `NAICSAnalyzer` class
2. Add node to workflow in `_build_graph()`
3. Define edges to/from the new node

Example:

```python
def custom_analysis(self, state: AnalysisState) -> AnalysisState:
    # Your custom logic here
    return state

# In _build_graph():
workflow.add_node("custom_analysis", self.custom_analysis)
workflow.add_edge("rank_opportunities", "custom_analysis")
workflow.add_edge("custom_analysis", "generate_report")
```

### Integrating Web Search

To add real-time web research (requires Tavily API):

```python
from langchain_community.tools import TavilySearchResults

search = TavilySearchResults(api_key=os.getenv("TAVILY_API_KEY"))
results = search.invoke({"query": f"NAICS {naics_code} industry trends"})
```

### Exporting to Database

Save results to a database:

```python
import sqlite3

def save_to_db(analysis_result):
    conn = sqlite3.connect('naics_analysis.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO analyses (naics_code, industry_name, analysis_json, created_at)
        VALUES (?, ?, ?, ?)
    ''', (
        analysis_result['naics_code'],
        analysis_result['industry_name'],
        json.dumps(analysis_result),
        datetime.now()
    ))

    conn.commit()
    conn.close()
```

## Roadmap

- [ ] Add parallel analysis for faster batch processing
- [ ] Integrate real-time web search for current data
- [ ] Add visualization of workflow diagrams
- [ ] Create web UI for interactive exploration
- [ ] Build opportunity comparison matrix
- [ ] Add export to PDF/PowerPoint
- [ ] Implement caching to avoid re-analyzing same NAICS codes

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[Add your license here]

## Support

For issues or questions:
- Open a GitHub issue
- Check OpenRouter status: https://status.openrouter.ai/

## Citation

If you use this tool in research, please cite:

```
Industry Taxonomy & AI Opportunity Finder
Using LangGraph and OpenRouter Sherlock-Think-Alpha
[Your Name/Organization], 2024
```

---

**Happy Opportunity Hunting! 🚀**
