#!/usr/bin/env python3
"""
Phase 2 Entry Point: Data-Vendor Opportunity Analysis

Main entry point for analyzing 8-digit NAICS segments to discover data-vendor
business opportunities. Supports single analysis or batch processing from CSV.

Usage:
    # Single NAICS analysis
    python run_data_vendor_analysis.py --naics 52411001 --description "Insurance Carriers"

    # Batch processing from CSV
    python run_data_vendor_analysis.py --csv data/naics_8digit_codes.csv

    # Resume batch processing (skip already analyzed)
    python run_data_vendor_analysis.py --csv data/naics_8digit_codes.csv --resume

    # Process specific range from CSV
    python run_data_vendor_analysis.py --csv data/naics_8digit_codes.csv --start 0 --end 100
"""

import os
import sys
import csv
import argparse
import json
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
from tqdm import tqdm
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from langchain_openai import ChatOpenAI
from src.data_vendor_analyzer import DataVendorAnalyzer
from src.audit_database import AuditDatabase
from src.database import DatabaseManager


class DataVendorAnalysisRunner:
    """Manages Phase 2 data-vendor opportunity analysis execution"""

    def __init__(self, output_dir: str = "output/phase2"):
        """
        Initialize analysis runner

        Args:
            output_dir: Directory for markdown reports and results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize LLM
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=api_key
        )

        # Initialize databases
        self.audit_db = AuditDatabase("data/audit.db")
        self.db_manager = DatabaseManager("data/opportunities.db")

        # Initialize analyzer
        self.analyzer = DataVendorAnalyzer(self.llm, self.audit_db)

        print("✅ Initialized DataVendorAnalysisRunner")
        print(f"   Model: gpt-4o-mini")
        print(f"   Output: {self.output_dir}")
        print(f"   Audit DB: data/audit.db")
        print(f"   Results DB: data/opportunities.db\n")

    def load_naics_from_csv(
        self,
        csv_path: str,
        start_idx: int = 0,
        end_idx: Optional[int] = None
    ) -> List[Tuple[str, str]]:
        """
        Load NAICS codes and descriptions from CSV

        Args:
            csv_path: Path to CSV file with columns: naics_8_digit, description
            start_idx: Start index (for resuming/chunking)
            end_idx: End index (for resuming/chunking)

        Returns:
            List of (naics_8_digit, description) tuples

        CSV Format:
            naics_8_digit,description
            52411001,Direct Property and Casualty Insurance Carriers
            52411002,Reinsurance Carriers
            ...
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        naics_list = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate headers
            if 'naics_8_digit' not in reader.fieldnames or 'description' not in reader.fieldnames:
                raise ValueError(
                    "CSV must have columns: naics_8_digit, description\n"
                    f"Found columns: {reader.fieldnames}"
                )

            for row in reader:
                naics_8_digit = row['naics_8_digit'].strip()
                description = row['description'].strip()

                # Validate NAICS code
                if len(naics_8_digit) != 8 or not naics_8_digit.isdigit():
                    print(f"⚠️  Skipping invalid NAICS: {naics_8_digit}")
                    continue

                naics_list.append((naics_8_digit, description))

        # Apply slicing
        if end_idx is not None:
            naics_list = naics_list[start_idx:end_idx]
        else:
            naics_list = naics_list[start_idx:]

        print(f"✅ Loaded {len(naics_list)} NAICS codes from {csv_path}")
        if start_idx > 0 or end_idx is not None:
            print(f"   Range: [{start_idx}:{end_idx if end_idx else 'end'}]")

        return naics_list

    def run_single_analysis(
        self,
        naics_8_digit: str,
        description: str,
        save_report: bool = True
    ) -> dict:
        """
        Run analysis for a single NAICS code

        Args:
            naics_8_digit: 8-digit NAICS code
            description: Segment description
            save_report: Whether to save markdown report and database record

        Returns:
            Analysis results dictionary
        """
        print(f"\n{'='*70}")
        print(f"Analyzing: {naics_8_digit} - {description}")
        print(f"{'='*70}\n")

        start_time = time.time()

        try:
            # Run analysis
            result = self.analyzer.analyze(naics_8_digit, description)

            elapsed = time.time() - start_time

            # Check for errors
            if result.get('error'):
                print(f"\n❌ Analysis failed: {result['error']}")
                return result

            # Extract summary
            opportunities = result.get('ranked_opportunities', [])
            tier1_count = sum(1 for opp in opportunities if opp.get('tier') == 'TIER_1')
            tier2_count = sum(1 for opp in opportunities if opp.get('tier') == 'TIER_2')

            print(f"\n{'='*70}")
            print(f"✅ Analysis Complete")
            print(f"   NAICS: {naics_8_digit}")
            print(f"   Time: {elapsed:.1f}s")
            print(f"   Opportunities: {len(opportunities)} total")
            print(f"   TIER_1: {tier1_count}, TIER_2: {tier2_count}")
            if opportunities:
                print(f"   Top Score: {opportunities[0].get('composite_score', 0):.1f}/100")
            print(f"{'='*70}\n")

            # Save results
            if save_report:
                self._save_results(naics_8_digit, description, result)

            return result

        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'naics_8_digit': naics_8_digit,
                'description': description
            }

    def run_batch_analysis(
        self,
        csv_path: str,
        start_idx: int = 0,
        end_idx: Optional[int] = None,
        resume: bool = False
    ):
        """
        Run batch analysis for multiple NAICS codes from CSV

        Args:
            csv_path: Path to CSV file
            start_idx: Start index
            end_idx: End index (None = process all)
            resume: Skip already analyzed NAICS codes
        """
        # Load NAICS list
        naics_list = self.load_naics_from_csv(csv_path, start_idx, end_idx)

        if not naics_list:
            print("❌ No NAICS codes to process")
            return

        # Filter already analyzed if resuming
        if resume:
            naics_list = self._filter_already_analyzed(naics_list)
            print(f"📝 Resume mode: {len(naics_list)} remaining to analyze")

        # Initialize counters
        total = len(naics_list)
        successful = 0
        failed = 0
        tier1_total = 0
        tier2_total = 0

        batch_start = time.time()

        print(f"\n{'='*70}")
        print(f"Starting Batch Analysis")
        print(f"   Total NAICS: {total}")
        print(f"   Estimated time: {total * 8 / 60:.1f} minutes")
        print(f"   Estimated cost: ${total * 1.5:.2f}")
        print(f"{'='*70}\n")

        # Process each NAICS with progress bar
        with tqdm(total=total, desc="Analyzing NAICS segments", unit="segment") as pbar:
            for idx, (naics, desc) in enumerate(naics_list, start=1):
                pbar.set_description(f"[{idx}/{total}] {naics}")

                try:
                    result = self.run_single_analysis(naics, desc, save_report=True)

                    if result.get('error'):
                        failed += 1
                    else:
                        successful += 1
                        opportunities = result.get('ranked_opportunities', [])
                        tier1_total += sum(1 for opp in opportunities if opp.get('tier') == 'TIER_1')
                        tier2_total += sum(1 for opp in opportunities if opp.get('tier') == 'TIER_2')

                except Exception as e:
                    print(f"❌ Error processing {naics}: {str(e)}")
                    failed += 1

                pbar.update(1)

                # Rate limiting between analyses
                time.sleep(2)

        # Print final summary
        elapsed = time.time() - batch_start
        print(f"\n{'='*70}")
        print(f"✅ Batch Analysis Complete")
        print(f"   Total Processed: {successful + failed}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print(f"   TIER_1 Opportunities: {tier1_total}")
        print(f"   TIER_2 Opportunities: {tier2_total}")
        print(f"   Total Time: {elapsed / 60:.1f} minutes")
        print(f"   Avg Time/Segment: {elapsed / total:.1f}s")
        print(f"{'='*70}\n")

        # Generate summary report
        self._generate_batch_summary(csv_path, successful, failed, tier1_total, tier2_total, elapsed)

    def _filter_already_analyzed(self, naics_list: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Filter out NAICS codes that have already been analyzed"""
        remaining = []
        for naics, desc in naics_list:
            # Check if report exists
            report_path = self.output_dir / f"{naics}_data_vendor_report.md"
            if not report_path.exists():
                remaining.append((naics, desc))
        return remaining

    def _save_results(self, naics_8_digit: str, description: str, result: dict):
        """Save analysis results to markdown report and database"""
        # Generate markdown report
        report_path = self.output_dir / f"{naics_8_digit}_data_vendor_report.md"
        self._generate_markdown_report(naics_8_digit, description, result, report_path)

        # Save to database
        try:
            self.db_manager.save_data_vendor_analysis(
                naics_8_digit=naics_8_digit,
                segment_description=description,
                analysis_results=result
            )
        except Exception as e:
            print(f"⚠️  Warning: Could not save to database: {str(e)}")

        # Save JSON backup
        json_path = self.output_dir / f"{naics_8_digit}_data_vendor_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def _generate_markdown_report(self, naics_8_digit: str, description: str, result: dict, output_path: Path):
        """Generate comprehensive markdown report"""
        opportunities = result.get('ranked_opportunities', [])
        metadata = result.get('metadata', {})

        report = f"""# Data-Vendor Opportunity Report

**NAICS Code**: {naics_8_digit}
**Segment**: {description}
**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Run ID**: {metadata.get('run_id', 'N/A')}

---

## Executive Summary

**Total Opportunities Identified**: {len(opportunities)}
**TIER_1 (Pursue Immediately)**: {sum(1 for opp in opportunities if opp.get('tier') == 'TIER_1')}
**TIER_2 (Validate Before Pursuing)**: {sum(1 for opp in opportunities if opp.get('tier') == 'TIER_2')}
**TIER_3 (Monitor)**: {sum(1 for opp in opportunities if opp.get('tier') == 'TIER_3')}

"""

        if opportunities:
            top_opp = opportunities[0]
            report += f"""
### Top Opportunity

**Data Type**: {top_opp.get('data_type', 'N/A')}
**Composite Score**: {top_opp.get('composite_score', 0):.1f}/100
**Tier**: {top_opp.get('tier', 'N/A')}
**Estimated TAM**: ${top_opp.get('market_size_score', {}).get('tam', 0):,.0f}
**Opportunity Type**: {top_opp.get('opportunity_type', 'N/A')}

"""

        report += "\n---\n\n## Ranked Opportunities\n\n"

        for idx, opp in enumerate(opportunities, 1):
            tier = opp.get('tier', 'N/A')
            score = opp.get('composite_score', 0)
            data_type = opp.get('data_type', 'N/A')
            tam = opp.get('market_size_score', {}).get('tam', 0)

            report += f"""
### {idx}. {data_type}

**Tier**: {tier} | **Score**: {score:.1f}/100 | **TAM**: ${tam:,.0f}

**Opportunity Type**: {opp.get('opportunity_type', 'N/A')}

**Key Strengths**:
"""
            for strength in opp.get('key_strengths', [])[:3]:
                report += f"- {strength}\n"

            report += f"""
**Key Risks**:
"""
            for risk in opp.get('key_risks', [])[:3]:
                report += f"- {risk}\n"

            report += "\n"

        # Add metadata
        report += f"""
---

## Analysis Metadata

**Execution Time**: {metadata.get('total_execution_time_seconds', 0):.1f} seconds

### Agent Execution Times
"""
        for agent, time_taken in metadata.get('agent_execution_times', {}).items():
            report += f"- {agent}: {time_taken:.1f}s\n"

        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📄 Report saved: {output_path}")

    def _generate_batch_summary(self, csv_path: str, successful: int, failed: int,
                                tier1_total: int, tier2_total: int, elapsed: float):
        """Generate summary report for batch processing"""
        summary_path = self.output_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        summary = f"""# Batch Analysis Summary

**CSV Input**: {csv_path}
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Results

- **Total Processed**: {successful + failed}
- **Successful**: {successful}
- **Failed**: {failed}
- **Success Rate**: {successful / (successful + failed) * 100:.1f}%

## Opportunities Discovered

- **TIER_1 Opportunities**: {tier1_total}
- **TIER_2 Opportunities**: {tier2_total}
- **Average TIER_1 per segment**: {tier1_total / successful if successful > 0 else 0:.2f}

## Performance

- **Total Time**: {elapsed / 60:.1f} minutes
- **Average Time per Segment**: {elapsed / (successful + failed):.1f} seconds
- **Estimated Cost**: ${(successful + failed) * 1.5:.2f}

---

**Generated by Phase 2 Data-Vendor Opportunity Discovery System**
"""

        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"\n📊 Batch summary saved: {summary_path}")


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Phase 2: Data-Vendor Opportunity Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single NAICS analysis
  python run_data_vendor_analysis.py --naics 52411001 --description "Insurance Carriers"

  # Batch processing from CSV
  python run_data_vendor_analysis.py --csv data/naics_8digit_codes.csv

  # Resume batch (skip already analyzed)
  python run_data_vendor_analysis.py --csv data/naics_8digit_codes.csv --resume

  # Process range from CSV
  python run_data_vendor_analysis.py --csv data/naics_8digit_codes.csv --start 0 --end 100
        """
    )

    # Single analysis arguments
    parser.add_argument('--naics', type=str, help='Single 8-digit NAICS code to analyze')
    parser.add_argument('--description', type=str, help='Segment description')

    # Batch analysis arguments
    parser.add_argument('--csv', type=str, help='CSV file with NAICS codes (columns: naics_8_digit, description)')
    parser.add_argument('--start', type=int, default=0, help='Start index for batch processing')
    parser.add_argument('--end', type=int, help='End index for batch processing')
    parser.add_argument('--resume', action='store_true', help='Skip already analyzed NAICS codes')

    # Output configuration
    parser.add_argument('--output', type=str, default='output/phase2', help='Output directory for reports')

    args = parser.parse_args()

    # Validate arguments
    if args.naics and not args.description:
        parser.error("--description required when using --naics")

    if not args.naics and not args.csv:
        parser.error("Either --naics or --csv must be provided")

    # Initialize runner
    runner = DataVendorAnalysisRunner(output_dir=args.output)

    # Run analysis
    if args.naics:
        # Single analysis
        runner.run_single_analysis(args.naics, args.description)
    else:
        # Batch analysis
        runner.run_batch_analysis(
            csv_path=args.csv,
            start_idx=args.start,
            end_idx=args.end,
            resume=args.resume
        )


if __name__ == "__main__":
    main()
