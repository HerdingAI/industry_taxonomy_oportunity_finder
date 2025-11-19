"""
Data Vendor Analyzer - Phase 2 Orchestrator

Main orchestrator that connects all 7 Phase 2 agents using LangGraph to analyze
data-vendor business opportunities for 8-digit NAICS segments.

Architecture:
    User Input (NAICS + Description)
        ↓
    DataVendorAnalyzer.analyze()
        ↓
    LangGraph Workflow (7 Sequential Agents)
        ↓
    Comprehensive Opportunity Report
"""

from typing import Dict, Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
import uuid
import time
from datetime import datetime

# Import all Phase 2 agents
from data_needs_researcher import DataNeedsResearcher
from vendor_intelligence_agent import VendorIntelligenceAgent
from data_source_mapper import DataSourceMapper
from data_market_sizer import DataMarketSizer
from data_moat_analyzer import DataMoatAnalyzer
from data_product_designer import DataProductDesigner
from data_opportunity_synthesizer import DataOpportunitySynthesizer


class DataVendorAnalysisState(TypedDict):
    """State object passed between agents in the LangGraph workflow"""

    # Input
    naics_8_digit: str
    segment_description: str
    run_id: str

    # Agent outputs
    data_needs: Optional[Dict[str, Any]]
    vendor_landscape: Optional[Dict[str, Any]]
    source_mapping: Optional[Dict[str, Any]]
    market_sizing: Optional[Dict[str, Any]]
    moat_analysis: Optional[Dict[str, Any]]
    product_design: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]

    # Metadata
    start_time: float
    error: Optional[str]
    agent_execution_times: Dict[str, float]


class DataVendorAnalyzer:
    """
    Main orchestrator for Phase 2 data-vendor opportunity analysis.

    Connects all 7 agents in a sequential LangGraph workflow to discover,
    analyze, and synthesize data-vendor business opportunities.
    """

    def __init__(self, llm: ChatOpenAI, audit_db=None, rag_db=None):
        """
        Initialize DataVendorAnalyzer with all Phase 2 agents

        Args:
            llm: ChatOpenAI instance for LLM analysis
            audit_db: AuditDatabase instance for tracking
            rag_db: RAGDatabase instance for context
        """
        self.llm = llm
        self.audit_db = audit_db
        self.rag_db = rag_db

        # Initialize all 7 Phase 2 agents
        self.data_needs_researcher = DataNeedsResearcher(llm, audit_db)
        self.vendor_intelligence = VendorIntelligenceAgent(llm, audit_db)
        self.data_source_mapper = DataSourceMapper(llm, audit_db)
        self.data_market_sizer = DataMarketSizer(llm, audit_db)
        self.data_moat_analyzer = DataMoatAnalyzer(llm, audit_db)
        self.data_product_designer = DataProductDesigner(llm, audit_db)
        self.data_opportunity_synthesizer = DataOpportunitySynthesizer(llm, audit_db)

        # Build LangGraph workflow
        self.workflow = self._build_workflow()

    def analyze(
        self,
        naics_8_digit: str,
        segment_description: str,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a single 8-digit NAICS segment for data-vendor opportunities

        Args:
            naics_8_digit: 8-digit NAICS code
            segment_description: Description of the segment
            run_id: Optional run ID for tracking (generated if not provided)

        Returns:
            Complete analysis report with opportunities ranked by composite score

        Example:
            analyzer = DataVendorAnalyzer(llm, audit_db)
            report = analyzer.analyze(
                "52411001",
                "Direct Property and Casualty Insurance Carriers"
            )
        """
        if not run_id:
            run_id = f"phase2_{naics_8_digit}_{uuid.uuid4().hex[:8]}"

        # Initialize state
        initial_state: DataVendorAnalysisState = {
            'naics_8_digit': naics_8_digit,
            'segment_description': segment_description,
            'run_id': run_id,
            'data_needs': None,
            'vendor_landscape': None,
            'source_mapping': None,
            'market_sizing': None,
            'moat_analysis': None,
            'product_design': None,
            'final_report': None,
            'start_time': time.time(),
            'error': None,
            'agent_execution_times': {}
        }

        # Log start of analysis
        if self.audit_db:
            self.audit_db.log_llm_call(
                run_id=run_id,
                agent_name='data_vendor_analyzer',
                prompt=f"Starting Phase 2 analysis for {naics_8_digit}: {segment_description}",
                response="WORKFLOW_START",
                prompt_tokens=0,
                completion_tokens=0,
                cost=0.0
            )

        try:
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)

            # Calculate total time
            total_time = time.time() - final_state['start_time']

            # Add summary metadata
            result = final_state['final_report'] if final_state.get('final_report') else {}
            result['metadata'] = {
                'naics_8_digit': naics_8_digit,
                'segment_description': segment_description,
                'run_id': run_id,
                'total_execution_time_seconds': round(total_time, 2),
                'agent_execution_times': final_state['agent_execution_times'],
                'timestamp': datetime.now().isoformat(),
                'error': final_state.get('error')
            }

            # Log completion
            if self.audit_db:
                self.audit_db.log_llm_call(
                    run_id=run_id,
                    agent_name='data_vendor_analyzer',
                    prompt=f"Completed Phase 2 analysis for {naics_8_digit}",
                    response="WORKFLOW_COMPLETE",
                    prompt_tokens=0,
                    completion_tokens=0,
                    cost=0.0
                )

            return result

        except Exception as e:
            error_msg = f"Workflow error: {str(e)}"
            print(f"❌ Error in DataVendorAnalyzer: {error_msg}")

            if self.audit_db:
                self.audit_db.log_llm_call(
                    run_id=run_id,
                    agent_name='data_vendor_analyzer',
                    prompt=f"Error in Phase 2 analysis for {naics_8_digit}",
                    response=f"ERROR: {error_msg}",
                    prompt_tokens=0,
                    completion_tokens=0,
                    cost=0.0
                )

            return {
                'error': error_msg,
                'naics_8_digit': naics_8_digit,
                'segment_description': segment_description,
                'run_id': run_id
            }

    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow connecting all 7 agents sequentially

        Workflow Flow:
            START → discover_needs → analyze_vendors → map_sources →
            size_market → analyze_moat → design_product → synthesize → END
        """
        workflow = StateGraph(DataVendorAnalysisState)

        # Add nodes for each agent
        workflow.add_node("discover_needs", self._node_discover_needs)
        workflow.add_node("analyze_vendors", self._node_analyze_vendors)
        workflow.add_node("map_sources", self._node_map_sources)
        workflow.add_node("size_market", self._node_size_market)
        workflow.add_node("analyze_moat", self._node_analyze_moat)
        workflow.add_node("design_product", self._node_design_product)
        workflow.add_node("synthesize", self._node_synthesize)

        # Define sequential flow
        workflow.add_edge(START, "discover_needs")
        workflow.add_edge("discover_needs", "analyze_vendors")
        workflow.add_edge("analyze_vendors", "map_sources")
        workflow.add_edge("map_sources", "size_market")
        workflow.add_edge("size_market", "analyze_moat")
        workflow.add_edge("analyze_moat", "design_product")
        workflow.add_edge("design_product", "synthesize")
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    # ========================================================================
    # NODE FUNCTIONS - One for each agent
    # ========================================================================

    def _node_discover_needs(self, state: DataVendorAnalysisState) -> Dict[str, Any]:
        """Node 1: Discover operational data needs"""
        print(f"\n🔍 [1/7] Discovering data needs for {state['naics_8_digit']}...")
        start = time.time()

        try:
            data_needs = self.data_needs_researcher.discover_data_needs(
                naics_8_digit=state['naics_8_digit'],
                segment_description=state['segment_description'],
                run_id=state['run_id']
            )

            elapsed = time.time() - start
            state['agent_execution_times']['discover_needs'] = round(elapsed, 2)
            state['data_needs'] = data_needs

            needs_count = len(data_needs.get('data_needs', []))
            print(f"✅ Discovered {needs_count} data needs in {elapsed:.1f}s")

        except Exception as e:
            print(f"❌ Error discovering needs: {str(e)}")
            state['error'] = f"discover_needs: {str(e)}"
            state['data_needs'] = {'data_needs': [], 'error': str(e)}

        return state

    def _node_analyze_vendors(self, state: DataVendorAnalysisState) -> Dict[str, Any]:
        """Node 2: Analyze vendor landscape"""
        print(f"\n🏢 [2/7] Analyzing vendor landscape...")
        start = time.time()

        try:
            data_needs = state.get('data_needs', {}).get('data_needs', [])

            vendor_landscape = self.vendor_intelligence.analyze_vendor_landscape(
                data_needs=data_needs,
                naics_8_digit=state['naics_8_digit'],
                segment_description=state['segment_description'],
                run_id=state['run_id']
            )

            elapsed = time.time() - start
            state['agent_execution_times']['analyze_vendors'] = round(elapsed, 2)
            state['vendor_landscape'] = vendor_landscape

            vendor_count = len(vendor_landscape.get('vendors_by_data_type', {}))
            print(f"✅ Analyzed {vendor_count} data type markets in {elapsed:.1f}s")

        except Exception as e:
            print(f"❌ Error analyzing vendors: {str(e)}")
            state['error'] = f"analyze_vendors: {str(e)}"
            state['vendor_landscape'] = {'vendors_by_data_type': {}, 'error': str(e)}

        return state

    def _node_map_sources(self, state: DataVendorAnalysisState) -> Dict[str, Any]:
        """Node 3: Map data sources and acquisition strategies"""
        print(f"\n📊 [3/7] Mapping data sources...")
        start = time.time()

        try:
            data_needs = state.get('data_needs', {}).get('data_needs', [])

            source_mapping = self.data_source_mapper.map_data_sources(
                data_needs=data_needs,
                naics_8_digit=state['naics_8_digit'],
                segment_description=state['segment_description'],
                run_id=state['run_id']
            )

            elapsed = time.time() - start
            state['agent_execution_times']['map_sources'] = round(elapsed, 2)
            state['source_mapping'] = source_mapping

            source_count = len(source_mapping.get('sources_by_data_type', {}))
            print(f"✅ Mapped {source_count} data source strategies in {elapsed:.1f}s")

        except Exception as e:
            print(f"❌ Error mapping sources: {str(e)}")
            state['error'] = f"map_sources: {str(e)}"
            state['source_mapping'] = {'sources_by_data_type': {}, 'error': str(e)}

        return state

    def _node_size_market(self, state: DataVendorAnalysisState) -> Dict[str, Any]:
        """Node 4: Calculate market size and unit economics"""
        print(f"\n💰 [4/7] Sizing market opportunity...")
        start = time.time()

        try:
            data_needs = state.get('data_needs', {}).get('data_needs', [])

            market_sizing = self.data_market_sizer.size_market(
                data_needs=data_needs,
                naics_8_digit=state['naics_8_digit'],
                segment_description=state['segment_description'],
                run_id=state['run_id']
            )

            elapsed = time.time() - start
            state['agent_execution_times']['size_market'] = round(elapsed, 2)
            state['market_sizing'] = market_sizing

            tam = market_sizing.get('total_tam', 0)
            print(f"✅ Estimated TAM: ${tam:,.0f} in {elapsed:.1f}s")

        except Exception as e:
            print(f"❌ Error sizing market: {str(e)}")
            state['error'] = f"size_market: {str(e)}"
            state['market_sizing'] = {'total_tam': 0, 'error': str(e)}

        return state

    def _node_analyze_moat(self, state: DataVendorAnalysisState) -> Dict[str, Any]:
        """Node 5: Analyze competitive moats and defensibility"""
        print(f"\n🏰 [5/7] Analyzing competitive moat...")
        start = time.time()

        try:
            data_needs = state.get('data_needs', {}).get('data_needs', [])
            source_mapping = state.get('source_mapping', {})

            moat_analysis = self.data_moat_analyzer.analyze_moats(
                data_needs=data_needs,
                source_mapping=source_mapping,
                naics_8_digit=state['naics_8_digit'],
                segment_description=state['segment_description'],
                run_id=state['run_id']
            )

            elapsed = time.time() - start
            state['agent_execution_times']['analyze_moat'] = round(elapsed, 2)
            state['moat_analysis'] = moat_analysis

            moat_score = moat_analysis.get('composite_moat_score', 0)
            print(f"✅ Composite moat score: {moat_score:.1f}/10 in {elapsed:.1f}s")

        except Exception as e:
            print(f"❌ Error analyzing moat: {str(e)}")
            state['error'] = f"analyze_moat: {str(e)}"
            state['moat_analysis'] = {'composite_moat_score': 0, 'error': str(e)}

        return state

    def _node_design_product(self, state: DataVendorAnalysisState) -> Dict[str, Any]:
        """Node 6: Design data product specifications"""
        print(f"\n🎨 [6/7] Designing product specifications...")
        start = time.time()

        try:
            data_needs = state.get('data_needs', {}).get('data_needs', [])
            vendor_landscape = state.get('vendor_landscape', {})
            market_sizing = state.get('market_sizing', {})

            product_design = self.data_product_designer.design_product(
                data_needs=data_needs,
                vendor_landscape=vendor_landscape,
                market_sizing=market_sizing,
                naics_8_digit=state['naics_8_digit'],
                segment_description=state['segment_description'],
                run_id=state['run_id']
            )

            elapsed = time.time() - start
            state['agent_execution_times']['design_product'] = round(elapsed, 2)
            state['product_design'] = product_design

            products_designed = len(product_design.get('products', []))
            print(f"✅ Designed {products_designed} product offerings in {elapsed:.1f}s")

        except Exception as e:
            print(f"❌ Error designing product: {str(e)}")
            state['error'] = f"design_product: {str(e)}"
            state['product_design'] = {'products': [], 'error': str(e)}

        return state

    def _node_synthesize(self, state: DataVendorAnalysisState) -> Dict[str, Any]:
        """Node 7: Synthesize final opportunity report"""
        print(f"\n📝 [7/7] Synthesizing opportunity report...")
        start = time.time()

        try:
            final_report = self.data_opportunity_synthesizer.synthesize_opportunities(
                naics_8_digit=state['naics_8_digit'],
                segment_description=state['segment_description'],
                data_needs=state.get('data_needs', {}),
                vendor_landscape=state.get('vendor_landscape', {}),
                source_mapping=state.get('source_mapping', {}),
                market_sizing=state.get('market_sizing', {}),
                moat_analysis=state.get('moat_analysis', {}),
                product_design=state.get('product_design', {}),
                run_id=state['run_id']
            )

            elapsed = time.time() - start
            state['agent_execution_times']['synthesize'] = round(elapsed, 2)
            state['final_report'] = final_report

            opportunities = len(final_report.get('ranked_opportunities', []))
            tier1_count = sum(1 for opp in final_report.get('ranked_opportunities', [])
                             if opp.get('tier') == 'TIER_1')
            print(f"✅ Synthesized {opportunities} opportunities ({tier1_count} TIER_1) in {elapsed:.1f}s")

            # Print final summary
            total_time = time.time() - state['start_time']
            print(f"\n{'='*60}")
            print(f"✨ Analysis Complete for {state['naics_8_digit']}")
            print(f"   Total Time: {total_time:.1f}s")
            print(f"   Opportunities: {opportunities} ({tier1_count} TIER_1)")
            print(f"   Composite Score: {final_report.get('ranked_opportunities', [{}])[0].get('composite_score', 0):.1f}/100")
            print(f"{'='*60}\n")

        except Exception as e:
            print(f"❌ Error synthesizing report: {str(e)}")
            state['error'] = f"synthesize: {str(e)}"
            state['final_report'] = {'ranked_opportunities': [], 'error': str(e)}

        return state


# ============================================================================
# STANDALONE USAGE
# ============================================================================

if __name__ == "__main__":
    """Test the DataVendorAnalyzer with a sample NAICS code"""
    import os
    from langchain_openai import ChatOpenAI
    from audit_database import AuditDatabase

    # Initialize components
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    audit_db = AuditDatabase("data/audit.db")

    # Create analyzer
    analyzer = DataVendorAnalyzer(llm, audit_db)

    # Test with a sample NAICS code
    test_naics = "52411001"
    test_description = "Direct Property and Casualty Insurance Carriers"

    print(f"Testing DataVendorAnalyzer with {test_naics}: {test_description}\n")

    result = analyzer.analyze(
        naics_8_digit=test_naics,
        segment_description=test_description
    )

    # Print summary
    if result.get('error'):
        print(f"\n❌ Analysis failed: {result['error']}")
    else:
        print("\n✅ Analysis succeeded!")
        print(f"   Run ID: {result['metadata']['run_id']}")
        print(f"   Execution Time: {result['metadata']['total_execution_time_seconds']}s")
        print(f"   Opportunities Found: {len(result.get('ranked_opportunities', []))}")
