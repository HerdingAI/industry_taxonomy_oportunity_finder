"""
Vendor Intelligence Agent

Maps existing data vendor landscape, identifies incumbents, pricing, customer satisfaction,
and competitive gaps for each identified data need.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from duckduckgo_search import DDGS
import json
import re
import time


class VendorIntelligenceAgent:
    """Analyzes data vendor competitive landscape"""

    def __init__(self, llm: ChatOpenAI, audit_db=None):
        """
        Initialize Vendor Intelligence Agent

        Args:
            llm: Language model for analysis
            audit_db: Optional AuditDatabase for operation tracking
        """
        self.llm = llm
        self.audit_db = audit_db
        self.ddg = DDGS()

    def analyze_vendor_landscape(
        self,
        data_needs: List[Dict],
        naics_8_digit: str,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """
        Map vendor landscape for each identified data need

        Args:
            data_needs: List of data needs from DataNeedsResearcher
            naics_8_digit: 8-digit NAICS code
            segment_description: Segment description
            run_id: Audit trail run ID

        Returns:
            {
                'naics_8_digit': str,
                'vendors_by_data_type': {
                    '<data_type>': {
                        'vendors': [
                            {
                                'name': str,
                                'pricing': str,
                                'coverage': str,
                                'update_frequency': str,
                                'data_format': str,
                                'market_position': str,
                                'customer_complaints': List[str],
                                'customer_satisfaction': str,
                                'strengths': List[str],
                                'weaknesses': List[str]
                            }
                        ],
                        'market_assessment': {
                            'competition_level': str,
                            'pricing_pressure': str,
                            'opportunity_type': str,
                            'barriers_to_entry': str,
                            'gaps': List[str]
                        }
                    }
                },
                'overall_landscape': {
                    'total_vendors_found': int,
                    'dominant_players': List[str],
                    'market_concentration': str,
                    'avg_customer_satisfaction': float,
                    'common_complaints': List[str]
                },
                'confidence': float
            }
        """
        print(f"\n📊 Analyzing vendor landscape for {len(data_needs)} data types...")

        vendors_by_data_type = {}

        # Analyze vendors for each data need
        for i, data_need in enumerate(data_needs[:5], 1):  # Top 5 data needs
            data_type = data_need.get('data_type', '')
            if not data_type:
                continue

            print(f"   Analyzing vendors for data type {i}/{min(len(data_needs), 5)}: {data_type[:50]}...")

            vendor_analysis = self._analyze_vendors_for_data_type(
                data_type, segment_description, run_id
            )

            vendors_by_data_type[data_type] = vendor_analysis

        # Overall landscape summary
        overall = self._summarize_landscape(vendors_by_data_type)

        print(f"   ✅ Found {overall['total_vendors_found']} total vendors")

        return {
            'naics_8_digit': naics_8_digit,
            'vendors_by_data_type': vendors_by_data_type,
            'overall_landscape': overall,
            'confidence': self._calculate_confidence(vendors_by_data_type)
        }

    def _analyze_vendors_for_data_type(
        self,
        data_type: str,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """Analyze vendors for a specific data type"""

        # Phase 1: Vendor discovery
        vendor_results = self._search_vendors(data_type, run_id)

        # Phase 2: Pricing research
        pricing_results = self._search_pricing(data_type, run_id)

        # Phase 3: Review/satisfaction research
        review_results = self._search_reviews(data_type, run_id)

        # Use LLM to analyze and structure
        analysis = self._analyze_vendor_data(
            data_type,
            vendor_results,
            pricing_results,
            review_results
        )

        return analysis

    def _search_vendors(
        self,
        data_type: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for vendors providing this data type"""

        queries = [
            f'"{data_type}" data vendor',
            f'"{data_type}" data provider API',
            f'buy "{data_type}" subscription',
            f'"{data_type}" database provider',
            f'best "{data_type}" data source'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=5)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='vendor_intelligence_agent',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_pricing(
        self,
        data_type: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for pricing information"""

        queries = [
            f'"{data_type}" pricing cost',
            f'"{data_type}" subscription price'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='vendor_intelligence_agent',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_reviews(
        self,
        data_type: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for vendor reviews and customer satisfaction"""

        queries = [
            f'site:g2.com "{data_type}"',
            f'site:capterra.com "{data_type}"',
            f'site:reddit.com "{data_type}" vendor review'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='vendor_intelligence_agent',
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

    def _analyze_vendor_data(
        self,
        data_type: str,
        vendor_results: List[Dict],
        pricing_results: List[Dict],
        review_results: List[Dict]
    ) -> Dict[str, Any]:
        """Use LLM to analyze vendor landscape"""

        # Compile research
        analysis_text = f"DATA TYPE: {data_type}\n\n"
        analysis_text += "VENDOR DISCOVERY:\n"
        for r in vendor_results[:10]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        analysis_text += "\nPRICING RESEARCH:\n"
        for r in pricing_results[:5]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        analysis_text += "\nREVIEWS/SATISFACTION:\n"
        for r in review_results[:5]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        prompt = f"""Analyze the vendor landscape for: {data_type}

{analysis_text}

Return ONLY valid JSON:
{{
  "vendors": [
    {{
      "name": "<vendor name>",
      "pricing": "<pricing info or estimate>",
      "coverage": "<what they cover>",
      "update_frequency": "<how often updated>",
      "data_format": "<API, Excel, etc>",
      "market_position": "<dominant|strong|moderate|weak>",
      "customer_complaints": ["<specific complaint>"],
      "customer_satisfaction": "<score or estimate>",
      "strengths": ["<strength>"],
      "weaknesses": ["<weakness>"]
    }}
  ],
  "market_assessment": {{
    "competition_level": "<monopolistic|oligopoly|competitive|fragmented>",
    "pricing_pressure": "<high|medium|low>",
    "opportunity_type": "<white-space|disruption|aggregation>",
    "barriers_to_entry": "<high|medium|low>",
    "gaps": ["<specific gap in market>"]
  }}
}}

If no vendors found, return empty vendors list with opportunity_type "white-space".
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a market intelligence analyst. Extract vendor information accurately."),
                HumanMessage(content=prompt)
            ])

            result = self._parse_json(response.content)
            if not result:
                return {
                    'vendors': [],
                    'market_assessment': {
                        'competition_level': 'unknown',
                        'pricing_pressure': 'unknown',
                        'opportunity_type': 'white-space',
                        'barriers_to_entry': 'unknown',
                        'gaps': []
                    }
                }

            return result

        except Exception as e:
            print(f"     ❌ Vendor analysis failed: {e}")
            return {
                'vendors': [],
                'market_assessment': {
                    'competition_level': 'unknown',
                    'pricing_pressure': 'unknown',
                    'opportunity_type': 'white-space',
                    'barriers_to_entry': 'unknown',
                    'gaps': []
                }
            }

    def _summarize_landscape(
        self,
        vendors_by_data_type: Dict
    ) -> Dict[str, Any]:
        """Summarize overall vendor landscape"""

        total_vendors = 0
        all_vendors = []
        all_complaints = []
        satisfactions = []

        for data_type, analysis in vendors_by_data_type.items():
            vendors = analysis.get('vendors', [])
            total_vendors += len(vendors)
            all_vendors.extend([v['name'] for v in vendors if 'name' in v])

            for v in vendors:
                if 'customer_complaints' in v:
                    all_complaints.extend(v['customer_complaints'])
                if 'customer_satisfaction' in v:
                    # Try to extract numeric rating
                    sat_str = v['customer_satisfaction']
                    match = re.search(r'(\d+\.?\d*)', sat_str)
                    if match:
                        satisfactions.append(float(match.group(1)))

        # Find dominant players (vendors mentioned multiple times)
        from collections import Counter
        vendor_counts = Counter(all_vendors)
        dominant = [v for v, count in vendor_counts.most_common(3)]

        # Calculate average satisfaction
        avg_sat = sum(satisfactions) / len(satisfactions) if satisfactions else 0

        # Find most common complaints
        complaint_counts = Counter(all_complaints)
        common_complaints = [c for c, _ in complaint_counts.most_common(5)]

        # Assess market concentration
        if len(set(all_vendors)) <= 2:
            concentration = 'high'
        elif len(set(all_vendors)) <= 5:
            concentration = 'medium'
        else:
            concentration = 'low'

        return {
            'total_vendors_found': total_vendors,
            'dominant_players': dominant,
            'market_concentration': concentration,
            'avg_customer_satisfaction': round(avg_sat, 2),
            'common_complaints': common_complaints
        }

    def _calculate_confidence(
        self,
        vendors_by_data_type: Dict
    ) -> float:
        """Calculate confidence in vendor analysis"""

        if not vendors_by_data_type:
            return 0.1

        # Count how many data types have vendor information
        types_with_vendors = sum(
            1 for analysis in vendors_by_data_type.values()
            if analysis.get('vendors')
        )

        coverage = types_with_vendors / len(vendors_by_data_type)
        return max(0.3, min(0.9, coverage))  # Confidence between 0.3 and 0.9

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
    # Test vendor intelligence agent
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

    agent = VendorIntelligenceAgent(llm)

    # Test with sample data needs
    sample_needs = [
        {
            'data_type': 'Worker compensation insurance rates by state and job classification',
            'business_function': 'Insurance pricing and risk assessment'
        }
    ]

    result = agent.analyze_vendor_landscape(
        data_needs=sample_needs,
        naics_8_digit="52412601",
        segment_description="Direct Property and Casualty Insurance Carriers"
    )

    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    print(json.dumps(result, indent=2))
