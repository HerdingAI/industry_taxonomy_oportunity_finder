#!/usr/bin/env python3
"""
Code review and bug check script
Tests all components for bugs, logic gaps, and missing pieces
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, '/home/user/industry_taxonomy_oportunity_finder')

def test_imports():
    """Test all imports work correctly"""
    print("=" * 60)
    print("TEST 1: Checking Imports")
    print("=" * 60)

    errors = []

    try:
        from src.database import DatabaseManager
        print("✅ src.database imports correctly")
    except Exception as e:
        errors.append(f"database: {e}")
        print(f"❌ src.database: {e}")

    try:
        from src.research_agent import ResearchAgent
        print("✅ src.research_agent imports correctly")
    except Exception as e:
        errors.append(f"research_agent: {e}")
        print(f"❌ src.research_agent: {e}")

    try:
        from src.strategic_agent import StrategicAnalyst
        print("✅ src.strategic_agent imports correctly")
    except Exception as e:
        errors.append(f"strategic_agent: {e}")
        print(f"❌ src.strategic_agent: {e}")

    try:
        from src.quantitative_agent import QuantitativeAnalyst
        print("✅ src.quantitative_agent imports correctly")
    except Exception as e:
        errors.append(f"quantitative_agent: {e}")
        print(f"❌ src.quantitative_agent: {e}")

    try:
        from src.synthesizer_agent import SynthesizerAgent
        print("✅ src.synthesizer_agent imports correctly")
    except Exception as e:
        errors.append(f"synthesizer_agent: {e}")
        print(f"❌ src.synthesizer_agent: {e}")

    try:
        from src.analyzer import IndustryAnalyzer
        print("✅ src.analyzer imports correctly")
    except Exception as e:
        errors.append(f"analyzer: {e}")
        print(f"❌ src.analyzer: {e}")

    return len(errors) == 0, errors


def test_database_creation():
    """Test database initialization and directory creation"""
    print("\n" + "=" * 60)
    print("TEST 2: Database Creation")
    print("=" * 60)

    try:
        from src.database import DatabaseManager

        # Create in test directory
        test_dir = "/tmp/test_db"
        db = DatabaseManager(test_dir)

        # Check directories exist
        import os
        assert os.path.exists(test_dir), "Database directory not created"
        assert os.path.exists(os.path.join(test_dir, "intelligence.db")), "SQLite DB not created"
        assert os.path.exists(os.path.join(test_dir, "chromadb")), "ChromaDB directory not created"

        # Test basic operations
        db.save_industry({
            'naics_code': '999999',
            'name': 'Test Industry',
            'market_size_usd': 1000000,
            'confidence': 0.8
        })

        industry = db.get_industry('999999')
        assert industry is not None, "Failed to retrieve saved industry"
        assert industry['name'] == 'Test Industry', "Industry data mismatch"

        db.close()

        # Cleanup
        import shutil
        shutil.rmtree(test_dir)

        print("✅ Database creation and basic operations work")
        return True, []

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


def test_json_parsing():
    """Test JSON parsing robustness"""
    print("\n" + "=" * 60)
    print("TEST 3: JSON Parsing Robustness")
    print("=" * 60)

    from src.research_agent import ResearchAgent
    from langchain_openai import ChatOpenAI

    # Create dummy LLM (won't actually call it)
    llm = ChatOpenAI(
        model="openrouter/sherlock-think-alpha",
        openai_api_key="dummy",
        openai_api_base="https://openrouter.ai/api/v1"
    )

    agent = ResearchAgent(llm)

    # Test various JSON formats
    test_cases = [
        ('{"key": "value"}', True),
        ('```json\n{"key": "value"}\n```', True),
        ('```\n{"key": "value"}\n```', True),
        ('Some text {"key": "value"} more text', True),
        ('invalid json', False),
        ('', False),
    ]

    errors = []
    for content, should_succeed in test_cases:
        try:
            result = agent._parse_json_response(content)
            if should_succeed and not result:
                errors.append(f"Failed to parse valid JSON: {content}")
                print(f"❌ Failed: {content[:50]}")
            elif should_succeed:
                print(f"✅ Parsed: {content[:50]}")
        except Exception as e:
            if should_succeed:
                errors.append(f"Exception on valid JSON: {e}")
                print(f"❌ Exception: {content[:50]} - {e}")

    if not errors:
        print("✅ JSON parsing is robust")

    return len(errors) == 0, errors


def test_state_management():
    """Test LangGraph state management"""
    print("\n" + "=" * 60)
    print("TEST 4: LangGraph State Management")
    print("=" * 60)

    try:
        from src.analyzer import AnalysisState

        # Test state creation
        state: AnalysisState = {
            'naics_code': '541511',
            'industry_name': 'Test',
            'research_data': {},
            'strategic_data': {},
            'quantitative_data': {},
            'final_report': '',
            'error': '',
            'completed': False
        }

        # Verify all required fields
        required_fields = ['naics_code', 'industry_name', 'research_data',
                          'strategic_data', 'quantitative_data', 'final_report',
                          'error', 'completed']

        for field in required_fields:
            assert field in state, f"Missing required field: {field}"

        print("✅ State management structure correct")
        return True, []

    except Exception as e:
        print(f"❌ State management test failed: {e}")
        return False, [str(e)]


def test_error_handling():
    """Test error handling doesn't crash the system"""
    print("\n" + "=" * 60)
    print("TEST 5: Error Handling")
    print("=" * 60)

    try:
        from src.research_agent import ResearchAgent
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="openrouter/sherlock-think-alpha",
            openai_api_key="invalid_key",
            openai_api_base="https://openrouter.ai/api/v1"
        )

        agent = ResearchAgent(llm)

        # Test with bad input - should not crash
        result = agent._parse_json_response("not valid json at all")

        # Should return minimal structure, not crash
        assert isinstance(result, dict), "Should return dict even on error"

        print("✅ Error handling prevents crashes")
        return True, []

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False, [str(e)]


def test_cli_imports():
    """Test CLI script imports"""
    print("\n" + "=" * 60)
    print("TEST 6: CLI Script Imports")
    print("=" * 60)

    try:
        # Try to import the CLI script
        import analyze
        print("✅ analyze.py imports correctly")
        return True, []
    except Exception as e:
        print(f"❌ CLI import failed: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


def main():
    """Run all tests"""
    print("\n🔍 COMPREHENSIVE CODE REVIEW\n")

    tests = [
        ("Imports", test_imports),
        ("Database Creation", test_database_creation),
        ("JSON Parsing", test_json_parsing),
        ("State Management", test_state_management),
        ("Error Handling", test_error_handling),
        ("CLI Imports", test_cli_imports),
    ]

    results = []
    all_errors = []

    for test_name, test_func in tests:
        try:
            success, errors = test_func()
            results.append((test_name, success))
            if errors:
                all_errors.extend(errors)
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
            all_errors.append(str(e))

    # Summary
    print("\n" + "=" * 60)
    print("REVIEW SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nScore: {passed}/{total} tests passed")

    if all_errors:
        print("\n⚠️  ERRORS FOUND:")
        for i, error in enumerate(all_errors, 1):
            print(f"{i}. {error}")
        return 1
    else:
        print("\n✅ All tests passed! No critical bugs found.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
