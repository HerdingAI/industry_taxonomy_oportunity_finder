#!/usr/bin/env python3
"""Test to see what AI opportunities are generated in web-search-only mode"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Mock research data (simulating web search results)
mock_research_data = {
    'naics_code': '541511',
    'industry_name': 'Custom Computer Programming Services',
    'market_size_usd': 185000000000,
    'growth_rate': 0.082,
    'pain_points': [
        {"pain": "Manual project scoping leading to 15-20% cost overruns", "frequency": "high", "cost_impact": "15-20% revenue lost"},
        {"pain": "Time-consuming code reviews", "frequency": "medium", "cost_impact": "10-15% developer productivity"},
        {"pain": "Client requirement gathering inefficiency", "frequency": "high", "cost_impact": "20+ hours per project"}
    ],
    'manual_processes': [
        'requirements gathering through meetings and documents',
        'manual code review and quality assurance',
        'project estimation and scoping',
        'client communication and status reporting'
    ],
    'digital_maturity': 'high',
    'key_trends': ['AI code generation', 'remote work'],
    'hhi_index': 182,
    'market_concentration': 'fragmented',
    'confidence': 0.75
}

print("Testing AI Opportunity Generation")
print("="*70)
print("\nInput Pain Points:")
for i, pp in enumerate(mock_research_data['pain_points'], 1):
    print(f"  {i}. {pp['pain']} ({pp['frequency']} frequency)")

print("\nInput Manual Processes:")
for i, mp in enumerate(mock_research_data['manual_processes'], 1):
    print(f"  {i}. {mp}")

# Test strategic agent value chain analysis
from src.strategic_agent import StrategicAnalyst
from langchain_openai import ChatOpenAI

try:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("\n❌ OPENROUTER_API_KEY not set")
        exit(1)
    
    llm = ChatOpenAI(
        model="openrouter/sherlock-think-alpha",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.4
    )
    
    analyst = StrategicAnalyst(llm)
    
    print("\n" + "="*70)
    print("Analyzing Value Chain for AI Opportunities...")
    print("="*70)
    
    strategic_data = analyst.analyze(mock_research_data)
    
    value_chain_opps = strategic_data.get('value_chain_opportunities', [])
    
    print(f"\n✅ Generated {len(value_chain_opps)} AI/automation opportunities")
    
    if value_chain_opps:
        print("\nAI OPPORTUNITIES IDENTIFIED:")
        print("="*70)
        for i, opp in enumerate(value_chain_opps, 1):
            print(f"\n{i}. **{opp.get('activity', 'Unknown')}**")
            print(f"   Current State: {opp.get('current_state', 'N/A')}")
            print(f"   AI Application: {opp.get('ai_application', 'N/A')}")
            print(f"   Automation Potential: {opp.get('automation_potential', 0):.0%}")
            print(f"   Strategic Value: {opp.get('strategic_value', 'N/A')}")
            print(f"   Moat Potential: {opp.get('moat_potential', 'N/A')}")
    else:
        print("\n❌ NO AI OPPORTUNITIES GENERATED")
        print("This is the problem - strategic agent returned empty list")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

