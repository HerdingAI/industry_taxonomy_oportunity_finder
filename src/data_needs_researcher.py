"""
Data Needs Researcher Agent

Discovers operational data requirements for businesses in specific 8-digit NAICS segments
through comprehensive web research, job posting analysis, and vendor review analysis.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from duckduckgo_search import DDGS
import json
import re
import time


class DataNeedsResearcher:
    """Researches and identifies core operational data needs for industry segments"""

    def __init__(self, llm: ChatOpenAI, audit_db=None):
        """
        Initialize Data Needs Researcher

        Args:
            llm: Language model for analysis
            audit_db: Optional AuditDatabase for operation tracking
        """
        self.llm = llm
        self.audit_db = audit_db
        self.ddg = DDGS()

    def discover_data_needs(
        self,
        naics_8_digit: str,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """
        Discover what operational data businesses in this segment need

        Args:
            naics_8_digit: 8-digit NAICS code
            segment_description: Description of the segment (from CSV)
            run_id: Audit trail run ID

        Returns:
            {
                'naics_8_digit': str,
                'segment_description': str,
                'data_needs': [
                    {
                        'data_type': str,  # Specific data type
                        'business_function': str,  # How it's used
                        'importance': str,  # critical, high, medium, low
                        'frequency_mentioned': int,  # Times found in research
                        'current_pain_points': List[str],
                        'use_cases': List[str],
                        'decision_impact': str,
                        'sources_found': List[str]  # URLs where mentioned
                    }
                ],
                'segment_characteristics': {
                    'typical_company_size': str,
                    'data_sophistication': str,  # low, medium, high
                    'budget_for_data': str
                },
                'confidence': float  # 0.0-1.0
            }
        """
        print(f"\n🔍 Discovering data needs for NAICS {naics_8_digit}...")
        print(f"   Segment: {segment_description}")

        # Phase 1: Direct data need searches
        direct_needs = self._search_direct_data_needs(
            naics_8_digit, segment_description, run_id
        )

        # Phase 2: Job posting analysis
        job_based_needs = self._search_job_postings(
            segment_description, run_id
        )

        # Phase 3: Regulatory/compliance data
        compliance_needs = self._search_compliance_data(
            segment_description, run_id
        )

        # Phase 4: Operational data discovery
        operational_needs = self._search_operational_data(
            segment_description, run_id
        )

        # Phase 5: Pain point discovery
        pain_points = self._search_pain_points(
            segment_description, run_id
        )

        # Consolidate and analyze all search results
        all_results = {
            'direct': direct_needs,
            'jobs': job_based_needs,
            'compliance': compliance_needs,
            'operational': operational_needs,
            'pain_points': pain_points
        }

        # Use LLM to extract and structure data needs
        data_needs_analysis = self._analyze_data_needs(
            all_results, naics_8_digit, segment_description
        )

        print(f"   ✅ Found {len(data_needs_analysis.get('data_needs', []))} data need types")

        return data_needs_analysis

    def _search_direct_data_needs(
        self,
        naics_8_digit: str,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for direct mentions of data needs"""
        print(f"   Phase 1: Direct data need searches...")

        queries = [
            f'site:reddit.com "{segment_description}" "what data"',
            f'site:reddit.com "{segment_description}" "data source"',
            f'"{segment_description}" industry "data requirements"',
            f'"{segment_description}" "business intelligence" needs',
            f'"{segment_description}" "KPIs" track'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=5)
            results.extend(search_results)

            # Log to audit database
            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_needs_researcher',
                    query_text=query,
                    results=search_results,
                    duration_seconds=None  # Will be tracked by wrapper
                )

        return results

    def _search_job_postings(
        self,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Analyze job postings to identify data requirements"""
        print(f"   Phase 2: Job posting analysis...")

        queries = [
            f'site:linkedin.com "{segment_description}" "data analyst" job',
            f'site:indeed.com "{segment_description}" data requirements',
            f'"{segment_description}" "business analyst" responsibilities data'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=5)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_needs_researcher',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_compliance_data(
        self,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for regulatory/compliance data requirements"""
        print(f"   Phase 3: Regulatory/compliance data...")

        queries = [
            f'"{segment_description}" regulatory reporting requirements',
            f'"{segment_description}" compliance data needed'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=5)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_needs_researcher',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_operational_data(
        self,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for operational data needs"""
        print(f"   Phase 4: Operational data discovery...")

        queries = [
            f'"{segment_description}" pricing data sources',
            f'"{segment_description}" market data providers',
            f'"{segment_description}" "how do you get" data',
            f'"{segment_description}" benchmarking data',
            f'"{segment_description}" industry metrics'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=5)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_needs_researcher',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_pain_points(
        self,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for pain points with current data access"""
        print(f"   Phase 5: Pain point discovery...")

        queries = [
            f'site:reddit.com "{segment_description}" "data is expensive"',
            f'"{segment_description}" "can\'t find data"',
            f'"{segment_description}" "data quality" problems',
            f'"{segment_description}" "need better data"'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=5)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_needs_researcher',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_with_retry(
        self,
        query: str,
        max_results: int = 5,
        max_retries: int = 3
    ) -> List[Dict]:
        """
        Perform web search with retry logic

        Args:
            query: Search query
            max_results: Maximum results to return
            max_retries: Maximum retry attempts

        Returns:
            List of search results
        """
        for attempt in range(max_retries):
            try:
                results = list(self.ddg.text(query, max_results=max_results))
                time.sleep(1)  # Rate limiting
                return results
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"     ⚠️  Search failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"     ❌ Search failed after {max_retries} attempts: {query}")
                    return []

        return []

    def _analyze_data_needs(
        self,
        all_results: Dict[str, List],
        naics_8_digit: str,
        segment_description: str
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze search results and extract structured data needs

        Args:
            all_results: Dictionary of search results by phase
            naics_8_digit: NAICS code
            segment_description: Segment description

        Returns:
            Structured data needs analysis
        """
        print(f"   Analyzing search results with LLM...")

        # Compile search results into analysis text
        analysis_text = f"NAICS {naics_8_digit}: {segment_description}\n\n"

        for phase, results in all_results.items():
            if results:
                analysis_text += f"\n{phase.upper()} SEARCH RESULTS:\n"
                for r in results[:10]:  # Limit to top 10 per phase
                    analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        # LLM prompt
        prompt = f"""Analyze these web search results about data needs in the {segment_description} industry.

{analysis_text}

Extract SPECIFIC data types that businesses in this industry need to operate effectively.

Return ONLY valid JSON matching this structure:
{{
  "data_needs": [
    {{
      "data_type": "<specific data type, NOT generic>",
      "business_function": "<how it's used>",
      "importance": "<critical|high|medium|low>",
      "frequency_mentioned": <count of mentions>,
      "current_pain_points": ["<specific pain>"],
      "use_cases": ["<specific use case>"],
      "decision_impact": "<description>",
      "sources_found": ["<source URLs>"]
    }}
  ],
  "segment_characteristics": {{
    "typical_company_size": "<estimate>",
    "data_sophistication": "<low|medium|high>",
    "budget_for_data": "<estimate>"
  }},
  "confidence": <0.0-1.0>
}}

Be SPECIFIC. Examples:
Bad: "market data"
Good: "daily commodity spot prices for corn, soybeans, and wheat"

Bad: "customer data"
Good: "retail foot traffic counts by hour and day of week"

Focus on operational data needed to run the business, not generic analytics.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a business data analyst. Extract specific, actionable data requirements from research."),
                HumanMessage(content=prompt)
            ])

            # Parse JSON response
            result = self._parse_json(response.content)

            if not result:
                # Return minimal structure if parsing fails
                return {
                    'naics_8_digit': naics_8_digit,
                    'segment_description': segment_description,
                    'data_needs': [],
                    'segment_characteristics': {},
                    'confidence': 0.1
                }

            # Add metadata
            result['naics_8_digit'] = naics_8_digit
            result['segment_description'] = segment_description

            return result

        except Exception as e:
            print(f"     ❌ LLM analysis failed: {e}")
            return {
                'naics_8_digit': naics_8_digit,
                'segment_description': segment_description,
                'data_needs': [],
                'segment_characteristics': {},
                'confidence': 0.1,
                'error': str(e)
            }

    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        content = content.strip()

        # Remove markdown code blocks
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
            # Try to extract JSON from text
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass

            print(f"     ⚠️  Failed to parse JSON response")
            return None


if __name__ == "__main__":
    # Test the data needs researcher
    import os
    from dotenv import load_dotenv

    load_dotenv()

    llm = ChatOpenAI(
        model="openrouter/sherlock-think-alpha",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.4,
        max_tokens=4000
    )

    researcher = DataNeedsResearcher(llm)

    # Test with sample 8-digit NAICS
    result = researcher.discover_data_needs(
        naics_8_digit="52412601",
        segment_description="Direct Property and Casualty Insurance Carriers"
    )

    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    print(json.dumps(result, indent=2))
