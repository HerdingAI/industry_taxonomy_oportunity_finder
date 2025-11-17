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
            'analysis_date': datetime.now(),
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
            datetime.now()
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
