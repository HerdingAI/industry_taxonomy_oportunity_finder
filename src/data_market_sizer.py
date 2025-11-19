"""
Data Market Sizer Agent

Calculates TAM/SAM/SOM and unit economics for potential data product opportunities.
Estimates market size, pricing potential, and revenue projections.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from duckduckgo_search import DDGS
import json
import re
import time


class DataMarketSizer:
    """Estimates market size and unit economics for data opportunities"""

    def __init__(self, llm: ChatOpenAI, audit_db=None):
        """
        Initialize Data Market Sizer

        Args:
            llm: Language model for analysis
            audit_db: Optional AuditDatabase for operation tracking
        """
        self.llm = llm
        self.audit_db = audit_db
        self.ddg = DDGS()

    def size_market(
        self,
        data_needs: List[Dict],
        naics_8_digit: str,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """
        Calculate market size and unit economics for data opportunities

        Args:
            data_needs: List of data needs from DataNeedsResearcher
            naics_8_digit: 8-digit NAICS code
            segment_description: Segment description
            run_id: Audit trail run ID

        Returns:
            {
                'naics_8_digit': str,
                'market_sizing_by_data_type': {
                    '<data_type>': {
                        'tam': {
                            'total_businesses': int,
                            'addressable_businesses': int,
                            'annual_tam_usd': float,
                            'calculation_basis': str
                        },
                        'sam': {
                            'serviceable_businesses': int,
                            'annual_sam_usd': float,
                            'market_filters': List[str]
                        },
                        'som': {
                            'obtainable_businesses_year1': int,
                            'annual_som_year1_usd': float,
                            'obtainable_businesses_year3': int,
                            'annual_som_year3_usd': float,
                            'assumptions': List[str]
                        },
                        'unit_economics': {
                            'estimated_price_per_customer_annual': float,
                            'estimated_cogs_per_customer': float,
                            'estimated_gross_margin_pct': float,
                            'estimated_cac': float,
                            'estimated_ltv': float,
                            'ltv_cac_ratio': float,
                            'payback_period_months': int
                        },
                        'pricing_benchmarks': List[Dict],
                        'growth_potential': str  # high, medium, low
                    }
                },
                'overall_market_assessment': {
                    'total_tam_across_all_needs': float,
                    'largest_opportunity': str,
                    'market_maturity': str,
                    'competitive_intensity': str
                },
                'confidence': float
            }
        """
        print(f"\n📏 Sizing market for {len(data_needs)} data types...")

        market_sizing_by_data_type = {}

        # Size market for each data need (top 5)
        for i, data_need in enumerate(data_needs[:5], 1):
            data_type = data_need.get('data_type', '')
            if not data_type:
                continue

            print(f"   Sizing market for data type {i}/{min(len(data_needs), 5)}: {data_type[:50]}...")

            market_sizing = self._size_market_for_data_type(
                data_type, naics_8_digit, segment_description, run_id
            )

            market_sizing_by_data_type[data_type] = market_sizing

        # Overall assessment
        overall = self._assess_overall_market(market_sizing_by_data_type)

        print(f"   ✅ Total TAM: ${overall['total_tam_across_all_needs']:,.0f}")

        return {
            'naics_8_digit': naics_8_digit,
            'market_sizing_by_data_type': market_sizing_by_data_type,
            'overall_market_assessment': overall,
            'confidence': self._calculate_confidence(market_sizing_by_data_type)
        }

    def _size_market_for_data_type(
        self,
        data_type: str,
        naics_8_digit: str,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """Size market for a specific data type"""

        # Phase 1: Industry size research
        industry_size_results = self._search_industry_size(
            naics_8_digit, segment_description, run_id
        )

        # Phase 2: Pricing benchmarks
        pricing_results = self._search_pricing_benchmarks(
            data_type, segment_description, run_id
        )

        # Phase 3: Adoption rates
        adoption_results = self._search_adoption_rates(
            data_type, segment_description, run_id
        )

        # Use LLM to calculate market sizing
        market_sizing = self._calculate_market_size(
            data_type,
            naics_8_digit,
            segment_description,
            industry_size_results,
            pricing_results,
            adoption_results
        )

        return market_sizing

    def _search_industry_size(
        self,
        naics_8_digit: str,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for industry size and business count data"""

        queries = [
            f'NAICS {naics_8_digit} number of businesses',
            f'"{segment_description}" industry size revenue',
            f'"{segment_description}" market size statistics',
            f'"{segment_description}" number of companies United States',
            f'site:census.gov NAICS {naics_8_digit}'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=5)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_market_sizer',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_pricing_benchmarks(
        self,
        data_type: str,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for pricing benchmarks for similar data products"""

        queries = [
            f'"{data_type}" subscription pricing',
            f'"{data_type}" data cost per year',
            f'"{segment_description}" data spend budget',
            f'B2B data pricing benchmarks {segment_description}'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_market_sizer',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_adoption_rates(
        self,
        data_type: str,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for data adoption and penetration rates"""

        queries = [
            f'"{segment_description}" data adoption rate',
            f'"{segment_description}" percent using data analytics',
            f'"{data_type}" market penetration'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_market_sizer',
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

    def _calculate_market_size(
        self,
        data_type: str,
        naics_8_digit: str,
        segment_description: str,
        industry_size_results: List[Dict],
        pricing_results: List[Dict],
        adoption_results: List[Dict]
    ) -> Dict[str, Any]:
        """Use LLM to calculate market sizing"""

        # Compile research
        analysis_text = f"DATA TYPE: {data_type}\n"
        analysis_text += f"NAICS: {naics_8_digit} - {segment_description}\n\n"

        analysis_text += "INDUSTRY SIZE RESEARCH:\n"
        for r in industry_size_results[:10]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        analysis_text += "\nPRICING BENCHMARKS:\n"
        for r in pricing_results[:10]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        analysis_text += "\nADOPTION RATES:\n"
        for r in adoption_results[:10]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        prompt = f"""Calculate market size for this data product opportunity:

{analysis_text}

Return ONLY valid JSON:
{{
  "tam": {{
    "total_businesses": <total businesses in segment>,
    "addressable_businesses": <businesses that could use this data>,
    "annual_tam_usd": <total addressable market in USD>,
    "calculation_basis": "<explain calculation>"
  }},
  "sam": {{
    "serviceable_businesses": <businesses you can realistically reach>,
    "annual_sam_usd": <serviceable addressable market USD>,
    "market_filters": ["<why TAM != SAM>"]
  }},
  "som": {{
    "obtainable_businesses_year1": <realistic customers year 1>,
    "annual_som_year1_usd": <obtainable market year 1 USD>,
    "obtainable_businesses_year3": <realistic customers year 3>,
    "annual_som_year3_usd": <obtainable market year 3 USD>,
    "assumptions": ["<key assumption>"]
  }},
  "unit_economics": {{
    "estimated_price_per_customer_annual": <annual price USD>,
    "estimated_cogs_per_customer": <cost of goods sold per customer>,
    "estimated_gross_margin_pct": <gross margin %>,
    "estimated_cac": <customer acquisition cost>,
    "estimated_ltv": <lifetime value>,
    "ltv_cac_ratio": <LTV/CAC ratio>,
    "payback_period_months": <months to recover CAC>
  }},
  "pricing_benchmarks": [
    {{
      "vendor": "<vendor name>",
      "price": "<price>",
      "notes": "<context>"
    }}
  ],
  "growth_potential": "<high|medium|low>"
}}

Guidelines:
- TAM = all businesses in segment × annual willingness to pay
- SAM = TAM × (% that match ideal customer profile)
- SOM Year 1 = SAM × (realistic market share % in year 1, typically 0.5-2%)
- SOM Year 3 = SAM × (realistic market share % in year 3, typically 3-10%)
- Price should reflect value and competitive landscape
- COGS includes data acquisition, infrastructure, support
- Typical SaaS CAC = 1-3x annual contract value
- Healthy LTV/CAC ratio > 3
- Be conservative but realistic
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a market sizing analyst. Calculate realistic market sizes with clear assumptions."),
                HumanMessage(content=prompt)
            ])

            result = self._parse_json(response.content)
            if not result:
                return self._get_default_market_sizing()

            return result

        except Exception as e:
            print(f"     ❌ Market sizing failed: {e}")
            return self._get_default_market_sizing()

    def _get_default_market_sizing(self) -> Dict[str, Any]:
        """Return default market sizing structure"""
        return {
            'tam': {
                'total_businesses': 0,
                'addressable_businesses': 0,
                'annual_tam_usd': 0,
                'calculation_basis': 'Insufficient data'
            },
            'sam': {
                'serviceable_businesses': 0,
                'annual_sam_usd': 0,
                'market_filters': []
            },
            'som': {
                'obtainable_businesses_year1': 0,
                'annual_som_year1_usd': 0,
                'obtainable_businesses_year3': 0,
                'annual_som_year3_usd': 0,
                'assumptions': []
            },
            'unit_economics': {
                'estimated_price_per_customer_annual': 0,
                'estimated_cogs_per_customer': 0,
                'estimated_gross_margin_pct': 0,
                'estimated_cac': 0,
                'estimated_ltv': 0,
                'ltv_cac_ratio': 0,
                'payback_period_months': 0
            },
            'pricing_benchmarks': [],
            'growth_potential': 'unknown'
        }

    def _assess_overall_market(
        self,
        market_sizing_by_data_type: Dict
    ) -> Dict[str, Any]:
        """Assess overall market opportunity"""

        if not market_sizing_by_data_type:
            return {
                'total_tam_across_all_needs': 0,
                'largest_opportunity': 'None identified',
                'market_maturity': 'unknown',
                'competitive_intensity': 'unknown'
            }

        # Sum TAMs
        total_tam = sum(
            sizing.get('tam', {}).get('annual_tam_usd', 0)
            for sizing in market_sizing_by_data_type.values()
        )

        # Find largest opportunity
        largest = max(
            market_sizing_by_data_type.items(),
            key=lambda x: x[1].get('tam', {}).get('annual_tam_usd', 0),
            default=(None, {})
        )
        largest_name = largest[0] if largest[0] else 'None'

        # Assess maturity based on growth potential
        high_growth_count = sum(
            1 for sizing in market_sizing_by_data_type.values()
            if sizing.get('growth_potential') == 'high'
        )

        if high_growth_count >= len(market_sizing_by_data_type) * 0.6:
            maturity = 'emerging'
        elif high_growth_count >= len(market_sizing_by_data_type) * 0.3:
            maturity = 'growing'
        else:
            maturity = 'mature'

        # Assess competitive intensity based on LTV/CAC ratios
        ltv_cac_ratios = [
            sizing.get('unit_economics', {}).get('ltv_cac_ratio', 0)
            for sizing in market_sizing_by_data_type.values()
        ]
        avg_ltv_cac = sum(ltv_cac_ratios) / len(ltv_cac_ratios) if ltv_cac_ratios else 0

        if avg_ltv_cac > 4:
            intensity = 'low'
        elif avg_ltv_cac > 2:
            intensity = 'medium'
        else:
            intensity = 'high'

        return {
            'total_tam_across_all_needs': total_tam,
            'largest_opportunity': largest_name,
            'market_maturity': maturity,
            'competitive_intensity': intensity
        }

    def _calculate_confidence(
        self,
        market_sizing_by_data_type: Dict
    ) -> float:
        """Calculate confidence in market sizing"""

        if not market_sizing_by_data_type:
            return 0.1

        # Count how many have non-zero TAM
        types_with_sizing = sum(
            1 for sizing in market_sizing_by_data_type.values()
            if sizing.get('tam', {}).get('annual_tam_usd', 0) > 0
        )

        coverage = types_with_sizing / len(market_sizing_by_data_type)
        return max(0.3, min(0.8, coverage))  # Market sizing inherently uncertain

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
    # Test data market sizer
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

    sizer = DataMarketSizer(llm)

    # Test with sample data needs
    sample_needs = [
        {
            'data_type': 'Worker compensation insurance rates by state and job classification',
            'business_function': 'Insurance pricing and risk assessment'
        }
    ]

    result = sizer.size_market(
        data_needs=sample_needs,
        naics_8_digit="52412601",
        segment_description="Direct Property and Casualty Insurance Carriers"
    )

    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    print(json.dumps(result, indent=2))
