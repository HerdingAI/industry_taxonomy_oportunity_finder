"""
RAG Database Connection and Query Module

Provides connection management and helper functions for querying the
PostgreSQL RAG database with pgvector semantic search.

Usage:
    from src.rag_database import RAGDatabase

    rag_db = RAGDatabase()
    results = rag_db.search_voice_of_customer(
        query_text="What are common complaints about insurance software?",
        naics_code='524210',
        limit_count=10
    )
"""

import os
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Optional imports - gracefully handle if not installed
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None
    RealDictCursor = None

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class RAGDatabase:
    """Connection and query interface for PostgreSQL RAG database"""

    def __init__(self):
        """Initialize database connection configuration"""
        # Check if required dependencies are available
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "psycopg2 is not installed. RAG database features require psycopg2. "
                "Install with: pip install psycopg2-binary"
            )

        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package is not installed. RAG database features require openai. "
                "Install with: pip install openai"
            )

        self.config = {
            'host': os.getenv('PG_HOST', 'localhost'),
            'port': os.getenv('PG_PORT', '5432'),
            'database': os.getenv('PG_DATABASE', 'meetup_events'),
            'user': os.getenv('PG_USER', 'meetup_app'),
            'password': os.getenv('PG_PASSWORD')
        }

        # OpenRouter API for embeddings
        self.openai_api_key = os.getenv('OPENROUTER_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            openai.api_base = 'https://openrouter.ai/api/v1'

        # Verify configuration
        self._verify_config()

    def _verify_config(self):
        """Verify database configuration is complete"""
        missing = [k for k, v in self.config.items() if v is None]
        if missing:
            raise ValueError(
                f"Missing database configuration: {', '.join(missing)}. "
                f"Please set PG_{', PG_'.join([k.upper() for k in missing])} "
                f"in your .env file."
            )

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate OpenAI ada-002 embedding for text

        Args:
            text: Text to embed

        Returns:
            List of 1536 floats (embedding vector)
        """
        if not self.openai_api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Cannot generate embeddings."
            )

        try:
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response['data'][0]['embedding']
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {e}")

    def search_voice_of_customer(
        self,
        query_text: str,
        naics_code: Optional[str] = None,
        source_types: Optional[List[str]] = None,
        limit_count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Semantic search on voice of customer data

        Args:
            query_text: Text query to search for
            naics_code: Filter by NAICS code (optional)
            source_types: Filter by source types (e.g., ['reddit', 'g2'])
            limit_count: Maximum number of results

        Returns:
            List of dicts with keys: id, content, pain_point_category,
            complaint_keywords, feature_gaps, url, similarity
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query_text)

        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT * FROM search_voice_of_customer(
                    query_embedding := %s::vector,
                    naics_code := %s,
                    source_types := %s,
                    limit_count := %s
                )
            """, (query_embedding, naics_code, source_types, limit_count))

            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

    def aggregate_pain_points(
        self,
        naics_code: str
    ) -> List[Dict[str, Any]]:
        """
        Aggregate pain points by category for a NAICS code

        Args:
            naics_code: NAICS code to analyze

        Returns:
            List of dicts with keys: pain_point_category, mention_count,
            all_keywords, negativity_score, example_content
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT * FROM aggregate_pain_points(
                    naics_code := %s
                )
            """, (naics_code,))

            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

    def get_recent_funding(
        self,
        naics_code: str,
        months_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent startup funding activity in an industry

        Args:
            naics_code: NAICS code to analyze
            months_back: How many months back to search (default 24)

        Returns:
            List of dicts with keys: company_name, funding_stage,
            funding_amount_usd, funding_date, product_category,
            key_features, total_funding_usd, source_url
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT * FROM get_recent_funding(
                    naics_code := %s,
                    since_date := CURRENT_DATE - make_interval(months => %s)
                )
            """, (naics_code, months_back))

            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

    def find_automation_opportunities(
        self,
        naics_code: str,
        min_genai_score: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Find workflows with high GenAI automation potential

        Args:
            naics_code: NAICS code to analyze
            min_genai_score: Minimum GenAI fit score (0-100)

        Returns:
            List of dicts with keys: workflow_name, job_role,
            genai_fit_score, automation_feasibility, time_spent_hours,
            frequency, pain_point_description, data_types
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT * FROM find_automation_opportunities(
                    naics_code := %s,
                    min_genai_score := %s
                )
            """, (naics_code, min_genai_score))

            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

    def get_industry_summary(
        self,
        naics_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get summary statistics for industries

        Args:
            naics_code: Specific NAICS code (optional, None for all)

        Returns:
            List of dicts with summary statistics by NAICS code
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if naics_code:
                cursor.execute("""
                    SELECT * FROM industry_rag_summary
                    WHERE naics_code = %s
                """, (naics_code,))
            else:
                cursor.execute("SELECT * FROM industry_rag_summary")

            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

    def insert_voice_of_customer(
        self,
        data: Dict[str, Any]
    ) -> int:
        """
        Insert a voice of customer entry

        Args:
            data: Dict with keys matching voice_of_customer schema
                Required: source_type, content
                Optional: industry_naics, industry_keywords, title,
                         software_mentioned, sentiment, pain_point_category,
                         complaint_keywords, feature_gaps, url

        Returns:
            ID of inserted row
        """
        # Generate embedding for content
        embedding = self.generate_embedding(data['content'])

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO voice_of_customer (
                    source_type, industry_naics, industry_keywords, title,
                    content, software_mentioned, sentiment, pain_point_category,
                    complaint_keywords, feature_gaps, url, embedding
                ) VALUES (
                    %(source_type)s, %(industry_naics)s, %(industry_keywords)s,
                    %(title)s, %(content)s, %(software_mentioned)s, %(sentiment)s,
                    %(pain_point_category)s, %(complaint_keywords)s,
                    %(feature_gaps)s, %(url)s, %(embedding)s
                )
                RETURNING id
            """, {
                'source_type': data.get('source_type'),
                'industry_naics': data.get('industry_naics'),
                'industry_keywords': data.get('industry_keywords'),
                'title': data.get('title'),
                'content': data.get('content'),
                'software_mentioned': data.get('software_mentioned'),
                'sentiment': data.get('sentiment'),
                'pain_point_category': data.get('pain_point_category'),
                'complaint_keywords': data.get('complaint_keywords'),
                'feature_gaps': data.get('feature_gaps'),
                'url': data.get('url'),
                'embedding': embedding
            })

            row_id = cursor.fetchone()[0]
            cursor.close()

            return row_id

    def insert_competitive_intelligence(
        self,
        data: Dict[str, Any]
    ) -> int:
        """
        Insert a competitive intelligence entry

        Args:
            data: Dict with keys matching competitive_intelligence schema
                Required: company_name
                Optional: All other fields

        Returns:
            ID of inserted row
        """
        # Generate embedding from company description
        desc_parts = [
            data.get('company_name', ''),
            data.get('industry_vertical', ''),
            data.get('product_category', ''),
            ' '.join(data.get('key_features', []))
        ]
        desc_text = ' '.join(filter(None, desc_parts))
        embedding = self.generate_embedding(desc_text)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO competitive_intelligence (
                    company_name, founded_year, employee_count_range,
                    industry_naics, industry_vertical, target_customer,
                    funding_stage, funding_amount_usd, funding_date,
                    total_funding_usd, product_category, key_features,
                    technology_stack, competitors, source_url, embedding
                ) VALUES (
                    %(company_name)s, %(founded_year)s, %(employee_count_range)s,
                    %(industry_naics)s, %(industry_vertical)s, %(target_customer)s,
                    %(funding_stage)s, %(funding_amount_usd)s, %(funding_date)s,
                    %(total_funding_usd)s, %(product_category)s, %(key_features)s,
                    %(technology_stack)s, %(competitors)s, %(source_url)s, %(embedding)s
                )
                RETURNING id
            """, {
                'company_name': data.get('company_name'),
                'founded_year': data.get('founded_year'),
                'employee_count_range': data.get('employee_count_range'),
                'industry_naics': data.get('industry_naics'),
                'industry_vertical': data.get('industry_vertical'),
                'target_customer': data.get('target_customer'),
                'funding_stage': data.get('funding_stage'),
                'funding_amount_usd': data.get('funding_amount_usd'),
                'funding_date': data.get('funding_date'),
                'total_funding_usd': data.get('total_funding_usd'),
                'product_category': data.get('product_category'),
                'key_features': data.get('key_features'),
                'technology_stack': data.get('technology_stack'),
                'competitors': data.get('competitors'),
                'source_url': data.get('source_url'),
                'embedding': embedding
            })

            row_id = cursor.fetchone()[0]
            cursor.close()

            return row_id

    def insert_workflow_intelligence(
        self,
        data: Dict[str, Any]
    ) -> int:
        """
        Insert a workflow intelligence entry

        Args:
            data: Dict with keys matching workflow_intelligence schema
                Required: industry_naics, workflow_name
                Optional: All other fields

        Returns:
            ID of inserted row
        """
        # Generate embedding from workflow description
        desc_parts = [
            data.get('workflow_name', ''),
            data.get('job_role', ''),
            data.get('pain_point_description', ''),
            ' '.join(data.get('manual_steps', []))
        ]
        desc_text = ' '.join(filter(None, desc_parts))
        embedding = self.generate_embedding(desc_text)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO workflow_intelligence (
                    industry_naics, job_role, workflow_name, manual_steps,
                    tools_used, time_spent_hours, frequency, volume_per_period,
                    pain_point_description, automation_feasibility,
                    genai_fit_score, data_types, data_volume_estimate,
                    source_url, embedding
                ) VALUES (
                    %(industry_naics)s, %(job_role)s, %(workflow_name)s,
                    %(manual_steps)s, %(tools_used)s, %(time_spent_hours)s,
                    %(frequency)s, %(volume_per_period)s,
                    %(pain_point_description)s, %(automation_feasibility)s,
                    %(genai_fit_score)s, %(data_types)s, %(data_volume_estimate)s,
                    %(source_url)s, %(embedding)s
                )
                RETURNING id
            """, {
                'industry_naics': data.get('industry_naics'),
                'job_role': data.get('job_role'),
                'workflow_name': data.get('workflow_name'),
                'manual_steps': data.get('manual_steps'),
                'tools_used': data.get('tools_used'),
                'time_spent_hours': data.get('time_spent_hours'),
                'frequency': data.get('frequency'),
                'volume_per_period': data.get('volume_per_period'),
                'pain_point_description': data.get('pain_point_description'),
                'automation_feasibility': data.get('automation_feasibility'),
                'genai_fit_score': data.get('genai_fit_score'),
                'data_types': data.get('data_types'),
                'data_volume_estimate': data.get('data_volume_estimate'),
                'source_url': data.get('source_url'),
                'embedding': embedding
            })

            row_id = cursor.fetchone()[0]
            cursor.close()

            return row_id


# Convenience function for quick testing
def test_connection():
    """Test database connection and basic queries"""
    try:
        db = RAGDatabase()
        print("✅ Database connection configured")

        # Test connection
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Connected to: {version.split(',')[0]}")

            # Check tables exist
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('voice_of_customer', 'competitive_intelligence', 'workflow_intelligence')
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Found tables: {', '.join(tables)}")

            cursor.close()

        print("\n✅ Database connection test successful!")
        return True

    except Exception as e:
        print(f"\n❌ Database connection test failed: {e}")
        return False


if __name__ == '__main__':
    # Run connection test when executed directly
    test_connection()
