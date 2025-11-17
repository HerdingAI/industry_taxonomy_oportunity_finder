#!/usr/bin/env python3
"""
CLI for Industry Analysis System

Usage:
    python analyze.py 541511                    # Analyze single NAICS code
    python analyze.py --sector 54               # Analyze all Professional Services
    python analyze.py --list                    # List analyzed industries
    python analyze.py --top                     # Show top opportunities
    python analyze.py --search "healthcare AI"  # Search opportunities
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from src.analyzer import IndustryAnalyzer

# Professional Services NAICS codes (54xxxx)
PROFESSIONAL_SERVICES_NAICS = [
    ("541110", "Offices of Lawyers"),
    ("541211", "Offices of Certified Public Accountants"),
    ("541219", "Other Accounting Services"),
    ("541310", "Architectural Services"),
    ("541320", "Landscape Architectural Services"),
    ("541330", "Engineering Services"),
    ("541340", "Drafting Services"),
    ("541350", "Building Inspection Services"),
    ("541360", "Geophysical Surveying & Mapping"),
    ("541370", "Surveying & Mapping (except Geophysical)"),
    ("541380", "Testing Laboratories"),
    ("541410", "Interior Design Services"),
    ("541420", "Industrial Design Services"),
    ("541430", "Graphic Design Services"),
    ("541490", "Other Specialized Design Services"),
    ("541511", "Custom Computer Programming Services"),
    ("541512", "Computer Systems Design Services"),
    ("541513", "Computer Facilities Management Services"),
    ("541519", "Other Computer Related Services"),
    ("541611", "Administrative Management & General Management Consulting"),
    ("541612", "Human Resources Consulting Services"),
    ("541613", "Marketing Consulting Services"),
    ("541614", "Process, Physical Distribution, & Logistics Consulting"),
    ("541618", "Other Management Consulting Services"),
    ("541620", "Environmental Consulting Services"),
    ("541690", "Other Scientific & Technical Consulting Services"),
    ("541713", "Research & Development in Nanotechnology"),
    ("541714", "Research & Development in Biotechnology"),
    ("541715", "Research & Development in Physical, Engineering, & Life Sciences"),
    ("541720", "Research & Development in Social Sciences & Humanities"),
    ("541810", "Advertising Agencies"),
    ("541820", "Public Relations Agencies"),
    ("541830", "Media Buying Agencies"),
    ("541840", "Media Representatives"),
    ("541850", "Outdoor Advertising"),
    ("541860", "Direct Mail Advertising"),
    ("541870", "Advertising Material Distribution Services"),
    ("541890", "Other Services Related to Advertising"),
    ("541910", "Marketing Research & Public Opinion Polling"),
    ("541920", "Photographic Services"),
    ("541930", "Translation & Interpretation Services"),
    ("541940", "Veterinary Services"),
    ("541990", "All Other Professional, Scientific, & Technical Services")
]


def analyze_single(analyzer: IndustryAnalyzer, naics_code: str):
    """Analyze a single NAICS code"""

    if not naics_code.isdigit() or len(naics_code) != 6:
        print(f"❌ Invalid NAICS code: {naics_code}")
        print("   Must be exactly 6 digits")
        return False

    try:
        result = analyzer.analyze(naics_code)

        if result.get('error'):
            print(f"\n❌ Analysis failed: {result['error']}")
            return False

        # Print report
        print("\n" + "="*60)
        print(result['final_report'])
        print("="*60)

        # Save report
        filename = analyzer.save_report(result)
        print(f"\n💾 Report saved: {filename}")

        return True

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def analyze_sector(analyzer: IndustryAnalyzer, sector_code: str):
    """Analyze all industries in a sector"""

    if sector_code == "54":
        codes_to_analyze = PROFESSIONAL_SERVICES_NAICS
        sector_name = "Professional Services"
    else:
        print(f"❌ Sector {sector_code} not supported yet")
        print("   Currently supported: 54 (Professional Services)")
        return

    print(f"\n🚀 Analyzing {sector_name} Sector ({len(codes_to_analyze)} industries)")
    print(f"{'='*60}\n")

    successful = 0
    failed = 0

    for i, (naics_code, industry_name) in enumerate(codes_to_analyze, 1):
        print(f"\n[{i}/{len(codes_to_analyze)}] {naics_code} - {industry_name}")
        print("-" * 60)

        try:
            result = analyzer.analyze(naics_code, industry_name)

            if result.get('error'):
                print(f"❌ Failed: {result['error']}")
                failed += 1
            else:
                analyzer.save_report(result)
                successful += 1
                print(f"✅ Complete")

        except KeyboardInterrupt:
            print("\n\n⚠️  Sector analysis interrupted")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1

        # Brief pause between analyses
        if i < len(codes_to_analyze):
            import time
            time.sleep(2)

    # Summary
    print(f"\n{'='*60}")
    print(f"SECTOR ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Successful: {successful}/{len(codes_to_analyze)}")
    print(f"Failed: {failed}/{len(codes_to_analyze)}")

    # Show top opportunities
    if successful > 0:
        print(f"\n🏆 Top Opportunities Across {sector_name}:")
        top_opps = analyzer.get_top_opportunities(10)
        for i, opp in enumerate(top_opps, 1):
            print(f"{i}. [{opp['naics_code']}] {opp['title']} (Score: {opp['risk_adjusted_score']:.0f})")


def list_industries(analyzer: IndustryAnalyzer):
    """List all analyzed industries"""

    summary = analyzer.get_industry_summary()

    if not summary:
        print("No industries analyzed yet.")
        print("\nRun: python analyze.py 541511")
        return

    print(f"\n{'='*60}")
    print(f"ANALYZED INDUSTRIES ({len(summary)})")
    print(f"{'='*60}\n")

    print(f"{'NAICS':<8} {'Name':<40} {'Score':<7} {'Opps':<5}")
    print("-" * 60)

    for ind in summary:
        name = ind['name'][:37] + "..." if len(ind['name']) > 40 else ind['name']
        score = ind['overall_score'] if ind['overall_score'] else 0
        num_opps = ind['num_opportunities'] if ind['num_opportunities'] else 0

        print(f"{ind['naics_code']:<8} {name:<40} {score:<7.0f} {num_opps:<5}")


def show_top_opportunities(analyzer: IndustryAnalyzer, limit: int = 20):
    """Show top opportunities across all industries"""

    top_opps = analyzer.get_top_opportunities(limit)

    if not top_opps:
        print("No opportunities found yet.")
        print("\nRun an analysis first: python analyze.py 541511")
        return

    print(f"\n{'='*60}")
    print(f"TOP {len(top_opps)} OPPORTUNITIES")
    print(f"{'='*60}\n")

    for i, opp in enumerate(top_opps, 1):
        score = opp.get('risk_adjusted_score', 0)
        conf = opp.get('confidence', 0)
        ltv_cac = opp.get('ltv_cac_ratio', 0)

        print(f"{i}. [{opp['naics_code']}] {opp['title']}")
        print(f"   Score: {score:.0f} | Confidence: {conf:.0%} | LTV:CAC: {ltv_cac:.1f}:1")
        print(f"   Moat: {opp.get('key_moat', 'N/A')}")
        print()


def search_opportunities(analyzer: IndustryAnalyzer, query: str, top_k: int = 10):
    """Search for opportunities using vector search"""

    results = analyzer.search_opportunities(query, top_k)

    if not results:
        print(f"No opportunities found matching '{query}'")
        return

    print(f"\n{'='*60}")
    print(f"SEARCH RESULTS: '{query}'")
    print(f"{'='*60}\n")

    for i, result in enumerate(results, 1):
        doc = result['document']
        meta = result['metadata']
        naics = meta.get('naics_code', 'Unknown')
        score = meta.get('score', 0)

        print(f"{i}. [{naics}] {doc[:80]}...")
        print(f"   Score: {score:.0f}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Strategic Market Intelligence System - Industry Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze.py 541511                    # Analyze Custom Computer Programming
  python analyze.py 541211                    # Analyze CPA Offices
  python analyze.py --sector 54               # Analyze all Professional Services
  python analyze.py --list                    # List analyzed industries
  python analyze.py --top 20                  # Show top 20 opportunities
  python analyze.py --search "healthcare AI"  # Search for opportunities

Professional Services (Sector 54) includes 43 industries from legal to veterinary services.
        """
    )

    parser.add_argument('naics_code', nargs='?', help='6-digit NAICS code to analyze')
    parser.add_argument('--sector', help='Analyze entire sector (e.g., 54 for Professional Services)')
    parser.add_argument('--list', action='store_true', help='List all analyzed industries')
    parser.add_argument('--top', type=int, nargs='?', const=20, help='Show top opportunities')
    parser.add_argument('--search', type=str, help='Search opportunities by keyword')

    args = parser.parse_args()

    # Load environment
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        print("\nSetup:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your OpenRouter API key")
        print("  3. Get API key at: https://openrouter.ai/")
        sys.exit(1)

    # Initialize analyzer
    try:
        analyzer = IndustryAnalyzer(api_key, db_dir="data")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        sys.exit(1)

    try:
        # Route to appropriate command
        if args.list:
            list_industries(analyzer)
        elif args.top is not None:
            show_top_opportunities(analyzer, args.top)
        elif args.search:
            search_opportunities(analyzer, args.search)
        elif args.sector:
            analyze_sector(analyzer, args.sector)
        elif args.naics_code:
            analyze_single(analyzer, args.naics_code)
        else:
            parser.print_help()

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
