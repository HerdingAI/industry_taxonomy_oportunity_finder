"""
NAICS Industry Analysis Agent using LangGraph
Analyzes 6-digit NAICS codes to identify AI/automation opportunities
"""

import os
import json
from typing import TypedDict, List, Dict, Any, Annotated
from datetime import datetime
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()


class AnalysisState(TypedDict):
    """State for the NAICS analysis workflow"""
    naics_code: str
    industry_name: str

    # Analysis sections
    industry_overview: Dict[str, Any]
    operational_workflows: Dict[str, Any]
    technology_landscape: Dict[str, Any]
    ai_opportunities: List[Dict[str, Any]]
    niche_segments: List[Dict[str, Any]]
    top_opportunities: List[Dict[str, Any]]

    # Metadata
    research_data: List[str]
    analysis_complete: bool
    error: str


class NAICSAnalyzer:
    """LangGraph-based NAICS industry analyzer"""

    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.model_name = os.getenv("OPENROUTER_MODEL", "openrouter/sherlock-think-alpha")

        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        # Initialize LLM with OpenRouter
        self.llm = ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.7,
            max_tokens=4000,
        )

        # Build the analysis graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AnalysisState)

        # Add nodes for each analysis step
        workflow.add_node("research_industry", self.research_industry)
        workflow.add_node("map_workflows", self.map_workflows)
        workflow.add_node("analyze_technology", self.analyze_technology)
        workflow.add_node("identify_opportunities", self.identify_opportunities)
        workflow.add_node("find_niches", self.find_niches)
        workflow.add_node("rank_opportunities", self.rank_opportunities)
        workflow.add_node("generate_report", self.generate_report)

        # Define the workflow edges
        workflow.set_entry_point("research_industry")
        workflow.add_edge("research_industry", "map_workflows")
        workflow.add_edge("map_workflows", "analyze_technology")
        workflow.add_edge("analyze_technology", "identify_opportunities")
        workflow.add_edge("identify_opportunities", "find_niches")
        workflow.add_edge("find_niches", "rank_opportunities")
        workflow.add_edge("rank_opportunities", "generate_report")
        workflow.add_edge("generate_report", END)

        return workflow.compile()

    def research_industry(self, state: AnalysisState) -> AnalysisState:
        """Node 1: Research the industry and gather foundational information"""
        print(f"\n🔍 Researching NAICS {state['naics_code']}...")

        prompt = f"""You are an industry research expert. Analyze NAICS code {state['naics_code']}.

Provide comprehensive information about:

1. **Industry Definition**: What does this industry do? What products/services do they provide?

2. **Major Sub-segments**: Break down the industry into its main categories and specialized niches

3. **Value Chain**: Describe the end-to-end value chain from suppliers to end customers

4. **Market Characteristics**:
   - Approximate market size (if known)
   - Major players and market structure
   - Geographic concentration
   - Growth trends

5. **Typical Business Models**: How do companies in this industry make money?

Be specific and detailed. If you don't have exact data, make informed inferences based on industry knowledge.

Return your analysis as a structured JSON object with keys: definition, sub_segments (array), value_chain, market_size, major_players (array), business_models (array)."""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an expert industry analyst specializing in detailed market research and business operations."),
                HumanMessage(content=prompt)
            ])

            # Extract JSON from response
            content = response.content
            overview_data = self._extract_json(content)

            state["industry_overview"] = overview_data
            state["industry_name"] = overview_data.get("definition", "")[:100]
            state["research_data"] = [content]

            print(f"✅ Industry overview completed")

        except Exception as e:
            print(f"❌ Error in research_industry: {str(e)}")
            state["error"] = str(e)

        return state

    def map_workflows(self, state: AnalysisState) -> AnalysisState:
        """Node 2: Map operational workflows and processes"""
        print(f"\n📋 Mapping operational workflows...")

        prompt = f"""Based on this industry overview:
{json.dumps(state['industry_overview'], indent=2)}

Map out the **detailed operational workflows** for typical businesses in NAICS {state['naics_code']}.

For each major workflow, identify:

1. **End-to-End Processes**: Step-by-step operational processes (e.g., order intake → fulfillment → billing)

2. **Daily Tasks & Jobs**: What do employees actually DO every day?
   - Administrative tasks
   - Customer interactions
   - Documentation and paperwork
   - Reporting and compliance
   - Communication workflows

3. **Pain Points**:
   - Manual data entry
   - Repetitive tasks
   - Paper-based processes
   - Communication bottlenecks
   - Regulatory/compliance burdens
   - Error-prone steps

4. **Tools & Systems Used**:
   - Software applications
   - Physical tools
   - Paper forms and documents
   - Communication methods

Focus especially on MANUAL, PAPER-BASED, and REPETITIVE workflows - these are automation opportunities.

Return as JSON with keys: workflows (array of objects with: name, steps, actors, pain_points, tools_used, frequency, criticality)."""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an operations expert who deeply understands day-to-day business processes and workflow bottlenecks."),
                HumanMessage(content=prompt)
            ])

            content = response.content
            workflow_data = self._extract_json(content)

            state["operational_workflows"] = workflow_data
            state["research_data"].append(content)

            print(f"✅ Workflow mapping completed")

        except Exception as e:
            print(f"❌ Error in map_workflows: {str(e)}")
            state["error"] = str(e)

        return state

    def analyze_technology(self, state: AnalysisState) -> AnalysisState:
        """Node 3: Analyze current technology landscape"""
        print(f"\n💻 Analyzing technology landscape...")

        prompt = f"""Based on this industry and its workflows:

Industry: {state['industry_name']}
Workflows: {json.dumps(state['operational_workflows'], indent=2)}

Analyze the **technology landscape** for NAICS {state['naics_code']}:

1. **Current Software Categories Used**:
   - ERP systems
   - CRM platforms
   - Industry-specific software
   - Communication tools
   - Document management
   - Specialized applications

2. **Major Vendors**: Who provides software to this industry?

3. **Adoption Levels**:
   - Digital maturity (low/medium/high)
   - Cloud adoption
   - Mobile usage
   - AI/automation current state

4. **Technology Gaps**:
   - Outdated systems still in use
   - Manual processes that should be automated
   - Integration problems
   - Data silos

5. **Barriers to Technology Adoption**:
   - Cost
   - Complexity
   - Regulatory constraints
   - Resistance to change
   - Lack of awareness

Return as JSON with keys: software_categories (array), major_vendors (array), adoption_level (object), technology_gaps (array), barriers (array)."""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a technology analyst specializing in enterprise software and digital transformation across industries."),
                HumanMessage(content=prompt)
            ])

            content = response.content
            tech_data = self._extract_json(content)

            state["technology_landscape"] = tech_data
            state["research_data"].append(content)

            print(f"✅ Technology analysis completed")

        except Exception as e:
            print(f"❌ Error in analyze_technology: {str(e)}")
            state["error"] = str(e)

        return state

    def identify_opportunities(self, state: AnalysisState) -> AnalysisState:
        """Node 4: Identify specific AI/automation opportunities"""
        print(f"\n🤖 Identifying AI & automation opportunities...")

        prompt = f"""Based on all previous analysis:

Industry: {state['industry_name']}
Workflows: {json.dumps(state['operational_workflows'], indent=2)}
Technology: {json.dumps(state['technology_landscape'], indent=2)}

Identify **specific, actionable AI and automation opportunities** for NAICS {state['naics_code']}.

For EACH opportunity, provide:

1. **Workflow Step**: Which specific process/task can be automated?

2. **Current State**: How is this done today? (be specific about the manual process)

3. **AI/Automation Solution**:
   - Technology type (GenAI, RPA, ML, Computer Vision, etc.)
   - Specific application
   - How it works

4. **Expected Value**:
   - Time savings
   - Cost reduction
   - Error reduction
   - Revenue impact
   - Risk mitigation

5. **Target Customer**:
   - Who would buy this?
   - What's their pain level?
   - Buying authority

6. **Why Unsolved**:
   - Why hasn't this been automated yet?
   - What's the market failure?

7. **Implementation Difficulty**:
   - Low/Medium/High
   - Key challenges
   - Required data sources
   - Integration complexity

8. **Competitive Advantage**:
   - What would create defensibility?
   - Network effects?
   - Data moat?

Focus on opportunities where:
- Manual work is significant
- Process is repetitive
- High error rates exist
- Compliance/regulatory burden is high
- Communication inefficiencies exist

Return as JSON array of opportunity objects with all fields above."""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are an AI product strategist and startup advisor specializing in finding automation opportunities in traditional industries."),
                HumanMessage(content=prompt)
            ])

            content = response.content
            opportunities = self._extract_json(content)

            # Ensure it's a list
            if isinstance(opportunities, dict) and "opportunities" in opportunities:
                opportunities = opportunities["opportunities"]
            elif not isinstance(opportunities, list):
                opportunities = [opportunities]

            state["ai_opportunities"] = opportunities
            state["research_data"].append(content)

            print(f"✅ Identified {len(opportunities)} opportunities")

        except Exception as e:
            print(f"❌ Error in identify_opportunities: {str(e)}")
            state["error"] = str(e)

        return state

    def find_niches(self, state: AnalysisState) -> AnalysisState:
        """Node 5: Identify hidden niches and underserved segments"""
        print(f"\n🔎 Finding hidden niches...")

        prompt = f"""Based on the industry analysis for NAICS {state['naics_code']}:

Industry: {state['industry_name']}

Identify **HIDDEN NICHES** - overlooked segments and micro-markets:

1. **Specialized Sub-Segments**:
   - Niche service providers
   - Geographic specializations
   - Specific customer types
   - Unique business models

2. **Highly Manual Micro-Workflows**:
   - Small but painful tasks
   - Specialized professional processes
   - Compliance-heavy activities
   - Communication-intensive workflows

3. **Underserved Technology Segments**:
   - Small business vs enterprise gaps
   - Regional players
   - Legacy system users
   - Non-digitized segments

4. **Low-Tech Maturity Pockets**:
   - Where is tech adoption lowest?
   - Who's still using paper?
   - Which tasks are "too hard" to automate (but actually aren't)?

For each niche, explain:
- What makes it hidden/overlooked?
- Size of the opportunity
- Why it's underserved
- Specific pain points

Return as JSON array of niche objects."""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a market research specialist focused on discovering overlooked opportunities and underserved markets."),
                HumanMessage(content=prompt)
            ])

            content = response.content
            niches = self._extract_json(content)

            # Ensure it's a list
            if isinstance(niches, dict) and "niches" in niches:
                niches = niches["niches"]
            elif not isinstance(niches, list):
                niches = [niches]

            state["niche_segments"] = niches
            state["research_data"].append(content)

            print(f"✅ Found {len(niches)} niche segments")

        except Exception as e:
            print(f"❌ Error in find_niches: {str(e)}")
            state["error"] = str(e)

        return state

    def rank_opportunities(self, state: AnalysisState) -> AnalysisState:
        """Node 6: Rank and select top 5 opportunities"""
        print(f"\n🏆 Ranking opportunities...")

        prompt = f"""Based on all identified opportunities and niches:

AI Opportunities:
{json.dumps(state['ai_opportunities'], indent=2)}

Niche Segments:
{json.dumps(state['niche_segments'], indent=2)}

Select and rank the **TOP 5 MOST VIABLE AI/AUTOMATION STARTUP OPPORTUNITIES** for NAICS {state['naics_code']}.

For each top opportunity, provide:

1. **Opportunity Title**: Clear, specific name

2. **Detailed Description**: What exactly is the solution?

3. **Target Market**:
   - Specific customer persona
   - Market size estimate
   - Current spending on this problem

4. **Value Proposition**:
   - Quantified benefits
   - Why it's a must-have vs nice-to-have

5. **Competitive Moat**:
   - Why this is defensible
   - What creates switching costs
   - Network effects or data advantages

6. **Why Now?**:
   - What's changed to make this possible?
   - Why hasn't it been done before?

7. **Go-to-Market**:
   - How to reach customers
   - Pricing strategy
   - Sales cycle expectations

8. **Risk Factors**:
   - What could go wrong?
   - Competitive threats
   - Market risks

Rank from 1-5 based on:
- Market size
- Pain severity
- Technical feasibility
- Defensibility
- Speed to market

Return as JSON array of top 5 opportunities with all fields."""

        try:
            response = self.llm.invoke([
                SystemMessage(content="You are a venture capital analyst and startup advisor specializing in evaluating AI/automation business opportunities."),
                HumanMessage(content=prompt)
            ])

            content = response.content
            top_opps = self._extract_json(content)

            # Ensure it's a list
            if isinstance(top_opps, dict) and "opportunities" in top_opps:
                top_opps = top_opps["opportunities"]
            elif not isinstance(top_opps, list):
                top_opps = [top_opps]

            state["top_opportunities"] = top_opps[:5]  # Ensure only top 5
            state["research_data"].append(content)

            print(f"✅ Ranked top {len(state['top_opportunities'])} opportunities")

        except Exception as e:
            print(f"❌ Error in rank_opportunities: {str(e)}")
            state["error"] = str(e)

        return state

    def generate_report(self, state: AnalysisState) -> AnalysisState:
        """Node 7: Generate final comprehensive report"""
        print(f"\n📄 Generating final report...")

        state["analysis_complete"] = True

        return state

    def _extract_json(self, content: str) -> Any:
        """Extract JSON from LLM response (handles markdown code blocks)"""
        content = content.strip()

        # Remove markdown code blocks if present
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
            # If JSON parsing fails, try to find JSON object in text
            start_idx = content.find('{')
            end_idx = content.rfind('}')

            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx+1]
                return json.loads(json_str)

            # If still fails, try array
            start_idx = content.find('[')
            end_idx = content.rfind(']')

            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx+1]
                return json.loads(json_str)

            raise ValueError(f"Could not extract valid JSON from response")

    def analyze(self, naics_code: str) -> Dict[str, Any]:
        """Run the complete analysis for a NAICS code"""

        # Initialize state
        initial_state: AnalysisState = {
            "naics_code": naics_code,
            "industry_name": "",
            "industry_overview": {},
            "operational_workflows": {},
            "technology_landscape": {},
            "ai_opportunities": [],
            "niche_segments": [],
            "top_opportunities": [],
            "research_data": [],
            "analysis_complete": False,
            "error": ""
        }

        print(f"\n{'='*60}")
        print(f"🚀 Starting NAICS Analysis: {naics_code}")
        print(f"{'='*60}")

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        if final_state.get("error"):
            print(f"\n❌ Analysis completed with errors: {final_state['error']}")
        else:
            print(f"\n✅ Analysis completed successfully!")

        return final_state

    def save_report(self, analysis_result: Dict[str, Any], output_dir: str = "outputs"):
        """Save analysis report to JSON and Markdown files"""

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        naics_code = analysis_result["naics_code"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_filename = f"{output_dir}/naics_{naics_code}_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(analysis_result, f, indent=2)

        print(f"\n💾 Saved JSON report: {json_filename}")

        # Generate Markdown report
        md_content = self._generate_markdown_report(analysis_result)
        md_filename = f"{output_dir}/naics_{naics_code}_{timestamp}.md"

        with open(md_filename, 'w') as f:
            f.write(md_content)

        print(f"💾 Saved Markdown report: {md_filename}")

        return json_filename, md_filename

    def _generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a formatted Markdown report"""

        md = f"""# NAICS Industry Analysis Report
## NAICS Code: {analysis['naics_code']}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 1. Industry Overview

### Definition
{analysis.get('industry_overview', {}).get('definition', 'N/A')}

### Sub-Segments
"""

        for segment in analysis.get('industry_overview', {}).get('sub_segments', []):
            md += f"- {segment}\n"

        md += f"\n### Value Chain\n{analysis.get('industry_overview', {}).get('value_chain', 'N/A')}\n\n"

        md += f"### Market Size\n{analysis.get('industry_overview', {}).get('market_size', 'N/A')}\n\n"

        md += "### Major Players\n"
        for player in analysis.get('industry_overview', {}).get('major_players', []):
            md += f"- {player}\n"

        md += "\n---\n\n## 2. Operational Workflow Mapping\n\n"

        for workflow in analysis.get('operational_workflows', {}).get('workflows', []):
            md += f"### {workflow.get('name', 'Unnamed Workflow')}\n\n"
            md += f"**Criticality:** {workflow.get('criticality', 'N/A')}\n\n"
            md += f"**Frequency:** {workflow.get('frequency', 'N/A')}\n\n"

            md += "**Steps:**\n"
            for step in workflow.get('steps', []):
                md += f"1. {step}\n"

            md += "\n**Pain Points:**\n"
            for pain in workflow.get('pain_points', []):
                md += f"- {pain}\n"

            md += "\n"

        md += "\n---\n\n## 3. Technology Landscape\n\n"

        tech = analysis.get('technology_landscape', {})

        md += "### Current Software Categories\n"
        for cat in tech.get('software_categories', []):
            md += f"- {cat}\n"

        md += "\n### Major Vendors\n"
        for vendor in tech.get('major_vendors', []):
            md += f"- {vendor}\n"

        md += f"\n### Adoption Level\n"
        adoption = tech.get('adoption_level', {})
        for key, value in adoption.items():
            md += f"- **{key.replace('_', ' ').title()}:** {value}\n"

        md += "\n### Technology Gaps\n"
        for gap in tech.get('technology_gaps', []):
            md += f"- {gap}\n"

        md += "\n---\n\n## 4. AI & Automation Opportunities\n\n"

        for i, opp in enumerate(analysis.get('ai_opportunities', []), 1):
            md += f"### Opportunity {i}: {opp.get('workflow_step', 'Unnamed')}\n\n"
            md += f"**Current State:** {opp.get('current_state', 'N/A')}\n\n"
            md += f"**Solution:** {opp.get('solution', {})}\n\n"
            md += f"**Expected Value:** {opp.get('expected_value', 'N/A')}\n\n"
            md += f"**Target Customer:** {opp.get('target_customer', 'N/A')}\n\n"
            md += f"**Why Unsolved:** {opp.get('why_unsolved', 'N/A')}\n\n"
            md += f"**Difficulty:** {opp.get('difficulty', 'N/A')}\n\n"
            md += "---\n\n"

        md += "\n## 5. Hidden Niches\n\n"

        for i, niche in enumerate(analysis.get('niche_segments', []), 1):
            md += f"### Niche {i}\n"
            md += f"{json.dumps(niche, indent=2)}\n\n"

        md += "\n---\n\n## 6. Top 5 Startup Opportunities\n\n"

        for i, top_opp in enumerate(analysis.get('top_opportunities', []), 1):
            md += f"### #{i}: {top_opp.get('title', 'Unnamed Opportunity')}\n\n"
            md += f"**Description:** {top_opp.get('description', 'N/A')}\n\n"
            md += f"**Target Market:** {top_opp.get('target_market', 'N/A')}\n\n"
            md += f"**Value Proposition:** {top_opp.get('value_proposition', 'N/A')}\n\n"
            md += f"**Competitive Moat:** {top_opp.get('competitive_moat', 'N/A')}\n\n"
            md += f"**Why Now:** {top_opp.get('why_now', 'N/A')}\n\n"
            md += f"**Go-to-Market:** {top_opp.get('go_to_market', 'N/A')}\n\n"
            md += f"**Risk Factors:** {top_opp.get('risk_factors', 'N/A')}\n\n"
            md += "---\n\n"

        return md


if __name__ == "__main__":
    # Example usage
    analyzer = NAICSAnalyzer()

    # Analyze a NAICS code
    naics_code = input("Enter 6-digit NAICS code to analyze: ").strip()

    result = analyzer.analyze(naics_code)

    # Save report
    analyzer.save_report(result)

    print("\n✅ Analysis complete! Check the 'outputs' folder for results.")
