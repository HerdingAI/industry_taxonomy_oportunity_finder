"""
Quantitative Analyst Agent - Data science scoring and financial modeling
Focus: Numbers, not narratives. Confidence intervals, not point estimates.
"""

import json
import re
from typing import Dict, Any, List, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class QuantitativeAnalyst:
    """Scores opportunities and builds financial models"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def analyze(
        self,
        research_data: Dict[str, Any],
        strategic_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score opportunities and build unit economics
        Returns quantitative assessments with confidence intervals
        """

        print(f"📊 Quantitative analysis...")

        # Identify and score opportunities from value chain analysis
        value_chain_opps = strategic_data.get('value_chain_opportunities', [])

        if not value_chain_opps:
            print("  ⚠️  No value chain opportunities to score")
            return {'opportunities': [], 'industry_metrics': self._calculate_industry_metrics(research_data)}

        # Score each opportunity
        scored_opportunities = []
        for opp in value_chain_opps[:5]:  # Top 5 only
            scored = self._score_opportunity(opp, research_data, strategic_data)
            if scored:
                scored_opportunities.append(scored)

        # Rank opportunities
        scored_opportunities.sort(key=lambda x: x.get('risk_adjusted_score', 0), reverse=True)

        print(f"✅ Scored {len(scored_opportunities)} opportunities")

        return {
            'opportunities': scored_opportunities,
            'industry_metrics': self._calculate_industry_metrics(research_data)
        }

    def _score_opportunity(
        self,
        opportunity: Dict[str, Any],
        research: Dict[str, Any],
        strategic: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score a single opportunity using multi-criteria model"""

        prompt = f"""Score this business opportunity using quantitative rigor. Use NUMBERS, not adjectives.

**Opportunity**: {opportunity.get('activity')}
**Current State**: {opportunity.get('current_state')}
**AI Solution**: {opportunity.get('ai_application')}
**Strategic Value**: {opportunity.get('strategic_value')}

**Industry Context**:
- Market size: {research.get('market_size_usd', 'unknown')}
- Establishments: {research.get('establishments', 'unknown')}
- Average wage: {research.get('avg_wage', 'unknown')}
- Growth rate: {research.get('growth_rate', 'unknown')}
- HHI: {research.get('hhi_index')}
- Overall attractiveness: {strategic.get('porters_five_forces', {}).get('overall_attractiveness')}

**Task**: Estimate market size, unit economics, and score this opportunity.

Return ONLY valid JSON:
{{
  "opportunity_title": "<Concise product/service name>",
  "opportunity_description": "<One sentence value prop>",

  "market_sizing": {{
    "tam_usd": <total addressable market in dollars>,
    "sam_usd": <serviceable addressable market>,
    "som_y3_usd": <serviceable obtainable market in year 3>,
    "assumptions": ["<key assumption 1>", "<key assumption 2>"],
    "confidence": <0.0 to 1.0>
  }},

  "unit_economics": {{
    "arpu": <annual revenue per user in dollars>,
    "gross_margin": <decimal like 0.85 for 85%>,
    "cac": <customer acquisition cost>,
    "ltv": <lifetime value>,
    "ltv_cac_ratio": <LTV/CAC>,
    "payback_months": <months to recover CAC>,
    "assumptions": ["<key assumption>"]
  }},

  "scoring": {{
    "market_size_score": <0-100, based on TAM: $1B=50, $10B=100>,
    "growth_score": <0-100, based on industry growth + this opp growth potential>,
    "margin_score": <0-100, gross_margin * 100>,
    "defensibility_score": <0-100, based on moat strength>,
    "competition_score": <0-100, inverse of market saturation>,
    "weighted_score": <0-100, calculated average>,
    "weights_used": {{"market_size": 0.25, "growth": 0.15, "margin": 0.20, "defensibility": 0.25, "competition": 0.15}}
  }},

  "risk_assessment": {{
    "key_risks": [
      {{"risk": "<specific risk>", "probability": <0.0-1.0>, "impact_usd": <negative number>}}
    ],
    "expected_value_y5_usd": <risk-adjusted expected value in year 5>,
    "confidence_interval_80pct": [<low estimate>, <high estimate>]
  }},

  "strategic_rationale": {{
    "why_now": "<One sentence: Why is timing right?>",
    "why_unsolved": "<One sentence: Why hasn't this been done?>",
    "key_moat": "<Primary defensibility mechanism>",
    "competitive_threat": "<Biggest competitive risk>"
  }},

  "overall_confidence": <0.0 to 1.0, based on data quality>
}}

**Calculation rules**:
- TAM: Industry market size × % addressable by this solution
- SAM: TAM × % you can realistically serve (geographic, segment, etc.)
- SOM Y3: SAM × realistic penetration by year 3 (usually 2-7%)
- ARPU: Estimate based on value created / pricing power
- Gross margin: Typical for software = 75-90%, services = 40-60%
- CAC: For B2B SaaS typically $3K-15K (SMB) or $25K-150K (enterprise)
- LTV: ARPU × (1 / annual churn rate) × gross margin
- Defensibility: Consider network effects, data moat, switching costs, IP, regulatory

**Be conservative** but not pessimistic. Use midpoint estimates. Show your math in assumptions.

Bad example: "Large market opportunity with good margins"
Good example: "$185B industry × 4.4% applicable to this workflow = $8.2B TAM. 25% reachable via partnerships = $2.1B SAM. 5% penetration Y3 (based on EHR adoption curves) = $105M SOM."
"""

        response = self.llm.invoke([
            SystemMessage(content="You are a quantitative analyst and financial modeler. Every number needs an assumption. Every estimate needs a range."),
            HumanMessage(content=prompt)
        ])

        result = self._parse_json(response.content)

        if not result:
            return None

        # Calculate risk-adjusted score
        confidence = result.get('overall_confidence', 0.5)
        weighted_score = result.get('scoring', {}).get('weighted_score', 0)
        risk_adjusted_score = weighted_score * confidence

        result['naics_code'] = research.get('naics_code')
        result['risk_adjusted_score'] = risk_adjusted_score

        return result

    def _calculate_industry_metrics(self, research: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key industry-level metrics"""

        market_size = research.get('market_size_usd')
        establishments = research.get('establishments')
        employment = research.get('employment')

        metrics = {
            'avg_revenue_per_firm': None,
            'revenue_per_employee': None,
            'employees_per_firm': None
        }

        if market_size and establishments and establishments > 0:
            metrics['avg_revenue_per_firm'] = int(market_size / establishments)

        if market_size and employment and employment > 0:
            metrics['revenue_per_employee'] = int(market_size / employment)

        if employment and establishments and establishments > 0:
            metrics['employees_per_firm'] = round(employment / establishments, 1)

        return metrics

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        content = content.strip()

        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass

            print(f"  ⚠️  Failed to parse JSON, returning minimal structure")
            return {
                'opportunity_title': 'Analysis Failed',
                'opportunity_description': 'Unable to generate opportunity description',
                'market_sizing': {
                    'tam_usd': None,
                    'sam_usd': None,
                    'som_y3_usd': None,
                    'confidence': 0.1
                },
                'unit_economics': {
                    'arpu': None,
                    'gross_margin': None,
                    'ltv': None,
                    'cac': None,
                    'ltv_cac_ratio': None,
                    'payback_months': None
                },
                'scoring': {
                    'weighted_score': 0
                },
                'risk_assessment': {
                    'key_risks': ['Insufficient data for analysis'],
                    'expected_value_y5_usd': None
                },
                'strategic_rationale': {
                    'key_moat': 'Unknown',
                    'why_now': 'Unknown',
                    'why_unsolved': 'Unknown',
                    'competitive_threat': 'Unknown'
                },
                'overall_confidence': 0.1,
                'risk_adjusted_score': 0
            }


if __name__ == "__main__":
    # Test quantitative analyst
    import os
    from dotenv import load_dotenv

    load_dotenv()

    llm = ChatOpenAI(
        model="openrouter/sherlock-think-alpha",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.3,
        max_tokens=4000
    )

    # Mock data
    research_data = {
        'naics_code': '541511',
        'industry_name': 'Custom Computer Programming Services',
        'market_size_usd': 185000000000,
        'establishments': 89400,
        'employment': 823000,
        'avg_wage': 98400,
        'growth_rate': 0.082,
        'hhi_index': 182
    }

    strategic_data = {
        'porters_five_forces': {'overall_attractiveness': 67},
        'value_chain_opportunities': [{
            'activity': 'Requirements gathering',
            'current_state': 'Manual meetings and documentation',
            'automation_potential': 0.85,
            'strategic_value': 'Errors cascade 10x downstream. High-margin firms spend 15-20% revenue re-scoping.',
            'ai_application': 'NLP to auto-structure requirements from conversations + historical project data',
            'moat_potential': 'high'
        }]
    }

    analyst = QuantitativeAnalyst(llm)
    results = analyst.analyze(research_data, strategic_data)

    print("\n" + "="*60)
    print("QUANTITATIVE ANALYSIS")
    print("="*60)
    print(json.dumps(results, indent=2))
