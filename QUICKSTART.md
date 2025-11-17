# Quick Start Guide

Get started analyzing NAICS industries in 5 minutes!

## Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## Step 2: Configure API Key

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenRouter API key
# Get one at: https://openrouter.ai/
```

Your `.env` should look like:
```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

## Step 3: Run Your First Analysis

```bash
python run_analysis.py 541511
```

This will analyze **NAICS 541511** (Custom Computer Programming Services).

Expected output:
```
🚀 Starting analysis for NAICS 541511...
This may take 5-10 minutes depending on the model's response time.

🔍 Researching NAICS 541511...
✅ Industry overview completed

📋 Mapping operational workflows...
✅ Workflow mapping completed

💻 Analyzing technology landscape...
✅ Technology analysis completed

🤖 Identifying AI & automation opportunities...
✅ Identified X opportunities

🔎 Finding hidden niches...
✅ Found X niche segments

🏆 Ranking opportunities...
✅ Ranked top 5 opportunities

📄 Generating final report...
✅ Analysis completed successfully!

💾 Saved JSON report: outputs/naics_541511_20241117_120000.json
💾 Saved Markdown report: outputs/naics_541511_20241117_120000.md
```

## Step 4: Review Results

Check the `outputs/` folder for:
- **JSON file**: Complete structured data
- **Markdown file**: Human-readable report

## What's in the Report?

Each analysis includes:

1. ✅ **Industry Overview** - Definition, segments, value chain
2. ✅ **Workflow Mapping** - Processes, tasks, pain points
3. ✅ **Technology Landscape** - Current software, gaps, vendors
4. ✅ **AI Opportunities** - Specific automation ideas
5. ✅ **Hidden Niches** - Overlooked market segments
6. ✅ **Top 5 Opportunities** - Ranked startup ideas

## Try More Industries

### High-Potential Industries for AI Disruption:

**Legal Services:**
```bash
python run_analysis.py 541110
```

**Accounting:**
```bash
python run_analysis.py 541211
```

**Medical Practices:**
```bash
python run_analysis.py 621111
```

**Construction:**
```bash
python run_analysis.py 236220
```

**Retail Bakeries:**
```bash
python run_analysis.py 311811
```

## Batch Analysis

Analyze multiple industries at once:

```bash
python batch_analyze.py example_naics_codes.txt
```

## Next Steps

- 📖 Read the full [README.md](README.md) for advanced features
- 🔍 Browse NAICS codes: https://www.census.gov/naics/
- 🚀 Customize prompts in `naics_analyzer.py` for your specific needs
- 💡 Use results to identify startup opportunities!

## Troubleshooting

**"OPENROUTER_API_KEY not found"**
→ Make sure `.env` file exists and contains your API key

**Analysis takes too long**
→ This is normal! Each analysis can take 5-10 minutes due to the depth of research

**JSON parsing errors**
→ The model occasionally returns malformed JSON. Re-run the analysis.

**Rate limiting**
→ Add delays between batch analyses (already included in batch script)

## Cost Estimate

Using OpenRouter with Sherlock-Think-Alpha:
- Approximate cost: $0.10 - $0.50 per NAICS analysis
- Depends on model pricing and response length

## Support

Need help?
- Check [README.md](README.md) for detailed docs
- Review example outputs in `outputs/` folder
- Open an issue on GitHub

---

**Happy analyzing! 🚀**
