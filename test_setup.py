#!/usr/bin/env python3
"""
Test script to verify the 7-agent MBA-Data Science system is working correctly
"""

import os
import sys
from dotenv import load_dotenv

def test_dependencies():
    """Check if all required packages are installed"""
    print("🔍 Checking dependencies...")

    required_packages = [
        ('langgraph', 'langgraph'),
        ('langchain', 'langchain'),
        ('langchain_openai', 'langchain-openai'),
        ('dotenv', 'python-dotenv'),
        ('chromadb', 'chromadb'),
        ('duckduckgo_search', 'duckduckgo-search'),
    ]

    optional_packages = [
        ('psycopg2', 'psycopg2-binary'),
        ('openai', 'openai'),
    ]

    missing = []
    missing_optional = []

    for package, pip_name in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            missing.append(pip_name)

    print("\n🔍 Checking optional dependencies (for RAG features)...")
    for package, pip_name in optional_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ⚠️  {package} - NOT INSTALLED (optional)")
            missing_optional.append(pip_name)

    if missing:
        print(f"\n❌ Missing required packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False

    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("System will run in web-search-only mode (no RAG features)")
        print("To enable RAG: pip install " + " ".join(missing_optional))

    print("✅ All required dependencies installed")
    return True


def test_env_config():
    """Check if .env file is configured"""
    print("\n🔍 Checking environment configuration...")

    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("  ❌ OPENROUTER_API_KEY not found")
        print("\nSetup steps:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your OpenRouter API key to .env")
        print("  3. Get API key at: https://openrouter.ai/")
        return False

    if api_key == "your_openrouter_api_key_here":
        print("  ❌ OPENROUTER_API_KEY not configured (still using example value)")
        print("\nPlease update .env with your actual API key")
        return False

    print(f"  ✅ OPENROUTER_API_KEY configured ({api_key[:10]}...)")

    model = os.getenv("OPENROUTER_MODEL", "openrouter/sherlock-think-alpha")
    print(f"  ✅ Model: {model}")

    # Check for optional RAG database config
    pg_host = os.getenv("PG_HOST")
    if pg_host:
        print(f"  ✅ PostgreSQL configured (host: {pg_host})")
    else:
        print(f"  ⚠️  PostgreSQL not configured (RAG features disabled)")

    return True


def test_analyzer_import():
    """Test if the 7-agent analyzer can be imported"""
    print("\n🔍 Testing 7-agent analyzer import...")

    try:
        from src.analyzer import IndustryAnalyzer
        print("  ✅ IndustryAnalyzer imported successfully")

        # Check API key
        load_dotenv()
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key == "your_openrouter_api_key_here":
            print("  ⚠️  Skipping initialization (API key not configured)")
            return True

        # Try to initialize
        analyzer = IndustryAnalyzer(api_key)
        print("  ✅ Analyzer initialized successfully")

        # Check RAG database status
        if analyzer.rag_db:
            print("  ✅ RAG database connected (full features available)")
        else:
            print("  ⚠️  RAG database not available (web-search-only mode)")

        analyzer.close()
        return True

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def test_output_directory():
    """Check if output directory can be created"""
    print("\n🔍 Checking output directory...")

    output_dir = "outputs"

    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"  ✅ Output directory ready: {output_dir}/")
        return True
    except Exception as e:
        print(f"  ❌ Cannot create output directory: {str(e)}")
        return False


def test_data_directory():
    """Check if data directory exists for local databases"""
    print("\n🔍 Checking data directory...")

    data_dir = "data"

    try:
        os.makedirs(data_dir, exist_ok=True)
        print(f"  ✅ Data directory ready: {data_dir}/")
        return True
    except Exception as e:
        print(f"  ❌ Cannot create data directory: {str(e)}")
        return False


def main():
    print("="*60)
    print("7-Agent MBA-Data Science System - Setup Test")
    print("="*60)

    tests = [
        ("Dependencies", test_dependencies),
        ("Environment Config", test_env_config),
        ("Analyzer Import", test_analyzer_import),
        ("Output Directory", test_output_directory),
        ("Data Directory", test_data_directory),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {str(e)}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n🎉 All tests passed! You're ready to start analyzing.")
        print("\nTry running:")
        print("  python run_analysis.py 541511")
        print("\nOr for a comprehensive test:")
        print("  python test_without_rag.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
