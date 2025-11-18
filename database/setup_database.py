#!/usr/bin/env python3
"""
PostgreSQL RAG Database Setup Script

This script automatically sets up the complete RAG database infrastructure
including tables, indexes, helper functions, and views.

Usage:
    python database/setup_database.py

Requirements:
    - PostgreSQL server running
    - Environment variables set in .env file
    - psycopg2-binary installed
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('PG_HOST', 'localhost'),
    'port': os.getenv('PG_PORT', '5432'),
    'database': os.getenv('PG_DATABASE', 'meetup_events'),
    'user': os.getenv('PG_USER', 'meetup_app'),
    'password': os.getenv('PG_PASSWORD')
}

# SQL files to execute in order
SCHEMA_FILES = [
    '01_create_extension.sql',
    '02_voice_of_customer.sql',
    '03_competitive_intelligence.sql',
    '04_workflow_intelligence.sql',
    '05_helper_functions.sql'
]

def print_banner(message):
    """Print a formatted banner message"""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70)

def print_step(step_num, message):
    """Print a formatted step message"""
    print(f"\n[Step {step_num}] {message}")
    print("-" * 70)

def verify_connection():
    """Verify database connection and credentials"""
    print_step(1, "Verifying Database Connection")

    # Check for missing credentials
    missing = [k for k, v in DB_CONFIG.items() if v is None]
    if missing:
        print(f"❌ Missing database credentials: {', '.join(missing)}")
        print("\nPlease set the following environment variables in your .env file:")
        for key in missing:
            print(f"  PG_{key.upper()}=your_value_here")
        return None

    # Test connection
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Get database version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]

        print(f"✅ Successfully connected to PostgreSQL")
        print(f"   Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"   Database: {DB_CONFIG['database']}")
        print(f"   User: {DB_CONFIG['user']}")
        print(f"   Version: {version.split(',')[0]}")

        cursor.close()
        return conn

    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        print("\nPlease verify:")
        print("  1. PostgreSQL server is running")
        print("  2. Database credentials are correct in .env")
        print("  3. Database exists and user has access")
        return None

def execute_sql_file(conn, file_path):
    """Execute a SQL file and return success status"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        cursor = conn.cursor()
        cursor.execute(sql_content)
        conn.commit()
        cursor.close()

        return True, None

    except psycopg2.Error as e:
        conn.rollback()
        return False, str(e)
    except Exception as e:
        return False, str(e)

def verify_setup(conn):
    """Verify all tables, functions, and views were created"""
    print_step(7, "Verifying Database Setup")

    cursor = conn.cursor()
    all_good = True

    # Check for pgvector extension
    cursor.execute("""
        SELECT EXISTS(
            SELECT 1 FROM pg_extension WHERE extname = 'vector'
        );
    """)
    if cursor.fetchone()[0]:
        print("✅ pgvector extension installed")
    else:
        print("❌ pgvector extension NOT found")
        all_good = False

    # Check for tables
    expected_tables = [
        'voice_of_customer',
        'competitive_intelligence',
        'workflow_intelligence'
    ]

    for table in expected_tables:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables
                WHERE table_name = %s
            );
        """, (table,))

        if cursor.fetchone()[0]:
            # Count rows
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(table)
            ))
            count = cursor.fetchone()[0]
            print(f"✅ Table '{table}' created (currently {count} rows)")
        else:
            print(f"❌ Table '{table}' NOT found")
            all_good = False

    # Check for helper functions
    expected_functions = [
        'search_voice_of_customer',
        'aggregate_pain_points',
        'get_recent_funding',
        'find_automation_opportunities'
    ]

    for func in expected_functions:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'public' AND p.proname = %s
            );
        """, (func,))

        if cursor.fetchone()[0]:
            print(f"✅ Function '{func}()' created")
        else:
            print(f"❌ Function '{func}()' NOT found")
            all_good = False

    # Check for view
    cursor.execute("""
        SELECT EXISTS(
            SELECT 1 FROM information_schema.views
            WHERE table_name = 'industry_rag_summary'
        );
    """)

    if cursor.fetchone()[0]:
        print("✅ View 'industry_rag_summary' created")
    else:
        print("❌ View 'industry_rag_summary' NOT found")
        all_good = False

    cursor.close()
    return all_good

def main():
    """Main setup procedure"""
    print_banner("PostgreSQL RAG Database Setup")
    print("This script will create all tables, indexes, and helper functions")
    print("for the NAICS Industry Opportunity Finder RAG database.")

    # Step 1: Verify connection
    conn = verify_connection()
    if conn is None:
        sys.exit(1)

    # Step 2: Execute schema files
    schema_dir = Path(__file__).parent / 'schema'

    for idx, filename in enumerate(SCHEMA_FILES, start=2):
        print_step(idx, f"Executing {filename}")

        file_path = schema_dir / filename
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            conn.close()
            sys.exit(1)

        success, error = execute_sql_file(conn, file_path)

        if success:
            print(f"✅ {filename} executed successfully")
        else:
            print(f"❌ Failed to execute {filename}")
            print(f"   Error: {error}")
            conn.close()
            sys.exit(1)

    # Step 7: Verify setup
    all_good = verify_setup(conn)

    # Close connection
    conn.close()

    # Final summary
    print_banner("Setup Complete!")

    if all_good:
        print("✅ All database components created successfully")
        print("\nNext steps:")
        print("  1. Populate voice_of_customer table with Reddit/G2 reviews")
        print("  2. Populate competitive_intelligence with Crunchbase data")
        print("  3. Populate workflow_intelligence with job description data")
        print("  4. Run 'python test_database.py' to verify RAG queries work")
        print("\nSee database/README.md for detailed documentation.")
    else:
        print("⚠️  Some components failed to create")
        print("Please review the errors above and fix before proceeding.")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
