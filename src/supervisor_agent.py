"""
Supervisor Agent - Orchestrates two-phase analysis workflow

Phase I: Quick screening (15-20 searches per NAICS)
- Rapid assessment of opportunity potential
- RAG database query first
- Light web search validation
- Scoring and ranking

Phase II/III: Deep dive (30-50 searches per selected NAICS)
- Full MBA-Data Science analysis
- Comprehensive staleness audit
- Detailed business model design
- Pre-mortem risk assessment

Manages 3000-query hard limit across all phases.
"""

import json
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class SupervisorAgent:
    """Orchestrates multi-phase opportunity discovery workflow"""

    def __init__(self, llm: ChatOpenAI, query_budget: int = 3000):
        """
        Initialize supervisor agent

        Args:
            llm: Language model for decision making
            query_budget: Total query budget across all phases (default 3000)
        """
        self.llm = llm
        self.query_budget = query_budget
        self.query_count = 0

    def should_proceed_phase_1(self, naics_code: str, rag_summary: Dict[str, Any]) -> bool:
        """
        Decide if NAICS code is worth Phase I screening based on RAG data

        Args:
            naics_code: NAICS code to evaluate
            rag_summary: Summary from industry_rag_summary view

        Returns:
            True if should proceed with Phase I, False to skip
        """
        # If no RAG data, proceed (we need to gather data)
        if not rag_summary:
            return True

        # Check for existing signals
        voc_count = rag_summary.get('voice_of_customer_count', 0)
        competitive_count = rag_summary.get('competitive_intel_count', 0)
        workflow_count = rag_summary.get('workflow_intel_count', 0)

        # If we have data, check for positive signals
        if voc_count > 0 or competitive_count > 0 or workflow_count > 0:
            negative_sentiment = rag_summary.get('negative_sentiment_ratio', 0)
            avg_genai_fit = rag_summary.get('avg_genai_fit_score', 0)
            recent_funding = rag_summary.get('total_recent_funding', 0)

            # Skip if:
            # - Very low negative sentiment (<10%) = happy customers
            # - Very low GenAI fit (<30) = poor automation potential
            # - No recent funding AND low negative sentiment = stale market
            if negative_sentiment < 0.1 and avg_genai_fit < 30:
                print(f"  ⏭️  Skipping NAICS {naics_code}: Low pain + low GenAI fit")
                return False

        return True

    def score_phase_1_results(
        self,
        naics_code: str,
        research_data: Dict[str, Any],
        rag_summary: Dict[str, Any],
        pain_points: List[Dict[str, Any]],
        automation_opps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Score Phase I results to decide if worth deep dive

        Scoring criteria (0-100 scale):
        - Pain Point Intensity (25 points)
        - Automation Potential (25 points)
        - Market Activity (20 points)
        - Market Size (15 points)
        - Competitive Gaps (15 points)

        Args:
            naics_code: NAICS code evaluated
            research_data: Research agent findings
            rag_summary: RAG database summary
            pain_points: Aggregated pain points from RAG
            automation_opps: High-fit automation opportunities

        Returns:
            Dict with phase_1_score, recommendation, reasoning
        """
        scores = {}

        # 1. Pain Point Intensity (25 points)
        pain_score = 0
        if pain_points:
            # Average negativity score across top pain points
            avg_negativity = sum(pp.get('negativity_score', 0) for pp in pain_points[:5]) / min(len(pain_points), 5)
            # Total mention count (capped at 100)
            mention_count = sum(pp.get('mention_count', 0) for pp in pain_points[:5])

            pain_score = min(25, (avg_negativity * 15) + (min(mention_count, 50) / 50 * 10))

        scores['pain_intensity'] = round(pain_score, 1)

        # 2. Automation Potential (25 points)
        automation_score = 0
        if automation_opps:
            # Average GenAI fit score
            avg_fit = sum(opp.get('genai_fit_score', 0) for opp in automation_opps[:5]) / min(len(automation_opps), 5)
            # Count of high-feasibility workflows
            high_feas_count = sum(1 for opp in automation_opps if opp.get('automation_feasibility') == 'high')

            automation_score = min(25, (avg_fit / 100 * 15) + (min(high_feas_count, 5) / 5 * 10))

        scores['automation_potential'] = round(automation_score, 1)

        # 3. Market Activity (20 points)
        activity_score = 0
        if rag_summary:
            funded_startups = rag_summary.get('funded_startups_12mo', 0)
            total_funding = rag_summary.get('total_recent_funding', 0)

            # Moderate funding activity is ideal (2-10 startups)
            # Too few = no validation, too many = crowded
            if 2 <= funded_startups <= 10:
                activity_score += 12
            elif 1 <= funded_startups <= 15:
                activity_score += 8
            elif funded_startups > 15:
                activity_score += 4  # Crowded

            # Total funding indicates market size belief
            if total_funding > 50_000_000:  # >$50M
                activity_score += 8
            elif total_funding > 10_000_000:  # >$10M
                activity_score += 5

        scores['market_activity'] = round(activity_score, 1)

        # 4. Market Size (15 points)
        size_score = 0
        market_size = research_data.get('market_size_usd', 0) or 0
        if market_size > 10_000_000_000:  # >$10B
            size_score = 15
        elif market_size > 1_000_000_000:  # >$1B
            size_score = 12
        elif market_size > 500_000_000:  # >$500M
            size_score = 9
        elif market_size > 100_000_000:  # >$100M
            size_score = 6

        scores['market_size'] = round(size_score, 1)

        # 5. Competitive Gaps (15 points)
        gap_score = 0
        if rag_summary and pain_points:
            # High pain + low competitive activity = gap
            voc_count = rag_summary.get('voice_of_customer_count', 0)
            competitive_count = rag_summary.get('competitive_intel_count', 0)
            negative_ratio = rag_summary.get('negative_sentiment_ratio', 0)

            # Lots of complaints but few competitors = opportunity
            if voc_count > 10 and competitive_count < 5 and negative_ratio > 0.4:
                gap_score = 15
            elif voc_count > 5 and competitive_count < 8 and negative_ratio > 0.3:
                gap_score = 10
            elif negative_ratio > 0.25:
                gap_score = 5

        scores['competitive_gap'] = round(gap_score, 1)

        # Total score
        total_score = sum(scores.values())
        scores['total'] = round(total_score, 1)

        # Recommendation based on score
        if total_score >= 60:
            recommendation = "PROCEED_DEEP_DIVE"
            reasoning = "Strong signals across multiple dimensions. High potential for GenAI opportunity."
        elif total_score >= 40:
            recommendation = "MAYBE"
            reasoning = "Moderate potential. Proceed if capacity allows or if strategic fit is strong."
        else:
            recommendation = "SKIP"
            reasoning = "Low scores indicate limited opportunity potential. Better to focus resources elsewhere."

        return {
            'naics_code': naics_code,
            'phase_1_score': total_score,
            'score_breakdown': scores,
            'recommendation': recommendation,
            'reasoning': reasoning,
            'rag_data_quality': self._assess_rag_data_quality(rag_summary),
            'top_pain_points': [pp.get('pain_point_category') for pp in pain_points[:3]],
            'top_workflows': [opp.get('workflow_name') for opp in automation_opps[:3]]
        }

    def _assess_rag_data_quality(self, rag_summary: Dict[str, Any]) -> str:
        """Assess quality/completeness of RAG data"""
        if not rag_summary:
            return "NO_DATA"

        voc = rag_summary.get('voice_of_customer_count', 0)
        ci = rag_summary.get('competitive_intel_count', 0)
        wi = rag_summary.get('workflow_intel_count', 0)

        total = voc + ci + wi

        if total >= 50:
            return "HIGH"
        elif total >= 20:
            return "MEDIUM"
        elif total >= 5:
            return "LOW"
        else:
            return "MINIMAL"

    def select_deep_dive_candidates(
        self,
        phase_1_scores: List[Dict[str, Any]],
        max_candidates: int = 5,
        score_threshold: float = 40.0
    ) -> List[str]:
        """
        Select which NAICS codes to deep dive based on Phase I scores

        Args:
            phase_1_scores: List of Phase I scoring results
            max_candidates: Maximum number to select
            score_threshold: Minimum score to consider

        Returns:
            List of NAICS codes to pursue
        """
        # Filter by threshold
        candidates = [
            s for s in phase_1_scores
            if s['phase_1_score'] >= score_threshold
        ]

        # Sort by score descending
        candidates.sort(key=lambda x: x['phase_1_score'], reverse=True)

        # Take top N
        selected = candidates[:max_candidates]

        return [s['naics_code'] for s in selected]

    def estimate_query_cost(
        self,
        phase: str,
        naics_codes: List[str],
        rag_data_quality: str = "MEDIUM"
    ) -> int:
        """
        Estimate query cost for analysis

        Args:
            phase: "PHASE_1" or "PHASE_2"
            naics_codes: List of NAICS codes to analyze
            rag_data_quality: Quality of existing RAG data

        Returns:
            Estimated number of queries needed
        """
        if phase == "PHASE_1":
            # Phase I: 15-20 queries per NAICS
            base_per_naics = 18

            # Adjust based on RAG data quality
            if rag_data_quality == "HIGH":
                base_per_naics = 12  # Less web search needed
            elif rag_data_quality == "LOW" or rag_data_quality == "MINIMAL":
                base_per_naics = 20  # More web search needed

            return len(naics_codes) * base_per_naics

        elif phase == "PHASE_2":
            # Phase II/III: 30-50 queries per NAICS
            base_per_naics = 40

            # Adjust based on RAG data quality
            if rag_data_quality == "HIGH":
                base_per_naics = 30
            elif rag_data_quality == "LOW" or rag_data_quality == "MINIMAL":
                base_per_naics = 50

            return len(naics_codes) * base_per_naics

        return 0

    def check_query_budget(self, required_queries: int) -> bool:
        """
        Check if we have budget for required queries

        Args:
            required_queries: Number of queries needed

        Returns:
            True if within budget, False otherwise
        """
        remaining = self.query_budget - self.query_count

        if required_queries > remaining:
            print(f"⚠️  Query budget exceeded: need {required_queries}, have {remaining}")
            return False

        return True

    def increment_query_count(self, count: int):
        """Track query usage"""
        self.query_count += count
        remaining = self.query_budget - self.query_count
        percent_used = (self.query_count / self.query_budget) * 100

        print(f"📊 Query budget: {self.query_count}/{self.query_budget} ({percent_used:.1f}%) | Remaining: {remaining}")

    def get_phase_2_search_strategy(
        self,
        naics_code: str,
        phase_1_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Design Phase II/III search strategy based on Phase I findings

        Args:
            naics_code: NAICS code for deep dive
            phase_1_results: Results from Phase I analysis

        Returns:
            Dict with search_focus_areas, query_count_allocation, specific_targets
        """
        strategy = {
            'naics_code': naics_code,
            'search_focus_areas': [],
            'query_allocation': {},
            'specific_targets': {}
        }

        score_breakdown = phase_1_results.get('score_breakdown', {})

        # Allocate queries based on what needs more investigation
        total_queries = 40
        allocation = {}

        # Always allocate baseline
        allocation['voice_of_customer'] = 10  # Reddit, G2, forums
        allocation['competitive_intelligence'] = 8  # Crunchbase, Product Hunt
        allocation['workflow_mapping'] = 8  # Job descriptions, LinkedIn
        allocation['market_validation'] = 7  # Industry reports, trends
        allocation['technology_landscape'] = 7  # Tech stack, tools

        # Adjust based on Phase I weaknesses
        if score_breakdown.get('pain_intensity', 0) < 15:
            allocation['voice_of_customer'] += 5  # Need more pain point data
            strategy['search_focus_areas'].append('pain_point_deep_dive')

        if score_breakdown.get('automation_potential', 0) < 15:
            allocation['workflow_mapping'] += 5  # Need more workflow data
            strategy['search_focus_areas'].append('workflow_deep_dive')

        if score_breakdown.get('competitive_gap', 0) < 10:
            allocation['competitive_intelligence'] += 5  # Need competitive clarity
            strategy['search_focus_areas'].append('competitive_deep_dive')

        strategy['query_allocation'] = allocation

        # Specific target searches based on top findings
        targets = {}

        top_pain_points = phase_1_results.get('top_pain_points', [])
        if top_pain_points:
            targets['pain_points'] = [
                query
                for pain in top_pain_points[:2]
                for query in [
                    f'site:reddit.com "{naics_code} {pain}" complaints',
                    f'site:g2.com "{pain}" reviews'
                ]
            ]

        top_workflows = phase_1_results.get('top_workflows', [])
        if top_workflows:
            targets['workflows'] = [
                query
                for workflow in top_workflows[:2]
                for query in [
                    f'"{workflow}" automation opportunity',
                    f'"{workflow}" manual process pain points'
                ]
            ]

        strategy['specific_targets'] = targets

        return strategy

    def format_phase_1_summary(self, all_scores: List[Dict[str, Any]]) -> str:
        """
        Format Phase I results for user selection

        Args:
            all_scores: List of all Phase I scoring results

        Returns:
            Formatted markdown summary
        """
        # Sort by score
        sorted_scores = sorted(all_scores, key=lambda x: x['phase_1_score'], reverse=True)

        summary = "# Phase I Screening Results\n\n"
        summary += f"**Analyzed**: {len(all_scores)} NAICS codes\n\n"

        # Recommendations table
        summary += "## Recommended for Deep Dive\n\n"
        summary += "| NAICS | Score | Pain | Auto | Activity | Size | Gap | Recommendation |\n"
        summary += "|-------|-------|------|------|----------|------|-----|----------------|\n"

        for result in sorted_scores:
            naics = result['naics_code']
            score = result['phase_1_score']
            breakdown = result['score_breakdown']
            rec = result['recommendation']

            if rec == "PROCEED_DEEP_DIVE":
                emoji = "🎯"
            elif rec == "MAYBE":
                emoji = "🤔"
            else:
                emoji = "⏭️"

            summary += f"| {naics} | {score:.1f} | {breakdown.get('pain_intensity', 0):.1f} | "
            summary += f"{breakdown.get('automation_potential', 0):.1f} | {breakdown.get('market_activity', 0):.1f} | "
            summary += f"{breakdown.get('market_size', 0):.1f} | {breakdown.get('competitive_gap', 0):.1f} | "
            summary += f"{emoji} {rec} |\n"

        # Top opportunities detail
        summary += "\n## Top 5 Opportunities\n\n"
        for i, result in enumerate(sorted_scores[:5], 1):
            summary += f"### {i}. NAICS {result['naics_code']} (Score: {result['phase_1_score']:.1f})\n\n"
            summary += f"**Recommendation**: {result['recommendation']}\n\n"
            summary += f"**Reasoning**: {result['reasoning']}\n\n"

            if result.get('top_pain_points'):
                summary += f"**Top Pain Points**: {', '.join(result['top_pain_points'])}\n\n"

            if result.get('top_workflows'):
                summary += f"**Top Automation Opportunities**: {', '.join(result['top_workflows'])}\n\n"

            summary += f"**RAG Data Quality**: {result.get('rag_data_quality', 'UNKNOWN')}\n\n"
            summary += "---\n\n"

        summary += "\n## Next Steps\n\n"
        summary += "Select which NAICS codes to proceed with for Phase II/III deep dive analysis.\n\n"

        recommended = [s['naics_code'] for s in sorted_scores if s['recommendation'] == 'PROCEED_DEEP_DIVE']
        if recommended:
            summary += f"**Recommended**: {', '.join(recommended)}\n\n"

        return summary
