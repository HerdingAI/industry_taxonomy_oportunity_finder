"""
Research Agent - Gathers real data using web search and APIs
Focus: Facts and numbers, not opinions
"""

import json
import re
from typing import Dict, Any, List
from duckduckgo_search import DDGS
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class ResearchAgent:
    """Gathers market data using web search and structured sources"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.ddg = DDGS()

    def research_industry(self, naics_code: str, industry_name: str = None) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a NAICS industry
        Returns structured data with confidence scores
        """

        print(f"🔍 Researching NAICS {naics_code}...")

        try:
            # Step 1: Get NAICS definition if not provided
            if not industry_name:
                try:
                    industry_name = self._get_naics_definition(naics_code)
                except Exception as e:
                    print(f"  ⚠️  Could not fetch industry name: {e}")
                    industry_name = f"Industry {naics_code}"  # Fallback

            # Step 2: Gather market data through targeted searches
            market_data = self._gather_market_data(naics_code, industry_name)

            # Step 3: Research competitive landscape
            competitive_data = self._research_competition(naics_code, industry_name)

            # Step 4: Identify technology stack and pain points
            tech_and_pain = self._research_tech_and_pain(naics_code, industry_name)

            # Step 5: Consolidate and structure findings
            consolidated = self._consolidate_findings(
                naics_code,
                industry_name,
                market_data,
                competitive_data,
                tech_and_pain
            )

            print(f"✅ Research complete (confidence: {consolidated.get('confidence', 0):.0%})")

            return consolidated

        except Exception as e:
            print(f"  ⚠️  Research encountered errors: {e}")
            # Return minimal valid structure to allow pipeline to continue
            return {
                'naics_code': naics_code,
                'industry_name': industry_name or f"Industry {naics_code}",
                'market_size_usd': None,
                'growth_rate': None,
                'establishments': None,
                'employment': None,
                'avg_wage': None,
                'market_concentration': 'unknown',
                'hhi_index': None,
                'top_players': [],
                'market_share_top_3': None,
                'competitive_dynamics': 'Unable to assess',
                'barriers_to_entry': 'unknown',
                'common_tools': [],
                'digital_maturity': 'unknown',
                'tech_spend_per_employee': None,
                'pain_points': [],
                'manual_processes': [],
                'key_trends': [],
                'confidence': 0.1,
                'sources': [],
                'research_timestamp': None
            }

    def _get_naics_definition(self, naics_code: str) -> str:
        """Get official NAICS industry definition"""

        search_query = f"NAICS {naics_code} definition census bureau"
        results = list(self.ddg.text(search_query, max_results=3))

        context = "\n\n".join([f"{r['title']}: {r['body']}" for r in results])

        prompt = f"""Based on this search data about NAICS {naics_code}, provide the industry name.

{context}

Return ONLY the industry name, nothing else."""

        response = self.llm.invoke([
            SystemMessage(content="You extract industry names from search results."),
            HumanMessage(content=prompt)
        ])

        return response.content.strip()

    def _gather_market_data(self, naics_code: str, industry_name: str) -> Dict[str, Any]:
        """Search for market size, growth, employment data"""

        queries = [
            f"NAICS {naics_code} market size revenue 2024",
            f"NAICS {naics_code} number of establishments businesses",
            f"NAICS {naics_code} employment statistics BLS",
            f"{industry_name} industry growth rate forecast",
            f"{industry_name} market trends 2024 2025"
        ]

        search_results = []
        for query in queries:
            try:
                results = list(self.ddg.text(query, max_results=3))
                if not results:
                    print(f"  ⚠️  No results for '{query}'")
                    continue
                search_results.extend(results)
            except Exception as e:
                print(f"  ⚠️  Search failed for '{query}': {e}")
                continue

        # Check if we got ANY results
        if not search_results:
            print(f"  ⚠️  No search results found. Using LLM knowledge (lower confidence).")

        # Extract structured data from search results
        context = self._format_search_results(search_results)

        prompt = f"""Extract market data for NAICS {naics_code} - {industry_name}.

Search results:
{context}

Extract and return ONLY a JSON object with these fields (use null if not found):
{{
  "market_size_usd": <number> or null,
  "growth_rate": <decimal like 0.05 for 5%> or null,
  "establishments": <number of businesses> or null,
  "employment": <total employees> or null,
  "avg_wage": <average annual wage> or null,
  "market_concentration": "<fragmented/moderate/concentrated>",
  "key_trends": [<array of 2-3 key trends>],
  "sources": [<sources used>],
  "confidence": <0.0 to 1.0 based on data quality>
}}

Focus on numbers. If you see ranges, use the midpoint. If data is for a year other than 2024, adjust estimates."""

        response = self.llm.invoke([
            SystemMessage(content="You are a data extraction specialist. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])

        return self._parse_json_response(response.content)

    def _research_competition(self, naics_code: str, industry_name: str) -> Dict[str, Any]:
        """Research competitive dynamics and major players"""

        queries = [
            f"{industry_name} major companies market share",
            f"{industry_name} competitive landscape market leaders",
            f"NAICS {naics_code} market concentration HHI"
        ]

        search_results = []
        for query in queries:
            try:
                results = list(self.ddg.text(query, max_results=3))
                if not results:
                    print(f"  ⚠️  No results for '{query}'")
                    continue
                search_results.extend(results)
            except Exception as e:
                print(f"  ⚠️  Search failed: {e}")
                continue

        # Check if we got ANY results
        if not search_results:
            print(f"  ⚠️  No search results found. Using LLM knowledge (lower confidence).")

        context = self._format_search_results(search_results)

        prompt = f"""Analyze competitive landscape for {industry_name} (NAICS {naics_code}).

Search results:
{context}

Return ONLY a JSON object:
{{
  "hhi_index": <number 0-10000, estimate if not given>,
  "top_players": [<array of major company names>],
  "market_share_top_3": <decimal like 0.25 for 25%> or null,
  "competitive_dynamics": "<1-2 sentence insight>",
  "barriers_to_entry": "<low/medium/high>",
  "confidence": <0.0 to 1.0>
}}

HHI index guide: <1000=fragmented, 1000-1800=moderate, >1800=concentrated
If you can't find HHI, estimate based on market structure descriptions."""

        response = self.llm.invoke([
            SystemMessage(content="You analyze competitive markets. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])

        return self._parse_json_response(response.content)

    def _research_tech_and_pain(self, naics_code: str, industry_name: str) -> Dict[str, Any]:
        """Research technology usage and pain points"""

        queries = [
            f"{industry_name} software tools commonly used",
            f"{industry_name} pain points challenges problems",
            f"{industry_name} digital transformation technology adoption",
            f"{industry_name} inefficiencies manual processes"
        ]

        search_results = []
        for query in queries:
            try:
                results = list(self.ddg.text(query, max_results=3))
                if not results:
                    print(f"  ⚠️  No results for '{query}'")
                    continue
                search_results.extend(results)
            except Exception as e:
                print(f"  ⚠️  Search failed: {e}")
                continue

        # Check if we got ANY results
        if not search_results:
            print(f"  ⚠️  No search results found. Using LLM knowledge (lower confidence).")

        context = self._format_search_results(search_results)

        prompt = f"""Analyze technology and pain points for {industry_name}.

Search results:
{context}

Return ONLY a JSON object:
{{
  "common_tools": [<array of software/tools used>],
  "digital_maturity": "<low/medium/high>",
  "tech_spend_per_employee": <annual $ amount> or null,
  "pain_points": [
    {{"pain": "<description>", "frequency": "<low/med/high>", "cost_impact": "<description>"}}
  ],
  "manual_processes": [<array of manual/paper-based workflows>],
  "confidence": <0.0 to 1.0>
}}

Focus on specific, actionable pain points (not generic statements).
Prioritize pain points related to manual work, data entry, compliance, communication."""

        response = self.llm.invoke([
            SystemMessage(content="You analyze business operations and technology. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])

        return self._parse_json_response(response.content)

    def _consolidate_findings(
        self,
        naics_code: str,
        industry_name: str,
        market_data: Dict,
        competitive_data: Dict,
        tech_pain_data: Dict
    ) -> Dict[str, Any]:
        """Consolidate all research into structured format"""

        # Calculate overall confidence
        confidences = [
            market_data.get('confidence', 0.5),
            competitive_data.get('confidence', 0.5),
            tech_pain_data.get('confidence', 0.5)
        ]
        overall_confidence = sum(confidences) / len(confidences)

        return {
            'naics_code': naics_code,
            'industry_name': industry_name,

            # Market data
            'market_size_usd': market_data.get('market_size_usd'),
            'growth_rate': market_data.get('growth_rate'),
            'establishments': market_data.get('establishments'),
            'employment': market_data.get('employment'),
            'avg_wage': market_data.get('avg_wage'),
            'market_concentration': market_data.get('market_concentration'),
            'key_trends': market_data.get('key_trends', []),

            # Competitive landscape
            'hhi_index': competitive_data.get('hhi_index'),
            'top_players': competitive_data.get('top_players', []),
            'market_share_top_3': competitive_data.get('market_share_top_3'),
            'competitive_dynamics': competitive_data.get('competitive_dynamics'),
            'barriers_to_entry': competitive_data.get('barriers_to_entry'),

            # Technology & operations
            'common_tools': tech_pain_data.get('common_tools', []),
            'digital_maturity': tech_pain_data.get('digital_maturity'),
            'tech_spend_per_employee': tech_pain_data.get('tech_spend_per_employee'),
            'pain_points': tech_pain_data.get('pain_points', []),
            'manual_processes': tech_pain_data.get('manual_processes', []),

            # Metadata
            'confidence': overall_confidence,
            'sources': market_data.get('sources', []),
            'research_timestamp': None  # Will be set when saved to DB
        }

    def _format_search_results(self, results: List[Dict]) -> str:
        """Format search results for LLM context"""
        formatted = []
        for i, r in enumerate(results[:10], 1):  # Limit to 10 results
            formatted.append(f"[{i}] {r.get('title', 'No title')}\n{r.get('body', '')}\n")

        return "\n".join(formatted)

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        # Remove markdown code blocks if present
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
            # Try to find JSON object in text
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass

            # If all fails, return minimal structure
            print(f"  ⚠️  Failed to parse JSON, returning empty structure")
            return {'confidence': 0.1}


if __name__ == "__main__":
    # Test the research agent
    import os
    from dotenv import load_dotenv

    load_dotenv()

    llm = ChatOpenAI(
        model="openrouter/sherlock-think-alpha",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.3
    )

    agent = ResearchAgent(llm)
    results = agent.research_industry("541511", "Custom Computer Programming Services")

    print("\n" + "="*60)
    print("RESEARCH RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2))
