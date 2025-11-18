"""
Strategic Analyst Agent - MBA-level analysis
Focus: Insight-dense strategic frameworks
Output: Why and so what, not what
"""

import json
import re
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class StrategicAnalyst:
    """Applies MBA frameworks to generate strategic insights"""

    def __init__(self, llm: ChatOpenAI, rag_db=None):
        """
        Initialize strategic analyst

        Args:
            llm: Language model for analysis
            rag_db: Optional RAGDatabase instance for staleness audit
        """
        self.llm = llm
        self.rag_db = rag_db

    def analyze(self, research_data: Dict[str, Any], naics_code: str = None) -> Dict[str, Any]:
        """
        Perform strategic analysis on research data
        Returns Porter's Five Forces, positioning insights, value chain opportunities, staleness audit

        Args:
            research_data: Research data from research agent
            naics_code: NAICS code (for staleness audit RAG query)
        """

        print(f"💼 Strategic analysis...")

        naics_code = naics_code or research_data.get('naics_code')
        industry_name = research_data['industry_name']

        # Porter's Five Forces Analysis
        porters = self._analyze_porters_forces(research_data)

        # Strategic positioning
        positioning = self._analyze_positioning(research_data, porters)

        # Value chain opportunities
        value_chain = self._analyze_value_chain(research_data)

        # Staleness Audit (Phase II of new methodology)
        staleness_audit = self._staleness_audit(naics_code, industry_name, research_data)

        consolidated = {
            'naics_code': naics_code,
            'porters_five_forces': porters,
            'strategic_positioning': positioning,
            'value_chain_opportunities': value_chain,
            'staleness_audit': staleness_audit
        }

        print(f"✅ Strategic analysis complete (attractiveness: {porters.get('overall_attractiveness')}/100)")

        return consolidated

    def _analyze_porters_forces(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply Porter's Five Forces framework
        Return scores (0-100) and concise insights
        """

        prompt = f"""Analyze Porter's Five Forces for this industry. Be CONCISE and INSIGHTFUL.

Industry: {data['industry_name']} (NAICS {data['naics_code']})

Data:
- Market concentration: {data.get('market_concentration')} (HHI: {data.get('hhi_index')})
- Barriers to entry: {data.get('barriers_to_entry')}
- Top players: {data.get('top_players', [])}
- Key trends: {data.get('key_trends', [])}
- Digital maturity: {data.get('digital_maturity')}

Return ONLY valid JSON:
{{
  "competitive_rivalry": {{
    "score": <0-100, higher = more intense>,
    "insight": "<One sentence WHY, with specific evidence. Focus on implications, not descriptions.>"
  }},
  "new_entrant_threat": {{
    "score": <0-100, higher = easier to enter>,
    "insight": "<One sentence explaining barriers/enablers and strategic implication.>"
  }},
  "supplier_power": {{
    "score": <0-100, higher = more supplier leverage>,
    "insight": "<One sentence on supplier dynamics and implication.>"
  }},
  "buyer_power": {{
    "score": <0-100, higher = more buyer leverage>,
    "insight": "<One sentence on buyer power and pricing implications.>"
  }},
  "substitute_threat": {{
    "score": <0-100, higher = more substitutes available>,
    "insight": "<One sentence on substitutes and strategic response needed.>"
  }},
  "overall_attractiveness": <0-100, weighted average>,
  "strategic_verdict": "<One sentence: Is this attractive? For whom? Under what conditions?>"
}}

Scoring guide:
- Competitive rivalry: HHI <1000 = 70+, 1000-1800 = 50-70, >1800 = <50
- New entrant threat: low barriers = 80+, medium = 50-80, high = <50
- Overall: Weight rivalry and new entrants highest (30% each), others 15-20% each

CRITICAL: Every insight must be:
1. Specific (use actual data points)
2. Strategic (explain implications/actions)
3. Concise (max 25 words)

Bad example: "There is high competition in this market"
Good example: "Fragmented (HHI=182) but commoditizing. Price competition intensifying in low-end; specialization rewarded at high-end."
"""

        response = self.llm.invoke([
            SystemMessage(content="You are an MBA strategy consultant. Every sentence must add strategic value. No filler. Be precise, not verbose."),
            HumanMessage(content=prompt)
        ])

        return self._parse_json(response.content)

    def _analyze_positioning(self, data: Dict[str, Any], porters: Dict[str, Any]) -> Dict[str, Any]:
        """Identify strategic positioning opportunities"""

        prompt = f"""Determine strategic positioning for this industry. Be INSIGHT-DENSE.

Industry: {data['industry_name']}
Overall Attractiveness: {porters.get('overall_attractiveness')}/100

Market dynamics:
- Competitive rivalry: {porters.get('competitive_rivalry', {}).get('insight')}
- New entrants: {porters.get('new_entrant_threat', {}).get('insight')}
- Digital maturity: {data.get('digital_maturity')}
- Key trends: {data.get('key_trends', [])}

Return ONLY valid JSON:
{{
  "best_positioning": "<How to win? Specific strategy, not generic advice. Max 15 words.>",
  "worst_positioning": "<What to avoid? Specific trap. Max 15 words.>",
  "market_dynamics_insight": "<One sentence on how market is evolving and strategic implications.>",
  "white_space_opportunity": "<Where's the gap competitors aren't addressing? Specific. Max 20 words.>"
}}

Bad example: "Focus on customer service and quality"
Good example: "Vertical specialization with proprietary data moats; avoid generalist hourly billing"
"""

        response = self.llm.invoke([
            SystemMessage(content="You identify strategic opportunities. Specificity > generality. Actionable > theoretical."),
            HumanMessage(content=prompt)
        ])

        return self._parse_json(response.content)

    def _analyze_value_chain(self, data: Dict[str, Any]) -> list:
        """Identify high-value activities and automation opportunities in value chain"""

        pain_points = data.get('pain_points', [])
        manual_processes = data.get('manual_processes', [])

        if not pain_points and not manual_processes:
            return []

        prompt = f"""Analyze value chain for automation opportunities. Be SPECIFIC and QUANTITATIVE.

Industry: {data['industry_name']}

Pain points identified:
{json.dumps(pain_points, indent=2)}

Manual processes:
{json.dumps(manual_processes, indent=2)}

Return ONLY valid JSON array (max 5 items):
[
  {{
    "activity": "<Specific workflow/process name>",
    "current_state": "<How it's done now, concisely>",
    "margin_impact": "<low/medium/high>",
    "automation_potential": <0.0 to 1.0>,
    "strategic_value": "<WHY this matters strategically. One sentence. Include $ impact if quantifiable.>",
    "ai_application": "<Specific AI/automation solution, not generic 'use AI'>",
    "moat_potential": "<low/medium/high - is this defensible?>"
  }}
]

Prioritize activities where:
1. Pain is severe/costly
2. Process is repetitive
3. Automation creates defensibility (not just cost savings)
4. Strategic impact is high

Bad example: {{"activity": "customer service", "strategic_value": "improve efficiency"}}
Good example: {{"activity": "requirements gathering", "current_state": "manual meetings + docs", "strategic_value": "Errors here cascade 10x downstream costs. High-margin firms spend 15-20% revenue re-scoping.", "ai_application": "NLP to auto-structure requirements from conversations + historical project data"}}
"""

        response = self.llm.invoke([
            SystemMessage(content="You find high-value automation opportunities. Specificity and quantification required. No vague suggestions."),
            HumanMessage(content=prompt)
        ])

        result = self._parse_json(response.content)
        return result if isinstance(result, list) else []

    def _staleness_audit(self, naics_code: str, industry_name: str, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase II Staleness Audit - identify incumbent technology gaps

        Analyzes:
        1. Incumbent software providers
        2. Voice-of-customer complaint signals
        3. Competitive gaps
        4. Data-related bottlenecks
        """
        if not self.rag_db or not naics_code:
            return {
                'staleness_score': 0,
                'data_available': False,
                'message': 'RAG database not available or NAICS code missing'
            }

        try:
            # Get aggregated pain points
            pain_points = self.rag_db.aggregate_pain_points(naics_code=naics_code)

            # Get VOC data for complaints
            voc_data = self.rag_db.search_voice_of_customer(
                query_text=f"{industry_name} software complaints outdated manual clunky",
                naics_code=naics_code,
                limit_count=30
            )

            # Get competitive intelligence
            funding_data = self.rag_db.get_recent_funding(naics_code=naics_code, months_back=24)

            if not pain_points and not voc_data:
                return {
                    'staleness_score': 0,
                    'data_available': False,
                    'message': 'No voice-of-customer data available for this NAICS code'
                }

            # Analyze complaint signals
            staleness_indicators = self._extract_staleness_indicators(voc_data, pain_points)

            # Identify incumbent software mentioned
            incumbent_software = self._identify_incumbents(voc_data)

            # Analyze competitive gaps
            competitive_gaps = self._analyze_competitive_gaps(funding_data, pain_points)

            # Calculate overall staleness score (0-100)
            staleness_score = self._calculate_staleness_score(
                staleness_indicators,
                incumbent_software,
                competitive_gaps
            )

            return {
                'staleness_score': staleness_score,
                'data_available': True,
                'staleness_indicators': staleness_indicators,
                'incumbent_software': incumbent_software,
                'competitive_gaps': competitive_gaps,
                'top_complaints': [
                    {
                        'category': pp.get('pain_point_category'),
                        'mentions': pp.get('mention_count'),
                        'keywords': pp.get('all_keywords', [])[:5]
                    }
                    for pp in pain_points[:3]
                ],
                'recommendation': self._staleness_recommendation(staleness_score, staleness_indicators)
            }

        except Exception as e:
            print(f"  ⚠️  Staleness audit failed: {e}")
            return {
                'staleness_score': 0,
                'data_available': False,
                'error': str(e)
            }

    def _extract_staleness_indicators(self, voc_data: list, pain_points: list) -> list:
        """Extract staleness complaint signals from VOC data"""
        staleness_keywords = [
            'outdated', 'old', 'legacy', 'ancient', 'clunky', 'slow',
            'no api', 'manual', 'manual workaround', 'no integration',
            'poor ui', 'ui from 2000', '90s interface', 'no mobile',
            'no automation', 'requires manual'
        ]

        indicators = []

        # Count from pain point keywords
        for pp in pain_points:
            keywords = pp.get('all_keywords', [])
            for kw in keywords:
                kw_lower = kw.lower()
                for stale_kw in staleness_keywords:
                    if stale_kw in kw_lower:
                        indicators.append({
                            'keyword': kw,
                            'category': pp.get('pain_point_category'),
                            'mentions': pp.get('mention_count', 0)
                        })
                        break

        # Count from VOC complaint keywords
        for v in voc_data:
            complaint_kws = v.get('complaint_keywords', [])
            for kw in complaint_kws:
                kw_lower = kw.lower()
                for stale_kw in staleness_keywords:
                    if stale_kw in kw_lower and kw not in [i['keyword'] for i in indicators]:
                        indicators.append({
                            'keyword': kw,
                            'category': v.get('pain_point_category', 'general'),
                            'mentions': 1
                        })
                        break

        # Deduplicate and sort by mentions
        unique_indicators = {}
        for ind in indicators:
            kw = ind['keyword']
            if kw in unique_indicators:
                unique_indicators[kw]['mentions'] += ind['mentions']
            else:
                unique_indicators[kw] = ind

        sorted_indicators = sorted(
            unique_indicators.values(),
            key=lambda x: x['mentions'],
            reverse=True
        )

        return sorted_indicators[:10]  # Top 10

    def _identify_incumbents(self, voc_data: list) -> list:
        """Identify incumbent software providers mentioned in VOC data"""
        software_mentions = {}

        for v in voc_data:
            software = v.get('software_mentioned')
            if software:
                if software not in software_mentions:
                    software_mentions[software] = {
                        'name': software,
                        'total_mentions': 0,
                        'negative_mentions': 0,
                        'complaints': []
                    }

                software_mentions[software]['total_mentions'] += 1

                sentiment = v.get('sentiment')
                if sentiment in ['negative', 'mixed']:
                    software_mentions[software]['negative_mentions'] += 1

                # Collect complaint keywords
                complaints = v.get('complaint_keywords', [])
                software_mentions[software]['complaints'].extend(complaints)

        # Calculate negativity ratio and sort
        incumbents = []
        for sw_name, data in software_mentions.items():
            total = data['total_mentions']
            negative = data['negative_mentions']
            negativity_ratio = negative / total if total > 0 else 0

            # Count unique complaints
            unique_complaints = list(set(data['complaints']))

            incumbents.append({
                'software_name': sw_name,
                'total_mentions': total,
                'negativity_ratio': round(negativity_ratio, 2),
                'top_complaints': unique_complaints[:5],
                'staleness_score': round(negativity_ratio * 100, 1)
            })

        # Sort by negativity ratio (staler = higher)
        incumbents.sort(key=lambda x: x['negativity_ratio'], reverse=True)

        return incumbents[:5]  # Top 5 most-complained-about

    def _analyze_competitive_gaps(self, funding_data: list, pain_points: list) -> Dict[str, Any]:
        """Analyze gaps between pain points and funded solutions"""
        if not funding_data or not pain_points:
            return {
                'gap_exists': True,
                'gap_score': 80,  # High gap if no funded startups
                'reason': 'No funded startups addressing pain points'
            }

        # Extract funded startup product categories
        funded_categories = [f.get('product_category') for f in funding_data if f.get('product_category')]

        # Extract pain point categories
        pain_categories = [pp.get('pain_point_category') for pp in pain_points]

        # Simple gap analysis: pain points not addressed by funded startups
        gaps = [pain for pain in pain_categories if pain not in funded_categories]

        gap_score = min(100, len(gaps) * 20)  # Up to 100

        return {
            'gap_exists': len(gaps) > 0,
            'gap_score': gap_score,
            'unaddressed_pain_points': gaps[:3],
            'funded_startups_count': len(funding_data),
            'total_funding_usd': sum(f.get('funding_amount_usd', 0) or 0 for f in funding_data)
        }

    def _calculate_staleness_score(
        self,
        staleness_indicators: list,
        incumbent_software: list,
        competitive_gaps: Dict[str, Any]
    ) -> float:
        """
        Calculate overall staleness score (0-100)

        Higher score = staler market = more opportunity
        """
        score = 0

        # Staleness indicators (40 points max)
        indicator_score = min(40, len(staleness_indicators) * 4)
        score += indicator_score

        # Incumbent negativity (30 points max)
        if incumbent_software:
            avg_negativity = sum(i['negativity_ratio'] for i in incumbent_software) / len(incumbent_software)
            score += avg_negativity * 30

        # Competitive gaps (30 points max)
        gap_score = competitive_gaps.get('gap_score', 0)
        score += (gap_score / 100) * 30

        return round(min(100, score), 1)

    def _staleness_recommendation(self, staleness_score: float, indicators: list) -> str:
        """Generate recommendation based on staleness score"""
        if staleness_score >= 70:
            return f"STRONG OPPORTUNITY: High staleness ({staleness_score}/100). Incumbents are vulnerable. Top complaints: {', '.join([i['keyword'] for i in indicators[:3]])}. Ideal for disruption."

        elif staleness_score >= 50:
            return f"MODERATE OPPORTUNITY: Moderate staleness ({staleness_score}/100). Some incumbent weakness. Focus on specific pain points: {', '.join([i['keyword'] for i in indicators[:3]])}."

        elif staleness_score >= 30:
            return f"LIMITED OPPORTUNITY: Low staleness ({staleness_score}/100). Market is somewhat satisfied or recently disrupted. Look for niche angles."

        else:
            return f"WEAK OPPORTUNITY: Very low staleness ({staleness_score}/100). Incumbents are well-regarded or market is actively innovating. Difficult to disrupt."

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        content = content.strip()

        # Remove markdown
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
            # Try to extract JSON
            # First try object
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass

            # Try array
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass

            print(f"  ⚠️  Failed to parse JSON response, returning minimal structure")
            return {
                'competitive_rivalry': {'score': 50, 'insight': 'Unable to assess'},
                'new_entrant_threat': {'score': 50, 'insight': 'Unable to assess'},
                'supplier_power': {'score': 50, 'insight': 'Unable to assess'},
                'buyer_power': {'score': 50, 'insight': 'Unable to assess'},
                'substitute_threat': {'score': 50, 'insight': 'Unable to assess'},
                'overall_attractiveness': 50,
                'strategic_verdict': 'Insufficient data for analysis'
            }


if __name__ == "__main__":
    # Test strategic analyst
    import os
    from dotenv import load_dotenv

    load_dotenv()

    llm = ChatOpenAI(
        model="openrouter/sherlock-think-alpha",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.4
    )

    # Mock research data
    research_data = {
        'naics_code': '541511',
        'industry_name': 'Custom Computer Programming Services',
        'market_concentration': 'highly fragmented',
        'hhi_index': 182,
        'barriers_to_entry': 'low',
        'top_players': ['Accenture', 'IBM', 'Deloitte'],
        'key_trends': ['AI code generation', 'offshore competition', 'cloud migration'],
        'digital_maturity': 'high',
        'pain_points': [
            {'pain': 'project scoping errors', 'frequency': 'high', 'cost_impact': '15-20% revenue overruns'},
            {'pain': 'resource allocation', 'frequency': 'medium', 'cost_impact': '10-15% inefficiency'}
        ],
        'manual_processes': ['requirements gathering', 'code review', 'client communication']
    }

    analyst = StrategicAnalyst(llm)
    results = analyst.analyze(research_data)

    print("\n" + "="*60)
    print("STRATEGIC ANALYSIS")
    print("="*60)
    print(json.dumps(results, indent=2))
