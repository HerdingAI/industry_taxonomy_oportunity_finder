"""
Synthesizer Agent - Creates final insight-dense reports
Principle: Depth ≠ Length
Every sentence must earn its place
"""

import json
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class SynthesizerAgent:
    """Synthesizes all analysis into concise, actionable reports"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def synthesize(
        self,
        research: Dict[str, Any],
        strategic: Dict[str, Any],
        quantitative: Dict[str, Any]
    ) -> str:
        """
        Create final report - max 2-3 pages, all signal, no noise
        """

        print(f"📄 Synthesizing final report...")

        naics_code = research.get('naics_code')
        industry_name = research.get('industry_name')

        # Get top opportunity
        opportunities = quantitative.get('opportunities', [])
        top_opp = opportunities[0] if opportunities else None

        # Generate concise report
        report = self._generate_report(research, strategic, quantitative, top_opp)

        print(f"✅ Report complete ({len(report)} chars)")

        return report

    def _generate_report(
        self,
        research: Dict,
        strategic: Dict,
        quant: Dict,
        top_opp: Dict
    ) -> str:
        """Generate insight-dense markdown report"""

        naics_code = research.get('naics_code')
        industry_name = research.get('industry_name')

        # Extract key data
        market_size = research.get('market_size_usd')
        growth_rate = research.get('growth_rate')
        establishments = research.get('establishments')
        hhi = research.get('hhi_index')

        porters = strategic.get('porters_five_forces', {})
        overall_attractiveness = porters.get('overall_attractiveness', 50)

        positioning = strategic.get('strategic_positioning', {})

        # Format report components
        market_line = self._format_market_reality(research, quant.get('industry_metrics', {}))
        strategic_section = self._format_strategic_insight(porters, positioning)
        opportunity_section = self._format_top_opportunity(top_opp) if top_opp else ""

        # Build final report
        confidence = research.get('confidence', 0.5)
        verdict = self._get_verdict(overall_attractiveness, top_opp)

        report = f"""## NAICS {naics_code}: {industry_name}

**Score**: {overall_attractiveness}/100 | **Confidence**: {confidence:.0%} | **Verdict**: {verdict}

### Market Reality
{market_line}

### Strategic Insight
{strategic_section}

{opportunity_section}

---
*Analysis confidence: {confidence:.0%} | Data sources: Web search, industry databases*
"""

        return report

    def _format_market_reality(self, research: Dict, metrics: Dict) -> str:
        """Format market reality section - numbers and trends"""

        market_size = research.get('market_size_usd')
        growth = research.get('growth_rate')
        establishments = research.get('establishments')
        hhi = research.get('hhi_index')
        concentration = research.get('market_concentration', 'unknown')

        lines = []

        # Market size and structure
        if market_size:
            size_b = market_size / 1e9
            if growth:
                growth_pct = growth * 100
                lines.append(f"- ${size_b:.1f}B market, {growth_pct:.1f}% CAGR")
            else:
                lines.append(f"- ${size_b:.1f}B market")

        # Market structure
        if establishments and hhi:
            hhi_interpretation = "hyper-fragmented" if hhi < 500 else "fragmented" if hhi < 1000 else "moderate concentration" if hhi < 1800 else "concentrated"
            lines.append(f"- {establishments:,} firms (HHI={hhi}: {hhi_interpretation})")

        # Firm economics
        avg_rev = metrics.get('avg_revenue_per_firm')
        if avg_rev:
            lines.append(f"- Avg firm revenue: ${avg_rev/1e6:.1f}M")

        # Key trends
        trends = research.get('key_trends', [])
        if trends:
            trend_list = ", ".join(trends[:3])  # Max 3
            lines.append(f"- Key trends: {trend_list}")

        # Digital maturity
        digital = research.get('digital_maturity')
        if digital:
            lines.append(f"- Digital maturity: {digital}")

        return "\n".join(lines) if lines else "Limited market data available"

    def _format_strategic_insight(self, porters: Dict, positioning: Dict) -> str:
        """Format strategic analysis section"""

        sections = []

        # Porter's verdict
        overall = porters.get('overall_attractiveness', 50)
        verdict = porters.get('strategic_verdict', '')
        if verdict:
            sections.append(f"**Porter's Analysis**: {verdict}")

        # Key forces (only if extreme)
        forces_to_show = []
        for force_name, force_key in [
            ("Rivalry", "competitive_rivalry"),
            ("Entry barriers", "new_entrant_threat"),
            ("Substitutes", "substitute_threat")
        ]:
            force = porters.get(force_key, {})
            score = force.get('score', 50)
            if score > 75 or score < 30:  # Only show extreme scores
                insight = force.get('insight', '')
                if insight:
                    forces_to_show.append(f"- **{force_name}**: {insight}")

        if forces_to_show:
            sections.append("\n".join(forces_to_show))

        # Strategic positioning
        best = positioning.get('best_positioning')
        worst = positioning.get('worst_positioning')
        if best:
            sections.append(f"\n**Winning strategy**: {best}")
        if worst:
            sections.append(f"**Avoid**: {worst}")

        white_space = positioning.get('white_space_opportunity')
        if white_space:
            sections.append(f"**White space**: {white_space}")

        return "\n\n".join(sections) if sections else "Strategic analysis pending"

    def _format_top_opportunity(self, opp: Dict) -> str:
        """Format top opportunity section - the money shot"""

        if not opp:
            return ""

        title = opp.get('opportunity_title', 'Unnamed Opportunity')
        description = opp.get('opportunity_description', '')
        score = opp.get('risk_adjusted_score', 0)

        sections = []

        # Header
        sections.append(f"### Top Opportunity: {title} (Score: {score:.0f}/100)\n")

        # One-line value prop
        if description:
            sections.append(f"**The Play**: {description}\n")

        # Numbers
        market_sizing = opp.get('market_sizing', {})
        unit_econ = opp.get('unit_economics', {})

        numbers = []

        tam = market_sizing.get('tam_usd')
        sam = market_sizing.get('sam_usd')
        som = market_sizing.get('som_y3_usd')

        if tam or sam:
            market_line = []
            if tam:
                market_line.append(f"TAM ${tam/1e9:.1f}B")
            if sam:
                market_line.append(f"SAM ${sam/1e9:.1f}B")
            if som:
                market_line.append(f"SOM Y3 ${som/1e6:.0f}M")
            numbers.append("- " + ", ".join(market_line))

        arpu = unit_econ.get('arpu')
        margin = unit_econ.get('gross_margin')
        ltv_cac = unit_econ.get('ltv_cac_ratio')

        if arpu or margin or ltv_cac:
            econ_line = []
            if arpu:
                econ_line.append(f"${arpu:,} ARPU")
            if margin:
                econ_line.append(f"{margin:.0%} margin")
            if ltv_cac:
                econ_line.append(f"{ltv_cac:.1f}:1 LTV:CAC")
            numbers.append("- " + ", ".join(econ_line))

        if numbers:
            sections.append("**Numbers**:\n" + "\n".join(numbers) + "\n")

        # Strategic rationale
        rationale = opp.get('strategic_rationale', {})

        why_now = rationale.get('why_now')
        why_unsolved = rationale.get('why_unsolved')
        moat = rationale.get('key_moat')
        threat = rationale.get('competitive_threat')

        strat_lines = []
        if why_now:
            strat_lines.append(f"**Why Now**: {why_now}")
        if why_unsolved:
            strat_lines.append(f"**Why Unsolved**: {why_unsolved}")
        if moat:
            strat_lines.append(f"**Moat**: {moat}")

        if strat_lines:
            sections.append("\n".join(strat_lines) + "\n")

        # Risks
        risk_assessment = opp.get('risk_assessment', {})
        key_risks = risk_assessment.get('key_risks', [])

        if key_risks:
            risk = key_risks[0]  # Show top risk only
            risk_name = risk.get('risk', '')
            risk_prob = risk.get('probability', 0)
            if risk_name:
                sections.append(f"**Key Risk**: {risk_name} ({risk_prob:.0%} probability)")

        return "\n".join(sections)

    def _get_verdict(self, attractiveness: int, top_opp: Dict) -> str:
        """Generate verdict based on scores"""

        if top_opp:
            opp_score = top_opp.get('risk_adjusted_score', 0)
            if opp_score >= 80:
                return "STRONG OPPORTUNITY"
            elif opp_score >= 65:
                return "MODERATE OPPORTUNITY"
            else:
                return "WEAK OPPORTUNITY"
        else:
            if attractiveness >= 75:
                return "ATTRACTIVE INDUSTRY"
            elif attractiveness >= 55:
                return "MODERATE POTENTIAL"
            else:
                return "UNATTRACTIVE"


if __name__ == "__main__":
    # Test synthesizer with mock data
    import os
    from dotenv import load_dotenv

    load_dotenv()

    llm = ChatOpenAI(
        model="openrouter/sherlock-think-alpha",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1"
    )

    # Mock data
    research = {
        'naics_code': '541511',
        'industry_name': 'Custom Computer Programming Services',
        'market_size_usd': 185000000000,
        'growth_rate': 0.082,
        'establishments': 89400,
        'hhi_index': 182,
        'market_concentration': 'highly fragmented',
        'key_trends': ['AI code generation', 'offshore competition', 'cloud migration'],
        'digital_maturity': 'high',
        'confidence': 0.76
    }

    strategic = {
        'porters_five_forces': {
            'overall_attractiveness': 67,
            'strategic_verdict': 'Unattractive for generalists; attractive for vertical specialists with moats',
            'competitive_rivalry': {
                'score': 78,
                'insight': 'Fragmented (HHI=182) but commoditizing. Price war at low-end; specialization wins high-end.'
            },
            'new_entrant_threat': {
                'score': 82,
                'insight': 'Near-zero barriers. Cloud + no-code = solo operators viable. Differentiation critical.'
            }
        },
        'strategic_positioning': {
            'best_positioning': 'Vertical specialization with proprietary data moats',
            'worst_positioning': 'Generalist hourly billing',
            'white_space_opportunity': 'Productized vertical AI solutions with compliance built-in'
        }
    }

    quantitative = {
        'opportunities': [{
            'opportunity_title': 'Healthcare-Specific AI Code Generator',
            'opportunity_description': 'HL7/FHIR-native code assistant with built-in HIPAA compliance',
            'risk_adjusted_score': 84.5,
            'market_sizing': {
                'tam_usd': 8200000000,
                'sam_usd': 2100000000,
                'som_y3_usd': 105000000
            },
            'unit_economics': {
                'arpu': 7188,
                'gross_margin': 0.87,
                'ltv_cac_ratio': 7.0
            },
            'strategic_rationale': {
                'why_now': 'GenAI crossed quality threshold; HIPAA-compliant code gen unsolved',
                'why_unsolved': 'Requires rare combo of healthcare domain + AI expertise',
                'key_moat': 'Compliance library + health system partnerships (data flywheel)',
                'competitive_threat': 'Epic/GitHub could bundle competing features'
            },
            'risk_assessment': {
                'key_risks': [
                    {'risk': 'Epic bundles competing feature', 'probability': 0.35, 'impact_usd': -40000000}
                ]
            }
        }],
        'industry_metrics': {
            'avg_revenue_per_firm': 2069000,
            'employees_per_firm': 9.2
        }
    }

    synthesizer = SynthesizerAgent(llm)
    report = synthesizer.synthesize(research, strategic, quantitative)

    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(report)
