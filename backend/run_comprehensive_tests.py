#!/usr/bin/env python3
"""
Comprehensive test runner for the AI PKM Tool testing suite.

This script runs all test categories with proper configuration and reporting:
- Unit tests for health check endpoints
- Integration tests for document processing pipeline
- Error handling and recovery scenario tests
- Service dependency failure tests
- Load tests for concurrent document processing

Usage:
    python run_comprehensive_tests.py [options]

Options:
    --category CATEGORY    Run specific test category (unit, integration, error, dependencies, load, all)
    --verbose             Enable verbose output
    --coverage            Generate coverage report
    --html-report         Generate HTML test report
    --parallel            Run tests in parallel (requires pytest-xdist)
    --quick               Run quick tests only (skip slow tests)
    --services            Run tests that require external services
    --benchmark           Run performance benchmarks
    --output-dir DIR      Directory for test outputs (default: test_results)

Requirements tested: 1.1, 1.3, 2.2, 2.4, 5.5, 6.5
"""

import os
import sys
import argparse
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveTestRunner:
    """Comprehensive test runner for the AI PKM Tool."""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.test_results = {}
        self.start_time = None
        self.end_time = None
    
    def run_test_category(self, category: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific test category."""
        logger.info(f"Running {category} tests...")
        
        # Define test file mappings
        test_files = {
            "unit": ["tests/test_health_endpoints.py"],
            "integration": ["tests/test_document_processing_integration.py"],
            "error": ["tests/test_error_handling.py"],
            "dependencies": ["tests/test_service_dependencies.py"],
            "load": ["tests/test_load_testing.py"],
            "all": [
                "tests/test_health_endpoints.py",
                "tests/test_document_processing_integration.py",
                "tests/test_error_handling.py",
                "tests/test_service_dependencies.py",
                "tests/test_load_testing.py"
            ]
        }
        
        if category not in test_files:
            raise ValueError(f"Unknown test category: {category}")
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add test files
        cmd.extend(test_files[category])
        
        # Add options
        if options.get("verbose"):
            cmd.append("-v")
        
        if options.get("coverage"):
            cmd.extend(["--cov=app", "--cov-report=term-missing"])
            if options.get("html_report"):
                cmd.append(f"--cov-report=html:{self.output_dir}/coverage_html")
        
        if options.get("parallel"):
            cmd.extend(["-n", "auto"])
        
        if options.get("quick"):
            cmd.extend(["-m", "not slow"])
        
        if not options.get("services"):
            cmd.extend(["-m", "not requires_services"])
        
        if options.get("benchmark"):
            cmd.extend(["-m", "benchmark"])
        
        # Add output options
        cmd.extend([
            f"--junit-xml={self.output_dir}/{category}_results.xml",
            f"--html={self.output_dir}/{category}_report.html",
            "--self-contained-html"
        ])
        
        # Run tests
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "category": category,
                "success": result.returncode == 0,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": " ".join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Test category {category} timed out after 30 minutes")
            return {
                "category": category,
                "success": False,
                "duration": 1800,
                "error": "Test execution timed out",
                "return_code": -1
            }
        
        except Exception as e:
            logger.error(f"Error running {category} tests: {e}")
            return {
                "category": category,
                "success": False,
                "duration": 0,
                "error": str(e),
                "return_code": -1
            }
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run system health checks before testing."""
        logger.info("Running pre-test health checks...")
        
        health_checks = {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "test_files_exist": self._check_test_files(),
            "dependencies_installed": self._check_dependencies(),
            "output_directory": str(self.output_dir.absolute())
        }
        
        return health_checks
    
    def _check_test_files(self) -> Dict[str, bool]:
        """Check if all test files exist."""
        test_files = [
            "tests/test_health_endpoints.py",
            "tests/test_document_processing_integration.py",
            "tests/test_error_handling.py",
            "tests/test_service_dependencies.py",
            "tests/test_load_testing.py",
            "tests/conftest.py"
        ]
        
        return {
            file: Path(file).exists()
            for file in test_files
        }
    
    def _check_dependencies(self) -> Dict[str, bool]:
        """Check if required dependencies are installed."""
        dependencies = ["pytest", "pytest-asyncio", "pytest-cov"]
        results = {}
        
        for dep in dependencies:
            try:
                subprocess.run(
                    [sys.executable, "-c", f"import {dep.replace('-', '_')}"],
                    check=True,
                    capture_output=True
                )
                results[dep] = True
            except subprocess.CalledProcessError:
                results[dep] = False
        
        return results
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive test summary report."""
        total_duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        
        # Calculate overall statistics
        total_categories = len(self.test_results)
        successful_categories = len([r for r in self.test_results.values() if r.get("success")])
        failed_categories = total_categories - successful_categories
        
        # Extract test counts from pytest output (if available)
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for result in self.test_results.values():
            if result.get("stdout"):
                # Parse pytest output for test counts
                stdout = result["stdout"]
                if "passed" in stdout:
                    # Simple parsing - could be improved
                    lines = stdout.split('\n')
                    for line in lines:
                        if "passed" in line and "failed" in line:
                            # Extract numbers from summary line
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "passed":
                                    try:
                                        passed_tests += int(parts[i-1])
                                    except (ValueError, IndexError):
                                        pass
                                elif part == "failed":
                                    try:
                                        failed_tests += int(parts[i-1])
                                    except (ValueError, IndexError):
                                        pass
        
        total_tests = passed_tests + failed_tests
        
        summary = {
            "execution_summary": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "total_duration": total_duration,
                "categories_run": total_categories,
                "successful_categories": successful_categories,
                "failed_categories": failed_categories
            },
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "category_results": self.test_results,
            "output_files": {
                "summary_report": str(self.output_dir / "test_summary.json"),
                "coverage_html": str(self.output_dir / "coverage_html" / "index.html"),
                "test_reports": [
                    str(self.output_dir / f"{cat}_report.html")
                    for cat in self.test_results.keys()
                ]
            },
            "requirements_coverage": {
                "1.1": "Document upload functionality - Tested in integration tests",
                "1.3": "Document processing pipeline - Tested in integration and load tests",
                "2.2": "Celery task processing - Tested in health checks and error handling",
                "2.4": "Error handling and recovery - Tested in error handling tests",
                "5.5": "AI processing performance - Tested in load tests",
                "6.5": "Knowledge graph performance - Tested in load tests",
                "7.1-7.5": "Service health checks - Tested in health endpoint tests",
                "8.4": "Health check endpoints - Tested in unit tests"
            }
        }
        
        return summary
    
    def save_summary_report(self, summary: Dict[str, Any]):
        """Save summary report to file."""
        summary_file = self.output_dir / "test_summary.json"
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Summary report saved to: {summary_file}")
        
        # Also create a human-readable summary
        readable_summary = self.output_dir / "test_summary.txt"
        
        with open(readable_summary, 'w') as f:
            f.write("AI PKM Tool - Comprehensive Test Suite Results\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Execution Time: {summary['execution_summary']['total_duration']:.2f} seconds\n")
            f.write(f"Categories Run: {summary['execution_summary']['categories_run']}\n")
            f.write(f"Successful Categories: {summary['execution_summary']['successful_categories']}\n")
            f.write(f"Failed Categories: {summary['execution_summary']['failed_categories']}\n\n")
            
            f.write(f"Total Tests: {summary['test_summary']['total_tests']}\n")
            f.write(f"Passed Tests: {summary['test_summary']['passed_tests']}\n")
            f.write(f"Failed Tests: {summary['test_summary']['failed_tests']}\n")
            f.write(f"Success Rate: {summary['test_summary']['success_rate']:.1f}%\n\n")
            
            f.write("Category Results:\n")
            f.write("-" * 20 + "\n")
            for category, result in summary['category_results'].items():
                status = "✅ PASS" if result.get("success") else "❌ FAIL"
                duration = result.get("duration", 0)
                f.write(f"{status} {category.upper()}: {duration:.2f}s\n")
            
            f.write("\nRequirements Coverage:\n")
            f.write("-" * 20 + "\n")
            for req, description in summary['requirements_coverage'].items():
                f.write(f"{req}: {description}\n")
        
        logger.info(f"Human-readable summary saved to: {readable_summary}")
    
    def run_comprehensive_tests(self, categories: List[str], options: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        logger.info("Starting comprehensive test suite...")
        
        self.start_time = time.time()
        
        # Run health checks
        health_status = self.run_health_checks()
        logger.info("Pre-test health checks completed")
        
        # Check for missing test files
        missing_files = [f for f, exists in health_status["test_files_exist"].items() if not exists]
        if missing_files:
            logger.error(f"Missing test files: {missing_files}")
            return {"error": "Missing required test files", "missing_files": missing_files}
        
        # Check for missing dependencies
        missing_deps = [d for d, installed in health_status["dependencies_installed"].items() if not installed]
        if missing_deps:
            logger.error(f"Missing dependencies: {missing_deps}")
            return {"error": "Missing required dependencies", "missing_dependencies": missing_deps}
        
        # Run test categories
        for category in categories:
            logger.info(f"Starting {category} test category...")
            result = self.run_test_category(category, options)
            self.test_results[category] = result
            
            if result["success"]:
                logger.info(f"✅ {category} tests completed successfully in {result['duration']:.2f}s")
            else:
                logger.error(f"❌ {category} tests failed in {result['duration']:.2f}s")
                if options.get("verbose") and result.get("stderr"):
                    logger.error(f"Error output: {result['stderr']}")
        
        self.end_time = time.time()
        
        # Generate and save summary
        summary = self.generate_summary_report()
        self.save_summary_report(summary)
        
        logger.info("Comprehensive test suite completed")
        
        return summary


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for AI PKM Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_comprehensive_tests.py --category all --coverage --html-report
    python run_comprehensive_tests.py --category unit --verbose
    python run_comprehensive_tests.py --category load --benchmark
    python run_comprehensive_tests.py --category integration --services
        """
    )
    
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "error", "dependencies", "load", "all"],
        default="all",
        help="Test category to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only (skip slow tests)"
    )
    
    parser.add_argument(
        "--services",
        action="store_true",
        help="Run tests that require external services"
    )
    
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmarks"
    )
    
    parser.add_argument(
        "--output-dir",
        default="test_results",
        help="Directory for test outputs (default: test_results)"
    )
    
    args = parser.parse_args()
    
    # Prepare options
    options = {
        "verbose": args.verbose,
        "coverage": args.coverage,
        "html_report": args.html_report,
        "parallel": args.parallel,
        "quick": args.quick,
        "services": args.services,
        "benchmark": args.benchmark
    }
    
    # Determine categories to run
    if args.category == "all":
        categories = ["unit", "integration", "error", "dependencies", "load"]
    else:
        categories = [args.category]
    
    # Create test runner
    runner = ComprehensiveTestRunner(args.output_dir)
    
    try:
        # Run tests
        summary = runner.run_comprehensive_tests(categories, options)
        
        if "error" in summary:
            logger.error(f"Test execution failed: {summary['error']}")
            sys.exit(1)
        
        # Print final summary
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST SUITE SUMMARY")
        print("=" * 60)
        
        exec_summary = summary["execution_summary"]
        test_summary = summary["test_summary"]
        
        print(f"Total Duration: {exec_summary['total_duration']:.2f} seconds")
        print(f"Categories: {exec_summary['successful_categories']}/{exec_summary['categories_run']} successful")
        print(f"Tests: {test_summary['passed_tests']}/{test_summary['total_tests']} passed ({test_summary['success_rate']:.1f}%)")
        
        print("\nCategory Results:")
        for category, result in summary["category_results"].items():
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            print(f"  {status} {category.upper()}: {result.get('duration', 0):.2f}s")
        
        print(f"\nDetailed reports available in: {args.output_dir}/")
        print(f"Summary report: {args.output_dir}/test_summary.json")
        
        # Exit with appropriate code
        overall_success = exec_summary["failed_categories"] == 0
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        logger.info("Test execution interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()