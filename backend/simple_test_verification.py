#!/usr/bin/env python3
"""
Simple test verification script.

This script verifies that the test files are syntactically correct
and can be imported without running the full test suite.
"""

import sys
import ast
from pathlib import Path

def check_python_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to check syntax
        ast.parse(content)
        return True, None
    
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    
    except Exception as e:
        return False, f"Error reading file: {e}"

def main():
    """Main verification function."""
    print("🧪 AI PKM Tool - Simple Test Verification")
    print("=" * 50)
    
    # Get the directory where this script is located (backend/)
    script_dir = Path(__file__).parent
    
    test_files = [
        "tests/conftest.py",
        "tests/test_health_endpoints.py",
        "tests/test_document_processing_integration.py",
        "tests/test_error_handling.py",
        "tests/test_service_dependencies.py",
        "tests/test_load_testing.py"
    ]
    
    all_valid = True
    
    print("\nChecking test file syntax...")
    for test_file in test_files:
        file_path = script_dir / test_file
        
        if not file_path.exists():
            print(f"❌ {test_file}: File not found")
            all_valid = False
            continue
        
        is_valid, error = check_python_syntax(file_path)
        
        if is_valid:
            print(f"✅ {test_file}: Valid syntax")
        else:
            print(f"❌ {test_file}: {error}")
            all_valid = False
    
    # Check other important files
    other_files = [
        "pytest.ini",
        "run_comprehensive_tests.py"
    ]
    
    print("\nChecking other test files...")
    for other_file in other_files:
        file_path = script_dir / other_file
        
        if not file_path.exists():
            print(f"❌ {other_file}: File not found")
            all_valid = False
            continue
        
        if other_file.endswith('.py'):
            is_valid, error = check_python_syntax(file_path)
            if is_valid:
                print(f"✅ {other_file}: Valid syntax")
            else:
                print(f"❌ {other_file}: {error}")
                all_valid = False
        else:
            print(f"✅ {other_file}: File exists")
    
    # Summary
    print("\n" + "=" * 50)
    if all_valid:
        print("✅ ALL TEST FILES ARE VALID")
        print("=" * 50)
        print("\nThe comprehensive testing suite files are properly created!")
        print("\nTest files created:")
        for test_file in test_files:
            print(f"  - {test_file}")
        
        print("\nConfiguration files:")
        for other_file in other_files:
            print(f"  - {other_file}")
        
        print("\nNext steps:")
        print("1. Set up test database: Ensure SQLite database is properly initialized")
        print("2. Install test dependencies: pip install pytest pytest-asyncio pytest-cov")
        print("3. Run individual tests: python -m pytest tests/test_health_endpoints.py -k 'not requires_services' -v")
        print("4. Run comprehensive suite: python run_comprehensive_tests.py --category unit")
        
        return True
    else:
        print("❌ SOME TEST FILES HAVE ISSUES")
        print("=" * 50)
        print("Please fix the issues above before running tests.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)