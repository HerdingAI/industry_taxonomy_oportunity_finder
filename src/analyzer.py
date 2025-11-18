"""
Main Analysis Orchestrator using LangGraph
Coordinates Research → Strategic → Quantitative → Synthesizer agents
"""

import os
from typing import TypedDict, Dict, Any
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from .database import DatabaseManager
from .audit_database import AuditDatabase
from .rag_database import RAGDatabase
from .research_agent import ResearchAgent
from .strategic_agent import StrategicAnalyst
from .quantitative_agent import QuantitativeAnalyst
from .synthesizer_agent import SynthesizerAgent
from .supervisor_agent import SupervisorAgent
from .technical_data_scientist_agent import TechnicalDataScientistAgent
from .product_manager_agent import ProductManagerAgent


class AnalysisState(TypedDict):
    """State passed between agents"""
    naics_code: str
    industry_name: str
    phase: str  # "PHASE_1" or "PHASE_2"
    run_id: str  # Audit trail identifier

    # Agent outputs
    research_data: Dict[str, Any]
    strategic_data: Dict[str, Any]
    quantitative_data: Dict[str, Any]
    customer_analysis: Dict[str, Any]  # Product Manager output
    automation_analysis: Dict[str, Any]  # Technical Data Scientist output
    final_report: str

    # Metadata
    error: str
    error_count: int
    completed: bool


class IndustryAnalyzer:
    """Main analyzer orchestrating all agents"""

    def __init__(
        self,
        openrouter_api_key: str,
        model: str = "openrouter/sherlock-think-alpha",
        db_dir: str = "data"
    ):
        """
        Initialize analyzer with all agents

        Args:
            openrouter_api_key: OpenRouter API key
            model: Model to use for analysis
            db_dir: Directory for databases
        """

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.4,
            max_tokens=4000
        )

        # Initialize databases
        self.db = DatabaseManager(db_dir)
        self.audit_db = AuditDatabase(db_dir)

        # Initialize RAG database (optional - gracefully handles if not configured)
        try:
            self.rag_db = RAGDatabase()
            print("✅ RAG database connected")
        except Exception as e:
            print(f"⚠️  RAG database not available: {e}")
            self.rag_db = None

        # Store model name for audit logging
        self.model_name = model

        # Initialize agents (pass RAG database where needed)
        self.research_agent = ResearchAgent(self.llm, rag_db=self.rag_db)
        self.strategic_agent = StrategicAnalyst(self.llm, rag_db=self.rag_db)
        self.quant_agent = QuantitativeAnalyst(self.llm, rag_db=self.rag_db)
        self.synthesizer = SynthesizerAgent(self.llm)

        # New agents for MBA-Data Science methodology
        self.supervisor_agent = SupervisorAgent(self.llm, query_budget=3000)
        self.technical_ds_agent = TechnicalDataScientistAgent(self.llm, rag_db=self.rag_db)
        self.product_mgr_agent = ProductManagerAgent(self.llm, rag_db=self.rag_db)

        # Build workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""

        workflow = StateGraph(AnalysisState)

        # Add nodes
        workflow.add_node("research", self._research_node)
        workflow.add_node("customer_analysis", self._customer_analysis_node)
        workflow.add_node("automation_analysis", self._automation_analysis_node)
        workflow.add_node("strategic_analysis", self._strategic_node)
        workflow.add_node("quantitative_analysis", self._quantitative_node)
        workflow.add_node("synthesize", self._synthesize_node)
        workflow.add_node("save_results", self._save_node)

        # Define flow: Research → Customer & Automation (parallel) → Strategic → Quantitative → Synthesize → Save
        workflow.set_entry_point("research")
        workflow.add_edge("research", "customer_analysis")
        workflow.add_edge("customer_analysis", "automation_analysis")
        workflow.add_edge("automation_analysis", "strategic_analysis")
        workflow.add_edge("strategic_analysis", "quantitative_analysis")
        workflow.add_edge("quantitative_analysis", "synthesize")
        workflow.add_edge("synthesize", "save_results")
        workflow.add_edge("save_results", END)

        return workflow.compile()

    def _research_node(self, state: AnalysisState) -> AnalysisState:
        """Research agent node"""
        try:
            phase = state.get('phase', 'PHASE_1')
            research_data = self.research_agent.research_industry(
                state['naics_code'],
                state.get('industry_name'),
                phase=phase
            )

            state['research_data'] = research_data
            state['industry_name'] = research_data.get('industry_name', '')

            # Store research in vector DB
            self.db.add_research(
                state['naics_code'],
                f"Industry: {research_data.get('industry_name', 'Unknown')}. "
                f"Market: ${(research_data.get('market_size_usd') or 0)/1e9:.1f}B, "
                f"growth {(research_data.get('growth_rate') or 0)*100:.1f}%. "
                f"Pain points: {', '.join([p.get('pain', '') for p in (research_data.get('pain_points') or [])[:3]])}",
                {
                    'phase': 'research',
                    'confidence': research_data.get('confidence') or 0.5
                }
            )

            # Save audit snapshot
            self.audit_db.save_snapshot(
                run_id=state.get('run_id'),
                snapshot_type='research_complete',
                data=research_data
            )

        except Exception as e:
            print(f"❌ Research failed: {e}")
            state['error'] = f"Research error: {str(e)}"
            state['error_count'] = state.get('error_count', 0) + 1

        return state

    def _customer_analysis_node(self, state: AnalysisState) -> AnalysisState:
        """Product Manager agent node - customer and buyer persona analysis"""
        try:
            if not self.product_mgr_agent.rag_db:
                print("⚠️  Skipping customer analysis (RAG database not available)")
                state['customer_analysis'] = {}
                return state

            customer_analysis = self.product_mgr_agent.analyze_customer_landscape(
                naics_code=state['naics_code'],
                industry_name=state['industry_name']
            )

            state['customer_analysis'] = customer_analysis

        except Exception as e:
            print(f"❌ Customer analysis failed: {e}")
            state['customer_analysis'] = {}
            state['error'] = f"Customer analysis error: {str(e)}"
            state['error_count'] = state.get('error_count', 0) + 1

        return state

    def _automation_analysis_node(self, state: AnalysisState) -> AnalysisState:
        """Technical Data Scientist agent node - automation potential analysis"""
        try:
            if not self.technical_ds_agent.rag_db:
                print("⚠️  Skipping automation analysis (RAG database not available)")
                state['automation_analysis'] = {}
                return state

            automation_analysis = self.technical_ds_agent.analyze_industry_automation_potential(
                naics_code=state['naics_code']
            )

            state['automation_analysis'] = automation_analysis

        except Exception as e:
            print(f"❌ Automation analysis failed: {e}")
            state['automation_analysis'] = {}
            state['error'] = f"Automation analysis error: {str(e)}"
            state['error_count'] = state.get('error_count', 0) + 1

        return state

    def _strategic_node(self, state: AnalysisState) -> AnalysisState:
        """Strategic analysis node"""
        try:
            strategic_data = self.strategic_agent.analyze(
                state['research_data'],
                naics_code=state['naics_code']
            )
            state['strategic_data'] = strategic_data

            # Store strategic insights in vector DB
            porters = strategic_data.get('porters_five_forces') or {}
            positioning = strategic_data.get('strategic_positioning') or {}

            insight_text = f"Porter's: {porters.get('strategic_verdict', '')}. " \
                          f"Best positioning: {positioning.get('best_positioning', '')}. " \
                          f"White space: {positioning.get('white_space_opportunity', '')}"

            self.db.add_insight(
                state['naics_code'],
                insight_text,
                'strategic_analysis'
            )

            # Save audit snapshot
            self.audit_db.save_snapshot(
                run_id=state.get('run_id'),
                snapshot_type='strategic_complete',
                data=strategic_data
            )

        except Exception as e:
            print(f"❌ Strategic analysis failed: {e}")
            state['error'] = f"Strategic error: {str(e)}"
            state['error_count'] = state.get('error_count', 0) + 1

        return state

    def _quantitative_node(self, state: AnalysisState) -> AnalysisState:
        """Quantitative analysis node"""
        try:
            quant_data = self.quant_agent.analyze(
                state['research_data'],
                state['strategic_data'],
                customer_analysis=state.get('customer_analysis'),
                automation_analysis=state.get('automation_analysis')
            )
            state['quantitative_data'] = quant_data

            # Save audit snapshot
            self.audit_db.save_snapshot(
                run_id=state.get('run_id'),
                snapshot_type='quantitative_complete',
                data=quant_data
            )

        except Exception as e:
            print(f"❌ Quantitative analysis failed: {e}")
            state['error'] = f"Quantitative error: {str(e)}"
            state['error_count'] = state.get('error_count', 0) + 1

        return state

    def _synthesize_node(self, state: AnalysisState) -> AnalysisState:
        """Synthesize final report"""
        try:
            # Use business_model format for Phase 2, comprehensive for Phase 1
            phase = state.get('phase', 'PHASE_1')
            report_format = "business_model" if phase == "PHASE_2" else "comprehensive"

            report = self.synthesizer.synthesize(
                state['research_data'],
                state['strategic_data'],
                state['quantitative_data'],
                customer_analysis=state.get('customer_analysis'),
                automation_analysis=state.get('automation_analysis'),
                report_format=report_format
            )
            state['final_report'] = report

        except Exception as e:
            print(f"❌ Synthesis failed: {e}")
            state['error'] = f"Synthesis error: {str(e)}"
            state['error_count'] = state.get('error_count', 0) + 1

        return state

    def _save_node(self, state: AnalysisState) -> AnalysisState:
        """Save results to database"""
        def safe_get(d, key, default=None):
            """Safely get nested dict values"""
            return d.get(key, default) if isinstance(d, dict) else default

        try:
            # Save industry data
            research = state['research_data']
            strategic = state['strategic_data']

            porters = safe_get(strategic, 'porters_five_forces', {})

            self.db.save_industry({
                'naics_code': state['naics_code'],
                'name': state['industry_name'],
                'establishments': safe_get(research, 'establishments'),
                'employment': safe_get(research, 'employment'),
                'avg_wage': safe_get(research, 'avg_wage'),
                'market_size_usd': safe_get(research, 'market_size_usd'),
                'growth_rate': safe_get(research, 'growth_rate'),
                'hhi_index': safe_get(research, 'hhi_index'),
                'digital_maturity_score': self._convert_maturity_to_score(safe_get(research, 'digital_maturity')),
                'overall_score': safe_get(porters, 'overall_attractiveness'),
                'confidence': safe_get(research, 'confidence')
            })

            # Save Porter's forces
            self.db.save_porters_forces(state['naics_code'], porters)

            # Save pain points
            for pain in research.get('pain_points', []):
                # No need to save, just for tracking
                pass

            # Save opportunities
            quant = state['quantitative_data']
            for opp in safe_get(quant, 'opportunities', []):
                market_sizing = safe_get(opp, 'market_sizing', {})
                unit_econ = safe_get(opp, 'unit_economics', {})
                rationale = safe_get(opp, 'strategic_rationale', {})
                risk = safe_get(opp, 'risk_assessment', {})

                opp_id = self.db.save_opportunity({
                    'naics_code': state['naics_code'],
                    'title': safe_get(opp, 'opportunity_title', 'Unnamed Opportunity'),
                    'description': safe_get(opp, 'opportunity_description', ''),
                    'opportunity_type': 'ai_automation',
                    'opportunity_score': safe_get(opp, 'risk_adjusted_score', 0),
                    'confidence': safe_get(opp, 'overall_confidence', 0),
                    'risk_adjusted_score': safe_get(opp, 'risk_adjusted_score', 0),
                    'tam_usd': safe_get(market_sizing, 'tam_usd'),
                    'sam_usd': safe_get(market_sizing, 'sam_usd'),
                    'som_y3_usd': safe_get(market_sizing, 'som_y3_usd'),
                    'arpu': safe_get(unit_econ, 'arpu'),
                    'gross_margin': safe_get(unit_econ, 'gross_margin'),
                    'ltv': safe_get(unit_econ, 'ltv'),
                    'cac': safe_get(unit_econ, 'cac'),
                    'ltv_cac_ratio': safe_get(unit_econ, 'ltv_cac_ratio'),
                    'payback_months': safe_get(unit_econ, 'payback_months'),
                    'key_moat': safe_get(rationale, 'key_moat', ''),
                    'why_now': safe_get(rationale, 'why_now', ''),
                    'why_unsolved': safe_get(rationale, 'why_unsolved', ''),
                    'competitive_threat': safe_get(rationale, 'competitive_threat', ''),
                    'risk_factors': safe_get(risk, 'key_risks', []),
                    'expected_value_y5_usd': safe_get(risk, 'expected_value_y5_usd')
                })

                # Add to vector DB
                self.db.add_opportunity_to_vector(
                    opp_id,
                    f"{safe_get(opp, 'opportunity_title', 'Unnamed')}: {safe_get(opp, 'opportunity_description', '')}",
                    {
                        'naics_code': state['naics_code'],
                        'score': safe_get(opp, 'risk_adjusted_score', 0)
                    }
                )

            state['completed'] = True
            print("✅ Results saved to database")

        except Exception as e:
            print(f"❌ Save failed: {e}")
            state['error'] = f"Save error: {str(e)}"
            state['error_count'] = state.get('error_count', 0) + 1

        return state

    def _convert_maturity_to_score(self, maturity: str) -> float:
        """Convert digital maturity text to score"""
        mapping = {
            'low': 30.0,
            'medium': 60.0,
            'high': 85.0
        }
        return mapping.get(maturity, 50.0)

    def analyze(self, naics_code: str, industry_name: str = None, phase: str = "PHASE_1") -> Dict[str, Any]:
        """
        Run complete analysis for a NAICS code

        Args:
            naics_code: 6-digit NAICS code
            industry_name: Optional industry name (will be looked up if not provided)
            phase: Analysis phase - "PHASE_1" (quick screening) or "PHASE_2" (deep dive)

        Returns:
            Analysis results including final report
        """

        print(f"\n{'='*60}")
        print(f"🚀 NAICS {naics_code} Analysis Starting ({phase})")
        print(f"{'='*60}\n")

        # Start audit tracking
        run_id = self.audit_db.start_analysis_run(
            naics_code=naics_code,
            industry_name=industry_name,
            phase=phase,
            model_name=self.model_name
        )

        start_time = datetime.now()

        # Initialize state
        initial_state: AnalysisState = {
            'naics_code': naics_code,
            'industry_name': industry_name or '',
            'phase': phase,
            'run_id': run_id,
            'research_data': {},
            'strategic_data': {},
            'quantitative_data': {},
            'customer_analysis': {},
            'automation_analysis': {},
            'final_report': '',
            'error': '',
            'error_count': 0,
            'completed': False
        }

        try:
            # Run workflow
            final_state = self.workflow.invoke(initial_state)

            # Save final snapshot
            self.audit_db.save_snapshot(
                run_id=run_id,
                snapshot_type='final_state',
                data=final_state
            )

            duration = (datetime.now() - start_time).total_seconds()

            # End audit tracking
            self.audit_db.end_analysis_run(
                run_id=run_id,
                completed=True,
                error_count=final_state.get('error_count', 0),
                final_error=final_state.get('error')
            )

            print(f"\n{'='*60}")
            error_count = final_state.get('error_count', 0)
            if error_count > 0:
                print(f"⚠️  Analysis completed with {error_count} error(s) in {duration:.1f}s")
                if error_count >= 3:
                    print(f"❌ WARNING: High error count ({error_count}) - results may be unreliable")
            else:
                print(f"✅ Analysis completed successfully in {duration:.1f}s")

            # Print audit summary
            summary = self.audit_db.get_run_summary(run_id)
            print(f"📊 Audit: {summary['llm_stats']['count']} LLM calls, {summary['search_stats']['count']} searches, ${summary['llm_stats']['total_cost']:.3f} cost")
            print(f"💾 Audit trail: {run_id}")
            print(f"{'='*60}\n")

            return final_state

        except Exception as e:
            # Log the error
            import traceback
            self.audit_db.log_error(
                run_id=run_id,
                agent_name='analyzer',
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )

            # End audit tracking with failure
            self.audit_db.end_analysis_run(
                run_id=run_id,
                completed=False,
                error_count=99,
                final_error=str(e)
            )

            raise

    def save_report(self, analysis_result: Dict[str, Any], output_dir: str = "outputs") -> str:
        """Save markdown report to file"""
        import os

        os.makedirs(output_dir, exist_ok=True)

        naics_code = analysis_result['naics_code']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{output_dir}/naics_{naics_code}_{timestamp}.md"

        with open(filename, 'w') as f:
            f.write(analysis_result['final_report'])

        return filename

    def get_industry_summary(self) -> list:
        """Get summary of all analyzed industries"""
        return self.db.get_industry_summary()

    def get_top_opportunities(self, limit: int = 20) -> list:
        """Get top opportunities across all industries"""
        return self.db.get_top_opportunities(limit)

    def search_opportunities(self, query: str, top_k: int = 10) -> list:
        """Search for similar opportunities using vector search"""
        return self.db.search_similar_opportunities(query, top_k)

    def get_run_summary(self, run_id: str) -> dict:
        """Get audit summary for a specific run"""
        return self.audit_db.get_run_summary(run_id)

    def get_cost_summary(self, start_date: str = None) -> dict:
        """Get cost summary across all runs"""
        return self.audit_db.get_cost_summary(start_date)

    def export_run_data(self, run_id: str, output_file: str):
        """Export complete run data to JSON file"""
        self.audit_db.export_run_data(run_id, output_file)

    def close(self):
        """Close database connections"""
        self.db.close()
        self.audit_db.close()


if __name__ == "__main__":
    # Test the analyzer
    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        exit(1)

    analyzer = IndustryAnalyzer(api_key)

    # Run analysis
    result = analyzer.analyze("541511")

    # Print report
    print("\n" + result['final_report'])

    # Save report
    filename = analyzer.save_report(result)
    print(f"\n💾 Report saved: {filename}")

    analyzer.close()
