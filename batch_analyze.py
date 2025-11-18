#!/usr/bin/env python3
"""
Batch analysis script for multiple NAICS codes using 7-agent MBA-Data Science system
Usage: python batch_analyze.py naics_codes.txt [--phase PHASE_1|PHASE_2]
"""

import sys
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python batch_analyze.py <naics_codes_file> [--phase PHASE_1|PHASE_2]")
        print("\nFile format: One NAICS code per line")
        print("Example:")
        print("  541511")
        print("  541512")
        print("  541513")
        print("\nOptions:")
        print("  --phase PHASE_1  Quick screening (default)")
        print("  --phase PHASE_2  Deep dive analysis")
        sys.exit(1)

    codes_file = sys.argv[1]
    phase = "PHASE_1"

    # Check for phase argument
    if len(sys.argv) >= 4 and sys.argv[2] == '--phase':
        phase = sys.argv[3]

    # Validate phase
    if phase not in ['PHASE_1', 'PHASE_2']:
        print(f"❌ Error: Phase must be PHASE_1 or PHASE_2, got '{phase}'")
        sys.exit(1)

    # Read NAICS codes from file
    try:
        with open(codes_file, 'r') as f:
            naics_codes = [line.strip() for line in f if line.strip() and line.strip().isdigit()]
    except FileNotFoundError:
        print(f"❌ Error: File '{codes_file}' not found")
        sys.exit(1)

    if not naics_codes:
        print(f"❌ Error: No valid NAICS codes found in '{codes_file}'")
        sys.exit(1)

    print(f"\n🚀 Batch Analysis Starting ({phase})")
    print(f"{'='*60}")
    print(f"Total NAICS codes to analyze: {len(naics_codes)}")
    print(f"{'='*60}\n")

    try:
        # Import new 7-agent system
        from src.analyzer import IndustryAnalyzer

        # Check for API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ Error: OPENROUTER_API_KEY not found in .env file")
            sys.exit(1)

        # Initialize analyzer once (reuse for efficiency)
        analyzer = IndustryAnalyzer(api_key)

        results = []
        failed = []

        for i, naics_code in enumerate(naics_codes, 1):
            print(f"\n[{i}/{len(naics_codes)}] Analyzing NAICS {naics_code} ({phase})...")

            try:
                # Run analysis
                result = analyzer.analyze(naics_code, phase=phase)

                # Save report
                filename = analyzer.save_report(result, output_dir="outputs")

                # Extract key metrics
                research = result.get('research_data', {})
                quant = result.get('quantitative_data', {})
                opportunities = quant.get('opportunities', [])

                results.append({
                    'naics_code': naics_code,
                    'status': 'success',
                    'industry_name': research.get('industry_name', 'Unknown'),
                    'market_size_usd': research.get('market_size_usd', 0),
                    'opportunities_count': len(opportunities),
                    'top_opportunity_score': opportunities[0].get('risk_adjusted_score', 0) if opportunities else 0,
                    'filename': filename
                })

                print(f"✅ Completed: {naics_code} - {research.get('industry_name', 'Unknown')}")
                print(f"   Opportunities: {len(opportunities)}, Top Score: {results[-1]['top_opportunity_score']:.1f}/100")

            except Exception as e:
                print(f"❌ Failed: {naics_code} - {str(e)}")
                failed.append({
                    'naics_code': naics_code,
                    'error': str(e)
                })

            # Rate limiting - wait between requests
            if i < len(naics_codes):
                wait_time = 15  # Longer wait for new system (more API calls)
                print(f"Waiting {wait_time} seconds before next analysis...")
                time.sleep(wait_time)

        # Close database connections
        analyzer.close()

        # Summary
        print("\n" + "="*60)
        print("📊 BATCH ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total analyzed: {len(naics_codes)}")
        print(f"Successful: {len(results)}")
        print(f"Failed: {len(failed)}")

        if results:
            print("\n✅ Successful Analyses:")
            # Sort by top opportunity score
            results.sort(key=lambda x: x['top_opportunity_score'], reverse=True)

            for i, item in enumerate(results, 1):
                print(f"\n{i}. NAICS {item['naics_code']} - {item['industry_name']}")
                print(f"   Market Size: ${(item['market_size_usd']/1e9):.1f}B")
                print(f"   Opportunities: {item['opportunities_count']}")
                print(f"   Top Score: {item['top_opportunity_score']:.1f}/100")
                print(f"   Report: {item['filename']}")

        if failed:
            print("\n❌ Failed NAICS codes:")
            for item in failed:
                print(f"  - {item['naics_code']}: {item['error'][:100]}")

        print("\n✅ Batch analysis complete!\n")

    except ImportError as e:
        print(f"\n❌ Import Error: {str(e)}")
        print("\nMake sure you're in the correct directory and all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
