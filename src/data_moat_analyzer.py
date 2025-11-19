"""
Data Moat Analyzer Agent

Assesses defensibility and competitive moats for data product opportunities.
Evaluates exclusivity, network effects, switching costs, and barriers to entry.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from duckduckgo_search import DDGS
import json
import re
import time


class DataMoatAnalyzer:
    """Analyzes competitive moats and defensibility for data opportunities"""

    def __init__(self, llm: ChatOpenAI, audit_db=None):
        """
        Initialize Data Moat Analyzer

        Args:
            llm: Language model for analysis
            audit_db: Optional AuditDatabase for operation tracking
        """
        self.llm = llm
        self.audit_db = audit_db
        self.ddg = DDGS()

    def analyze_moats(
        self,
        data_needs: List[Dict],
        source_mapping: Dict[str, Any],
        naics_8_digit: str,
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze competitive moats for data opportunities

        Args:
            data_needs: List of data needs from DataNeedsResearcher
            source_mapping: Source mapping from DataSourceMapper
            naics_8_digit: 8-digit NAICS code
            segment_description: Segment description
            run_id: Audit trail run ID

        Returns:
            {
                'naics_8_digit': str,
                'moat_analysis_by_data_type': {
                    '<data_type>': {
                        'moat_factors': {
                            'exclusivity': {
                                'score': float,  # 0-10
                                'assessment': str,
                                'reasoning': str
                            },
                            'network_effects': {
                                'score': float,
                                'assessment': str,
                                'reasoning': str
                            },
                            'data_quality': {
                                'score': float,
                                'assessment': str,
                                'reasoning': str
                            },
                            'switching_costs': {
                                'score': float,
                                'assessment': str,
                                'reasoning': str
                            },
                            'scale_advantages': {
                                'score': float,
                                'assessment': str,
                                'reasoning': str
                            },
                            'regulatory_barriers': {
                                'score': float,
                                'assessment': str,
                                'reasoning': str
                            }
                        },
                        'composite_moat_score': float,  # 0-10
                        'moat_strength': str,  # strong, moderate, weak
                        'key_defensibility_factors': List[str],
                        'vulnerabilities': List[str],
                        'time_to_build_moat': str
                    }
                },
                'overall_moat_assessment': {
                    'avg_moat_score': float,
                    'strongest_moat_opportunity': str,
                    'common_vulnerabilities': List[str]
                },
                'confidence': float
            }
        """
        print(f"\n🏰 Analyzing competitive moats for {len(data_needs)} data types...")

        moat_analysis_by_data_type = {}

        # Analyze moats for each data need (top 5)
        for i, data_need in enumerate(data_needs[:5], 1):
            data_type = data_need.get('data_type', '')
            if not data_type:
                continue

            print(f"   Analyzing moats for data type {i}/{min(len(data_needs), 5)}: {data_type[:50]}...")

            # Get source mapping for this data type
            sources = source_mapping.get('sources_by_data_type', {}).get(data_type, {})

            moat_analysis = self._analyze_moat_for_data_type(
                data_type, sources, segment_description, run_id
            )

            moat_analysis_by_data_type[data_type] = moat_analysis

        # Overall assessment
        overall = self._assess_overall_moats(moat_analysis_by_data_type)

        print(f"   ✅ Average moat score: {overall['avg_moat_score']:.1f}/10")

        return {
            'naics_8_digit': naics_8_digit,
            'moat_analysis_by_data_type': moat_analysis_by_data_type,
            'overall_moat_assessment': overall,
            'confidence': self._calculate_confidence(moat_analysis_by_data_type)
        }

    def _analyze_moat_for_data_type(
        self,
        data_type: str,
        sources: Dict[str, Any],
        segment_description: str,
        run_id: str = None
    ) -> Dict[str, Any]:
        """Analyze moat for a specific data type"""

        # Phase 1: Barriers to entry research
        barrier_results = self._search_barriers_to_entry(
            data_type, segment_description, run_id
        )

        # Phase 2: Competitive dynamics
        competitive_results = self._search_competitive_dynamics(
            data_type, segment_description, run_id
        )

        # Phase 3: Data exclusivity research
        exclusivity_results = self._search_data_exclusivity(
            data_type, run_id
        )

        # Use LLM to analyze moat factors
        moat_analysis = self._analyze_moat_factors(
            data_type,
            sources,
            barrier_results,
            competitive_results,
            exclusivity_results
        )

        return moat_analysis

    def _search_barriers_to_entry(
        self,
        data_type: str,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for barriers to entry in this data market"""

        queries = [
            f'"{data_type}" barriers to entry',
            f'"{segment_description}" data business challenges',
            f'how hard to start "{data_type}" business',
            f'"{data_type}" regulatory requirements'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_moat_analyzer',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_competitive_dynamics(
        self,
        data_type: str,
        segment_description: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for competitive dynamics and switching costs"""

        queries = [
            f'"{data_type}" vendor lock-in',
            f'"{data_type}" switching costs',
            f'"{segment_description}" data integration challenges',
            f'"{data_type}" network effects'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_moat_analyzer',
                    query_text=query,
                    results=search_results
                )

        return results

    def _search_data_exclusivity(
        self,
        data_type: str,
        run_id: str = None
    ) -> List[Dict]:
        """Search for data exclusivity and unique access"""

        queries = [
            f'"{data_type}" exclusive data access',
            f'"{data_type}" proprietary data',
            f'"{data_type}" unique data source'
        ]

        results = []
        for query in queries:
            search_results = self._search_with_retry(query, max_results=3)
            results.extend(search_results)

            if self.audit_db and run_id:
                self.audit_db.log_search_query(
                    run_id=run_id,
                    agent_name='data_moat_analyzer',
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

    def _analyze_moat_factors(
        self,
        data_type: str,
        sources: Dict[str, Any],
        barrier_results: List[Dict],
        competitive_results: List[Dict],
        exclusivity_results: List[Dict]
    ) -> Dict[str, Any]:
        """Use LLM to analyze moat factors"""

        # Compile research
        analysis_text = f"DATA TYPE: {data_type}\n\n"

        # Include source information
        analysis_text += "DATA SOURCE CHARACTERISTICS:\n"
        primary_sources = sources.get('primary_sources', [])
        for source in primary_sources[:3]:
            analysis_text += f"- {source.get('source_name', '')}: "
            analysis_text += f"{source.get('accessibility', '')}, "
            analysis_text += f"{source.get('source_type', '')}\n"

        acquisition_strategy = sources.get('acquisition_strategy', {})
        analysis_text += f"\nExclusivity potential: {acquisition_strategy.get('exclusivity_potential', 'unknown')}\n"
        analysis_text += f"Data moat notes: {acquisition_strategy.get('data_moat', 'N/A')}\n"

        analysis_text += "\nBARRIERS TO ENTRY:\n"
        for r in barrier_results[:5]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        analysis_text += "\nCOMPETITIVE DYNAMICS:\n"
        for r in competitive_results[:5]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        analysis_text += "\nEXCLUSIVITY RESEARCH:\n"
        for r in exclusivity_results[:5]:
            analysis_text += f"- {r.get('title', '')}: {r.get('body', '')[:200]}\n"

        prompt = f"""Analyze competitive moats for this data opportunity:

{analysis_text}

Evaluate each moat factor on a 0-10 scale:

1. EXCLUSIVITY: Can you get unique/exclusive access to this data?
   - 10: Exclusive partnerships, proprietary collection methods
   - 5: Public data but complex to aggregate
   - 0: Freely available, easy to replicate

2. NETWORK EFFECTS: Does data get better as you get more customers?
   - 10: Strong two-sided network (more customers = more data = more customers)
   - 5: Moderate feedback loops
   - 0: No network effects

3. DATA QUALITY: Can you achieve superior data quality?
   - 10: Unique quality through curation, validation, expertise
   - 5: Moderate quality differentiation possible
   - 0: Commoditized, quality parity

4. SWITCHING COSTS: How hard is it for customers to switch away?
   - 10: High integration costs, workflow dependency
   - 5: Moderate switching friction
   - 0: Easy to switch, commoditized

5. SCALE ADVANTAGES: Do you get better with scale?
   - 10: Strong economies of scale in data acquisition/processing
   - 5: Moderate scale benefits
   - 0: No scale advantages

6. REGULATORY BARRIERS: Are there regulatory protections?
   - 10: Strong regulatory moats, licensing requirements
   - 5: Some regulatory complexity
   - 0: No regulatory barriers

Return ONLY valid JSON:
{{
  "moat_factors": {{
    "exclusivity": {{
      "score": <0-10>,
      "assessment": "<strong|moderate|weak>",
      "reasoning": "<specific reason>"
    }},
    "network_effects": {{
      "score": <0-10>,
      "assessment": "<strong|moderate|weak>",
      "reasoning": "<specific reason>"
    }},
    "data_quality": {{
      "score": <0-10>,
      "assessment": "<strong|moderate|weak>",
      "reasoning": "<specific reason>"
    }},
    "switching_costs": {{
      "score": <0-10>,
      "assessment": "<strong|moderate|weak>",
      "reasoning": "<specific reason>"
    }},
    "scale_advantages": {{
      "score": <0-10>,
      "assessment": "<strong|moderate|weak>",
      "reasoning": "<specific reason>"
    }},
    "regulatory_barriers": {{
      "score": <0-10>,
      "assessment": "<strong|moderate|weak>",
      "reasoning": "<specific reason>"
    }}
  }},
  "composite_moat_score": <average of all scores>,
  "moat_strength": "<strong|moderate|weak>",
  "key_defensibility_factors": ["<top 2-3 moat factors>"],
  "vulnerabilities": ["<main risks to moat>"],
  "time_to_build_moat": "<6 months|1 year|2+ years>"
}}

Be realistic. Most data businesses have moderate moats (4-6 range).
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a competitive strategy analyst. Assess moat defensibility honestly."),
                HumanMessage(content=prompt)
            ])

            result = self._parse_json(response.content)
            if not result:
                return self._get_default_moat_analysis()

            return result

        except Exception as e:
            print(f"     ❌ Moat analysis failed: {e}")
            return self._get_default_moat_analysis()

    def _get_default_moat_analysis(self) -> Dict[str, Any]:
        """Return default moat analysis structure"""
        return {
            'moat_factors': {
                'exclusivity': {
                    'score': 0,
                    'assessment': 'unknown',
                    'reasoning': 'Insufficient data'
                },
                'network_effects': {
                    'score': 0,
                    'assessment': 'unknown',
                    'reasoning': 'Insufficient data'
                },
                'data_quality': {
                    'score': 0,
                    'assessment': 'unknown',
                    'reasoning': 'Insufficient data'
                },
                'switching_costs': {
                    'score': 0,
                    'assessment': 'unknown',
                    'reasoning': 'Insufficient data'
                },
                'scale_advantages': {
                    'score': 0,
                    'assessment': 'unknown',
                    'reasoning': 'Insufficient data'
                },
                'regulatory_barriers': {
                    'score': 0,
                    'assessment': 'unknown',
                    'reasoning': 'Insufficient data'
                }
            },
            'composite_moat_score': 0,
            'moat_strength': 'unknown',
            'key_defensibility_factors': [],
            'vulnerabilities': [],
            'time_to_build_moat': 'unknown'
        }

    def _assess_overall_moats(
        self,
        moat_analysis_by_data_type: Dict
    ) -> Dict[str, Any]:
        """Assess overall moat landscape"""

        if not moat_analysis_by_data_type:
            return {
                'avg_moat_score': 0,
                'strongest_moat_opportunity': 'None identified',
                'common_vulnerabilities': []
            }

        # Calculate average moat score
        moat_scores = [
            analysis.get('composite_moat_score', 0)
            for analysis in moat_analysis_by_data_type.values()
        ]
        avg_moat = sum(moat_scores) / len(moat_scores) if moat_scores else 0

        # Find strongest moat
        strongest = max(
            moat_analysis_by_data_type.items(),
            key=lambda x: x[1].get('composite_moat_score', 0),
            default=(None, {})
        )
        strongest_name = strongest[0] if strongest[0] else 'None'

        # Collect common vulnerabilities
        from collections import Counter
        all_vulnerabilities = []
        for analysis in moat_analysis_by_data_type.values():
            all_vulnerabilities.extend(analysis.get('vulnerabilities', []))

        vulnerability_counts = Counter(all_vulnerabilities)
        common_vulnerabilities = [v for v, _ in vulnerability_counts.most_common(3)]

        return {
            'avg_moat_score': round(avg_moat, 1),
            'strongest_moat_opportunity': strongest_name,
            'common_vulnerabilities': common_vulnerabilities
        }

    def _calculate_confidence(
        self,
        moat_analysis_by_data_type: Dict
    ) -> float:
        """Calculate confidence in moat analysis"""

        if not moat_analysis_by_data_type:
            return 0.1

        # Count how many have actual moat scores
        types_with_moats = sum(
            1 for analysis in moat_analysis_by_data_type.values()
            if analysis.get('composite_moat_score', 0) > 0
        )

        coverage = types_with_moats / len(moat_analysis_by_data_type)
        return max(0.3, min(0.8, coverage))  # Moat analysis inherently subjective

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
    # Test data moat analyzer
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

    analyzer = DataMoatAnalyzer(llm)

    # Test with sample data needs
    sample_needs = [
        {
            'data_type': 'Worker compensation insurance rates by state and job classification',
            'business_function': 'Insurance pricing and risk assessment'
        }
    ]

    sample_sources = {
        'sources_by_data_type': {
            'Worker compensation insurance rates by state and job classification': {
                'primary_sources': [
                    {
                        'source_name': 'NCCI',
                        'accessibility': 'licensable',
                        'source_type': 'government'
                    }
                ],
                'acquisition_strategy': {
                    'exclusivity_potential': 'medium',
                    'data_moat': 'Regulatory relationships, data quality curation'
                }
            }
        }
    }

    result = analyzer.analyze_moats(
        data_needs=sample_needs,
        source_mapping=sample_sources,
        naics_8_digit="52412601",
        segment_description="Direct Property and Casualty Insurance Carriers"
    )

    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    print(json.dumps(result, indent=2))
