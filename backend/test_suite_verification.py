#!/usr/bin/env python3
"""
Test suite verification script.

This script verifies that the comprehensive testing suite is properly set up
and can run basic tests without requiring external services.

Usage:
    python test_suite_verification.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_test_files():
    """Check if all test files exist."""
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
    
    missing_files = []
    for file in test_files:
        full_path = script_dir / file
        if not full_path.exists():
            missing_files.append(file)
    
    return missing_files

def check_pytest_installation():
    """Check if pytest and required plugins are installed."""
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            return False, "pytest not installed"
        
        # Check for pytest-asyncio
        result = subprocess.run([sys.executable, "-c", "import pytest_asyncio"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            return False, "pytest-asyncio not installed"
        
        return True, "pytest and plugins are installed"
    
    except Exception as e:
        return False, f"Error checking pytest: {e}"

def run_basic_test():
    """Run a basic test to verify the test suite works."""
    try:
        # Change to backend directory for test execution
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # Run a simple test that doesn't require external services
        cmd = [
            sys.executable, "-m", "pytest", 
            "tests/test_health_endpoints.py::TestRedisHealthCheck::test_redis_healthy",
            "-v", "--tb=short"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Test execution timed out"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main verification function."""
    print("🧪 AI PKM Tool - Test Suite Verification")
    print("=" * 50)
    
    # Check 1: Test files exist
    print("\n1. Checking test files...")
    missing_files = check_test_files()
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False
    else:
        print("✅ All test files found")
    
    # Check 2: pytest installation
    print("\n2. Checking pytest installation...")
    pytest_ok, pytest_msg = check_pytest_installation()
    if not pytest_ok:
        print(f"❌ {pytest_msg}")
        print("Please install pytest and pytest-asyncio:")
        print("pip install pytest pytest-asyncio pytest-cov")
        return False
    else:
        print(f"✅ {pytest_msg}")
    
    # Check 3: Run basic test
    print("\n3. Running basic test...")
    test_result = run_basic_test()
    if test_result["success"]:
        print("✅ Basic test passed")
        print("Test output:")
        print(test_result["stdout"])
    else:
        print("❌ Basic test failed")
        if "error" in test_result:
            print(f"Error: {test_result['error']}")
        else:
            print("STDOUT:", test_result.get("stdout", ""))
            print("STDERR:", test_result.get("stderr", ""))
        return False
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ TEST SUITE VERIFICATION SUCCESSFUL")
    print("=" * 50)
    print("\nThe comprehensive testing suite is properly set up!")
    print("\nNext steps:")
    print("1. Run unit tests: python -m pytest tests/test_health_endpoints.py -v")
    print("2. Run integration tests: python -m pytest tests/test_document_processing_integration.py -v")
    print("3. Run all tests: python run_comprehensive_tests.py --category all")
    print("4. Run with coverage: python run_comprehensive_tests.py --category all --coverage")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)