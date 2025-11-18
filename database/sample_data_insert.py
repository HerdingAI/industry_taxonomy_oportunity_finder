#!/usr/bin/env python3
"""
Sample Data Insertion Examples

This script demonstrates how to populate the RAG database with sample data.
Use this as a template for your own data population scripts.

Usage:
    python database/sample_data_insert.py
"""

from datetime import date
from src.rag_database import RAGDatabase

print("=" * 70)
print("  Sample Data Insertion Examples")
print("=" * 70)
print("\nThis script shows how to insert data into each RAG table.")
print("Review the code to see the exact format required.\n")

# Initialize database connection
db = RAGDatabase()

# Example 1: Insert voice of customer data
print("[Example 1] Inserting Voice of Customer Data")
print("-" * 70)

voc_data = {
    'source_type': 'reddit',
    'industry_naics': '524210',  # Insurance Agencies and Brokerages
    'industry_keywords': ['insurance', 'broker', 'agency'],
    'title': 'Frustrated with our agency management system',
    'content': (
        "Our insurance agency has been using Applied Epic for years and it's "
        "incredibly clunky. Everything is manual - we have to copy-paste data "
        "between systems, there's no API integration, and the UI looks like "
        "it's from 2005. We waste hours every day on data entry that should "
        "be automated. Looking for alternatives but everything in the insurance "
        "space seems equally outdated."
    ),
    'software_mentioned': 'Applied Epic',
    'sentiment': 'negative',
    'pain_point_category': 'manual_process',
    'complaint_keywords': ['clunky', 'manual', 'outdated', 'no API', 'data entry'],
    'feature_gaps': ['automation', 'modern UI', 'API integration', 'workflow automation'],
    'url': 'https://reddit.com/r/InsurancePros/example123'
}

try:
    voc_id = db.insert_voice_of_customer(voc_data)
    print(f"✅ Inserted voice of customer entry (ID: {voc_id})")
    print(f"   Source: {voc_data['source_type']}")
    print(f"   Industry: {voc_data['industry_naics']}")
    print(f"   Software: {voc_data['software_mentioned']}")
    print(f"   Pain points: {', '.join(voc_data['complaint_keywords'][:3])}...")
except Exception as e:
    print(f"❌ Failed to insert: {e}")

# Example 2: Insert competitive intelligence data
print("\n[Example 2] Inserting Competitive Intelligence Data")
print("-" * 70)

ci_data = {
    'company_name': 'InsureTech AI',
    'founded_year': 2022,
    'employee_count_range': '11-50',
    'industry_naics': '524210',
    'industry_vertical': 'insurance technology',
    'target_customer': 'independent insurance agencies and brokers',
    'funding_stage': 'seed',
    'funding_amount_usd': 2500000,
    'funding_date': date(2023, 6, 15),
    'total_funding_usd': 2500000,
    'product_category': 'workflow_automation',
    'key_features': [
        'automated quote generation',
        'document OCR and parsing',
        'carrier API integration',
        'AI-powered client matching'
    ],
    'technology_stack': ['ai', 'nlp', 'ocr', 'api'],
    'competitors': ['Applied Systems', 'Vertafore', 'EZLynx'],
    'source_url': 'https://crunchbase.com/organization/insuretech-ai'
}

try:
    ci_id = db.insert_competitive_intelligence(ci_data)
    print(f"✅ Inserted competitive intelligence entry (ID: {ci_id})")
    print(f"   Company: {ci_data['company_name']}")
    print(f"   Funding: ${ci_data['funding_amount_usd']:,} ({ci_data['funding_stage']})")
    print(f"   Target: {ci_data['target_customer']}")
    print(f"   Features: {', '.join(ci_data['key_features'][:2])}...")
except Exception as e:
    print(f"❌ Failed to insert: {e}")

# Example 3: Insert workflow intelligence data
print("\n[Example 3] Inserting Workflow Intelligence Data")
print("-" * 70)

wi_data = {
    'industry_naics': '524210',
    'job_role': 'insurance broker',
    'workflow_name': 'Quote Generation and Comparison',
    'manual_steps': [
        'Collect client information via phone/email',
        'Manually enter data into each carrier portal',
        'Wait 24-48 hours for quote responses',
        'Copy quotes into Excel spreadsheet',
        'Manually compare coverage and pricing',
        'Create presentation for client'
    ],
    'tools_used': ['Excel', 'Email', 'Applied Epic', 'Multiple carrier portals'],
    'time_spent_hours': 3.5,
    'frequency': 'daily',
    'volume_per_period': 12,  # 12 quotes per day
    'pain_point_description': (
        'Insurance brokers spend 3-4 hours daily generating and comparing quotes '
        'from multiple carriers. The process is entirely manual - data must be '
        're-entered into each carrier system, responses come back via email or '
        'portal, and comparison requires manually building Excel spreadsheets. '
        'No automation exists, and the process hasn\'t changed in 20 years.'
    ),
    'automation_feasibility': 'high',
    'genai_fit_score': 85,
    'data_types': ['email', 'pdf', 'excel', 'web_forms'],
    'data_volume_estimate': '200-300 quotes per month per broker',
    'source_url': 'https://linkedin.com/posts/insurance-broker-daily-workflow'
}

try:
    wi_id = db.insert_workflow_intelligence(wi_data)
    print(f"✅ Inserted workflow intelligence entry (ID: {wi_id})")
    print(f"   Workflow: {wi_data['workflow_name']}")
    print(f"   Role: {wi_data['job_role']}")
    print(f"   Time: {wi_data['time_spent_hours']} hours × {wi_data['volume_per_period']}/day")
    print(f"   GenAI Fit: {wi_data['genai_fit_score']}/100")
    print(f"   Automation: {wi_data['automation_feasibility']}")
except Exception as e:
    print(f"❌ Failed to insert: {e}")

# Example 4: Query the data we just inserted
print("\n[Example 4] Querying Inserted Data")
print("-" * 70)

try:
    # Get industry summary
    summary = db.get_industry_summary(naics_code='524210')
    if summary:
        s = summary[0]
        print(f"✅ Industry Summary for NAICS 524210:")
        print(f"   VOC entries: {s.get('voice_of_customer_count', 0)}")
        print(f"   Competitive entries: {s.get('competitive_intel_count', 0)}")
        print(f"   Workflow entries: {s.get('workflow_intel_count', 0)}")
        print(f"   Avg GenAI fit: {s.get('avg_genai_fit_score', 0):.1f}/100")
    else:
        print("⚠️  No summary data found")

    # Search for pain points
    pain_points = db.aggregate_pain_points(naics_code='524210')
    if pain_points:
        print(f"\n✅ Top Pain Points:")
        for pp in pain_points[:3]:
            print(f"   - {pp['pain_point_category']}: {pp['mention_count']} mentions")
            print(f"     Keywords: {', '.join(pp['all_keywords'][:5])}")
    else:
        print("⚠️  No pain points found")

    # Find automation opportunities
    opportunities = db.find_automation_opportunities(
        naics_code='524210',
        min_genai_score=70
    )
    if opportunities:
        print(f"\n✅ High-Value Automation Opportunities:")
        for opp in opportunities[:3]:
            print(f"   - {opp['workflow_name']} ({opp['genai_fit_score']}/100)")
            print(f"     Time: {opp['time_spent_hours']} hrs {opp['frequency']}")
    else:
        print("⚠️  No automation opportunities found")

except Exception as e:
    print(f"❌ Query failed: {e}")

# Example 5: Semantic search
print("\n[Example 5] Semantic Search")
print("-" * 70)

try:
    query_text = "software complaints about manual data entry and lack of automation"
    results = db.search_voice_of_customer(
        query_text=query_text,
        naics_code='524210',
        limit_count=3
    )

    if results:
        print(f"✅ Search results for: '{query_text}'")
        print(f"   Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"   {i}. Similarity: {result['similarity']:.3f}")
            print(f"      Content: {result['content'][:100]}...")
            print(f"      Keywords: {', '.join(result.get('complaint_keywords', [])[:3])}")
            print()
    else:
        print("⚠️  No search results found")

except Exception as e:
    print(f"❌ Search failed: {e}")

# Final summary
print("=" * 70)
print("  Sample Data Insertion Complete!")
print("=" * 70)
print("\nYou can now:")
print("  1. View data in PostgreSQL: psql -d meetup_events")
print("  2. Query using Python: from src.rag_database import RAGDatabase")
print("  3. Build more data population scripts based on these examples")
print("\nSee database/README.md for more query examples.")
print("=" * 70)
