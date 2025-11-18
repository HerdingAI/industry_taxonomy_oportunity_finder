#!/usr/bin/env python3
"""
Test PostgreSQL RAG Database Setup and Connectivity

This script verifies:
1. Database connection works
2. All tables exist
3. All helper functions exist
4. Sample queries work
5. Embedding generation works (if API key provided)

Usage:
    python test_database.py
"""

import sys
from src.rag_database import RAGDatabase

print("=" * 70)
print("  PostgreSQL RAG Database Test")
print("=" * 70)

# Test 1: Connection
print("\n[Test 1] Database Connection")
print("-" * 70)

try:
    db = RAGDatabase()
    print("✅ RAGDatabase initialized")
    print(f"   Host: {db.config['host']}:{db.config['port']}")
    print(f"   Database: {db.config['database']}")
    print(f"   User: {db.config['user']}")
except Exception as e:
    print(f"❌ Failed to initialize: {e}")
    sys.exit(1)

# Test 2: Connection and PostgreSQL version
print("\n[Test 2] PostgreSQL Connection")
print("-" * 70)

try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected successfully")
        print(f"   Version: {version.split(',')[0]}")
        cursor.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# Test 3: pgvector extension
print("\n[Test 3] pgvector Extension")
print("-" * 70)

try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            );
        """)
        exists = cursor.fetchone()[0]
        cursor.close()

        if exists:
            print("✅ pgvector extension installed")
        else:
            print("❌ pgvector extension NOT installed")
            print("   Run: CREATE EXTENSION vector; (requires superuser)")
            sys.exit(1)
except Exception as e:
    print(f"❌ Failed to check extension: {e}")
    sys.exit(1)

# Test 4: Tables exist
print("\n[Test 4] Database Tables")
print("-" * 70)

expected_tables = [
    'voice_of_customer',
    'competitive_intelligence',
    'workflow_intelligence'
]

try:
    with db.get_connection() as conn:
        cursor = conn.cursor()

        for table in expected_tables:
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = %s
                );
            """, (table,))
            exists = cursor.fetchone()[0]

            if exists:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Table '{table}' exists ({count} rows)")
            else:
                print(f"❌ Table '{table}' NOT found")
                sys.exit(1)

        cursor.close()
except Exception as e:
    print(f"❌ Failed to check tables: {e}")
    sys.exit(1)

# Test 5: Helper functions exist
print("\n[Test 5] Helper Functions")
print("-" * 70)

expected_functions = [
    'search_voice_of_customer',
    'aggregate_pain_points',
    'get_recent_funding',
    'find_automation_opportunities'
]

try:
    with db.get_connection() as conn:
        cursor = conn.cursor()

        for func in expected_functions:
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_proc p
                    JOIN pg_namespace n ON p.pronamespace = n.oid
                    WHERE n.nspname = 'public' AND p.proname = %s
                );
            """, (func,))
            exists = cursor.fetchone()[0]

            if exists:
                print(f"✅ Function '{func}()' exists")
            else:
                print(f"❌ Function '{func}()' NOT found")
                sys.exit(1)

        cursor.close()
except Exception as e:
    print(f"❌ Failed to check functions: {e}")
    sys.exit(1)

# Test 6: Views exist
print("\n[Test 6] Database Views")
print("-" * 70)

try:
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.views
                WHERE table_name = 'industry_rag_summary'
            );
        """)
        exists = cursor.fetchone()[0]

        if exists:
            # Get row count
            cursor.execute("SELECT COUNT(*) FROM industry_rag_summary")
            count = cursor.fetchone()[0]
            print(f"✅ View 'industry_rag_summary' exists ({count} rows)")
        else:
            print("❌ View 'industry_rag_summary' NOT found")
            sys.exit(1)

        cursor.close()
except Exception as e:
    print(f"❌ Failed to check views: {e}")
    sys.exit(1)

# Test 7: Sample queries work (even with empty tables)
print("\n[Test 7] Sample Queries")
print("-" * 70)

try:
    # Test industry summary (will work even with no data)
    summary = db.get_industry_summary()
    print(f"✅ get_industry_summary() works ({len(summary)} industries)")

    # Test recent funding query (will return empty if no data)
    funding = db.get_recent_funding(naics_code='541511', months_back=12)
    print(f"✅ get_recent_funding() works ({len(funding)} results)")

    # Test automation opportunities (will return empty if no data)
    opportunities = db.find_automation_opportunities(
        naics_code='541511',
        min_genai_score=60
    )
    print(f"✅ find_automation_opportunities() works ({len(opportunities)} results)")

except Exception as e:
    print(f"❌ Query failed: {e}")
    sys.exit(1)

# Test 8: Embedding generation (if API key provided)
print("\n[Test 8] Embedding Generation")
print("-" * 70)

try:
    if db.openai_api_key:
        print("Generating test embedding...")
        embedding = db.generate_embedding("Test text for embedding")

        if len(embedding) == 1536:
            print(f"✅ Embedding generation works (dimension: {len(embedding)})")
            print(f"   First 5 values: {embedding[:5]}")
        else:
            print(f"❌ Unexpected embedding dimension: {len(embedding)} (expected 1536)")
            sys.exit(1)
    else:
        print("⚠️  OPENROUTER_API_KEY not set - skipping embedding test")
        print("   (This is OK for database structure testing)")

except Exception as e:
    print(f"❌ Embedding generation failed: {e}")
    print("   Check that OPENROUTER_API_KEY is set correctly in .env")
    sys.exit(1)

# Test 9: Indexes exist
print("\n[Test 9] Database Indexes")
print("-" * 70)

try:
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Count indexes per table
        for table in expected_tables:
            cursor.execute("""
                SELECT COUNT(*)
                FROM pg_indexes
                WHERE tablename = %s
            """, (table,))
            count = cursor.fetchone()[0]
            print(f"✅ Table '{table}' has {count} indexes")

        cursor.close()
except Exception as e:
    print(f"❌ Failed to check indexes: {e}")
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("  ✅ ALL TESTS PASSED!")
print("=" * 70)
print("\nDatabase setup verified successfully!")
print("\nNext steps:")
print("  1. Populate voice_of_customer with Reddit/G2 reviews")
print("  2. Populate competitive_intelligence with Crunchbase data")
print("  3. Populate workflow_intelligence with job description data")
print("\nSee database/README.md for data population examples.")
print("=" * 70)
