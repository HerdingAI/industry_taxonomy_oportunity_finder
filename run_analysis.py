#!/usr/bin/env python3
"""
Simple runner script for NAICS analysis
Usage: python run_analysis.py <naics_code>
"""

import sys
from naics_analyzer import NAICSAnalyzer


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_analysis.py <naics_code>")
        print("\nExample: python run_analysis.py 541511")
        print("\nOr run interactively:")
        naics_code = input("Enter 6-digit NAICS code to analyze: ").strip()
    else:
        naics_code = sys.argv[1]

    # Validate NAICS code format
    if not naics_code.isdigit() or len(naics_code) != 6:
        print(f"❌ Error: '{naics_code}' is not a valid 6-digit NAICS code")
        sys.exit(1)

    print(f"\n🚀 Starting analysis for NAICS {naics_code}...")
    print("This may take 5-10 minutes depending on the model's response time.\n")

    try:
        # Initialize analyzer
        analyzer = NAICSAnalyzer()

        # Run analysis
        result = analyzer.analyze(naics_code)

        # Save reports
        json_file, md_file = analyzer.save_report(result)

        print("\n" + "="*60)
        print("✅ ANALYSIS COMPLETE!")
        print("="*60)
        print(f"\nResults saved to:")
        print(f"  📊 JSON: {json_file}")
        print(f"  📄 Markdown: {md_file}")
        print("\nTop Opportunities:")

        for i, opp in enumerate(result.get('top_opportunities', [])[:5], 1):
            title = opp.get('title', 'Unnamed Opportunity')
            print(f"  {i}. {title}")

        print("\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
