"""
Audit Database - Comprehensive tracking of all analysis steps

Captures:
- Every web search query and results
- Every LLM call with prompts, responses, and token counts
- Agent execution timing and outcomes
- Complete data snapshots at each step
- Cost tracking
- Error logs

This enables:
1. Full reproducibility of analyses
2. Cost tracking and optimization
3. Debugging and troubleshooting
4. RAG database population over time
5. Understanding what queries/prompts work best
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib


class AuditDatabase:
    """Comprehensive audit trail for all analysis operations"""

    def __init__(self, db_dir: str = "data"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.db_dir / "audit_trail.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self):
        """Create comprehensive audit tables"""
        cursor = self.conn.cursor()

        # Analysis runs - top level tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                run_id TEXT PRIMARY KEY,
                naics_code TEXT NOT NULL,
                industry_name TEXT,
                phase TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds REAL,
                completed BOOLEAN,
                error_count INTEGER,
                final_error TEXT,

                -- Metadata
                model_name TEXT,
                total_cost_usd REAL,
                total_llm_calls INTEGER,
                total_search_queries INTEGER,
                total_tokens_input INTEGER,
                total_tokens_output INTEGER,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Search queries - every web search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                agent_name TEXT,
                query_text TEXT NOT NULL,
                search_engine TEXT,
                max_results INTEGER,
                timestamp TIMESTAMP,

                -- Results
                num_results INTEGER,
                results_json TEXT,  -- Full results as JSON
                error TEXT,
                retry_count INTEGER,

                -- Performance
                duration_seconds REAL,

                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_run ON search_queries(run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_query ON search_queries(query_text)")

        # LLM calls - every LLM interaction
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                agent_name TEXT,
                method_name TEXT,
                timestamp TIMESTAMP,

                -- Request
                model TEXT,
                temperature REAL,
                max_tokens INTEGER,
                system_prompt TEXT,
                user_prompt TEXT,
                prompt_hash TEXT,  -- For deduplication

                -- Response
                response_text TEXT,
                parsed_json TEXT,  -- If response was parsed as JSON
                tokens_input INTEGER,
                tokens_output INTEGER,
                cost_usd REAL,

                -- Performance
                duration_seconds REAL,
                error TEXT,

                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_run ON llm_calls(run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_agent ON llm_calls(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_hash ON llm_calls(prompt_hash)")

        # Agent steps - timing and flow
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                step_name TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration_seconds REAL,

                -- Input/Output
                input_data TEXT,  -- JSON snapshot of input
                output_data TEXT,  -- JSON snapshot of output

                -- Status
                success BOOLEAN,
                error TEXT,
                confidence_score REAL,

                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_step_run ON agent_steps(run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_step_agent ON agent_steps(agent_name)")

        # RAG queries - track RAG database lookups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                agent_name TEXT,
                query_type TEXT,  -- 'vector_search', 'customer_data', 'workflow_intel', etc.
                query_text TEXT,
                timestamp TIMESTAMP,

                -- Results
                num_results INTEGER,
                results_json TEXT,

                -- Performance
                duration_seconds REAL,

                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rag_run ON rag_queries(run_id)")

        # Complete data snapshots - full state at key points
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                snapshot_type TEXT,  -- 'research_complete', 'strategic_complete', etc.
                timestamp TIMESTAMP,
                data_json TEXT,  -- Complete state as JSON

                FOREIGN KEY (run_id) REFERENCES analysis_runs(run_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_run ON data_snapshots(run_id)")

        # Error log - detailed error tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                agent_name TEXT,
                error_type TEXT,
                error_message TEXT,
                stack_trace TEXT,
                context_json TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_run ON error_log(run_id)")

        # Cost tracking summary view
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS cost_summary AS
            SELECT
                run_id,
                SUM(cost_usd) as total_llm_cost,
                COUNT(*) as num_llm_calls,
                SUM(tokens_input) as total_input_tokens,
                SUM(tokens_output) as total_output_tokens,
                AVG(duration_seconds) as avg_call_duration
            FROM llm_calls
            GROUP BY run_id
        """)

        # Search performance view
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS search_performance AS
            SELECT
                query_text,
                COUNT(*) as times_used,
                AVG(num_results) as avg_results,
                AVG(duration_seconds) as avg_duration,
                SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as error_count
            FROM search_queries
            GROUP BY query_text
            ORDER BY times_used DESC
        """)

        self.conn.commit()

    # ==================
    # Analysis Run Tracking
    # ==================

    def start_analysis_run(
        self,
        naics_code: str,
        industry_name: str = None,
        phase: str = "PHASE_1",
        model_name: str = None
    ) -> str:
        """Start tracking a new analysis run"""
        run_id = f"{naics_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO analysis_runs (
                run_id, naics_code, industry_name, phase, start_time, model_name,
                completed, error_count, total_llm_calls, total_search_queries,
                total_tokens_input, total_tokens_output, total_cost_usd
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, naics_code, industry_name, phase,
            datetime.now().isoformat(), model_name,
            False, 0, 0, 0, 0, 0, 0.0
        ))
        self.conn.commit()

        return run_id

    def end_analysis_run(
        self,
        run_id: str,
        completed: bool = True,
        error_count: int = 0,
        final_error: str = None
    ):
        """Mark analysis run as complete"""
        cursor = self.conn.cursor()

        # Get start time to calculate duration
        cursor.execute("SELECT start_time FROM analysis_runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        if row:
            start_time = datetime.fromisoformat(row['start_time'])
            duration = (datetime.now() - start_time).total_seconds()
        else:
            duration = None

        cursor.execute("""
            UPDATE analysis_runs
            SET end_time = ?,
                duration_seconds = ?,
                completed = ?,
                error_count = ?,
                final_error = ?
            WHERE run_id = ?
        """, (
            datetime.now().isoformat(),
            duration,
            completed,
            error_count,
            final_error,
            run_id
        ))
        self.conn.commit()

    # ==================
    # Search Query Tracking
    # ==================

    def log_search_query(
        self,
        run_id: str,
        agent_name: str,
        query_text: str,
        search_engine: str = "duckduckgo",
        max_results: int = 5,
        results: List[Dict] = None,
        error: str = None,
        retry_count: int = 0,
        duration_seconds: float = None
    ) -> int:
        """Log a web search query and its results"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO search_queries (
                run_id, agent_name, query_text, search_engine, max_results,
                timestamp, num_results, results_json, error, retry_count,
                duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, agent_name, query_text, search_engine, max_results,
            datetime.now().isoformat(),
            len(results) if results else 0,
            json.dumps(results) if results else None,
            error,
            retry_count,
            duration_seconds
        ))

        # Update analysis run counters
        cursor.execute("""
            UPDATE analysis_runs
            SET total_search_queries = total_search_queries + 1
            WHERE run_id = ?
        """, (run_id,))

        self.conn.commit()
        return cursor.lastrowid

    # ==================
    # LLM Call Tracking
    # ==================

    def log_llm_call(
        self,
        run_id: str,
        agent_name: str,
        method_name: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        response_text: str,
        parsed_json: Dict = None,
        tokens_input: int = None,
        tokens_output: int = None,
        cost_usd: float = None,
        duration_seconds: float = None,
        error: str = None,
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> int:
        """Log an LLM API call"""
        cursor = self.conn.cursor()

        # Create prompt hash for deduplication analysis
        prompt_hash = hashlib.md5(
            f"{system_prompt}|||{user_prompt}".encode()
        ).hexdigest()[:16]

        cursor.execute("""
            INSERT INTO llm_calls (
                run_id, agent_name, method_name, timestamp, model, temperature,
                max_tokens, system_prompt, user_prompt, prompt_hash,
                response_text, parsed_json, tokens_input, tokens_output,
                cost_usd, duration_seconds, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, agent_name, method_name, datetime.now().isoformat(),
            model, temperature, max_tokens, system_prompt, user_prompt,
            prompt_hash, response_text,
            json.dumps(parsed_json) if parsed_json else None,
            tokens_input, tokens_output, cost_usd, duration_seconds, error
        ))

        # Update analysis run counters
        cursor.execute("""
            UPDATE analysis_runs
            SET total_llm_calls = total_llm_calls + 1,
                total_tokens_input = total_tokens_input + ?,
                total_tokens_output = total_tokens_output + ?,
                total_cost_usd = total_cost_usd + ?
            WHERE run_id = ?
        """, (
            tokens_input or 0,
            tokens_output or 0,
            cost_usd or 0.0,
            run_id
        ))

        self.conn.commit()
        return cursor.lastrowid

    # ==================
    # Agent Step Tracking
    # ==================

    def start_agent_step(
        self,
        run_id: str,
        agent_name: str,
        step_name: str,
        input_data: Dict = None
    ) -> int:
        """Start tracking an agent step"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO agent_steps (
                run_id, agent_name, step_name, start_time, input_data
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            run_id, agent_name, step_name,
            datetime.now().isoformat(),
            json.dumps(input_data) if input_data else None
        ))

        self.conn.commit()
        return cursor.lastrowid

    def end_agent_step(
        self,
        step_id: int,
        output_data: Dict = None,
        success: bool = True,
        error: str = None,
        confidence_score: float = None
    ):
        """Complete an agent step"""
        cursor = self.conn.cursor()

        # Get start time to calculate duration
        cursor.execute("SELECT start_time FROM agent_steps WHERE id = ?", (step_id,))
        row = cursor.fetchone()
        if row:
            start_time = datetime.fromisoformat(row['start_time'])
            duration = (datetime.now() - start_time).total_seconds()
        else:
            duration = None

        cursor.execute("""
            UPDATE agent_steps
            SET end_time = ?,
                duration_seconds = ?,
                output_data = ?,
                success = ?,
                error = ?,
                confidence_score = ?
            WHERE id = ?
        """, (
            datetime.now().isoformat(),
            duration,
            json.dumps(output_data) if output_data else None,
            success,
            error,
            confidence_score,
            step_id
        ))

        self.conn.commit()

    # ==================
    # RAG Query Tracking
    # ==================

    def log_rag_query(
        self,
        run_id: str,
        agent_name: str,
        query_type: str,
        query_text: str,
        results: List[Dict] = None,
        duration_seconds: float = None
    ) -> int:
        """Log a RAG database query"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO rag_queries (
                run_id, agent_name, query_type, query_text, timestamp,
                num_results, results_json, duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id, agent_name, query_type, query_text,
            datetime.now().isoformat(),
            len(results) if results else 0,
            json.dumps(results) if results else None,
            duration_seconds
        ))

        self.conn.commit()
        return cursor.lastrowid

    # ==================
    # Data Snapshots
    # ==================

    def save_snapshot(
        self,
        run_id: str,
        snapshot_type: str,
        data: Dict
    ):
        """Save complete data snapshot at a point in the workflow"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO data_snapshots (
                run_id, snapshot_type, timestamp, data_json
            ) VALUES (?, ?, ?, ?)
        """, (
            run_id, snapshot_type,
            datetime.now().isoformat(),
            json.dumps(data, indent=2)
        ))

        self.conn.commit()

    # ==================
    # Error Logging
    # ==================

    def log_error(
        self,
        run_id: str,
        agent_name: str,
        error_type: str,
        error_message: str,
        stack_trace: str = None,
        context: Dict = None
    ):
        """Log an error with context"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO error_log (
                run_id, agent_name, error_type, error_message,
                stack_trace, context_json
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            run_id, agent_name, error_type, error_message,
            stack_trace,
            json.dumps(context) if context else None
        ))

        self.conn.commit()

    # ==================
    # Query and Analysis
    # ==================

    def get_run_summary(self, run_id: str) -> Dict:
        """Get comprehensive summary of an analysis run"""
        cursor = self.conn.cursor()

        # Main run data
        cursor.execute("SELECT * FROM analysis_runs WHERE run_id = ?", (run_id,))
        run_data = dict(cursor.fetchone())

        # Search queries
        cursor.execute("""
            SELECT COUNT(*) as count,
                   AVG(num_results) as avg_results,
                   SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as errors
            FROM search_queries WHERE run_id = ?
        """, (run_id,))
        run_data['search_stats'] = dict(cursor.fetchone())

        # LLM calls
        cursor.execute("""
            SELECT COUNT(*) as count,
                   SUM(tokens_input) as total_input_tokens,
                   SUM(tokens_output) as total_output_tokens,
                   SUM(cost_usd) as total_cost,
                   AVG(duration_seconds) as avg_duration
            FROM llm_calls WHERE run_id = ?
        """, (run_id,))
        run_data['llm_stats'] = dict(cursor.fetchone())

        # Agent steps
        cursor.execute("""
            SELECT agent_name, COUNT(*) as steps,
                   SUM(duration_seconds) as total_duration
            FROM agent_steps WHERE run_id = ?
            GROUP BY agent_name
        """, (run_id,))
        run_data['agent_stats'] = [dict(row) for row in cursor.fetchall()]

        return run_data

    def get_all_searches(self, run_id: str) -> List[Dict]:
        """Get all search queries for a run"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM search_queries
            WHERE run_id = ?
            ORDER BY timestamp
        """, (run_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_all_llm_calls(self, run_id: str) -> List[Dict]:
        """Get all LLM calls for a run"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM llm_calls
            WHERE run_id = ?
            ORDER BY timestamp
        """, (run_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_cost_summary(self, start_date: str = None) -> Dict:
        """Get cost summary across all runs"""
        cursor = self.conn.cursor()

        if start_date:
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT run_id) as total_runs,
                    SUM(total_cost_usd) as total_cost,
                    AVG(total_cost_usd) as avg_cost_per_run,
                    SUM(total_llm_calls) as total_llm_calls,
                    SUM(total_search_queries) as total_searches,
                    SUM(total_tokens_input) as total_input_tokens,
                    SUM(total_tokens_output) as total_output_tokens
                FROM analysis_runs
                WHERE start_time >= ?
            """, (start_date,))
        else:
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT run_id) as total_runs,
                    SUM(total_cost_usd) as total_cost,
                    AVG(total_cost_usd) as avg_cost_per_run,
                    SUM(total_llm_calls) as total_llm_calls,
                    SUM(total_search_queries) as total_searches,
                    SUM(total_tokens_input) as total_input_tokens,
                    SUM(total_tokens_output) as total_output_tokens
                FROM analysis_runs
            """)

        return dict(cursor.fetchone())

    def get_search_performance(self) -> List[Dict]:
        """Get search query performance metrics"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM search_performance LIMIT 50")
        return [dict(row) for row in cursor.fetchall()]

    def export_run_data(self, run_id: str, output_file: str):
        """Export complete run data to JSON file"""
        data = {
            'summary': self.get_run_summary(run_id),
            'searches': self.get_all_searches(run_id),
            'llm_calls': self.get_all_llm_calls(run_id),
        }

        # Get snapshots
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT snapshot_type, data_json
            FROM data_snapshots
            WHERE run_id = ?
            ORDER BY timestamp
        """, (run_id,))

        data['snapshots'] = {}
        for row in cursor.fetchall():
            data['snapshots'][row['snapshot_type']] = json.loads(row['data_json'])

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    # Test the audit database
    audit_db = AuditDatabase()

    # Start a test run
    run_id = audit_db.start_analysis_run(
        naics_code="541511",
        industry_name="Custom Computer Programming",
        phase="PHASE_1",
        model_name="sherlock-think-alpha"
    )
    print(f"Started run: {run_id}")

    # Log a search
    audit_db.log_search_query(
        run_id=run_id,
        agent_name="research_agent",
        query_text="site:reddit.com 541511 complaints",
        results=[{"title": "Test", "url": "http://example.com"}],
        duration_seconds=1.2
    )

    # Log an LLM call
    audit_db.log_llm_call(
        run_id=run_id,
        agent_name="strategic_agent",
        method_name="_analyze_porters_forces",
        model="sherlock-think-alpha",
        system_prompt="You are a strategic analyst",
        user_prompt="Analyze this industry...",
        response_text='{"score": 75}',
        tokens_input=500,
        tokens_output=150,
        cost_usd=0.05,
        duration_seconds=3.5
    )

    # End the run
    audit_db.end_analysis_run(run_id, completed=True, error_count=0)

    # Get summary
    summary = audit_db.get_run_summary(run_id)
    print(f"\n✅ Run Summary:")
    print(f"  Duration: {summary['duration_seconds']:.1f}s")
    print(f"  Searches: {summary['search_stats']['count']}")
    print(f"  LLM calls: {summary['llm_stats']['count']}")
    print(f"  Total cost: ${summary['llm_stats']['total_cost']:.3f}")

    audit_db.close()
    print("\n✅ Audit database test passed!")
