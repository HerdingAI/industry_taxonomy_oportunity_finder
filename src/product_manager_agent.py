"""
Product Manager Agent - Customer-centric opportunity analysis

Core Responsibilities:
1. Extract buyer personas from voice-of-customer data
2. Identify pain point patterns and categories
3. Map jobs-to-be-done framework
4. Analyze feature gaps in existing solutions
5. Understand decision-making units (user, buyer, decision-maker)
6. Sentiment analysis and complaint pattern recognition

Data Sources:
- RAG database (voice_of_customer table)
- Web searches (Reddit, G2, Capterra, LinkedIn)
- Competitive intelligence (what customers say about competitors)
"""

import json
from typing import Dict, Any, List, Optional
from collections import Counter
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class ProductManagerAgent:
    """Customer-centric analysis for opportunity discovery"""

    def __init__(self, llm: ChatOpenAI, rag_db=None):
        """
        Initialize product manager agent

        Args:
            llm: Language model for analysis
            rag_db: RAGDatabase instance for querying VOC data (optional)
        """
        self.llm = llm
        self.rag_db = rag_db

    def analyze_customer_landscape(
        self,
        naics_code: str,
        industry_name: str,
        voc_data: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive customer landscape analysis

        Args:
            naics_code: NAICS code to analyze
            industry_name: Industry name
            voc_data: Voice of customer data (or None to query RAG)

        Returns:
            Dict with buyer_personas, pain_points, feature_gaps, jobs_to_be_done
        """
        # Get VOC data from RAG if not provided
        if voc_data is None and self.rag_db:
            try:
                # Get aggregated pain points
                pain_points = self.rag_db.aggregate_pain_points(naics_code)

                # Also do semantic search for general complaints
                voc_data = self.rag_db.search_voice_of_customer(
                    query_text=f"{industry_name} software complaints pain points",
                    naics_code=naics_code,
                    limit_count=50
                )
            except:
                voc_data = []
                pain_points = []
        else:
            voc_data = voc_data or []
            pain_points = []

        # Extract buyer personas
        buyer_personas = self._extract_buyer_personas(voc_data, industry_name)

        # Analyze pain points
        pain_point_analysis = self._analyze_pain_points(voc_data, pain_points)

        # Extract feature gaps
        feature_gaps = self._extract_feature_gaps(voc_data)

        # Map jobs-to-be-done
        jobs_to_be_done = self._map_jobs_to_be_done(voc_data, industry_name)

        # Analyze sentiment patterns
        sentiment_analysis = self._analyze_sentiment_patterns(voc_data)

        # Identify decision-making unit
        decision_unit = self._identify_decision_unit(voc_data, industry_name)

        return {
            'naics_code': naics_code,
            'industry_name': industry_name,
            'data_sources': len(voc_data),
            'buyer_personas': buyer_personas,
            'pain_point_analysis': pain_point_analysis,
            'feature_gaps': feature_gaps,
            'jobs_to_be_done': jobs_to_be_done,
            'sentiment_analysis': sentiment_analysis,
            'decision_making_unit': decision_unit,
            'confidence': self._calculate_confidence(voc_data)
        }

    def _extract_buyer_personas(
        self,
        voc_data: List[Dict[str, Any]],
        industry_name: str
    ) -> List[Dict[str, Any]]:
        """Extract buyer personas from VOC data"""
        if not voc_data:
            return self._generate_default_personas(industry_name)

        # Use LLM to extract personas from VOC data
        prompt = f"""Analyze the following voice-of-customer data from the {industry_name} industry and extract 2-3 distinct buyer personas.

For each persona, identify:
- Role/Title (e.g., "Operations Manager", "IT Director")
- Primary Goals (what they're trying to achieve)
- Key Pain Points (their biggest frustrations)
- Software Usage Context (how they use technology)
- Decision Authority (budget holder, influencer, end user)

Voice of Customer Data:
{json.dumps([{
    'content': v.get('content', '')[:200],
    'software': v.get('software_mentioned', ''),
    'pain_category': v.get('pain_point_category', '')
} for v in voc_data[:10]], indent=2)}

Return ONLY a JSON array of personas with this structure:
[{{
    "role": "string",
    "primary_goals": ["goal1", "goal2"],
    "pain_points": ["pain1", "pain2"],
    "usage_context": "string",
    "decision_authority": "budget_holder|influencer|end_user",
    "quote": "representative quote from data"
}}]"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            # Extract JSON from response
            response_text = response.content

            # Find JSON array in response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                personas = json.loads(json_str)
                return personas
            else:
                return self._generate_default_personas(industry_name)

        except Exception as e:
            print(f"  ⚠️  Persona extraction failed: {e}")
            return self._generate_default_personas(industry_name)

    def _generate_default_personas(self, industry_name: str) -> List[Dict[str, Any]]:
        """Generate default personas when data is insufficient"""
        return [
            {
                "role": "Operations Manager",
                "primary_goals": ["Improve efficiency", "Reduce costs", "Automate manual work"],
                "pain_points": ["Too many manual processes", "Data entry errors", "Slow turnaround"],
                "usage_context": f"Manages day-to-day operations in {industry_name}",
                "decision_authority": "influencer",
                "quote": "N/A - insufficient data"
            },
            {
                "role": "IT Director / CTO",
                "primary_goals": ["Modernize tech stack", "Improve integration", "Enable scalability"],
                "pain_points": ["Legacy systems", "No API access", "Poor vendor support"],
                "usage_context": f"Responsible for technology decisions in {industry_name}",
                "decision_authority": "budget_holder",
                "quote": "N/A - insufficient data"
            }
        ]

    def _analyze_pain_points(
        self,
        voc_data: List[Dict[str, Any]],
        aggregated_pain_points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze pain point patterns and intensity"""
        if not voc_data and not aggregated_pain_points:
            return {
                'top_pain_points': [],
                'pain_intensity_score': 0,
                'data_quality': 'NO_DATA'
            }

        # Use aggregated pain points if available
        if aggregated_pain_points:
            sorted_pains = sorted(
                aggregated_pain_points,
                key=lambda x: x.get('mention_count', 0),
                reverse=True
            )

            top_pains = []
            for pain in sorted_pains[:5]:
                top_pains.append({
                    'category': pain.get('pain_point_category', 'Unknown'),
                    'mention_count': pain.get('mention_count', 0),
                    'keywords': pain.get('all_keywords', [])[:5],
                    'negativity_score': round(pain.get('negativity_score', 0), 2),
                    'example': pain.get('example_content', '')[:150]
                })

            # Calculate overall pain intensity
            avg_negativity = sum(p.get('negativity_score', 0) for p in top_pains) / len(top_pains) if top_pains else 0
            total_mentions = sum(p.get('mention_count', 0) for p in top_pains)

            pain_intensity = min(100, (avg_negativity * 50) + (min(total_mentions, 50) / 50 * 50))

            return {
                'top_pain_points': top_pains,
                'pain_intensity_score': round(pain_intensity, 1),
                'total_pain_mentions': total_mentions,
                'data_quality': 'HIGH' if len(aggregated_pain_points) >= 5 else 'MEDIUM'
            }

        # Fallback: analyze from raw VOC data
        pain_categories = [v.get('pain_point_category') for v in voc_data if v.get('pain_point_category')]
        pain_counter = Counter(pain_categories)

        top_pains = [
            {
                'category': cat,
                'mention_count': count,
                'keywords': [],
                'negativity_score': 0.5,
                'example': ''
            }
            for cat, count in pain_counter.most_common(5)
        ]

        return {
            'top_pain_points': top_pains,
            'pain_intensity_score': 50.0,  # Moderate default
            'total_pain_mentions': len(pain_categories),
            'data_quality': 'LOW'
        }

    def _extract_feature_gaps(
        self,
        voc_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract feature gaps from VOC data"""
        if not voc_data:
            return []

        # Collect all feature gaps mentioned
        all_gaps = []
        for v in voc_data:
            gaps = v.get('feature_gaps', [])
            if gaps:
                all_gaps.extend(gaps)

        # Count frequency
        gap_counter = Counter(all_gaps)

        # Return top 10 most mentioned feature gaps
        top_gaps = [
            {
                'feature': gap,
                'mention_count': count,
                'urgency': 'high' if count >= 5 else 'medium' if count >= 3 else 'low'
            }
            for gap, count in gap_counter.most_common(10)
        ]

        return top_gaps

    def _map_jobs_to_be_done(
        self,
        voc_data: List[Dict[str, Any]],
        industry_name: str
    ) -> List[Dict[str, Any]]:
        """Map jobs-to-be-done from customer perspective"""
        if not voc_data:
            return self._generate_default_jtbd(industry_name)

        # Use LLM to extract JTBD from VOC data
        prompt = f"""Analyze the following voice-of-customer data from {industry_name} and identify the top 3-5 "Jobs to Be Done" using the JTBD framework.

For each job, identify:
- Functional Job (what task they're trying to accomplish)
- Emotional Job (how they want to feel)
- Social Job (how they want to be perceived)
- Current Solution (what they use now)
- Desired Outcome (what success looks like)

Voice of Customer Data:
{json.dumps([{
    'content': v.get('content', '')[:200],
    'pain_category': v.get('pain_point_category', '')
} for v in voc_data[:10]], indent=2)}

Return ONLY a JSON array with this structure:
[{{
    "functional_job": "string",
    "emotional_job": "string",
    "social_job": "string",
    "current_solution": "string",
    "desired_outcome": "string",
    "importance_score": 1-10
}}]"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            response_text = response.content

            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                jtbd = json.loads(json_str)
                return jtbd
            else:
                return self._generate_default_jtbd(industry_name)

        except Exception as e:
            print(f"  ⚠️  JTBD extraction failed: {e}")
            return self._generate_default_jtbd(industry_name)

    def _generate_default_jtbd(self, industry_name: str) -> List[Dict[str, Any]]:
        """Generate default JTBD when data is insufficient"""
        return [
            {
                "functional_job": f"Process and manage data efficiently in {industry_name}",
                "emotional_job": "Feel confident that work is accurate and complete",
                "social_job": "Be seen as efficient and reliable",
                "current_solution": "Manual processes with Excel and email",
                "desired_outcome": "Automated, error-free processing with minimal manual work",
                "importance_score": 8
            }
        ]

    def _analyze_sentiment_patterns(
        self,
        voc_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze sentiment patterns in VOC data"""
        if not voc_data:
            return {
                'sentiment_distribution': {},
                'negative_ratio': 0,
                'data_quality': 'NO_DATA'
            }

        # Count sentiment distribution
        sentiments = [v.get('sentiment') for v in voc_data if v.get('sentiment')]
        sentiment_counter = Counter(sentiments)

        total = len(sentiments)
        if total == 0:
            return {
                'sentiment_distribution': {},
                'negative_ratio': 0,
                'data_quality': 'NO_DATA'
            }

        distribution = {
            'positive': sentiment_counter.get('positive', 0) / total,
            'negative': sentiment_counter.get('negative', 0) / total,
            'neutral': sentiment_counter.get('neutral', 0) / total,
            'mixed': sentiment_counter.get('mixed', 0) / total
        }

        return {
            'sentiment_distribution': {k: round(v, 2) for k, v in distribution.items()},
            'negative_ratio': distribution['negative'],
            'total_reviews': total,
            'data_quality': 'HIGH' if total >= 20 else 'MEDIUM' if total >= 10 else 'LOW'
        }

    def _identify_decision_unit(
        self,
        voc_data: List[Dict[str, Any]],
        industry_name: str
    ) -> Dict[str, Any]:
        """Identify the decision-making unit (buyer, user, influencer)"""
        # This is typically derived from persona analysis
        # In B2B software, common pattern:

        return {
            'economic_buyer': {
                'role': 'Owner / CEO / CFO',
                'concerns': ['ROI', 'Cost', 'Risk'],
                'decision_criteria': 'Financial impact, total cost of ownership'
            },
            'technical_buyer': {
                'role': 'IT Director / CTO',
                'concerns': ['Integration', 'Security', 'Scalability'],
                'decision_criteria': 'Technical fit, vendor reliability'
            },
            'end_user': {
                'role': 'Operations Staff / Managers',
                'concerns': ['Ease of use', 'Efficiency', 'Training'],
                'decision_criteria': 'User experience, time savings'
            },
            'champion': {
                'role': 'Operations Manager / Department Head',
                'concerns': ['Team productivity', 'Process improvement'],
                'decision_criteria': 'Solves team pain points'
            },
            'recommended_sales_approach': 'Bottom-up (champion → technical buyer → economic buyer)'
        }

    def _calculate_confidence(self, voc_data: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on data availability"""
        if not voc_data:
            return 0.0

        data_count = len(voc_data)

        if data_count >= 30:
            return 0.9
        elif data_count >= 20:
            return 0.8
        elif data_count >= 10:
            return 0.6
        elif data_count >= 5:
            return 0.4
        else:
            return 0.2

    def identify_software_complaints(
        self,
        naics_code: str,
        software_name: str = None
    ) -> Dict[str, Any]:
        """
        Identify specific complaints about software in this industry

        Args:
            naics_code: NAICS code to analyze
            software_name: Specific software to analyze (or None for all)

        Returns:
            Dict with complaint_categories, top_complaints, staleness_indicators
        """
        if not self.rag_db:
            return {'error': 'RAG database not available'}

        try:
            # Query for complaints
            query_text = f"{software_name} complaints" if software_name else "software complaints manual process"

            voc_results = self.rag_db.search_voice_of_customer(
                query_text=query_text,
                naics_code=naics_code,
                source_types=['reddit', 'g2', 'capterra', 'trustradius'],
                limit_count=30
            )

            if not voc_results:
                return {
                    'software_name': software_name,
                    'complaints_found': 0,
                    'message': 'No complaint data available'
                }

            # Aggregate complaints by keyword
            all_keywords = []
            for v in voc_results:
                keywords = v.get('complaint_keywords', [])
                if keywords:
                    all_keywords.extend(keywords)

            keyword_counter = Counter(all_keywords)

            # Categorize staleness indicators
            staleness_indicators = []
            staleness_keywords = ['outdated', 'old', 'legacy', 'ancient', 'clunky', 'slow', 'no api', 'manual']

            for keyword in staleness_keywords:
                count = keyword_counter.get(keyword, 0)
                if count > 0:
                    staleness_indicators.append({
                        'indicator': keyword,
                        'mention_count': count
                    })

            return {
                'software_name': software_name or 'Industry Software',
                'complaints_found': len(voc_results),
                'top_complaint_keywords': [
                    {'keyword': kw, 'count': count}
                    for kw, count in keyword_counter.most_common(15)
                ],
                'staleness_indicators': sorted(staleness_indicators, key=lambda x: x['mention_count'], reverse=True),
                'staleness_score': min(100, len(staleness_indicators) * 10),
                'example_complaints': [
                    v.get('content', '')[:200]
                    for v in voc_results[:3]
                ]
            }

        except Exception as e:
            return {'error': str(e)}

    def generate_buyer_persona_summary(
        self,
        customer_analysis: Dict[str, Any]
    ) -> str:
        """Generate markdown summary of buyer personas and customer insights"""
        personas = customer_analysis.get('buyer_personas', [])
        pain_analysis = customer_analysis.get('pain_point_analysis', {})
        feature_gaps = customer_analysis.get('feature_gaps', [])
        jtbd = customer_analysis.get('jobs_to_be_done', [])

        summary = "## Customer & Buyer Persona Analysis\n\n"

        # Data quality indicator
        data_sources = customer_analysis.get('data_sources', 0)
        confidence = customer_analysis.get('confidence', 0)
        summary += f"**Data Sources**: {data_sources} voice-of-customer entries | **Confidence**: {confidence:.0%}\n\n"

        # Buyer Personas
        summary += "### Buyer Personas\n\n"
        for i, persona in enumerate(personas, 1):
            summary += f"#### {i}. {persona.get('role', 'Unknown Role')}\n\n"
            summary += f"- **Decision Authority**: {persona.get('decision_authority', 'Unknown')}\n"
            summary += f"- **Primary Goals**: {', '.join(persona.get('primary_goals', []))}\n"
            summary += f"- **Key Pain Points**: {', '.join(persona.get('pain_points', []))}\n"
            summary += f"- **Usage Context**: {persona.get('usage_context', 'N/A')}\n"
            if persona.get('quote') != 'N/A - insufficient data':
                summary += f"- **Quote**: \"{persona.get('quote', '')}\"\n"
            summary += "\n"

        # Pain Points
        summary += "### Pain Point Analysis\n\n"
        pain_intensity = pain_analysis.get('pain_intensity_score', 0)
        summary += f"**Pain Intensity Score**: {pain_intensity:.1f}/100\n\n"

        top_pains = pain_analysis.get('top_pain_points', [])
        if top_pains:
            summary += "| Category | Mentions | Negativity | Top Keywords |\n"
            summary += "|----------|----------|------------|---------------|\n"
            for pain in top_pains:
                keywords = ', '.join(pain.get('keywords', [])[:3])
                summary += f"| {pain.get('category', 'Unknown')} | {pain.get('mention_count', 0)} | "
                summary += f"{pain.get('negativity_score', 0):.2f} | {keywords} |\n"
            summary += "\n"

        # Feature Gaps
        if feature_gaps:
            summary += "### Most Requested Features (Gaps in Current Solutions)\n\n"
            for gap in feature_gaps[:5]:
                summary += f"- **{gap.get('feature', 'Unknown')}** ({gap.get('mention_count', 0)} mentions) - "
                summary += f"Urgency: {gap.get('urgency', 'low')}\n"
            summary += "\n"

        # Jobs to Be Done
        if jtbd:
            summary += "### Jobs to Be Done\n\n"
            for i, job in enumerate(jtbd, 1):
                summary += f"#### {i}. {job.get('functional_job', 'Unknown')}\n\n"
                summary += f"- **Emotional Job**: {job.get('emotional_job', 'N/A')}\n"
                summary += f"- **Current Solution**: {job.get('current_solution', 'N/A')}\n"
                summary += f"- **Desired Outcome**: {job.get('desired_outcome', 'N/A')}\n"
                summary += f"- **Importance**: {job.get('importance_score', 0)}/10\n\n"

        return summary
