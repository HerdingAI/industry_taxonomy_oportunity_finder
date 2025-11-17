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

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def analyze(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform strategic analysis on research data
        Returns Porter's Five Forces, positioning insights, value chain opportunities
        """

        print(f"💼 Strategic analysis...")

        naics_code = research_data['naics_code']
        industry_name = research_data['industry_name']

        # Porter's Five Forces Analysis
        porters = self._analyze_porters_forces(research_data)

        # Strategic positioning
        positioning = self._analyze_positioning(research_data, porters)

        # Value chain opportunities
        value_chain = self._analyze_value_chain(research_data)

        consolidated = {
            'naics_code': naics_code,
            'porters_five_forces': porters,
            'strategic_positioning': positioning,
            'value_chain_opportunities': value_chain
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

            print(f"  ⚠️  Failed to parse JSON response")
            return {}


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
