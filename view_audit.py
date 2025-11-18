#!/usr/bin/env python3
"""
Audit Data Viewer - Inspect analysis runs, costs, and performance

Usage:
    python view_audit.py --summary                    # Overall cost summary
    python view_audit.py --runs                       # List all runs
    python view_audit.py --run 541511_20241118_120000 # Details for specific run
    python view_audit.py --export 541511_20241118_120000 audit.json  # Export run data
    python view_audit.py --search-performance         # Search query performance
    python view_audit.py --costs --since 2024-11-01   # Costs since date
"""

import argparse
import sys
from pathlib import Path
from src.audit_database import AuditDatabase


def format_currency(amount):
    """Format currency with appropriate precision"""
    if amount < 0.01:
        return f"${amount:.4f}"
    elif amount < 1:
        return f"${amount:.3f}"
    else:
        return f"${amount:.2f}"


def list_runs(audit_db: AuditDatabase):
    """List all analysis runs"""
    cursor = audit_db.conn.cursor()
    cursor.execute("""
        SELECT run_id, naics_code, industry_name, phase,
               start_time, duration_seconds, completed,
               total_cost_usd, total_llm_calls, total_search_queries
        FROM analysis_runs
        ORDER BY start_time DESC
    """)

    runs = cursor.fetchall()

    if not runs:
        print("No analysis runs found.")
        return

    print(f"\n{'='*120}")
    print(f"{'Run ID':<30} {'NAICS':<8} {'Phase':<8} {'Duration':<10} {'LLMs':<6} {'Searches':<10} {'Cost':<10} {'Status'}")
    print(f"{'='*120}")

    for run in runs:
        run_id = run['run_id'][:28] + ".." if len(run['run_id']) > 30 else run['run_id']
        status = "✅" if run['completed'] else "❌"
        duration = f"{run['duration_seconds']:.1f}s" if run['duration_seconds'] else "N/A"
        cost = format_currency(run['total_cost_usd'] or 0)

        print(f"{run_id:<30} {run['naics_code']:<8} {run['phase']:<8} {duration:<10} "
              f"{run['total_llm_calls']:<6} {run['total_search_queries']:<10} {cost:<10} {status}")

    print(f"{'='*120}\n")


def show_run_details(audit_db: AuditDatabase, run_id: str):
    """Show detailed information for a specific run"""
    summary = audit_db.get_run_summary(run_id)

    print(f"\n{'='*80}")
    print(f"RUN DETAILS: {run_id}")
    print(f"{'='*80}\n")

    print(f"NAICS Code: {summary['naics_code']}")
    print(f"Industry: {summary['industry_name'] or 'N/A'}")
    print(f"Phase: {summary['phase']}")
    print(f"Model: {summary['model_name']}")
    print(f"Duration: {summary['duration_seconds']:.1f}s")
    print(f"Completed: {'✅ Yes' if summary['completed'] else '❌ No'}")

    if summary.get('final_error'):
        print(f"Error: {summary['final_error']}")

    print(f"\n{'─'*80}")
    print("SEARCH STATISTICS")
    print(f"{'─'*80}")
    print(f"Total searches: {summary['search_stats']['count']}")
    print(f"Avg results per search: {summary['search_stats']['avg_results']:.1f}")
    print(f"Failed searches: {summary['search_stats']['errors']}")

    print(f"\n{'─'*80}")
    print("LLM STATISTICS")
    print(f"{'─'*80}")
    print(f"Total LLM calls: {summary['llm_stats']['count']}")
    print(f"Input tokens: {summary['llm_stats']['total_input_tokens']:,}")
    print(f"Output tokens: {summary['llm_stats']['total_output_tokens']:,}")
    print(f"Total cost: {format_currency(summary['llm_stats']['total_cost'] or 0)}")
    print(f"Avg call duration: {summary['llm_stats']['avg_duration']:.1f}s")

    if summary.get('agent_stats'):
        print(f"\n{'─'*80}")
        print("AGENT PERFORMANCE")
        print(f"{'─'*80}")
        for agent in summary['agent_stats']:
            print(f"{agent['agent_name']:<30} {agent['steps']} steps, {agent['total_duration']:.1f}s")

    # Show searches
    searches = audit_db.get_all_searches(run_id)
    if searches:
        print(f"\n{'─'*80}")
        print(f"SEARCH QUERIES ({len(searches)} total)")
        print(f"{'─'*80}")
        for i, search in enumerate(searches[:10], 1):
            query = search['query_text'][:60] + "..." if len(search['query_text']) > 60 else search['query_text']
            results = search['num_results']
            error = "❌" if search['error'] else ""
            print(f"{i:2}. [{search['agent_name'][:15]}] {query} → {results} results {error}")

        if len(searches) > 10:
            print(f"    ... and {len(searches) - 10} more searches")

    # Show LLM calls
    llm_calls = audit_db.get_all_llm_calls(run_id)
    if llm_calls:
        print(f"\n{'─'*80}")
        print(f"LLM CALLS ({len(llm_calls)} total)")
        print(f"{'─'*80}")
        for i, call in enumerate(llm_calls[:10], 1):
            method = f"{call['agent_name']}.{call['method_name']}"[:40]
            tokens = f"{call['tokens_input']:,}→{call['tokens_output']:,}"
            cost = format_currency(call['cost_usd'] or 0)
            print(f"{i:2}. {method:<40} {tokens:<15} {cost}")

        if len(llm_calls) > 10:
            print(f"    ... and {len(llm_calls) - 10} more calls")

    print(f"\n{'='*80}\n")


def show_cost_summary(audit_db: AuditDatabase, since_date: str = None):
    """Show cost summary across all runs"""
    summary = audit_db.get_cost_summary(since_date)

    print(f"\n{'='*80}")
    print(f"COST SUMMARY" + (f" (since {since_date})" if since_date else " (all time)"))
    print(f"{'='*80}\n")

    print(f"Total runs: {summary['total_runs']}")
    print(f"Total cost: {format_currency(summary['total_cost'] or 0)}")
    print(f"Avg cost per run: {format_currency(summary['avg_cost_per_run'] or 0)}")
    print(f"\nTotal LLM calls: {summary['total_llm_calls']}")
    print(f"Total searches: {summary['total_searches']}")
    print(f"\nInput tokens: {summary['total_input_tokens']:,}")
    print(f"Output tokens: {summary['total_output_tokens']:,}")

    # Cost breakdown by recent runs
    cursor = audit_db.conn.cursor()
    if since_date:
        cursor.execute("""
            SELECT naics_code, phase, COUNT(*) as runs,
                   AVG(total_cost_usd) as avg_cost,
                   SUM(total_cost_usd) as total_cost
            FROM analysis_runs
            WHERE start_time >= ?
            GROUP BY naics_code, phase
            ORDER BY total_cost DESC
            LIMIT 10
        """, (since_date,))
    else:
        cursor.execute("""
            SELECT naics_code, phase, COUNT(*) as runs,
                   AVG(total_cost_usd) as avg_cost,
                   SUM(total_cost_usd) as total_cost
            FROM analysis_runs
            GROUP BY naics_code, phase
            ORDER BY total_cost DESC
            LIMIT 10
        """)

    top_costs = cursor.fetchall()

    if top_costs:
        print(f"\n{'─'*80}")
        print("TOP COST BY NAICS CODE")
        print(f"{'─'*80}")
        print(f"{'NAICS':<8} {'Phase':<8} {'Runs':<6} {'Avg Cost':<12} {'Total Cost'}")
        print(f"{'─'*80}")
        for row in top_costs:
            print(f"{row['naics_code']:<8} {row['phase']:<8} {row['runs']:<6} "
                  f"{format_currency(row['avg_cost']):<12} {format_currency(row['total_cost'])}")

    print(f"\n{'='*80}\n")


def show_search_performance(audit_db: AuditDatabase):
    """Show search query performance metrics"""
    perf = audit_db.get_search_performance()

    if not perf:
        print("No search performance data available.")
        return

    print(f"\n{'='*100}")
    print("SEARCH QUERY PERFORMANCE")
    print(f"{'='*100}\n")

    print(f"{'Query':<60} {'Uses':<6} {'Avg Results':<12} {'Errors'}")
    print(f"{'─'*100}")

    for row in perf[:20]:
        query = row['query_text'][:57] + "..." if len(row['query_text']) > 60 else row['query_text']
        avg_results = f"{row['avg_results']:.1f}" if row['avg_results'] else "0.0"
        errors = f"❌ {row['error_count']}" if row['error_count'] > 0 else ""

        print(f"{query:<60} {row['times_used']:<6} {avg_results:<12} {errors}")

    print(f"\n{'='*100}\n")


def export_run(audit_db: AuditDatabase, run_id: str, output_file: str):
    """Export run data to JSON"""
    audit_db.export_run_data(run_id, output_file)
    print(f"✅ Exported run data to {output_file}")

    # Show file size
    size = Path(output_file).stat().st_size
    print(f"   File size: {size:,} bytes ({size/1024:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(
        description="Audit Data Viewer - Inspect analysis runs and performance",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--summary', action='store_true', help='Show overall cost summary')
    parser.add_argument('--runs', action='store_true', help='List all analysis runs')
    parser.add_argument('--run', type=str, help='Show details for specific run ID')
    parser.add_argument('--export', nargs=2, metavar=('RUN_ID', 'FILE'), help='Export run data to JSON')
    parser.add_argument('--search-performance', action='store_true', help='Show search query performance')
    parser.add_argument('--costs', action='store_true', help='Show cost summary')
    parser.add_argument('--since', type=str, help='Filter by date (YYYY-MM-DD)')
    parser.add_argument('--db-dir', type=str, default='data', help='Database directory (default: data)')

    args = parser.parse_args()

    # Initialize audit database
    try:
        audit_db = AuditDatabase(args.db_dir)
    except Exception as e:
        print(f"❌ Failed to open audit database: {e}")
        sys.exit(1)

    try:
        if args.runs:
            list_runs(audit_db)
        elif args.run:
            show_run_details(audit_db, args.run)
        elif args.export:
            export_run(audit_db, args.export[0], args.export[1])
        elif args.search_performance:
            show_search_performance(audit_db)
        elif args.costs or args.summary:
            show_cost_summary(audit_db, args.since)
        else:
            # Default: show summary
            show_cost_summary(audit_db, args.since)
            print("\nTip: Use --help to see all available options")

    finally:
        audit_db.close()


if __name__ == "__main__":
    main()
