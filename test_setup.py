#!/usr/bin/env python3
"""
Test script to verify the setup is working correctly
"""

import os
import sys
from dotenv import load_dotenv

def test_dependencies():
    """Check if all required packages are installed"""
    print("🔍 Checking dependencies...")

    required_packages = [
        'langgraph',
        'langchain',
        'langchain_openai',
        'dotenv',
        'requests',
        'pydantic'
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            missing.append(package)

    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False

    print("✅ All dependencies installed")
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

    return True


def test_analyzer_import():
    """Test if the analyzer can be imported"""
    print("\n🔍 Testing analyzer import...")

    try:
        from naics_analyzer import NAICSAnalyzer
        print("  ✅ NAICSAnalyzer imported successfully")

        # Try to initialize
        analyzer = NAICSAnalyzer()
        print("  ✅ Analyzer initialized successfully")

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


def main():
    print("="*60)
    print("NAICS Analyzer - Setup Test")
    print("="*60)

    tests = [
        ("Dependencies", test_dependencies),
        ("Environment Config", test_env_config),
        ("Analyzer Import", test_analyzer_import),
        ("Output Directory", test_output_directory)
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
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
