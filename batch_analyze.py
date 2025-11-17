#!/usr/bin/env python3
"""
Batch analysis script for multiple NAICS codes
Usage: python batch_analyze.py naics_codes.txt
"""

import sys
import time
from pathlib import Path
from naics_analyzer import NAICSAnalyzer


def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_analyze.py <naics_codes_file>")
        print("\nFile format: One NAICS code per line")
        print("Example:")
        print("  541511")
        print("  541512")
        print("  541513")
        sys.exit(1)

    codes_file = sys.argv[1]

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

    print(f"\n🚀 Batch Analysis Starting")
    print(f"{'='*60}")
    print(f"Total NAICS codes to analyze: {len(naics_codes)}")
    print(f"{'='*60}\n")

    analyzer = NAICSAnalyzer()
    results = []
    failed = []

    for i, naics_code in enumerate(naics_codes, 1):
        print(f"\n[{i}/{len(naics_codes)}] Analyzing NAICS {naics_code}...")

        try:
            result = analyzer.analyze(naics_code)
            json_file, md_file = analyzer.save_report(result)

            results.append({
                'naics_code': naics_code,
                'status': 'success',
                'json_file': json_file,
                'md_file': md_file
            })

            print(f"✅ Completed: {naics_code}")

        except Exception as e:
            print(f"❌ Failed: {naics_code} - {str(e)}")
            failed.append({
                'naics_code': naics_code,
                'error': str(e)
            })

        # Rate limiting - wait between requests
        if i < len(naics_codes):
            print("Waiting 10 seconds before next analysis...")
            time.sleep(10)

    # Summary
    print("\n" + "="*60)
    print("📊 BATCH ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total analyzed: {len(naics_codes)}")
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFailed NAICS codes:")
        for item in failed:
            print(f"  - {item['naics_code']}: {item['error']}")

    print("\n✅ Batch analysis complete!\n")


if __name__ == "__main__":
    main()
