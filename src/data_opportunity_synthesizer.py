"""
Data Opportunity Synthesizer Agent

Synthesizes all analysis into final ranked opportunity reports with composite scoring.
Generates actionable recommendations and executive summaries.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re


class DataOpportunitySynthesizer:
    """Synthesizes all analyses into final ranked opportunity reports"""

    def __init__(self, llm: ChatOpenAI, audit_db=None):
        """
        Initialize Data Opportunity Synthesizer

        Args:
            llm: Language model for synthesis
            audit_db: Optional AuditDatabase for operation tracking
        """
        self.llm = llm
        self.audit_db = audit_db

    def synthesize_opportunities(
        self,
        naics_8_digit: str,
        segment_description: str,
        data_needs: Dict[str, Any],
        vendor_landscape: Dict[str, Any],
        source_mapping: Dict[str, Any],
        market_sizing: Dict[str, Any],
        moat_analysis: Dict[str, Any],
        product_design: Dict[str, Any],
        run_id: str = None
    ) -> Dict[str, Any]:
        """
        Synthesize all analyses into ranked opportunities

        Args:
            naics_8_digit: 8-digit NAICS code
            segment_description: Segment description
            data_needs: Results from DataNeedsResearcher
            vendor_landscape: Results from VendorIntelligenceAgent
            source_mapping: Results from DataSourceMapper
            market_sizing: Results from DataMarketSizer
            moat_analysis: Results from DataMoatAnalyzer
            product_design: Results from DataProductDesigner
            run_id: Audit trail run ID

        Returns:
            {
                'naics_8_digit': str,
                'segment_description': str,
                'opportunities': [
                    {
                        'rank': int,
                        'data_type': str,
                        'opportunity_type': str,  # white-space, disruption, aggregation
                        'composite_score': float,  # 0-100
                        'tier': str,  # TIER_1, TIER_2, TIER_3, PASS
                        'dimension_scores': {
                            'market_size': float,  # 0-100
                            'moat': float,
                            'accessibility': float,
                            'competition': float,
                            'unit_economics': float
                        },
                        'key_insights': {
                            'market_opportunity': str,
                            'competitive_positioning': str,
                            'go_to_market': str,
                            'risks': List[str],
                            'timeline_to_launch': str
                        },
                        'product_summary': {
                            'product_name': str,
                            'pricing_range': str,
                            'target_customers': str
                        },
                        'financials': {
                            'estimated_tam': float,
                            'year1_revenue_potential': float,
                            'year3_revenue_potential': float,
                            'gross_margin_pct': float
                        },
                        'next_steps': List[str]
                    }
                ],
                'executive_summary': {
                    'segment_overview': str,
                    'total_opportunities_identified': int,
                    'tier1_count': int,
                    'tier2_count': int,
                    'total_tam': float,
                    'recommended_priority': str,
                    'key_themes': List[str]
                },
                'analysis_metadata': {
                    'data_needs_found': int,
                    'avg_confidence': float,
                    'search_queries_executed': int
                }
            }
        """
        print(f"\n🔄 Synthesizing opportunities for {naics_8_digit}...")

        # Extract data needs list
        data_needs_list = data_needs.get('data_needs', [])

        # Score each opportunity
        opportunities = []
        for data_need in data_needs_list[:5]:  # Top 5
            data_type = data_need.get('data_type', '')
            if not data_type:
                continue

            opportunity = self._score_opportunity(
                data_type,
                data_need,
                vendor_landscape,
                source_mapping,
                market_sizing,
                moat_analysis,
                product_design
            )

            opportunities.append(opportunity)

        # Sort by composite score
        opportunities.sort(key=lambda x: x['composite_score'], reverse=True)

        # Assign ranks
        for i, opp in enumerate(opportunities, 1):
            opp['rank'] = i

        # Generate executive summary
        exec_summary = self._generate_executive_summary(
            segment_description,
            opportunities,
            data_needs,
            vendor_landscape,
            market_sizing
        )

        # Analysis metadata
        metadata = self._generate_metadata(
            data_needs,
            vendor_landscape,
            source_mapping,
            market_sizing,
            moat_analysis,
            product_design
        )

        print(f"   ✅ Synthesized {len(opportunities)} opportunities")
        print(f"   🎯 TIER_1: {exec_summary['tier1_count']}, TIER_2: {exec_summary['tier2_count']}")

        return {
            'naics_8_digit': naics_8_digit,
            'segment_description': segment_description,
            'opportunities': opportunities,
            'executive_summary': exec_summary,
            'analysis_metadata': metadata
        }

    def _score_opportunity(
        self,
        data_type: str,
        data_need: Dict,
        vendor_landscape: Dict,
        source_mapping: Dict,
        market_sizing: Dict,
        moat_analysis: Dict,
        product_design: Dict
    ) -> Dict[str, Any]:
        """Score a single opportunity across all dimensions"""

        # Extract relevant data for this data type
        vendors = vendor_landscape.get('vendors_by_data_type', {}).get(data_type, {})
        sources = source_mapping.get('sources_by_data_type', {}).get(data_type, {})
        market = market_sizing.get('market_sizing_by_data_type', {}).get(data_type, {})
        moat = moat_analysis.get('moat_analysis_by_data_type', {}).get(data_type, {})
        product = product_design.get('product_designs_by_data_type', {}).get(data_type, {})

        # Calculate dimension scores (0-100 scale)
        market_size_score = self._score_market_size(market)
        moat_score = self._score_moat(moat)
        accessibility_score = self._score_accessibility(sources)
        competition_score = self._score_competition(vendors)
        unit_econ_score = self._score_unit_economics(market)

        # Weighted composite score
        # Market Size: 30%, Moat: 25%, Accessibility: 20%, Competition: 15%, Unit Economics: 10%
        composite_score = (
            market_size_score * 0.30 +
            moat_score * 0.25 +
            accessibility_score * 0.20 +
            competition_score * 0.15 +
            unit_econ_score * 0.10
        )

        # Determine tier
        if composite_score >= 80:
            tier = 'TIER_1'
        elif composite_score >= 60:
            tier = 'TIER_2'
        elif composite_score >= 40:
            tier = 'TIER_3'
        else:
            tier = 'PASS'

        # Opportunity type
        opportunity_type = vendors.get('market_assessment', {}).get('opportunity_type', 'unknown')

        # Generate insights using LLM
        insights = self._generate_insights(
            data_type, data_need, vendors, sources, market, moat, product,
            composite_score, tier
        )

        # Product summary
        product_summary = {
            'product_name': product.get('product_name', 'N/A'),
            'pricing_range': self._get_pricing_range(product),
            'target_customers': self._get_target_customers(product)
        }

        # Financials
        financials = {
            'estimated_tam': market.get('tam', {}).get('annual_tam_usd', 0),
            'year1_revenue_potential': market.get('som', {}).get('annual_som_year1_usd', 0),
            'year3_revenue_potential': market.get('som', {}).get('annual_som_year3_usd', 0),
            'gross_margin_pct': market.get('unit_economics', {}).get('estimated_gross_margin_pct', 0)
        }

        # Next steps
        next_steps = self._generate_next_steps(tier, opportunity_type, sources, vendors)

        return {
            'rank': 0,  # Will be set after sorting
            'data_type': data_type,
            'opportunity_type': opportunity_type,
            'composite_score': round(composite_score, 1),
            'tier': tier,
            'dimension_scores': {
                'market_size': round(market_size_score, 1),
                'moat': round(moat_score, 1),
                'accessibility': round(accessibility_score, 1),
                'competition': round(competition_score, 1),
                'unit_economics': round(unit_econ_score, 1)
            },
            'key_insights': insights,
            'product_summary': product_summary,
            'financials': financials,
            'next_steps': next_steps
        }

    def _score_market_size(self, market: Dict) -> float:
        """Score market size dimension (0-100)"""
        tam = market.get('tam', {}).get('annual_tam_usd', 0)
        sam = market.get('sam', {}).get('annual_sam_usd', 0)

        # Score based on TAM
        if tam >= 100_000_000:  # $100M+
            tam_score = 100
        elif tam >= 50_000_000:  # $50M+
            tam_score = 80
        elif tam >= 10_000_000:  # $10M+
            tam_score = 60
        elif tam >= 5_000_000:  # $5M+
            tam_score = 40
        elif tam >= 1_000_000:  # $1M+
            tam_score = 20
        else:
            tam_score = 10

        # Adjust for SAM/TAM ratio
        if tam > 0:
            sam_ratio = sam / tam
            if sam_ratio >= 0.5:
                adjustment = 1.0
            elif sam_ratio >= 0.3:
                adjustment = 0.9
            elif sam_ratio >= 0.1:
                adjustment = 0.8
            else:
                adjustment = 0.7
        else:
            adjustment = 0.5

        return tam_score * adjustment

    def _score_moat(self, moat: Dict) -> float:
        """Score moat dimension (0-100)"""
        composite_moat = moat.get('composite_moat_score', 0)  # 0-10 scale
        return composite_moat * 10  # Convert to 0-100

    def _score_accessibility(self, sources: Dict) -> float:
        """Score data accessibility dimension (0-100)"""
        primary_sources = sources.get('primary_sources', [])
        if not primary_sources:
            return 20

        # Count accessible sources
        accessible_count = sum(
            1 for source in primary_sources
            if source.get('accessibility') in ['public', 'licensable']
        )

        if not primary_sources:
            return 20

        accessibility_ratio = accessible_count / len(primary_sources)

        # Check collection complexity
        low_complexity = sum(
            1 for source in primary_sources
            if source.get('collection_complexity') == 'low'
        )

        complexity_ratio = low_complexity / len(primary_sources)

        # Combined score
        score = (accessibility_ratio * 0.6 + complexity_ratio * 0.4) * 100

        return max(20, score)  # Minimum 20

    def _score_competition(self, vendors: Dict) -> float:
        """Score competition dimension (0-100)"""
        market_assessment = vendors.get('market_assessment', {})
        competition_level = market_assessment.get('competition_level', '')
        opportunity_type = market_assessment.get('opportunity_type', '')

        # Base score by competition level
        if competition_level == 'monopolistic':
            base_score = 30  # Hard to compete
        elif competition_level == 'oligopoly':
            base_score = 50  # Moderate opportunity
        elif competition_level == 'competitive':
            base_score = 60  # Good opportunity
        elif competition_level == 'fragmented':
            base_score = 80  # Great opportunity
        else:
            base_score = 50

        # Adjust for opportunity type
        if opportunity_type == 'white-space':
            adjustment = 1.3
        elif opportunity_type == 'disruption':
            adjustment = 1.1
        elif opportunity_type == 'aggregation':
            adjustment = 1.0
        else:
            adjustment = 0.9

        score = base_score * adjustment
        return min(100, score)  # Cap at 100

    def _score_unit_economics(self, market: Dict) -> float:
        """Score unit economics dimension (0-100)"""
        unit_econ = market.get('unit_economics', {})

        ltv_cac = unit_econ.get('ltv_cac_ratio', 0)
        gross_margin = unit_econ.get('estimated_gross_margin_pct', 0)
        payback = unit_econ.get('payback_period_months', 99)

        # Score LTV/CAC ratio
        if ltv_cac >= 5:
            ltv_score = 100
        elif ltv_cac >= 3:
            ltv_score = 80
        elif ltv_cac >= 2:
            ltv_score = 60
        elif ltv_cac >= 1:
            ltv_score = 40
        else:
            ltv_score = 20

        # Score gross margin
        if gross_margin >= 80:
            margin_score = 100
        elif gross_margin >= 70:
            margin_score = 80
        elif gross_margin >= 60:
            margin_score = 60
        elif gross_margin >= 50:
            margin_score = 40
        else:
            margin_score = 20

        # Score payback period
        if payback <= 6:
            payback_score = 100
        elif payback <= 12:
            payback_score = 80
        elif payback <= 18:
            payback_score = 60
        elif payback <= 24:
            payback_score = 40
        else:
            payback_score = 20

        # Weighted average
        score = ltv_score * 0.4 + margin_score * 0.4 + payback_score * 0.2
        return score

    def _generate_insights(
        self,
        data_type: str,
        data_need: Dict,
        vendors: Dict,
        sources: Dict,
        market: Dict,
        moat: Dict,
        product: Dict,
        composite_score: float,
        tier: str
    ) -> Dict[str, Any]:
        """Generate key insights using LLM"""

        # Compile context
        context = f"DATA TYPE: {data_type}\n"
        context += f"COMPOSITE SCORE: {composite_score:.1f}/100 ({tier})\n\n"

        context += f"IMPORTANCE: {data_need.get('importance', 'N/A')}\n"
        context += f"USE CASES: {', '.join(data_need.get('use_cases', []))}\n\n"

        context += f"TAM: ${market.get('tam', {}).get('annual_tam_usd', 0):,.0f}\n"
        context += f"Year 1 SOM: ${market.get('som', {}).get('annual_som_year1_usd', 0):,.0f}\n"
        context += f"Competition: {vendors.get('market_assessment', {}).get('competition_level', 'unknown')}\n"
        context += f"Moat Score: {moat.get('composite_moat_score', 0):.1f}/10\n"

        prompt = f"""Generate concise insights for this data opportunity:

{context}

Return ONLY valid JSON:
{{
  "market_opportunity": "<1 sentence on market size and growth>",
  "competitive_positioning": "<1 sentence on how to compete>",
  "go_to_market": "<1 sentence on GTM approach>",
  "risks": ["<top 2-3 risks>"],
  "timeline_to_launch": "<6 months|1 year|18+ months>"
}}

Be concise and actionable.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a strategic analyst. Provide concise, actionable insights."),
                HumanMessage(content=prompt)
            ])

            result = self._parse_json(response.content)
            if not result:
                return self._get_default_insights()

            return result

        except Exception as e:
            print(f"     ⚠️  Insight generation warning: {e}")
            return self._get_default_insights()

    def _get_default_insights(self) -> Dict[str, Any]:
        """Return default insights structure"""
        return {
            'market_opportunity': 'Analysis in progress',
            'competitive_positioning': 'Requires further research',
            'go_to_market': 'To be determined',
            'risks': ['Insufficient data for risk assessment'],
            'timeline_to_launch': 'TBD'
        }

    def _get_pricing_range(self, product: Dict) -> str:
        """Extract pricing range from product"""
        tiers = product.get('pricing_tiers', [])
        if not tiers:
            return 'TBD'

        prices = [tier.get('annual_price', 0) for tier in tiers if tier.get('annual_price', 0) > 0]
        if not prices:
            return 'TBD'

        min_price = min(prices)
        max_price = max(prices)
        return f"${min_price:,.0f} - ${max_price:,.0f}/year"

    def _get_target_customers(self, product: Dict) -> str:
        """Extract target customers from product"""
        gtm = product.get('gtm_strategy', {})
        segments = gtm.get('target_segments', [])
        if segments:
            return ', '.join(segments[:3])
        return 'To be defined'

    def _generate_next_steps(
        self,
        tier: str,
        opportunity_type: str,
        sources: Dict,
        vendors: Dict
    ) -> List[str]:
        """Generate recommended next steps based on tier"""

        if tier == 'TIER_1':
            steps = [
                'Conduct detailed customer discovery interviews (10-15 target customers)',
                'Build MVP with core data pipeline and basic API',
                'Secure pilot customers with LOIs',
                'Raise pre-seed/seed funding'
            ]
        elif tier == 'TIER_2':
            steps = [
                'Validate data need with 5-10 target customer conversations',
                'Assess data acquisition feasibility and costs',
                'Prototype basic data product',
                'Evaluate competitive positioning'
            ]
        elif tier == 'TIER_3':
            steps = [
                'Monitor market developments',
                'Build relationships with potential data sources',
                'Track competitor movements'
            ]
        else:  # PASS
            steps = [
                'Deprioritize - monitor only if market conditions change'
            ]

        return steps

    def _generate_executive_summary(
        self,
        segment_description: str,
        opportunities: List[Dict],
        data_needs: Dict,
        vendor_landscape: Dict,
        market_sizing: Dict
    ) -> Dict[str, Any]:
        """Generate executive summary"""

        tier1_count = sum(1 for opp in opportunities if opp['tier'] == 'TIER_1')
        tier2_count = sum(1 for opp in opportunities if opp['tier'] == 'TIER_2')

        total_tam = sum(opp['financials']['estimated_tam'] for opp in opportunities)

        # Recommend priority
        if tier1_count > 0:
            top_opp = opportunities[0]
            recommended = f"Pursue '{top_opp['data_type'][:50]}...' immediately (Score: {top_opp['composite_score']}/100)"
        elif tier2_count > 0:
            recommended = "Validate top TIER_2 opportunities before pursuing"
        else:
            recommended = "No strong opportunities identified - monitor market"

        # Extract key themes
        themes = []
        opportunity_types = [opp['opportunity_type'] for opp in opportunities]
        if 'white-space' in opportunity_types:
            themes.append("Underserved data needs with no clear market leader")
        if 'disruption' in opportunity_types:
            themes.append("Opportunities to disrupt expensive/weak incumbents")
        if 'aggregation' in opportunity_types:
            themes.append("Fragmented markets ripe for consolidation")

        avg_moat = sum(opp['dimension_scores']['moat'] for opp in opportunities) / len(opportunities) if opportunities else 0
        if avg_moat >= 60:
            themes.append("Strong moat potential across opportunities")

        segment_overview = f"{segment_description}: {len(opportunities)} data product opportunities identified"

        return {
            'segment_overview': segment_overview,
            'total_opportunities_identified': len(opportunities),
            'tier1_count': tier1_count,
            'tier2_count': tier2_count,
            'total_tam': total_tam,
            'recommended_priority': recommended,
            'key_themes': themes
        }

    def _generate_metadata(
        self,
        data_needs: Dict,
        vendor_landscape: Dict,
        source_mapping: Dict,
        market_sizing: Dict,
        moat_analysis: Dict,
        product_design: Dict
    ) -> Dict[str, Any]:
        """Generate analysis metadata"""

        confidences = [
            data_needs.get('confidence', 0),
            vendor_landscape.get('confidence', 0),
            source_mapping.get('confidence', 0),
            market_sizing.get('confidence', 0),
            moat_analysis.get('confidence', 0),
            product_design.get('confidence', 0)
        ]

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            'data_needs_found': len(data_needs.get('data_needs', [])),
            'avg_confidence': round(avg_confidence, 2),
            'search_queries_executed': 0  # Will be populated from audit DB
        }

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
    # Test synthesizer
    print("Data Opportunity Synthesizer - Test mode")
    print("Use in integration with full pipeline")
