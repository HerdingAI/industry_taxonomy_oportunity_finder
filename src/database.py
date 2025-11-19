"""
Database layer for Market Intelligence System
- SQLite for structured data (industries, opportunities, metrics)
- ChromaDB for vector storage (semantic search across research)
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings


class DatabaseManager:
    """Manages both SQL and vector databases"""

    def __init__(self, db_dir: str = "data"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)

        # SQLite for structured data
        self.sql_path = self.db_dir / "intelligence.db"
        self.conn = sqlite3.connect(str(self.sql_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts
        self._initialize_sql_schema()

        # ChromaDB for vector storage
        chroma_path = self.db_dir / "chromadb"
        self.chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )

        # Collections for different types of knowledge
        self.research_collection = self.chroma_client.get_or_create_collection(
            name="industry_research",
            metadata={"description": "Research findings from web and APIs"}
        )

        self.opportunities_collection = self.chroma_client.get_or_create_collection(
            name="opportunities",
            metadata={"description": "Identified business opportunities"}
        )

        self.insights_collection = self.chroma_client.get_or_create_collection(
            name="strategic_insights",
            metadata={"description": "Strategic analysis and patterns"}
        )

    def _initialize_sql_schema(self):
        """Create SQL tables if they don't exist"""

        cursor = self.conn.cursor()

        # Industries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS industries (
                naics_code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector_code TEXT,
                establishments INTEGER,
                employment INTEGER,
                avg_wage INTEGER,
                market_size_usd BIGINT,
                growth_rate REAL,
                hhi_index INTEGER,
                digital_maturity_score REAL,
                overall_score REAL,
                analysis_date TIMESTAMP,
                data_confidence REAL
            )
        """)

        # Opportunities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                naics_code TEXT,
                title TEXT NOT NULL,
                description TEXT,
                opportunity_type TEXT,

                -- Scoring
                opportunity_score REAL,
                confidence REAL,
                risk_adjusted_score REAL,

                -- Market sizing
                tam_usd BIGINT,
                sam_usd BIGINT,
                som_y3_usd BIGINT,

                -- Unit economics
                arpu INTEGER,
                gross_margin REAL,
                ltv INTEGER,
                cac INTEGER,
                ltv_cac_ratio REAL,
                payback_months INTEGER,

                -- Strategic
                key_moat TEXT,
                why_now TEXT,
                why_unsolved TEXT,
                competitive_threat TEXT,

                -- Risk
                risk_factors TEXT,  -- JSON
                expected_value_y5_usd BIGINT,

                created_at TIMESTAMP,

                FOREIGN KEY (naics_code) REFERENCES industries(naics_code)
            )
        """)

        # Pain points table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pain_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                naics_code TEXT,
                pain_description TEXT NOT NULL,
                frequency TEXT,
                cost_impact TEXT,
                automation_potential REAL,

                FOREIGN KEY (naics_code) REFERENCES industries(naics_code)
            )
        """)

        # Technology usage table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS technology_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                naics_code TEXT,
                software_category TEXT,
                common_tools TEXT,  -- JSON array
                adoption_rate REAL,
                avg_spend_per_employee INTEGER,

                FOREIGN KEY (naics_code) REFERENCES industries(naics_code)
            )
        """)

        # Porter's Five Forces scores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS porters_forces (
                naics_code TEXT PRIMARY KEY,
                competitive_rivalry_score INTEGER,
                competitive_rivalry_insight TEXT,
                new_entrant_threat_score INTEGER,
                new_entrant_insight TEXT,
                supplier_power_score INTEGER,
                supplier_power_insight TEXT,
                buyer_power_score INTEGER,
                buyer_power_insight TEXT,
                substitute_threat_score INTEGER,
                substitute_threat_insight TEXT,
                overall_attractiveness INTEGER,

                FOREIGN KEY (naics_code) REFERENCES industries(naics_code)
            )
        """)

        # Phase 2: Data-Vendor Opportunities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_vendor_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                naics_8_digit TEXT NOT NULL,
                segment_description TEXT,
                run_id TEXT NOT NULL,
                analysis_date TIMESTAMP,

                -- Summary metrics
                total_opportunities INTEGER,
                tier1_count INTEGER,
                tier2_count INTEGER,
                tier3_count INTEGER,
                total_tam REAL,
                avg_composite_score REAL,

                -- Complete analysis JSON blob
                full_analysis_json TEXT,

                -- Metadata
                avg_confidence REAL,
                search_queries_executed INTEGER,
                llm_calls_made INTEGER,
                total_cost REAL,
                processing_time_seconds INTEGER,

                UNIQUE(naics_8_digit, run_id)
            )
        """)

        # Indexes for Phase 2
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_naics_8digit ON data_vendor_opportunities(naics_8_digit)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_id ON data_vendor_opportunities(run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tier1_count ON data_vendor_opportunities(tier1_count)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_composite_score ON data_vendor_opportunities(avg_composite_score)")

        # Create useful views
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS top_opportunities AS
            SELECT
                o.naics_code,
                i.name as industry_name,
                o.title,
                o.opportunity_score,
                o.confidence,
                o.risk_adjusted_score,
                o.expected_value_y5_usd,
                o.ltv_cac_ratio,
                o.key_moat
            FROM opportunities o
            JOIN industries i ON o.naics_code = i.naics_code
            WHERE o.confidence > 0.6
            ORDER BY (o.opportunity_score * o.confidence) DESC
        """)

        cursor.execute("""
            CREATE VIEW IF NOT EXISTS industry_summary AS
            SELECT
                i.naics_code,
                i.name,
                i.market_size_usd,
                i.growth_rate,
                i.overall_score,
                i.data_confidence,
                p.overall_attractiveness as porters_score,
                COUNT(DISTINCT o.id) as num_opportunities,
                MAX(o.opportunity_score) as best_opportunity_score
            FROM industries i
            LEFT JOIN porters_forces p ON i.naics_code = p.naics_code
            LEFT JOIN opportunities o ON i.naics_code = o.naics_code
            GROUP BY i.naics_code
            ORDER BY i.overall_score DESC
        """)

        # Phase 2 views
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS phase2_tier1_opportunities AS
            SELECT
                naics_8_digit,
                segment_description,
                tier1_count,
                total_tam,
                avg_composite_score,
                analysis_date
            FROM data_vendor_opportunities
            WHERE tier1_count > 0
            ORDER BY tier1_count DESC, avg_composite_score DESC
        """)

        cursor.execute("""
            CREATE VIEW IF NOT EXISTS phase2_summary AS
            SELECT
                COUNT(*) as total_analyzed,
                SUM(tier1_count) as total_tier1_opps,
                SUM(tier2_count) as total_tier2_opps,
                SUM(total_tam) as cumulative_tam,
                AVG(avg_composite_score) as avg_score,
                SUM(processing_time_seconds) as total_processing_time,
                SUM(total_cost) as total_cost
            FROM data_vendor_opportunities
        """)

        self.conn.commit()

    # ====================
    # SQL Operations
    # ====================

    def save_industry(self, data: Dict[str, Any]):
        """Save or update industry data"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO industries VALUES (
                :naics_code, :name, :sector_code, :establishments, :employment,
                :avg_wage, :market_size_usd, :growth_rate, :hhi_index,
                :digital_maturity_score, :overall_score, :analysis_date, :data_confidence
            )
        """, {
            'naics_code': data.get('naics_code'),
            'name': data.get('name'),
            'sector_code': data.get('naics_code', '')[:2],
            'establishments': data.get('establishments'),
            'employment': data.get('employment'),
            'avg_wage': data.get('avg_wage'),
            'market_size_usd': data.get('market_size_usd'),
            'growth_rate': data.get('growth_rate'),
            'hhi_index': data.get('hhi_index'),
            'digital_maturity_score': data.get('digital_maturity_score'),
            'overall_score': data.get('overall_score'),
            'analysis_date': datetime.now().isoformat(),
            'data_confidence': data.get('confidence', 0.5)
        })

        self.conn.commit()

    def save_opportunity(self, data: Dict[str, Any]) -> int:
        """Save opportunity and return its ID"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO opportunities (
                naics_code, title, description, opportunity_type,
                opportunity_score, confidence, risk_adjusted_score,
                tam_usd, sam_usd, som_y3_usd,
                arpu, gross_margin, ltv, cac, ltv_cac_ratio, payback_months,
                key_moat, why_now, why_unsolved, competitive_threat,
                risk_factors, expected_value_y5_usd, created_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            data.get('naics_code'),
            data.get('title'),
            data.get('description'),
            data.get('opportunity_type'),
            data.get('opportunity_score'),
            data.get('confidence'),
            data.get('risk_adjusted_score'),
            data.get('tam_usd'),
            data.get('sam_usd'),
            data.get('som_y3_usd'),
            data.get('arpu'),
            data.get('gross_margin'),
            data.get('ltv'),
            data.get('cac'),
            data.get('ltv_cac_ratio'),
            data.get('payback_months'),
            data.get('key_moat'),
            data.get('why_now'),
            data.get('why_unsolved'),
            data.get('competitive_threat'),
            json.dumps(data.get('risk_factors', [])),
            data.get('expected_value_y5_usd'),
            datetime.now().isoformat()
        ))

        self.conn.commit()
        return cursor.lastrowid

    def save_porters_forces(self, naics_code: str, forces: Dict[str, Any]):
        """Save Porter's Five Forces analysis"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO porters_forces VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            naics_code,
            forces.get('competitive_rivalry', {}).get('score'),
            forces.get('competitive_rivalry', {}).get('insight'),
            forces.get('new_entrant_threat', {}).get('score'),
            forces.get('new_entrant_threat', {}).get('insight'),
            forces.get('supplier_power', {}).get('score'),
            forces.get('supplier_power', {}).get('insight'),
            forces.get('buyer_power', {}).get('score'),
            forces.get('buyer_power', {}).get('insight'),
            forces.get('substitute_threat', {}).get('score'),
            forces.get('substitute_threat', {}).get('insight'),
            forces.get('overall_attractiveness')
        ))

        self.conn.commit()

    def get_industry(self, naics_code: str) -> Optional[Dict]:
        """Get industry data"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM industries WHERE naics_code = ?", (naics_code,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_opportunities(self, naics_code: Optional[str] = None, min_score: float = 0.0) -> List[Dict]:
        """Get opportunities, optionally filtered"""
        cursor = self.conn.cursor()

        if naics_code:
            cursor.execute("""
                SELECT * FROM opportunities
                WHERE naics_code = ? AND opportunity_score >= ?
                ORDER BY opportunity_score DESC
            """, (naics_code, min_score))
        else:
            cursor.execute("""
                SELECT * FROM opportunities
                WHERE opportunity_score >= ?
                ORDER BY opportunity_score DESC
            """, (min_score,))

        return [dict(row) for row in cursor.fetchall()]

    def get_top_opportunities(self, limit: int = 20) -> List[Dict]:
        """Get top opportunities across all industries"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM top_opportunities LIMIT {limit}")
        return [dict(row) for row in cursor.fetchall()]

    def get_industry_summary(self) -> List[Dict]:
        """Get summary of all analyzed industries"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM industry_summary")
        return [dict(row) for row in cursor.fetchall()]

    # ====================
    # Phase 2: Data-Vendor Operations
    # ====================

    def save_data_vendor_analysis(
        self,
        naics_8_digit: str,
        segment_description: str,
        analysis_results: Dict[str, Any]
    ) -> int:
        """
        Save Phase 2 data-vendor opportunity analysis results

        Args:
            naics_8_digit: 8-digit NAICS code
            segment_description: Segment description
            analysis_results: Complete analysis results from DataVendorAnalyzer

        Returns:
            Database row ID
        """
        cursor = self.conn.cursor()

        # Extract summary metrics
        opportunities = analysis_results.get('ranked_opportunities', [])
        metadata = analysis_results.get('metadata', {})

        tier1_count = sum(1 for opp in opportunities if opp.get('tier') == 'TIER_1')
        tier2_count = sum(1 for opp in opportunities if opp.get('tier') == 'TIER_2')
        tier3_count = sum(1 for opp in opportunities if opp.get('tier') == 'TIER_3')

        # Calculate aggregate metrics
        total_tam = sum(opp.get('market_size_score', {}).get('tam', 0) for opp in opportunities)
        avg_composite = sum(opp.get('composite_score', 0) for opp in opportunities) / len(opportunities) if opportunities else 0
        avg_confidence = sum(opp.get('confidence', 0) for opp in opportunities) / len(opportunities) if opportunities else 0

        # Get run metadata
        run_id = metadata.get('run_id', 'unknown')
        processing_time = metadata.get('total_execution_time_seconds', 0)

        cursor.execute("""
            INSERT OR REPLACE INTO data_vendor_opportunities (
                naics_8_digit, segment_description, run_id, analysis_date,
                total_opportunities, tier1_count, tier2_count, tier3_count,
                total_tam, avg_composite_score,
                full_analysis_json,
                avg_confidence, search_queries_executed, llm_calls_made,
                total_cost, processing_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            naics_8_digit,
            segment_description,
            run_id,
            datetime.now().isoformat(),
            len(opportunities),
            tier1_count,
            tier2_count,
            tier3_count,
            total_tam,
            avg_composite,
            json.dumps(analysis_results),
            avg_confidence,
            0,  # Search queries (tracked in audit DB)
            0,  # LLM calls (tracked in audit DB)
            0.0,  # Cost (tracked in audit DB)
            processing_time
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_data_vendor_analysis(
        self,
        naics_8_digit: str,
        run_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Retrieve Phase 2 analysis for a NAICS code

        Args:
            naics_8_digit: 8-digit NAICS code
            run_id: Optional specific run ID (gets latest if not provided)

        Returns:
            Complete analysis results or None
        """
        cursor = self.conn.cursor()

        if run_id:
            cursor.execute("""
                SELECT * FROM data_vendor_opportunities
                WHERE naics_8_digit = ? AND run_id = ?
            """, (naics_8_digit, run_id))
        else:
            cursor.execute("""
                SELECT * FROM data_vendor_opportunities
                WHERE naics_8_digit = ?
                ORDER BY analysis_date DESC
                LIMIT 1
            """, (naics_8_digit,))

        row = cursor.fetchone()
        if not row:
            return None

        result = dict(row)
        # Parse JSON blob
        if result.get('full_analysis_json'):
            result['analysis'] = json.loads(result['full_analysis_json'])

        return result

    def get_all_tier1_opportunities(self) -> List[Dict]:
        """Get all segments with TIER_1 opportunities"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM phase2_tier1_opportunities")
        return [dict(row) for row in cursor.fetchall()]

    def get_phase2_summary(self) -> Optional[Dict]:
        """Get overall Phase 2 analysis summary"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM phase2_summary")
        row = cursor.fetchone()
        return dict(row) if row else None

    def compare_naics_opportunities(self, naics_list: List[str]) -> List[Dict]:
        """
        Compare Phase 2 opportunities across multiple NAICS codes

        Args:
            naics_list: List of 8-digit NAICS codes

        Returns:
            Comparison data for each NAICS
        """
        cursor = self.conn.cursor()
        placeholders = ','.join('?' * len(naics_list))

        cursor.execute(f"""
            SELECT
                naics_8_digit,
                segment_description,
                tier1_count,
                tier2_count,
                total_opportunities,
                total_tam,
                avg_composite_score,
                analysis_date
            FROM data_vendor_opportunities
            WHERE naics_8_digit IN ({placeholders})
            ORDER BY avg_composite_score DESC
        """, naics_list)

        return [dict(row) for row in cursor.fetchall()]

    def get_top_phase2_opportunities(self, min_tier1: int = 1, limit: int = 20) -> List[Dict]:
        """
        Get top Phase 2 opportunities by composite score

        Args:
            min_tier1: Minimum number of TIER_1 opportunities
            limit: Max results to return

        Returns:
            Top opportunities
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM data_vendor_opportunities
            WHERE tier1_count >= ?
            ORDER BY avg_composite_score DESC, tier1_count DESC
            LIMIT ?
        """, (min_tier1, limit))

        return [dict(row) for row in cursor.fetchall()]

    # ====================
    # Vector Operations
    # ====================

    def add_research(self, naics_code: str, content: str, metadata: Dict[str, Any]):
        """Add research document to vector DB"""
        doc_id = f"{naics_code}_{datetime.now().timestamp()}"

        self.research_collection.add(
            documents=[content],
            ids=[doc_id],
            metadatas=[{
                'naics_code': naics_code,
                'timestamp': datetime.now().isoformat(),
                **metadata
            }]
        )

    def add_opportunity_to_vector(self, opportunity_id: int, description: str, metadata: Dict[str, Any]):
        """Add opportunity to vector DB for semantic search"""
        self.opportunities_collection.add(
            documents=[description],
            ids=[f"opp_{opportunity_id}"],
            metadatas=[{
                'opportunity_id': opportunity_id,
                'timestamp': datetime.now().isoformat(),
                **metadata
            }]
        )

    def add_insight(self, naics_code: str, insight: str, category: str):
        """Add strategic insight to vector DB"""
        doc_id = f"{naics_code}_{category}_{datetime.now().timestamp()}"

        self.insights_collection.add(
            documents=[insight],
            ids=[doc_id],
            metadatas=[{
                'naics_code': naics_code,
                'category': category,
                'timestamp': datetime.now().isoformat()
            }]
        )

    def search_similar_research(self, query: str, sector: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        """Search for similar research across industries"""
        where_filter = {'sector': sector} if sector else None

        results = self.research_collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter if where_filter else None
        )

        if not results['documents'] or not results['documents'][0]:
            return []

        return [{
            'document': doc,
            'metadata': meta,
            'distance': dist
        } for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )]

    def search_similar_opportunities(self, query: str, top_k: int = 10) -> List[Dict]:
        """Find similar opportunities across industries"""
        results = self.opportunities_collection.query(
            query_texts=[query],
            n_results=top_k
        )

        if not results['documents'] or not results['documents'][0]:
            return []

        return [{
            'document': doc,
            'metadata': meta,
            'distance': dist
        } for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )]

    def search_insights(self, query: str, category: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        """Search strategic insights"""
        where_filter = {'category': category} if category else None

        results = self.insights_collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter if where_filter else None
        )

        if not results['documents'] or not results['documents'][0]:
            return []

        return [{
            'document': doc,
            'metadata': meta,
            'distance': dist
        } for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )]

    def close(self):
        """Close database connections"""
        self.conn.close()


if __name__ == "__main__":
    # Test the database
    db = DatabaseManager()

    # Test SQL
    db.save_industry({
        'naics_code': '541511',
        'name': 'Custom Computer Programming Services',
        'establishments': 89400,
        'employment': 823000,
        'avg_wage': 98400,
        'market_size_usd': 185000000000,
        'growth_rate': 0.082,
        'hhi_index': 182,
        'overall_score': 84.5,
        'confidence': 0.88
    })

    # Test vector search
    db.add_research(
        '541511',
        "Custom programming services market is highly fragmented with low barriers to entry",
        {'source': 'test', 'type': 'market_analysis'}
    )

    similar = db.search_similar_research("fragmented software markets")
    print(f"Found {len(similar)} similar research documents")

    db.close()
    print("✅ Database test passed!")
