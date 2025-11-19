"""
Data Product Designer Agent

Designs the actual data product offering including format, delivery, pricing tiers,
and integration capabilities. Creates actionable product specifications.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from duckduckgo_search import DDGS
import json
import re
import time


class DataProductDesigner:
    """Designs data product specifications and go-to-market strategy"""

    def __init__(self, llm: ChatOpenAI, audit_db=None):
        """
        Initialize Data Product Designer

        Args:
            llm: Language model for analysis
            audit_db: Optional AuditDatabase for operation tracking
        """
        self.llm = llm
        self.audit_db = audit_db
        self.ddg = DDGS()

    def design_product(
        self,
        data_needs: List[Dict],
        vendor_landscape: Dict[str, Any],
        market_sizing: Dict[str, Any],
        naics_8_digit: str,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """
        Design data product specifications

        Args:
            data_needs: List of data needs from DataNeedsResearcher
            vendor_landscape: Vendor analysis from VendorIntelligenceAgent
            market_sizing: Market sizing from DataMarketSizer
            naics_8_digit: 8-digit NAICS code
            segment_description: Segment description
            run_id: Audit trail run ID

        Returns:
            {
                'naics_8_digit': str,
                'product_designs_by_data_type': {
                    '<data_type>': {
                        'product_name': str,
                        'value_proposition': str,
                        'product_format': {
                            'delivery_methods': List[str],  # api, flat_file, dashboard, data_feed
                            'data_format': List[str],  # json, csv, parquet, sql
                            'update_frequency': str,  # realtime, daily, weekly, monthly
                            'data_coverage': str,
                            'historical_depth': str
                        },
                        'pricing_tiers': [
                            {
                                'tier_name': str,
                                'annual_price': float,
                                'features': List[str],
                                'target_customer': str,
                                'api_calls_per_month': int
                            }
                        ],
                        'integrations': {
                            'priority_integrations': List[str],
                            'developer_tools': List[str],
                            'supported_platforms': List[str]
                        },
                        'competitive_differentiation': {
                            'unique_features': List[str],
                            'vs_incumbents': str,
                            'positioning': str
                        },
                        'gtm_strategy': {
                            'target_segments': List[str],
                            'primary_channels': List[str],
                            'key_partnerships': List[str],
                            'initial_traction_plan': str
                        }
                    }
                },
                'overall_product_strategy': {
                    'product_portfolio_approach': str,
                    'cross_sell_opportunities': List[str],
                    'platform_vision': str
                },
                'confidence': float
            }
        """
        print(f"\n🎨 Designing products for {len(data_needs)} data types...")

        product_designs_by_data_type = {}

        # Design product for each data need (top 5)
        for i, data_need in enumerate(data_needs[:5], 1):
            data_type = data_need.get('data_type', '')
            if not data_type:
                continue

            print(f"   Designing product {i}/{min(len(data_needs), 5)}: {data_type[:50]}...")

            # Get vendor and market context
            vendors = vendor_landscape.get('vendors_by_data_type', {}).get(data_type, {})
            market = market_sizing.get('market_sizing_by_data_type', {}).get(data_type, {})

            product_design = self._design_product_for_data_type(
                data_type, data_need, vendors, market, segment_description, run_id
            )

            product_designs_by_data_type[data_type] = product_design

        # Overall strategy
        overall = self._design_overall_strategy(product_designs_by_data_type, segment_description)

        print(f"   ✅ Designed {len(product_designs_by_data_type)} product specifications")

        return {
            'naics_8_digit': naics_8_digit,
            'product_designs_by_data_type': product_designs_by_data_type,
            'overall_product_strategy': overall,
            'confidence': self._calculate_confidence(product_designs_by_data_type)
        }

    def _design_product_for_data_type(
        self,
        data_type: str,
        data_need: Dict,
        vendors: Dict,
        market: Dict,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """Design product for a specific data type"""

        # Phase 1: API design patterns
        api_results = self._search_api_patterns(data_type, run_id)

        # Phase 2: Pricing models
        pricing_results = self._search_pricing_models(data_type, segment_description, run_id)

        # Phase 3: Integration requirements
        integration_results = self._search_integration_needs(segment_description, run_id)

        # Use LLM to design product
        product_design = self._generate_product_design(
            data_type,
            data_need,
            vendors,
            market,
            api_results,
            pricing_results,
            integration_results,
            segment_description
        )

        return product_design

    def _search_api_patterns(
        self,
        data_type: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for API design patterns for similar data products"""

        queries = [
            f'"{data_type}" API documentation',
            f'data API best practices {data_type}',
            f'"{data_type}" REST API design'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_product_designer',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_pricing_models(
        self,
        data_type: str,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for pricing models and tiers"""

        queries = [
            f'data API pricing tiers {data_type}',
            f'SaaS pricing strategy {segment_description}',
            f'"{data_type}" freemium model'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_product_designer',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_integration_needs(
        self,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for integration requirements"""

        queries = [
            f'"{segment_description}" software integrations',
            f'"{segment_description}" tech stack popular tools',
            f'"{segment_description}" API integrations needed'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_product_designer',
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

    def _generate_product_design(
        self,
        data_type: str,
        data_need: Dict,
        vendors: Dict,
        market: Dict,
        api_results: List[Dict],
        pricing_results: List[Dict],
        integration_results: List[Dict],
        segment_description: str
    ) -> Dict[str, Any]:
        """Use LLM to generate product design"""

        # Compile context
        analysis_text = f"DATA TYPE: {data_type}\n"
        analysis_text += f"SEGMENT: {segment_description}\n\n"

        analysis_text += "DATA NEED CONTEXT:\n"
        analysis_text += f"Business function: {data_need.get('business_function', 'N/A')}\n"
        analysis_text += f"Importance: {data_need.get('importance', 'N/A')}\n"
        analysis_text += f"Use cases: {', '.join(data_need.get('use_cases', []))}\n"
        pain_points = data_need.get('current_pain_points', [])
        if pain_points:
            analysis_text += f"Pain points: {', '.join(pain_points)}\n"

        analysis_text += "\nCOMPETITIVE CONTEXT:\n"
        market_assessment = vendors.get('market_assessment', {})
        analysis_text += f"Competition level: {market_assessment.get('competition_level', 'unknown')}\n"
        analysis_text += f"Opportunity type: {market_assessment.get('opportunity_type', 'unknown')}\n"
        gaps = market_assessment.get('gaps', [])
        if gaps:
            analysis_text += f"Market gaps: {', '.join(gaps)}\n"

        vendor_list = vendors.get('vendors', [])
        if vendor_list:
            analysis_text += "\nExisting vendors:\n"
            for v in vendor_list[:3]:
                analysis_text += f"- {v.get('name', 'Unknown')}: {v.get('pricing', 'N/A')}, "
                analysis_text += f"weaknesses: {', '.join(v.get('weaknesses', []))}\n"

        analysis_text += "\nMARKET SIZING:\n"
        unit_econ = market.get('unit_economics', {})
        analysis_text += f"Estimated annual price: ${unit_econ.get('estimated_price_per_customer_annual', 0):,.0f}\n"
        analysis_text += f"TAM: ${market.get('tam', {}).get('annual_tam_usd', 0):,.0f}\n"
        analysis_text += f"SAM: ${market.get('sam', {}).get('annual_sam_usd', 0):,.0f}\n"

        analysis_text += "\nAPI PATTERNS:\n"
        for r in api_results[:3]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:150]}\n"

        analysis_text += "\nPRICING RESEARCH:\n"
        for r in pricing_results[:3]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:150]}\n"

        analysis_text += "\nINTEGRATION NEEDS:\n"
        for r in integration_results[:3]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:150]}\n"

        prompt = f"""Design a data product for this opportunity:

{analysis_text}

Create a complete product specification including:

1. Product positioning and value prop
2. Technical format (API, files, dashboard)
3. Pricing tiers (typically 3: Starter, Professional, Enterprise)
4. Key integrations needed
5. Competitive differentiation
6. Go-to-market strategy

Return ONLY valid JSON:
{{
  "product_name": "<memorable name>",
  "value_proposition": "<clear one-sentence value prop>",
  "product_format": {{
    "delivery_methods": ["<api|flat_file|dashboard|data_feed>"],
    "data_format": ["<json|csv|parquet|sql>"],
    "update_frequency": "<realtime|daily|weekly|monthly>",
    "data_coverage": "<scope of data>",
    "historical_depth": "<how far back>"
  }},
  "pricing_tiers": [
    {{
      "tier_name": "Starter",
      "annual_price": <price in USD>,
      "features": ["<feature>"],
      "target_customer": "<customer type>",
      "api_calls_per_month": <number>
    }},
    {{
      "tier_name": "Professional",
      "annual_price": <price>,
      "features": ["<feature>"],
      "target_customer": "<customer type>",
      "api_calls_per_month": <number>
    }},
    {{
      "tier_name": "Enterprise",
      "annual_price": <price>,
      "features": ["<feature>"],
      "target_customer": "<customer type>",
      "api_calls_per_month": <number>
    }}
  ],
  "integrations": {{
    "priority_integrations": ["<top 3-5 tools to integrate with>"],
    "developer_tools": ["<SDKs, libraries>"],
    "supported_platforms": ["<platforms>"]
  }},
  "competitive_differentiation": {{
    "unique_features": ["<what makes you different>"],
    "vs_incumbents": "<how you beat competition>",
    "positioning": "<market positioning>"
  }},
  "gtm_strategy": {{
    "target_segments": ["<specific customer segments>"],
    "primary_channels": ["<acquisition channels>"],
    "key_partnerships": ["<strategic partners>"],
    "initial_traction_plan": "<how to get first 10 customers>"
  }}
}}

Pricing guidelines:
- Starter: Small businesses, $500-5000/year
- Professional: Mid-market, $5000-50000/year
- Enterprise: Large companies, $50000-500000/year
- Base pricing on market research and competitor analysis

Be specific and actionable.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a product manager designing B2B data products. Be specific and actionable."),
                HumanMessage(content=prompt)
            ])

            result = self._parse_json(response.content)
            if not result:
                return self._get_default_product_design()

            return result

        except Exception as e:
            print(f"     ❌ Product design failed: {e}")
            return self._get_default_product_design()

    def _get_default_product_design(self) -> Dict[str, Any]:
        """Return default product design structure"""
        return {
            'product_name': 'Unknown',
            'value_proposition': 'Insufficient data to design product',
            'product_format': {
                'delivery_methods': [],
                'data_format': [],
                'update_frequency': 'unknown',
                'data_coverage': 'unknown',
                'historical_depth': 'unknown'
            },
            'pricing_tiers': [],
            'integrations': {
                'priority_integrations': [],
                'developer_tools': [],
                'supported_platforms': []
            },
            'competitive_differentiation': {
                'unique_features': [],
                'vs_incumbents': '',
                'positioning': ''
            },
            'gtm_strategy': {
                'target_segments': [],
                'primary_channels': [],
                'key_partnerships': [],
                'initial_traction_plan': ''
            }
        }

    def _design_overall_strategy(
        self,
        product_designs_by_data_type: Dict,
        segment_description: str
    ) -> Dict[str, Any]:
        """Design overall product portfolio strategy"""

        if not product_designs_by_data_type:
            return {
                'product_portfolio_approach': 'Insufficient data',
                'cross_sell_opportunities': [],
                'platform_vision': ''
            }

        # Analyze if products should be bundled or separate
        num_products = len(product_designs_by_data_type)

        if num_products == 1:
            approach = 'Single product focus'
        elif num_products <= 3:
            approach = 'Multi-product portfolio with potential bundling'
        else:
            approach = 'Platform approach with unified access to multiple datasets'

        # Identify cross-sell opportunities
        cross_sell = []
        if num_products >= 2:
            cross_sell.append('Bundle discount for multiple data products')
            cross_sell.append('Unified API access across all datasets')
            cross_sell.append('Cross-dataset analytics and insights')

        # Platform vision
        if num_products >= 3:
            vision = f'Build a comprehensive data platform for {segment_description}, providing one-stop access to all critical operational data needs'
        elif num_products == 2:
            vision = f'Start with core data products and expand based on customer demand within {segment_description}'
        else:
            vision = f'Establish market leadership in single high-value data product for {segment_description}'

        return {
            'product_portfolio_approach': approach,
            'cross_sell_opportunities': cross_sell,
            'platform_vision': vision
        }

    def _calculate_confidence(
        self,
        product_designs_by_data_type: Dict
    ) -> float:
        """Calculate confidence in product designs"""

        if not product_designs_by_data_type:
            return 0.1

        # Count designs with pricing tiers
        designs_with_pricing = sum(
            1 for design in product_designs_by_data_type.values()
            if design.get('pricing_tiers') and len(design.get('pricing_tiers', [])) > 0
        )

        coverage = designs_with_pricing / len(product_designs_by_data_type)
        return max(0.4, min(0.85, coverage))

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
    # Test data product designer
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

    designer = DataProductDesigner(llm)

    # Test with sample data
    sample_needs = [
        {
            'data_type': 'Worker compensation insurance rates by state and job classification',
            'business_function': 'Insurance pricing and risk assessment',
            'importance': 'critical',
            'use_cases': ['Premium calculation', 'Risk assessment'],
            'current_pain_points': ['Expensive', 'Fragmented sources']
        }
    ]

    sample_vendors = {
        'vendors_by_data_type': {
            'Worker compensation insurance rates by state and job classification': {
                'vendors': [
                    {
                        'name': 'NCCI',
                        'pricing': '$10000-50000/year',
                        'weaknesses': ['Expensive', 'Complex integration']
                    }
                ],
                'market_assessment': {
                    'competition_level': 'oligopoly',
                    'opportunity_type': 'disruption',
                    'gaps': ['Affordable options for small insurers', 'Modern API']
                }
            }
        }
    }

    sample_market = {
        'market_sizing_by_data_type': {
            'Worker compensation insurance rates by state and job classification': {
                'tam': {'annual_tam_usd': 50000000},
                'sam': {'annual_sam_usd': 20000000},
                'unit_economics': {'estimated_price_per_customer_annual': 15000}
            }
        }
    }

    result = designer.design_product(
        data_needs=sample_needs,
        vendor_landscape=sample_vendors,
        market_sizing=sample_market,
        naics_8_digit="52412601",
        segment_description="Direct Property and Casualty Insurance Carriers"
    )

    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    print(json.dumps(result, indent=2))
