"""
Research Agent - Gathers real data using web search and APIs
Focus: Facts and numbers, not opinions
"""

import json
import re
import time
from typing import Dict, Any, List

# Try new package name first, fallback to old
try:
    from ddgs import DDGS  # New package name
except ImportError:
    try:
        from duckduckgo_search import DDGS  # Old package name (deprecated)
        import warnings
        warnings.warn(
            "Using deprecated 'duckduckgo-search' package. "
            "Please upgrade: pip uninstall duckduckgo-search && pip install ddgs",
            DeprecationWarning,
            stacklevel=2
        )
    except ImportError:
        raise ImportError(
            "No DuckDuckGo search package found. Install with: pip install ddgs"
        )

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class ResearchAgent:
    """Gathers market data using web search and structured sources"""

    def __init__(self, llm: ChatOpenAI, rag_db=None):
        """
        Initialize research agent

        Args:
            llm: Language model for analysis
            rag_db: Optional RAGDatabase instance for querying existing data
        """
        self.llm = llm
        self.ddg = DDGS()
        self.rag_db = rag_db

    def _simplify_industry_name(self, industry_name: str) -> str:
        """Convert formal NAICS names to searchable terms"""
        # Remove common formal terms that don't appear in search results
        replacements = {
            'Custom Computer Programming Services': 'software development',
            'Computer Systems Design Services': 'IT consulting systems design',
            'Offices of Certified Public Accountants': 'accounting CPA services',
            'Offices of Lawyers': 'legal services law firms',
            'Architectural Services': 'architecture firms',
            'Engineering Services': 'engineering consulting',
        }

        # Return specific mapping if exists, otherwise clean up the name
        if industry_name in replacements:
            return replacements[industry_name]

        # Generic cleanup: remove "services", "offices of", etc.
        cleaned = industry_name.lower()
        cleaned = cleaned.replace(' services', '')
        cleaned = cleaned.replace('offices of ', '')
        cleaned = cleaned.replace(' (except', '')  # Remove exceptions

        return cleaned

    def _search_with_retry(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search with exponential backoff retry and rate limiting

        Handles:
        - Rate limiting (waits between attempts)
        - Transient failures (retries up to 3 times)
        - Complete failures (returns empty list)

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search result dictionaries, or empty list if all attempts fail
        """
        for attempt in range(3):
            try:
                # Add delay to avoid rate limiting
                if attempt > 0:
                    wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                    print(f"  ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    # Always wait 1s between searches to be respectful
                    time.sleep(1)

                results = list(self.ddg.text(query, max_results=max_results))

                if results:
                    return results
                else:
                    # No results doesn't mean error, but let's try again in case it's transient
                    if attempt < 2:
                        print(f"  ⚠️  No results, retrying... (attempt {attempt + 2}/3)")

            except Exception as e:
                if attempt < 2:
                    print(f"  ⚠️  Search error, retrying... (attempt {attempt + 2}/3)")
                else:
                    # Final attempt failed
                    print(f"  ⚠️  Search failed after 3 attempts: {type(e).__name__}")

        return []

    def _query_rag_database(self, naics_code: str, industry_name: str) -> Dict[str, Any]:
        """Query RAG database for existing data on this NAICS code"""
        if not self.rag_db:
            return None

        try:
            # Get industry summary from RAG
            summary = self.rag_db.get_industry_summary(naics_code=naics_code)

            if not summary or len(summary) == 0:
                return None

            summary_data = summary[0]

            # Get pain points
            pain_points = self.rag_db.aggregate_pain_points(naics_code=naics_code)

            # Get recent funding/competitive data
            funding = self.rag_db.get_recent_funding(naics_code=naics_code, months_back=24)

            # Get automation opportunities
            automation_opps = self.rag_db.find_automation_opportunities(
                naics_code=naics_code,
                min_genai_score=0  # Get all
            )

            return {
                'summary': summary_data,
                'pain_points': pain_points,
                'competitive_funding': funding,
                'automation_opportunities': automation_opps,
                'total_entries': (
                    summary_data.get('voice_of_customer_count', 0) +
                    summary_data.get('competitive_intel_count', 0) +
                    summary_data.get('workflow_intel_count', 0)
                )
            }

        except Exception as e:
            print(f"  ⚠️  RAG database query failed: {e}")
            return None

    def research_industry(self, naics_code: str, industry_name: str = None, phase: str = "PHASE_1") -> Dict[str, Any]:
        """
        Conduct comprehensive research on a NAICS industry
        Returns structured data with confidence scores

        Args:
            naics_code: 6-digit NAICS code
            industry_name: Industry name (optional)
            phase: "PHASE_1" (quick screening) or "PHASE_2" (deep dive)
        """

        print(f"🔍 Researching NAICS {naics_code} ({phase})...")

        try:
            # Step 0: Query RAG database for existing data
            rag_data = self._query_rag_database(naics_code, industry_name)

            if rag_data:
                print(f"  📊 Found {rag_data.get('total_entries', 0)} RAG database entries")

            # Step 1: Get NAICS definition if not provided
            if not industry_name:
                try:
                    industry_name = self._get_naics_definition(naics_code)
                except Exception as e:
                    print(f"  ⚠️  Could not fetch industry name: {e}")
                    industry_name = f"Industry {naics_code}"  # Fallback

            # Step 2: Gather market data through targeted searches
            # Reduce queries if we have RAG data
            market_data = self._gather_market_data(naics_code, industry_name, rag_data)

            # Step 3: Research competitive landscape
            # Use RAG competitive intelligence if available
            competitive_data = self._research_competition(naics_code, industry_name, rag_data)

            # Step 4: Identify technology stack and pain points
            # Use RAG voice-of-customer and workflow data
            tech_and_pain = self._research_tech_and_pain(naics_code, industry_name, rag_data, phase)

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

        # Try multiple query variations
        queries = [
            f"NAICS {naics_code} definition",
            f"what is NAICS code {naics_code}",
            f"NAICS {naics_code} industry"
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=2)
            results.extend(search_results)
            if results:  # Stop if we got some results
                break

        if not results:
            # Fallback: use LLM knowledge
            prompt = f"What industry does NAICS code {naics_code} represent? Return only the industry name."
            response = self.llm.invoke([
                SystemMessage(content="You provide NAICS industry names."),
                HumanMessage(content=prompt)
            ])
            return response.content.strip()

        context = "\n\n".join([f"{r['title']}: {r['body']}" for r in results])

        prompt = f"""Based on this search data about NAICS {naics_code}, provide the industry name.

{context}

Return ONLY the industry name, nothing else."""

        response = self.llm.invoke([
            SystemMessage(content="You extract industry names from search results."),
            HumanMessage(content=prompt)
        ])

        return response.content.strip()

    def _gather_market_data(self, naics_code: str, industry_name: str, rag_data: Dict = None) -> Dict[str, Any]:
        """Search for market size, growth, employment data"""

        # Use simplified, searchable industry terms
        search_term = self._simplify_industry_name(industry_name)

        # Adaptive search based on RAG data availability
        if rag_data and rag_data.get('total_entries', 0) > 20:
            # Have good RAG data, reduce web searches
            queries = [f"{search_term} market size 2024"]
            print(f"  📊 Using RAG data, reducing market searches to 1 query")
        else:
            # Limited RAG data, do more web searches
            queries = [
                f"{search_term} market size 2024",
                f"how big is the {search_term} industry",
                f"{search_term} industry trends 2024"
            ]

        search_results = []
        for query in queries:
            results = self._search_with_retry(query, max_results=3)
            if not results:
                print(f"  ⚠️  No results for '{query}'")
            else:
                search_results.extend(results)

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

        result = self._parse_json_response(response.content)

        # Ensure minimal valid structure if parsing failed
        if not result or len(result) <= 1:  # Only has confidence or is empty
            print(f"  ⚠️  Incomplete market data, using minimal structure")
            return {
                'market_size_usd': None,
                'growth_rate': None,
                'establishments': None,
                'employment': None,
                'avg_wage': None,
                'market_concentration': None,
                'key_trends': [],
                'sources': [],
                'confidence': 0.1
            }

        return result

    def _research_competition(self, naics_code: str, industry_name: str, rag_data: Dict = None) -> Dict[str, Any]:
        """Research competitive dynamics and major players"""

        search_term = self._simplify_industry_name(industry_name)

        # Check RAG database for competitive intel
        rag_competitive_data = {}
        if rag_data and rag_data.get('competitive_funding'):
            funding_data = rag_data['competitive_funding']
            if len(funding_data) > 0:
                print(f"  📊 Found {len(funding_data)} funded startups in RAG database")
                rag_competitive_data = {
                    'funded_startups': funding_data,
                    'total_funding': sum(f.get('funding_amount_usd', 0) or 0 for f in funding_data),
                    'recent_activity': len([f for f in funding_data if f.get('funding_date')])
                }

        # Adaptive search based on RAG competitive data
        if rag_competitive_data.get('recent_activity', 0) > 5:
            # Have good RAG competitive data, reduce searches
            queries = [f"top companies in {search_term}"]
            print(f"  📊 Using RAG competitive data, reducing to 1 query")
        else:
            # Need more competitive intelligence
            queries = [
                f"top companies in {search_term}",
                f"{search_term} market leaders",
                f"biggest {search_term} companies"
            ]

        search_results = []
        for query in queries:
            results = self._search_with_retry(query, max_results=3)
            if not results:
                print(f"  ⚠️  No results for '{query}'")
            else:
                search_results.extend(results)

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

        result = self._parse_json_response(response.content)

        # Ensure minimal valid structure if parsing failed
        if not result or len(result) <= 1:  # Only has confidence or is empty
            print(f"  ⚠️  Incomplete competitive data, using minimal structure")
            return {
                'hhi_index': None,
                'top_players': [],
                'market_share_top_3': None,
                'competitive_dynamics': 'Insufficient data',
                'barriers_to_entry': 'unknown',
                'confidence': 0.1
            }

        return result

    def _research_tech_and_pain(self, naics_code: str, industry_name: str, rag_data: Dict = None, phase: str = "PHASE_1") -> Dict[str, Any]:
        """Research technology usage and pain points"""

        search_term = self._simplify_industry_name(industry_name)

        # Check RAG database for pain points and workflow data
        rag_pain_data = {}
        if rag_data:
            pain_points = rag_data.get('pain_points', [])
            automation_opps = rag_data.get('automation_opportunities', [])

            if len(pain_points) > 0 or len(automation_opps) > 0:
                print(f"  📊 Found {len(pain_points)} pain point categories and {len(automation_opps)} workflows in RAG")
                rag_pain_data = {
                    'pain_points': pain_points,
                    'automation_opportunities': automation_opps
                }

        # Build search queries based on phase and RAG data
        queries = []

        if phase == "PHASE_2" or not rag_pain_data:
            # Phase II or no RAG data: Use site-specific searches for VOC
            queries.extend([
                f'site:reddit.com "{search_term}" software complaints',
                f'site:g2.com "{search_term}" reviews',
                f"{search_term} pain points challenges"
            ])
        else:
            # Phase I with RAG data: Lighter searches
            queries.extend([
                f"what software do {search_term} companies use",
                f"{search_term} biggest challenges"
            ])

        search_results = []
        for query in queries:
            results = self._search_with_retry(query, max_results=3)
            if not results:
                print(f"  ⚠️  No results for '{query}'")
            else:
                search_results.extend(results)

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

        result = self._parse_json_response(response.content)

        # Ensure minimal valid structure if parsing failed
        if not result or len(result) <= 1:  # Only has confidence or is empty
            print(f"  ⚠️  Incomplete tech/pain data, using minimal structure")
            return {
                'common_tools': [],
                'digital_maturity': 'unknown',
                'tech_spend_per_employee': None,
                'pain_points': [],
                'manual_processes': [],
                'confidence': 0.1
            }

        return result

    def _consolidate_findings(
        self,
        naics_code: str,
        industry_name: str,
        market_data: Dict,
        competitive_data: Dict,
        tech_pain_data: Dict
    ) -> Dict[str, Any]:
        """Consolidate all research into structured format"""

        # Calculate overall confidence (handle None values)
        confidences = [
            market_data.get('confidence') or 0.5,
            competitive_data.get('confidence') or 0.5,
            tech_pain_data.get('confidence') or 0.5
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
