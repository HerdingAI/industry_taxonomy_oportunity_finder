#!/usr/bin/env python3
"""
Simple runner script for NAICS analysis using the 7-agent MBA-Data Science system
Usage: python run_analysis.py <naics_code> [--phase PHASE_1|PHASE_2]
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    # Parse arguments
    naics_code = None
    phase = "PHASE_1"

    if len(sys.argv) < 2:
        print("Usage: python run_analysis.py <naics_code> [--phase PHASE_1|PHASE_2]")
        print("\nExample: python run_analysis.py 541511")
        print("Example: python run_analysis.py 541511 --phase PHASE_2")
        print("\nOr run interactively:")
        naics_code = input("Enter 6-digit NAICS code to analyze: ").strip()
    else:
        naics_code = sys.argv[1]

        # Check for phase argument
        if len(sys.argv) >= 4 and sys.argv[2] == '--phase':
            phase = sys.argv[3]

    # Validate NAICS code format
    if not naics_code.isdigit() or len(naics_code) != 6:
        print(f"❌ Error: '{naics_code}' is not a valid 6-digit NAICS code")
        sys.exit(1)

    # Validate phase
    if phase not in ['PHASE_1', 'PHASE_2']:
        print(f"❌ Error: Phase must be PHASE_1 or PHASE_2, got '{phase}'")
        sys.exit(1)

    print(f"\n🚀 Starting {phase} analysis for NAICS {naics_code}...")
    if phase == "PHASE_1":
        print("This is a quick screening (15-20 queries, ~1-2 minutes)")
    else:
        print("This is a deep dive (30-50 queries, ~3-5 minutes)")
    print()

    try:
        # Import new 7-agent system
        from src.analyzer import IndustryAnalyzer

        # Check for API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ Error: OPENROUTER_API_KEY not found in .env file")
            print("\nSetup steps:")
            print("  1. Copy .env.example to .env")
            print("  2. Add your OpenRouter API key to .env")
            print("  3. Get API key at: https://openrouter.ai/")
            sys.exit(1)

        # Initialize analyzer
        analyzer = IndustryAnalyzer(api_key)

        # Run analysis
        result = analyzer.analyze(naics_code, phase=phase)

        # Save report
        filename = analyzer.save_report(result, output_dir="outputs")

        print("\n" + "="*60)
        print("✅ ANALYSIS COMPLETE!")
        print("="*60)
        print(f"\nFull report saved to: {filename}")

        # Show summary
        print("\n📊 SUMMARY")
        print("="*60)

        research = result.get('research_data', {})
        strategic = result.get('strategic_data', {})
        quant = result.get('quantitative_data', {})

        print(f"\nIndustry: {research.get('industry_name', 'Unknown')}")
        print(f"Market Size: ${(research.get('market_size_usd', 0)/1e9):.1f}B")
        print(f"Growth Rate: {(research.get('growth_rate', 0)*100):.1f}%")

        porters = strategic.get('porters_five_forces', {})
        print(f"Attractiveness: {porters.get('overall_attractiveness', 0):.0f}/100")

        opportunities = quant.get('opportunities', [])
        print(f"\nOpportunities Identified: {len(opportunities)}")

        if opportunities:
            print("\nTop Opportunity:")
            top = opportunities[0]
            print(f"  Title: {top.get('opportunity_title', 'Unknown')}")
            print(f"  Score: {top.get('risk_adjusted_score', 0):.1f}/100")

            market_sizing = top.get('market_sizing', {})
            print(f"  TAM: ${(market_sizing.get('tam_usd', 0)/1e9):.1f}B")
            print(f"  SOM Y3: ${(market_sizing.get('som_y3_usd', 0)/1e6):.1f}M")

            unit_econ = top.get('unit_economics', {})
            ltv_cac = unit_econ.get('ltv_cac_ratio', 0)
            if ltv_cac:
                print(f"  LTV/CAC: {ltv_cac:.1f}x")

        # VC criteria
        vc_assessment = quant.get('vc_criteria_assessment', {})
        if vc_assessment:
            print(f"\nVC Investment Score: {vc_assessment.get('overall_vc_score', 0):.1f}/100")
            print(f"Tier: {vc_assessment.get('tier', 'Unknown')}")

        print("\n" + "="*60)
        print(f"\n📄 Read full report: {filename}\n")

        # Close database connections
        analyzer.close()

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except ImportError as e:
        print(f"\n❌ Import Error: {str(e)}")
        print("\nMake sure you're in the correct directory and all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
