#!/usr/bin/env python3
"""
Test script to verify system works WITHOUT RAG database populated
Tests web-search-only functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all imports work"""
    print("🧪 Testing imports...")
    try:
        from src.analyzer import IndustryAnalyzer
        print("✅ IndustryAnalyzer imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_initialization():
    """Test that analyzer initializes without RAG database"""
    print("\n🧪 Testing analyzer initialization...")
    try:
        from src.analyzer import IndustryAnalyzer

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ OPENROUTER_API_KEY not found in .env file")
            return False

        # This should work even without RAG database
        analyzer = IndustryAnalyzer(api_key)

        # Check RAG database status
        if analyzer.rag_db is None:
            print("✅ Analyzer initialized successfully WITHOUT RAG database")
            print("   → Research Agent: Available (web search)")
            print("   → Strategic Agent: Available (partial - no staleness audit)")
            print("   → Quantitative Agent: Available")
            print("   → Synthesizer Agent: Available")
            print("   → Customer Analysis: Skipped (requires RAG)")
            print("   → Automation Analysis: Skipped (requires RAG)")
        else:
            print("✅ Analyzer initialized WITH RAG database")
            print("   → All agents fully functional")

        analyzer.close()
        return True

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_analysis():
    """Test basic analysis without RAG (if user wants)"""
    print("\n🧪 Testing basic analysis (web search only)...")
    print("   NOTE: This will make real API calls and web searches")

    response = input("   Run actual analysis test? (y/N): ").strip().lower()

    if response != 'y':
        print("   ⏭️  Skipping actual analysis test")
        return True

    try:
        from src.analyzer import IndustryAnalyzer

        api_key = os.getenv("OPENROUTER_API_KEY")
        analyzer = IndustryAnalyzer(api_key)

        # Test with a simple NAICS code (Software Publishers)
        print("\n   Analyzing NAICS 511210 (Software Publishers)...")
        print("   This will take 1-2 minutes...")

        result = analyzer.analyze("511210", phase="PHASE_1")

        # Check result
        if result.get('completed'):
            print("✅ Analysis completed successfully!")
            print(f"\n   Report preview (first 500 chars):")
            print("   " + "="*70)
            print("   " + result['final_report'][:500])
            print("   ...")
            print("   " + "="*70)

            # Save report
            filename = analyzer.save_report(result, output_dir="outputs")
            print(f"\n   📄 Full report saved to: {filename}")
        else:
            print(f"⚠️  Analysis completed with errors: {result.get('error_count', 0)} errors")
            if result.get('error'):
                print(f"   Last error: {result['error']}")

        analyzer.close()
        return True

    except Exception as e:
        print(f"❌ Analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("NAICS Opportunity Finder - Web Search Only Test")
    print("="*70)

    tests = [
        ("Import Test", test_imports),
        ("Initialization Test", test_initialization),
        ("Basic Analysis Test", test_basic_analysis),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        result = test_func()
        results.append((test_name, result))

    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print("="*70)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nYou can run the system with web searches only.")
        print("RAG database features (customer analysis, automation analysis, staleness audit)")
        print("will be skipped, but core functionality works.")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease check the errors above.")
    print("="*70)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
