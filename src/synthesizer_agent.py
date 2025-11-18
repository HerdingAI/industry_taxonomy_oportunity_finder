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
        quantitative: Dict[str, Any],
        customer_analysis: Dict[str, Any] = None,
        automation_analysis: Dict[str, Any] = None,
        report_format: str = "comprehensive"
    ) -> str:
        """
        Create final report - max 2-3 pages, all signal, no noise

        Args:
            research: Research agent output
            strategic: Strategic agent output
            quantitative: Quantitative agent output
            customer_analysis: Product Manager agent output (optional)
            automation_analysis: Technical Data Scientist agent output (optional)
            report_format: "comprehensive" (default) or "business_model" (CLIENT/SERVICE/VALUE/REVENUE/MOAT)
        """

        print(f"📄 Synthesizing final report ({report_format} format)...")

        naics_code = research.get('naics_code')
        industry_name = research.get('industry_name')

        # Get top opportunity
        opportunities = quantitative.get('opportunities', [])
        top_opp = opportunities[0] if opportunities else None

        # Generate report based on format
        if report_format == "business_model":
            report = self._generate_business_model_report(
                research, strategic, quantitative,
                customer_analysis, automation_analysis, top_opp
            )
        else:
            # Enhanced comprehensive report with new data
            report = self._generate_comprehensive_report(
                research, strategic, quantitative,
                customer_analysis, automation_analysis, top_opp
            )

        print(f"✅ Report complete ({len(report)} chars)")

        return report

    def _generate_comprehensive_report(
        self,
        research: Dict,
        strategic: Dict,
        quant: Dict,
        customer_analysis: Dict = None,
        automation_analysis: Dict = None,
        top_opp: Dict = None
    ) -> str:
        """Generate comprehensive insight-dense markdown report"""

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

    def _generate_business_model_report(
        self,
        research: Dict,
        strategic: Dict,
        quant: Dict,
        customer_analysis: Dict = None,
        automation_analysis: Dict = None,
        top_opp: Dict = None
    ) -> str:
        """
        Generate business model report in CLIENT/SERVICE/VALUE PROP/REVENUE/MOAT format

        This is the format requested by user for final opportunity presentation
        """
        naics_code = research.get('naics_code')
        industry_name = research.get('industry_name')

        # Extract data
        vc_assessment = quant.get('vc_criteria_assessment', {})
        staleness = strategic.get('staleness_audit', {})

        # Get buyer personas from customer analysis
        personas = []
        if customer_analysis:
            personas = customer_analysis.get('buyer_personas', [])

        # Get top automation opportunities
        top_workflows = []
        if automation_analysis:
            top_opps = automation_analysis.get('top_opportunities', [])
            top_workflows = [opp.get('workflow_name') for opp in top_opps[:3]]

        report = f"""# Business Opportunity: {industry_name}

**NAICS**: {naics_code} | **VC Score**: {vc_assessment.get('overall_vc_score', 0):.1f}/100 ({vc_assessment.get('tier', 'Unknown')})

---

## 🎯 CLIENT

**Who Pays Us**:
"""

        # Add buyer personas
        if personas:
            for i, persona in enumerate(personas[:2], 1):
                role = persona.get('role', 'Unknown Role')
                authority = persona.get('decision_authority', 'unknown')
                report += f"\n{i}. **{role}** ({authority})\n"
                report += f"   - Goals: {', '.join(persona.get('primary_goals', [])[:3])}\n"
                report += f"   - Pain Points: {', '.join(persona.get('pain_points', [])[:3])}\n"
        else:
            report += "\n*Insufficient customer data - conduct VOC research*\n"

        report += f"""

---

## 💼 SERVICE

**What We Automate/Provide**:
"""

        # Add top workflows/services
        if top_workflows:
            for i, workflow in enumerate(top_workflows, 1):
                report += f"\n{i}. {workflow}\n"
        elif top_opp:
            report += f"\n1. {top_opp.get('opportunity_title', 'Unknown')}\n"
            report += f"   - {top_opp.get('opportunity_description', '')}\n"
        else:
            report += "\n*No specific automation opportunities identified*\n"

        # Add technology approach
        if automation_analysis and automation_analysis.get('top_opportunities'):
            top_auto_opp = automation_analysis['top_opportunities'][0]
            report += f"\n**Technical Approach**: {top_auto_opp.get('recommended_approach', 'GenAI-powered automation')}\n"

        report += f"""

---

## 🎁 VALUE PROPOSITION

**Why They Switch**:
"""

        # Staleness indicators
        if staleness.get('data_available') and staleness.get('staleness_score', 0) > 50:
            staleness_score = staleness.get('staleness_score')
            indicators = staleness.get('staleness_indicators', [])
            report += f"\n**Incumbent Weakness** (Staleness: {staleness_score:.0f}/100):\n"
            for ind in indicators[:3]:
                report += f"- {ind.get('keyword')}: {ind.get('mentions')} mentions\n"
            report += "\n"

        # Pain point value prop
        if customer_analysis:
            pain_analysis = customer_analysis.get('pain_point_analysis', {})
            top_pains = pain_analysis.get('top_pain_points', [])
            if top_pains:
                report += f"**Customer Pain Relief**:\n"
                for pain in top_pains[:2]:
                    category = pain.get('category', 'Unknown')
                    keywords = ', '.join(pain.get('keywords', [])[:3])
                    report += f"- {category}: {keywords}\n"
                report += "\n"

        # Automation ROI value
        if automation_analysis and automation_analysis.get('total_annual_roi_potential_usd'):
            roi = automation_analysis['total_annual_roi_potential_usd']
            report += f"**Quantified Value**: ${roi:,.0f} annual savings potential per customer\n\n"

        # Strategic positioning
        positioning = strategic.get('strategic_positioning', {})
        if positioning.get('best_positioning'):
            report += f"**Positioning**: {positioning.get('best_positioning')}\n"

        report += f"""

---

## 💰 REVENUE MODEL

**How We Charge**:
"""

        # Unit economics from top opportunity
        if top_opp:
            unit_econ = top_opp.get('unit_economics', {})
            market_sizing = top_opp.get('market_sizing', {})

            report += f"\n**Pricing**:\n"
            report += f"- ARPU: ${unit_econ.get('arpu', 0):,.0f}/year\n"
            report += f"- Gross Margin: {unit_econ.get('gross_margin', 0):.0%}\n"
            report += f"- LTV: ${unit_econ.get('ltv', 0):,.0f}\n"
            report += f"- CAC: ${unit_econ.get('cac', 0):,.0f}\n"
            report += f"- LTV/CAC: {unit_econ.get('ltv_cac_ratio', 0):.1f}x\n"
            report += f"- Payback: {unit_econ.get('payback_months', 0):.0f} months\n\n"

            report += f"**Market Sizing**:\n"
            report += f"- TAM: ${market_sizing.get('tam_usd', 0):,.0f}\n"
            report += f"- SAM: ${market_sizing.get('sam_usd', 0):,.0f}\n"
            report += f"- SOM (Y3): ${market_sizing.get('som_y3_usd', 0):,.0f}\n\n"

            assumptions = market_sizing.get('assumptions', [])
            if assumptions:
                report += f"**Key Assumptions**:\n"
                for assumption in assumptions[:3]:
                    report += f"- {assumption}\n"
        else:
            report += "\n*Conduct detailed opportunity analysis for unit economics*\n"

        report += f"""

---

## 🏰 COMPETITIVE MOAT

**Why Defensible**:
"""

        # Defensibility from strategic rationale
        if top_opp:
            rationale = top_opp.get('strategic_rationale', {})
            report += f"\n**Primary Moat**: {rationale.get('key_moat', 'Unknown')}\n\n"
            report += f"**Why Now**: {rationale.get('why_now', 'Unknown')}\n\n"
            report += f"**Why Unsolved**: {rationale.get('why_unsolved', 'Unknown')}\n\n"

        # VC criteria strengths
        strengths = vc_assessment.get('strengths', [])
        if strengths:
            report += f"**VC Strengths**:\n"
            for strength in strengths:
                report += f"- {strength}\n"

        # Competitive threat
        if top_opp:
            threat = top_opp.get('strategic_rationale', {}).get('competitive_threat', 'Unknown')
            report += f"\n**Competitive Threat**: {threat}\n"

        report += f"""

---

## ⚠️ PRE-MORTEM: Why This Might NOT Work

"""

        # Pre-mortem from top opportunity
        if top_opp and top_opp.get('pre_mortem'):
            premortem = top_opp['pre_mortem']
            most_likely = premortem.get('most_likely_failure', 'Unknown')
            survival_prob = premortem.get('survival_probability_y3', 0.5)

            report += f"**Most Likely Failure**: {most_likely}\n\n"
            report += f"**Survival Probability (Y3)**: {survival_prob:.0%}\n\n"

            failure_scenarios = premortem.get('failure_scenarios', [])
            if failure_scenarios:
                report += f"**Top Failure Scenarios**:\n\n"
                for i, scenario in enumerate(failure_scenarios[:3], 1):
                    report += f"{i}. **{scenario.get('scenario')}** (p={scenario.get('probability', 0):.0%}, impact={scenario.get('impact')})\n"
                    report += f"   - Root Cause: {scenario.get('root_cause')}\n"
                    report += f"   - Mitigation: {scenario.get('mitigation')}\n\n"

            derisking = premortem.get('derisking_priorities', [])
            if derisking:
                report += f"**Derisking Priorities**:\n"
                for priority in derisking[:3]:
                    report += f"- {priority}\n"

        report += f"""

---

## 📊 VC Investment Criteria Assessment

"""

        # VC criteria detailed breakdown
        criteria_scores = vc_assessment.get('criteria_scores', {})
        report += f"**Overall VC Score**: {vc_assessment.get('overall_vc_score', 0):.1f}/100\n\n"

        report += f"| Criterion | Score | Weight |\n"
        report += f"|-----------|-------|--------|\n"
        weights = vc_assessment.get('weights', {})
        report += f"| TAM | {criteria_scores.get('tam_score', 0):.1f}/100 | {weights.get('tam', 0):.0%} |\n"
        report += f"| Growth | {criteria_scores.get('growth_score', 0):.1f}/100 | {weights.get('growth', 0):.0%} |\n"
        report += f"| Fragmentation | {criteria_scores.get('fragmentation_score', 0):.1f}/100 | {weights.get('fragmentation', 0):.0%} |\n"
        report += f"| Staleness | {criteria_scores.get('incumbent_staleness_score', 0):.1f}/100 | {weights.get('staleness', 0):.0%} |\n"
        report += f"| Pain Intensity | {criteria_scores.get('pain_intensity_score', 0):.1f}/100 | {weights.get('pain_intensity', 0):.0%} |\n"
        report += f"| Defensibility | {criteria_scores.get('defensibility_score', 0):.1f}/100 | {weights.get('defensibility', 0):.0%} |\n\n"

        report += f"**Verdict**: {vc_assessment.get('verdict', 'Unknown')}\n\n"

        # Weaknesses
        weaknesses = vc_assessment.get('weaknesses', [])
        if weaknesses:
            report += f"**Key Weaknesses**:\n"
            for weakness in weaknesses:
                report += f"- {weakness}\n"

        report += f"""

---

*Data Confidence: {research.get('confidence', 0.5):.0%} | Analysis Date: {research.get('research_timestamp', 'N/A')}*
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
