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

    def __init__(self, llm: ChatOpenAI, rag_db=None):
        """
        Initialize quantitative analyst

        Args:
            llm: Language model for analysis
            rag_db: Optional RAGDatabase instance for market data
        """
        self.llm = llm
        self.rag_db = rag_db

    def analyze(
        self,
        research_data: Dict[str, Any],
        strategic_data: Dict[str, Any],
        customer_analysis: Dict[str, Any] = None,
        automation_analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Score opportunities and build unit economics
        Returns quantitative assessments with confidence intervals

        Args:
            research_data: Research agent output
            strategic_data: Strategic agent output
            customer_analysis: Product Manager agent output (optional)
            automation_analysis: Technical Data Scientist agent output (optional)
        """

        print(f"📊 Quantitative analysis...")

        # Identify and score opportunities from value chain analysis
        value_chain_opps = strategic_data.get('value_chain_opportunities', [])

        if not value_chain_opps:
            print("  ⚠️  No value chain opportunities to score")
            return {
                'opportunities': [],
                'industry_metrics': self._calculate_industry_metrics(research_data),
                'vc_criteria_assessment': self._assess_vc_criteria(research_data, strategic_data, customer_analysis)
            }

        # Score each opportunity
        scored_opportunities = []
        total_opps = min(len(value_chain_opps), 5)
        for i, opp in enumerate(value_chain_opps[:5], 1):  # Top 5 only
            print(f"  Scoring opportunity {i}/{total_opps}: {opp.get('activity', 'Unknown')[:50]}...")
            scored = self._score_opportunity(opp, research_data, strategic_data)
            if scored:
                score = scored.get('risk_adjusted_score', 0)
                print(f"  ✅ Score: {score:.1f}/100")
                # Add pre-mortem analysis
                print(f"  Running pre-mortem analysis...")
                scored['pre_mortem'] = self._pre_mortem_analysis(scored, research_data, strategic_data)
                scored_opportunities.append(scored)
            else:
                print(f"  ⚠️  Scoring failed, skipping opportunity")

        # Rank opportunities
        scored_opportunities.sort(key=lambda x: x.get('risk_adjusted_score', 0), reverse=True)

        # VC criteria assessment
        vc_assessment = self._assess_vc_criteria(research_data, strategic_data, customer_analysis)

        print(f"✅ Scored {len(scored_opportunities)} opportunities")

        return {
            'opportunities': scored_opportunities,
            'industry_metrics': self._calculate_industry_metrics(research_data),
            'vc_criteria_assessment': vc_assessment
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

    def _assess_vc_criteria(
        self,
        research: Dict[str, Any],
        strategic: Dict[str, Any],
        customer_analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Assess opportunity against VC investment criteria

        VC Criteria:
        1. TAM (Total Addressable Market) - Size matters
        2. Growth Rate - Market trajectory
        3. Market Fragmentation - Opportunity for consolidation
        4. Defensibility - Moat strength
        5. Unit Economics - LTV/CAC, gross margin
        6. Team Execution Risk - Lower for established operators
        """
        market_size = research.get('market_size_usd') or 0
        growth_rate = research.get('growth_rate') or 0
        hhi = research.get('hhi_index') or 0

        staleness = strategic.get('staleness_audit', {})
        staleness_score = staleness.get('staleness_score', 0)

        # Criterion 1: TAM Score (0-100)
        # $100M = 20, $500M = 40, $1B = 60, $5B = 80, $10B+ = 100
        if market_size >= 10_000_000_000:
            tam_score = 100
        elif market_size >= 5_000_000_000:
            tam_score = 80
        elif market_size >= 1_000_000_000:
            tam_score = 60
        elif market_size >= 500_000_000:
            tam_score = 40
        elif market_size >= 100_000_000:
            tam_score = 20
        else:
            tam_score = 10

        # Criterion 2: Growth Score (0-100)
        # <2% = 20, 2-5% = 40, 5-10% = 60, 10-20% = 80, >20% = 100
        if growth_rate >= 0.20:
            growth_score = 100
        elif growth_rate >= 0.10:
            growth_score = 80
        elif growth_rate >= 0.05:
            growth_score = 60
        elif growth_rate >= 0.02:
            growth_score = 40
        else:
            growth_score = 20

        # Criterion 3: Fragmentation Score (0-100)
        # More fragmented (lower HHI) = more opportunity
        # HHI <500 = 100 (highly fragmented), HHI >2500 = 20 (consolidated)
        if hhi < 500:
            fragmentation_score = 100
        elif hhi < 1000:
            fragmentation_score = 80
        elif hhi < 1500:
            fragmentation_score = 60
        elif hhi < 2000:
            fragmentation_score = 40
        elif hhi < 2500:
            fragmentation_score = 30
        else:
            fragmentation_score = 20

        # Criterion 4: Incumbent Staleness Score (0-100)
        # High staleness = more opportunity
        incumbent_score = staleness_score

        # Criterion 5: Pain Point Intensity (0-100)
        if customer_analysis:
            pain_analysis = customer_analysis.get('pain_point_analysis', {})
            pain_intensity = pain_analysis.get('pain_intensity_score', 50)
        else:
            pain_intensity = 50  # Neutral if no data

        # Criterion 6: Defensibility Potential (0-100)
        # Based on Porter's forces and strategic positioning
        porters = strategic.get('porters_five_forces', {})
        overall_attractiveness = porters.get('overall_attractiveness', 50)

        # High barriers to entry = high defensibility
        barriers = porters.get('new_entrant_threat', {}).get('score', 50)
        defensibility_score = 100 - barriers  # Invert: high threat = low barriers = low defensibility

        # Overall VC Score (weighted average)
        weights = {
            'tam': 0.25,
            'growth': 0.15,
            'fragmentation': 0.15,
            'staleness': 0.15,
            'pain_intensity': 0.15,
            'defensibility': 0.15
        }

        overall_vc_score = (
            tam_score * weights['tam'] +
            growth_score * weights['growth'] +
            fragmentation_score * weights['fragmentation'] +
            incumbent_score * weights['staleness'] +
            pain_intensity * weights['pain_intensity'] +
            defensibility_score * weights['defensibility']
        )

        # Determine VC attractiveness tier
        if overall_vc_score >= 75:
            tier = "TIER 1 - Highly Attractive"
            verdict = "Strong VC case: Large, growing market with clear pain points and stale incumbents."
        elif overall_vc_score >= 60:
            tier = "TIER 2 - Attractive"
            verdict = "Good VC case: Solid fundamentals, some compelling dimensions."
        elif overall_vc_score >= 45:
            tier = "TIER 3 - Borderline"
            verdict = "Weak VC case: Missing key criteria. Better for bootstrapping or strategic exit."
        else:
            tier = "TIER 4 - Unattractive"
            verdict = "Poor VC case: Unlikely to attract institutional capital."

        return {
            'overall_vc_score': round(overall_vc_score, 1),
            'tier': tier,
            'verdict': verdict,
            'criteria_scores': {
                'tam_score': round(tam_score, 1),
                'growth_score': round(growth_score, 1),
                'fragmentation_score': round(fragmentation_score, 1),
                'incumbent_staleness_score': round(incumbent_score, 1),
                'pain_intensity_score': round(pain_intensity, 1),
                'defensibility_score': round(defensibility_score, 1)
            },
            'weights': weights,
            'strengths': self._identify_vc_strengths(
                tam_score, growth_score, fragmentation_score,
                incumbent_score, pain_intensity, defensibility_score
            ),
            'weaknesses': self._identify_vc_weaknesses(
                tam_score, growth_score, fragmentation_score,
                incumbent_score, pain_intensity, defensibility_score
            )
        }

    def _identify_vc_strengths(self, tam, growth, frag, staleness, pain, defense) -> List[str]:
        """Identify top VC strengths"""
        strengths = []

        if tam >= 80:
            strengths.append(f"Large TAM (score: {tam:.0f}/100) - billion-dollar market opportunity")
        if growth >= 80:
            strengths.append(f"High growth (score: {growth:.0f}/100) - rapidly expanding market")
        if frag >= 80:
            strengths.append(f"Fragmented market (score: {frag:.0f}/100) - consolidation opportunity")
        if staleness >= 70:
            strengths.append(f"Stale incumbents (score: {staleness:.0f}/100) - vulnerable to disruption")
        if pain >= 70:
            strengths.append(f"High pain intensity (score: {pain:.0f}/100) - customers desperate for solutions")
        if defense >= 70:
            strengths.append(f"Defensible (score: {defense:.0f}/100) - strong moat potential")

        return strengths[:3]  # Top 3

    def _identify_vc_weaknesses(self, tam, growth, frag, staleness, pain, defense) -> List[str]:
        """Identify top VC weaknesses"""
        weaknesses = []

        if tam < 40:
            weaknesses.append(f"Small TAM (score: {tam:.0f}/100) - limited market size")
        if growth < 40:
            weaknesses.append(f"Low growth (score: {growth:.0f}/100) - slow-growing or declining market")
        if frag < 40:
            weaknesses.append(f"Consolidated market (score: {frag:.0f}/100) - hard to compete with incumbents")
        if staleness < 40:
            weaknesses.append(f"Satisfied customers (score: {staleness:.0f}/100) - incumbents doing well")
        if pain < 40:
            weaknesses.append(f"Low pain intensity (score: {pain:.0f}/100) - weak customer pull")
        if defense < 40:
            weaknesses.append(f"Low defensibility (score: {defense:.0f}/100) - hard to build moat")

        return weaknesses[:3]  # Top 3

    def _pre_mortem_analysis(
        self,
        opportunity: Dict[str, Any],
        research: Dict[str, Any],
        strategic: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Pre-mortem analysis: "Why might this NOT work?"

        Imagines the opportunity failed and works backwards to identify
        the most likely causes of failure.
        """
        prompt = f"""Conduct a pre-mortem analysis for this business opportunity.

**Opportunity**: {opportunity.get('opportunity_title')}
**Description**: {opportunity.get('opportunity_description')}

**Context**:
- TAM: ${opportunity.get('market_sizing', {}).get('tam_usd', 0):,.0f}
- SOM Y3: ${opportunity.get('market_sizing', {}).get('som_y3_usd', 0):,.0f}
- LTV/CAC: {opportunity.get('unit_economics', {}).get('ltv_cac_ratio', 0):.1f}
- Key Moat: {opportunity.get('strategic_rationale', {}).get('key_moat', 'Unknown')}
- Industry HHI: {research.get('hhi_index', 'Unknown')}
- Competitive Threat: {opportunity.get('strategic_rationale', {}).get('competitive_threat', 'Unknown')}

**Task**: Imagine it's 3 years from now and this opportunity FAILED. What went wrong?

Return ONLY valid JSON:
{{
  "failure_scenarios": [
    {{
      "scenario": "<Specific failure mode>",
      "probability": <0.0 to 1.0>,
      "impact": "<critical/high/medium/low>",
      "root_cause": "<Why this happened>",
      "early_warning_signs": ["<sign 1>", "<sign 2>"],
      "mitigation": "<How to prevent or reduce risk>"
    }}
  ],
  "most_likely_failure": "<Single most likely reason for failure>",
  "survival_probability_y3": <0.0 to 1.0>,
  "critical_assumptions": ["<assumption that if wrong, kills the business>"],
  "derisking_priorities": ["<what to validate first>"]
}}

**Common B2B SaaS Failure Modes**:
- Product: Wrong product-market fit, feature bloat, technical debt
- Go-to-Market: Wrong ICP, can't scale sales, CAC too high
- Market: Market too small, no urgency, incumbents respond aggressively
- Execution: Team lacks domain expertise, runs out of capital, co-founder conflict
- Competition: Faster/better-funded competitor emerges, incumbents add feature

Be SPECIFIC and REALISTIC. Don't list generic risks. Ground in the actual context.

Bad example: "Market risk - competition could increase"
Good example: "Incumbent adds AI feature to existing platform (30% probability). They have distribution advantage (50K customers). We're 18 months behind in sales infrastructure. Mitigation: Build on top of their platform as integration vs. replacement."
"""

        response = self.llm.invoke([
            SystemMessage(content="You conduct pre-mortem analyses. Be specific, quantitative, and realistic about failure modes."),
            HumanMessage(content=prompt)
        ])

        result = self._parse_json(response.content)

        if not result or 'failure_scenarios' not in result:
            return {
                'failure_scenarios': [],
                'most_likely_failure': 'Insufficient data for pre-mortem',
                'survival_probability_y3': 0.5
            }

        return result

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
