"""
Data Source Mapper Agent

Identifies where data originates, assesses acquisition feasibility, and recommends
sourcing strategies for each identified data need.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from duckduckgo_search import DDGS
import json
import re
import time


class DataSourceMapper:
    """Maps data sources and acquisition strategies"""

    def __init__(self, llm: ChatOpenAI, audit_db=None):
        """
        Initialize Data Source Mapper

        Args:
            llm: Language model for analysis
            audit_db: Optional AuditDatabase for operation tracking
        """
        self.llm = llm
        self.audit_db = audit_db
        self.ddg = DDGS()

    def map_data_sources(
        self,
        data_needs: List[Dict],
        naics_8_digit: str,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """
        Identify data sources and acquisition strategies for each data need

        Args:
            data_needs: List of data needs
            naics_8_digit: 8-digit NAICS code
            segment_description: Segment description
            run_id: Audit trail run ID

        Returns:
            {
                'naics_8_digit': str,
                'sources_by_data_type': {
                    '<data_type>': {
                        'primary_sources': [
                            {
                                'source_name': str,
                                'source_type': str,  # government, corporate, user-generated, sensor, transaction
                                'accessibility': str,  # public, licensable, proprietary, restricted
                                'access_method': str,  # api, web_scraping, manual_collection, partnership, purchase
                                'cost_estimate': str,
                                'update_frequency': str,
                                'coverage': str,
                                'data_quality': str,  # authoritative, reliable, moderate, uncertain
                                'legal_restrictions': str,
                                'collection_complexity': str  # low, medium, high
                            }
                        ],
                        'acquisition_strategy': {
                            'recommended_approach': str,
                            'estimated_setup_cost': str,
                            'ongoing_cost': str,
                            'time_to_first_data': str,
                            'exclusivity_potential': str,  # high, medium, low
                            'scalability': str,  # high, medium, low
                            'data_moat': str
                        },
                        'alternative_sources': List[Dict]
                    }
                },
                'overall_assessment': {
                    'avg_accessibility': str,
                    'avg_setup_cost': float,
                    'avg_ongoing_cost': float,
                    'feasibility': str  # high, medium, low
                },
                'confidence': float
            }
        """
        print(f"\n🗺️  Mapping data sources for {len(data_needs)} data types...")

        sources_by_data_type = {}

        # Map sources for each data need (top 5)
        for i, data_need in enumerate(data_needs[:5], 1):
            data_type = data_need.get('data_type', '')
            if not data_type:
                continue

            print(f"   Mapping sources for data type {i}/{min(len(data_needs), 5)}: {data_type[:50]}...")

            source_mapping = self._map_sources_for_data_type(
                data_type, segment_description, run_id
            )

            sources_by_data_type[data_type] = source_mapping

        # Overall assessment
        overall = self._assess_overall_feasibility(sources_by_data_type)

        print(f"   ✅ Mapped sources for {len(sources_by_data_type)} data types")

        return {
            'naics_8_digit': naics_8_digit,
            'sources_by_data_type': sources_by_data_type,
            'overall_assessment': overall,
            'confidence': self._calculate_confidence(sources_by_data_type)
        }

    def _map_sources_for_data_type(
        self,
        data_type: str,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """Map sources for a specific data type"""

        # Phase 1: Government/public sources
        govt_results = self._search_government_sources(data_type, run_id)

        # Phase 2: API discovery
        api_results = self._search_api_sources(data_type, run_id)

        # Phase 3: Industry sources
        industry_results = self._search_industry_sources(data_type, segment_description, run_id)

        # Use LLM to analyze and recommend strategy
        analysis = self._analyze_sources(
            data_type,
            govt_results,
            api_results,
            industry_results
        )

        return analysis

    def _search_government_sources(
        self,
        data_type: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for government/public data sources"""

        queries = [
            f'"{data_type}" government database',
            f'"{data_type}" public data API',
            f'"{data_type}" open data portal'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=5)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_source_mapper',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_api_sources(
        self,
        data_type: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for API sources"""

        queries = [
            f'"{data_type}" API documentation',
            f'"{data_type}" REST API'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_source_mapper',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_industry_sources(
        self,
        data_type: str,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for industry association or trade group sources"""

        queries = [
            f'{segment_description} association "{data_type}"',
            f'{segment_description} trade group data',
            f'where to get "{data_type}"'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_source_mapper',
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
        """Perform web search with retry logic"""
        for attempt in range(max_retries):
            try:
                results = list(self.ddg.text(query, max_results=max_results))
                time.sleep(1)  # Rate limiting
                return results
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    return []
        return []

    def _analyze_sources(
        self,
        data_type: str,
        govt_results: List[Dict],
        api_results: List[Dict],
        industry_results: List[Dict]
    ) -> Dict[str, Any]:
        """Use LLM to analyze sources and recommend strategy"""

        # Compile research
        analysis_text = f"DATA TYPE: {data_type}\n\n"
        analysis_text += "GOVERNMENT/PUBLIC SOURCES:\n"
        for r in govt_results[:5]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        analysis_text += "\nAPI SOURCES:\n"
        for r in api_results[:5]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        analysis_text += "\nINDUSTRY SOURCES:\n"
        for r in industry_results[:5]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        prompt = f"""Analyze data sources for: {data_type}

{analysis_text}

Return ONLY valid JSON:
{{
  "primary_sources": [
    {{
      "source_name": "<specific source name>",
      "source_type": "<government|corporate|user-generated|sensor|transaction>",
      "accessibility": "<public|licensable|proprietary|restricted>",
      "access_method": "<api|web_scraping|manual_collection|partnership|purchase>",
      "cost_estimate": "<specific cost or 'free'>",
      "update_frequency": "<how often updated>",
      "coverage": "<what it covers>",
      "data_quality": "<authoritative|reliable|moderate|uncertain>",
      "legal_restrictions": "<any restrictions>",
      "collection_complexity": "<low|medium|high>"
    }}
  ],
  "acquisition_strategy": {{
    "recommended_approach": "<specific recommendation>",
    "estimated_setup_cost": "<dollar amount>",
    "ongoing_cost": "<monthly/annual cost>",
    "time_to_first_data": "<timeframe>",
    "exclusivity_potential": "<high|medium|low>",
    "scalability": "<high|medium|low>",
    "data_moat": "<what makes this defensible>"
  }},
  "alternative_sources": [
    {{
      "source_name": "<name>",
      "cost_estimate": "<cost>",
      "pros": ["<pro>"],
      "cons": ["<con>"]
    }}
  ]
}}

Be specific about costs and methods. If sources not found, recommend web scraping or partnerships.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a data sourcing strategist. Recommend practical, cost-effective data acquisition approaches."),
                HumanMessage(content=prompt)
            ])

            result = self._parse_json(response.content)
            if not result:
                return {
                    'primary_sources': [],
                    'acquisition_strategy': {
                        'recommended_approach': 'Research required',
                        'estimated_setup_cost': 'Unknown',
                        'ongoing_cost': 'Unknown',
                        'time_to_first_data': 'Unknown',
                        'exclusivity_potential': 'low',
                        'scalability': 'medium',
                        'data_moat': 'Unknown'
                    },
                    'alternative_sources': []
                }

            return result

        except Exception as e:
            print(f"     ❌ Source analysis failed: {e}")
            return {
                'primary_sources': [],
                'acquisition_strategy': {},
                'alternative_sources': []
            }

    def _assess_overall_feasibility(
        self,
        sources_by_data_type: Dict
    ) -> Dict[str, Any]:
        """Assess overall data acquisition feasibility"""

        if not sources_by_data_type:
            return {
                'avg_accessibility': 'unknown',
                'avg_setup_cost': 0,
                'avg_ongoing_cost': 0,
                'feasibility': 'low'
            }

        # Count accessibility types
        public_count = 0
        total_sources = 0

        setup_costs = []
        ongoing_costs = []

        for data_type, mapping in sources_by_data_type.items():
            sources = mapping.get('primary_sources', [])
            total_sources += len(sources)

            for source in sources:
                if source.get('accessibility') == 'public':
                    public_count += 1

                # Extract numeric costs if possible
                setup_cost_str = mapping.get('acquisition_strategy', {}).get('estimated_setup_cost', '$0')
                match = re.search(r'[\$]?([\d,]+)', setup_cost_str)
                if match:
                    setup_costs.append(float(match.group(1).replace(',', '')))

                ongoing_cost_str = mapping.get('acquisition_strategy', {}).get('ongoing_cost', '$0')
                match = re.search(r'[\$]?([\d,]+)', ongoing_cost_str)
                if match:
                    ongoing_costs.append(float(match.group(1).replace(',', '')))

        # Calculate averages
        if total_sources > 0:
            public_pct = public_count / total_sources
            if public_pct > 0.7:
                avg_accessibility = 'high'
            elif public_pct > 0.3:
                avg_accessibility = 'medium'
            else:
                avg_accessibility = 'low'
        else:
            avg_accessibility = 'unknown'

        avg_setup = sum(setup_costs) / len(setup_costs) if setup_costs else 0
        avg_ongoing = sum(ongoing_costs) / len(ongoing_costs) if ongoing_costs else 0

        # Determine overall feasibility
        if avg_accessibility in ['high', 'medium'] and avg_setup < 50000:
            feasibility = 'high'
        elif avg_accessibility == 'medium' or avg_setup < 100000:
            feasibility = 'medium'
        else:
            feasibility = 'low'

        return {
            'avg_accessibility': avg_accessibility,
            'avg_setup_cost': avg_setup,
            'avg_ongoing_cost': avg_ongoing,
            'feasibility': feasibility
        }

    def _calculate_confidence(
        self,
        sources_by_data_type: Dict
    ) -> float:
        """Calculate confidence in source mapping"""

        if not sources_by_data_type:
            return 0.1

        # Count how many data types have identified sources
        types_with_sources = sum(
            1 for mapping in sources_by_data_type.values()
            if mapping.get('primary_sources')
        )

        coverage = types_with_sources / len(sources_by_data_type)
        return max(0.3, min(0.9, coverage))

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
            return None


if __name__ == "__main__":
    # Test data source mapper
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

    mapper = DataSourceMapper(llm)

    # Test with sample data needs
    sample_needs = [
        {
            'data_type': 'Worker compensation insurance rates by state and job classification',
            'business_function': 'Insurance pricing'
        }
    ]

    result = mapper.map_data_sources(
        data_needs=sample_needs,
        naics_8_digit="52412601",
        segment_description="Direct Property and Casualty Insurance Carriers"
    )

    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    print(json.dumps(result, indent=2))
