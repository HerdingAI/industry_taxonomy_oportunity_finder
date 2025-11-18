"""
Technical Data Scientist Agent - Assesses GenAI automation potential

Core Responsibilities:
1. Score workflows for GenAI fit (0-100 scale)
2. Identify data-heavy automation opportunities
3. Evaluate data availability and quality
4. Calculate ROI from time savings
5. Assess technical feasibility

Scoring Methodology:
- Data Volume & Variety (25 pts)
- Task Repeatability (20 pts)
- Current Manual Effort (20 pts)
- Data Structure/Accessibility (15 pts)
- Output Standardization (10 pts)
- User Acceptance Likelihood (10 pts)
"""

import json
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class TechnicalDataScientistAgent:
    """Evaluates technical feasibility and GenAI automation potential"""

    def __init__(self, llm: ChatOpenAI, rag_db=None):
        """
        Initialize technical data scientist agent

        Args:
            llm: Language model for analysis
            rag_db: RAGDatabase instance for querying workflow data (optional)
        """
        self.llm = llm
        self.rag_db = rag_db

    def assess_genai_fit(
        self,
        workflow_name: str,
        workflow_description: str,
        data_types: List[str],
        manual_steps: List[str],
        current_tools: List[str],
        frequency: str,
        time_spent_hours: float,
        volume_per_period: int
    ) -> Dict[str, Any]:
        """
        Assess GenAI automation fit for a specific workflow

        Args:
            workflow_name: Name of workflow
            workflow_description: Detailed description
            data_types: Types of data involved (pdf, email, excel, etc.)
            manual_steps: List of manual steps
            current_tools: Current tools used
            frequency: How often (hourly, daily, weekly, monthly)
            time_spent_hours: Time per execution
            volume_per_period: Number of executions per period

        Returns:
            Dict with genai_fit_score, automation_feasibility, reasoning, roi_estimate
        """
        # Calculate individual scoring components
        scores = {}

        # 1. Data Volume & Variety (25 points)
        data_score = self._score_data_characteristics(
            data_types, volume_per_period, time_spent_hours
        )
        scores['data_volume_variety'] = data_score

        # 2. Task Repeatability (20 points)
        repeatability_score = self._score_repeatability(
            manual_steps, frequency, volume_per_period
        )
        scores['task_repeatability'] = repeatability_score

        # 3. Current Manual Effort (20 points)
        effort_score = self._score_manual_effort(
            time_spent_hours, frequency, volume_per_period, manual_steps
        )
        scores['manual_effort'] = effort_score

        # 4. Data Structure/Accessibility (15 points)
        structure_score = self._score_data_structure(
            data_types, current_tools
        )
        scores['data_structure'] = structure_score

        # 5. Output Standardization (10 points)
        output_score = self._score_output_standardization(
            workflow_description, manual_steps
        )
        scores['output_standardization'] = output_score

        # 6. User Acceptance Likelihood (10 points)
        acceptance_score = self._score_user_acceptance(
            workflow_name, current_tools
        )
        scores['user_acceptance'] = acceptance_score

        # Total GenAI fit score (0-100)
        total_score = sum(scores.values())

        # Determine automation feasibility
        if total_score >= 70:
            feasibility = "high"
        elif total_score >= 50:
            feasibility = "medium"
        else:
            feasibility = "low"

        # Calculate ROI estimate
        roi_estimate = self._calculate_roi_estimate(
            time_spent_hours, frequency, volume_per_period, total_score
        )

        # Generate reasoning
        reasoning = self._generate_genai_reasoning(
            workflow_name, scores, total_score, data_types, manual_steps
        )

        return {
            'workflow_name': workflow_name,
            'genai_fit_score': round(total_score, 1),
            'automation_feasibility': feasibility,
            'score_breakdown': scores,
            'reasoning': reasoning,
            'roi_estimate': roi_estimate,
            'recommended_approach': self._recommend_approach(data_types, manual_steps, total_score)
        }

    def _score_data_characteristics(
        self,
        data_types: List[str],
        volume: int,
        time_hours: float
    ) -> float:
        """Score based on data volume and variety (max 25 points)"""
        score = 0

        # Data variety bonus (more types = better for GenAI)
        genai_friendly_types = ['pdf', 'email', 'text', 'word', 'images', 'scanned_docs']
        friendly_count = sum(1 for dt in data_types if dt.lower() in genai_friendly_types)

        score += min(10, friendly_count * 2.5)  # Up to 10 points for variety

        # Volume bonus (high volume = better ROI)
        if volume >= 100:
            score += 10
        elif volume >= 50:
            score += 7
        elif volume >= 20:
            score += 5
        elif volume >= 5:
            score += 3

        # Time complexity bonus (more time = more value to automate)
        if time_hours >= 3:
            score += 5
        elif time_hours >= 1:
            score += 3
        elif time_hours >= 0.5:
            score += 2

        return min(25, score)

    def _score_repeatability(
        self,
        manual_steps: List[str],
        frequency: str,
        volume: int
    ) -> float:
        """Score task repeatability (max 20 points)"""
        score = 0

        # Frequency bonus
        freq_scores = {
            'hourly': 20,
            'daily': 15,
            'weekly': 10,
            'monthly': 5,
            'quarterly': 2
        }
        score += freq_scores.get(frequency.lower(), 5)

        # Penalize if very low volume
        if volume < 5:
            score *= 0.5  # Low volume reduces repeatability value

        # Bonus if steps are structured
        if len(manual_steps) >= 5:
            score += 0  # Already at max, no bonus
        elif len(manual_steps) >= 3:
            score -= 2  # Slightly less structured

        return min(20, round(score, 1))

    def _score_manual_effort(
        self,
        time_hours: float,
        frequency: str,
        volume: int,
        manual_steps: List[str]
    ) -> float:
        """Score current manual effort level (max 20 points)"""
        # Calculate total hours per week
        freq_multipliers = {
            'hourly': 168,  # 24*7 (if truly hourly)
            'daily': 7,
            'weekly': 1,
            'monthly': 0.25,
            'quarterly': 0.08
        }

        multiplier = freq_multipliers.get(frequency.lower(), 1)
        weekly_hours = time_hours * volume * multiplier

        # Score based on weekly effort
        if weekly_hours >= 20:
            score = 20  # Full-time equivalent
        elif weekly_hours >= 10:
            score = 16
        elif weekly_hours >= 5:
            score = 12
        elif weekly_hours >= 2:
            score = 8
        else:
            score = 4

        return round(score, 1)

    def _score_data_structure(
        self,
        data_types: List[str],
        current_tools: List[str]
    ) -> float:
        """Score data structure and accessibility (max 15 points)"""
        score = 0

        # Structured data is easier to work with initially
        structured_types = ['excel', 'csv', 'database', 'api', 'json', 'xml']
        unstructured_types = ['pdf', 'email', 'text', 'images', 'scanned_docs', 'word']

        structured_count = sum(1 for dt in data_types if dt.lower() in structured_types)
        unstructured_count = sum(1 for dt in data_types if dt.lower() in unstructured_types)

        # GenAI excels at unstructured -> structured transformation
        if unstructured_count >= 2:
            score += 10  # Perfect for GenAI
        elif unstructured_count == 1:
            score += 6

        # Some structured data is good for validation
        if structured_count >= 1:
            score += 3

        # Accessibility check
        accessible_tools = ['api', 'web_portal', 'email', 'sharepoint', 'google_drive']
        if any(tool.lower() in str(current_tools).lower() for tool in accessible_tools):
            score += 2

        return min(15, round(score, 1))

    def _score_output_standardization(
        self,
        workflow_description: str,
        manual_steps: List[str]
    ) -> float:
        """Score output standardization potential (max 10 points)"""
        score = 0

        # Keywords indicating standardizable outputs
        standard_keywords = [
            'report', 'summary', 'form', 'template', 'document',
            'spreadsheet', 'comparison', 'analysis', 'recommendation'
        ]

        desc_lower = workflow_description.lower()
        steps_text = ' '.join(manual_steps).lower()

        matches = sum(1 for kw in standard_keywords if kw in desc_lower or kw in steps_text)

        score = min(10, matches * 2)

        return round(score, 1)

    def _score_user_acceptance(
        self,
        workflow_name: str,
        current_tools: List[str]
    ) -> float:
        """Score likely user acceptance (max 10 points)"""
        score = 8  # Default: moderate acceptance

        # High acceptance workflows
        high_acceptance = [
            'data entry', 'document processing', 'report generation',
            'email sorting', 'scheduling', 'quote generation'
        ]

        # Low acceptance workflows (human judgment critical)
        low_acceptance = [
            'hiring', 'termination', 'diagnosis', 'legal advice', 'creative'
        ]

        workflow_lower = workflow_name.lower()

        if any(hw in workflow_lower for hw in high_acceptance):
            score = 10
        elif any(lw in workflow_lower for lw in low_acceptance):
            score = 4

        # If they're already using software tools, more open to automation
        if len(current_tools) >= 3:
            score += 0  # Already at reasonable level

        return min(10, round(score, 1))

    def _calculate_roi_estimate(
        self,
        time_hours: float,
        frequency: str,
        volume: int,
        genai_score: float
    ) -> Dict[str, Any]:
        """Estimate ROI from automation"""
        # Calculate annual hours saved
        freq_multipliers = {
            'hourly': 168 * 52,  # Hours in a year
            'daily': 365,
            'weekly': 52,
            'monthly': 12,
            'quarterly': 4
        }

        multiplier = freq_multipliers.get(frequency.lower(), 52)
        annual_hours = time_hours * volume * multiplier

        # Automation efficiency based on GenAI score
        automation_efficiency = genai_score / 100

        hours_saved_annually = annual_hours * automation_efficiency * 0.7  # 70% typical automation rate

        # Value calculation (assuming $75/hr fully-loaded cost)
        hourly_cost = 75
        annual_savings = hours_saved_annually * hourly_cost

        # Implementation cost estimate
        if genai_score >= 70:
            implementation_months = 2
        elif genai_score >= 50:
            implementation_months = 3
        else:
            implementation_months = 4

        implementation_cost = implementation_months * 20000  # $20k/month development

        # Payback period
        if annual_savings > 0:
            payback_months = (implementation_cost / annual_savings) * 12
        else:
            payback_months = 999

        return {
            'annual_hours_saved': round(hours_saved_annually, 1),
            'annual_cost_savings_usd': round(annual_savings, 0),
            'implementation_cost_usd': implementation_cost,
            'payback_months': round(payback_months, 1),
            'year_3_npv_usd': round(annual_savings * 3 - implementation_cost, 0),
            'automation_efficiency_pct': round(automation_efficiency * 100, 1)
        }

    def _recommend_approach(
        self,
        data_types: List[str],
        manual_steps: List[str],
        genai_score: float
    ) -> str:
        """Recommend technical approach for automation"""
        if genai_score >= 70:
            approach = "Full GenAI Automation: "

            if 'pdf' in data_types or 'images' in data_types:
                approach += "OCR + LLM extraction → "

            if 'email' in data_types:
                approach += "Email parsing + classification → "

            approach += "LLM-powered workflow orchestration → Automated output generation. "
            approach += "Implement in 2-3 months with GPT-4 + LangChain."

        elif genai_score >= 50:
            approach = "Hybrid Automation: "
            approach += "GenAI for unstructured data processing (documents, emails), "
            approach += "traditional automation for structured workflows, "
            approach += "human review for edge cases. 3-4 month implementation."

        else:
            approach = "Assisted Automation: "
            approach += "GenAI as copilot/assistant rather than full automation. "
            approach += "Focus on specific high-value steps rather than end-to-end. "
            approach += "Lower risk, faster to implement (4-6 weeks)."

        return approach

    def _generate_genai_reasoning(
        self,
        workflow_name: str,
        scores: Dict[str, float],
        total_score: float,
        data_types: List[str],
        manual_steps: List[str]
    ) -> str:
        """Generate human-readable reasoning for GenAI fit score"""
        reasoning = f"GenAI Fit Score: {total_score:.1f}/100. "

        # Identify strengths
        strengths = []
        if scores.get('data_volume_variety', 0) >= 18:
            strengths.append("high data volume and variety")

        if scores.get('task_repeatability', 0) >= 15:
            strengths.append("highly repetitive task")

        if scores.get('manual_effort', 0) >= 15:
            strengths.append("significant manual effort required")

        if scores.get('data_structure', 0) >= 10:
            strengths.append("unstructured data well-suited for LLMs")

        # Identify weaknesses
        weaknesses = []
        if scores.get('data_volume_variety', 0) < 10:
            weaknesses.append("low data volume limits ROI")

        if scores.get('task_repeatability', 0) < 10:
            weaknesses.append("infrequent task reduces value")

        if scores.get('manual_effort', 0) < 8:
            weaknesses.append("minimal time savings potential")

        if scores.get('user_acceptance', 0) < 6:
            weaknesses.append("potential user resistance")

        reasoning += f"Strengths: {', '.join(strengths) if strengths else 'limited strengths identified'}. "
        reasoning += f"Challenges: {', '.join(weaknesses) if weaknesses else 'no major blockers'}. "

        # Data type specific note
        if 'pdf' in data_types or 'images' in data_types or 'email' in data_types:
            reasoning += "Strong LLM use case for document/email processing. "

        return reasoning

    def analyze_industry_automation_potential(
        self,
        naics_code: str,
        workflow_data: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze overall GenAI automation potential for an industry

        Args:
            naics_code: NAICS code to analyze
            workflow_data: List of workflow dictionaries (or None to query RAG)

        Returns:
            Dict with industry_genai_score, top_opportunities, total_roi_potential
        """
        # Get workflow data from RAG if not provided
        if workflow_data is None and self.rag_db:
            try:
                workflow_data = self.rag_db.find_automation_opportunities(
                    naics_code=naics_code,
                    min_genai_score=0  # Get all to do our own scoring
                )
            except:
                workflow_data = []

        if not workflow_data:
            return {
                'naics_code': naics_code,
                'industry_genai_score': 0,
                'data_quality': 'NO_DATA',
                'message': 'No workflow data available for analysis'
            }

        # Score each workflow
        scored_workflows = []
        for wf in workflow_data:
            try:
                assessment = self.assess_genai_fit(
                    workflow_name=wf.get('workflow_name', 'Unknown'),
                    workflow_description=wf.get('pain_point_description', ''),
                    data_types=wf.get('data_types', []),
                    manual_steps=wf.get('manual_steps', []),
                    current_tools=wf.get('tools_used', []),
                    frequency=wf.get('frequency', 'weekly'),
                    time_spent_hours=wf.get('time_spent_hours', 0) or 0,
                    volume_per_period=wf.get('volume_per_period', 0) or 0
                )
                scored_workflows.append(assessment)
            except Exception as e:
                continue  # Skip problematic workflows

        if not scored_workflows:
            return {
                'naics_code': naics_code,
                'industry_genai_score': 0,
                'data_quality': 'POOR',
                'message': 'Could not score any workflows'
            }

        # Calculate industry score (weighted average)
        total_score = sum(wf['genai_fit_score'] for wf in scored_workflows)
        avg_score = total_score / len(scored_workflows)

        # Calculate total ROI potential
        total_annual_savings = sum(
            wf['roi_estimate']['annual_cost_savings_usd']
            for wf in scored_workflows
        )

        # Top opportunities
        top_opps = sorted(scored_workflows, key=lambda x: x['genai_fit_score'], reverse=True)[:5]

        return {
            'naics_code': naics_code,
            'industry_genai_score': round(avg_score, 1),
            'workflows_analyzed': len(scored_workflows),
            'high_fit_count': sum(1 for wf in scored_workflows if wf['genai_fit_score'] >= 70),
            'medium_fit_count': sum(1 for wf in scored_workflows if 50 <= wf['genai_fit_score'] < 70),
            'low_fit_count': sum(1 for wf in scored_workflows if wf['genai_fit_score'] < 50),
            'total_annual_roi_potential_usd': round(total_annual_savings, 0),
            'top_opportunities': [
                {
                    'workflow_name': opp['workflow_name'],
                    'genai_fit_score': opp['genai_fit_score'],
                    'annual_savings_usd': opp['roi_estimate']['annual_cost_savings_usd'],
                    'payback_months': opp['roi_estimate']['payback_months']
                }
                for opp in top_opps
            ],
            'data_quality': 'HIGH' if len(scored_workflows) >= 10 else 'MEDIUM' if len(scored_workflows) >= 5 else 'LOW'
        }
