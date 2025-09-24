#!/usr/bin/env python3
"""
Test Runner for Legal QA Project

This script provides a comprehensive test runner with various options for executing
unit tests across the Legal QA project. It supports running individual test modules,
generating coverage reports, and filtering tests by patterns.

Usage:
    python test_runner.py                    # Run all tests
    python test_runner.py --module test_get_legal_qa_urls  # Run specific module
    python test_runner.py --coverage         # Run with coverage report
    python test_runner.py --pattern "test_json"  # Run tests matching pattern
    python test_runner.py --verbose          # Run with verbose output
    python test_runner.py --failfast         # Stop on first failure
"""

import unittest
import sys
import os
import argparse
import time
from pathlib import Path
from typing import List, Optional
import importlib


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class TestRunner:
    """Enhanced test runner with reporting and filtering capabilities."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.available_modules = self._discover_test_modules()
        
        # Add project directories to Python path
        sys.path.insert(0, str(self.project_root))
        sys.path.insert(0, str(self.project_root / 'scripts'))
        
    def _discover_test_modules(self) -> List[str]:
        """Discover all test modules in the test directory."""
        modules = []
        for file_path in self.test_dir.glob('test_*.py'):
            if file_path.name != 'test_runner.py':
                module_name = file_path.stem
                modules.append(module_name)
        return sorted(modules)
    
    def _print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{title.center(60)}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*60}{Colors.END}")
    
    def _print_module_info(self, module_name: str):
        """Print information about a test module."""
        print(f"\n{Colors.BLUE}{Colors.BOLD}Running: {module_name}{Colors.END}")
        print(f"{Colors.BLUE}{'─' * 40}{Colors.END}")
    
    def _print_results(self, result: unittest.TestResult, duration: float):
        """Print test results summary."""
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
        passed = total_tests - failures - errors - skipped
        
        print(f"\n{Colors.BOLD}Test Results Summary:{Colors.END}")
        print(f"{'─' * 40}")
        print(f"Total Tests:  {Colors.CYAN}{total_tests}{Colors.END}")
        print(f"Passed:       {Colors.GREEN}{passed}{Colors.END}")
        print(f"Failed:       {Colors.RED}{failures}{Colors.END}")
        print(f"Errors:       {Colors.RED}{errors}{Colors.END}")
        print(f"Skipped:      {Colors.YELLOW}{skipped}{Colors.END}")
        print(f"Duration:     {Colors.MAGENTA}{duration:.2f}s{Colors.END}")
        
        # Overall status
        if failures == 0 and errors == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.END}")
            return True
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.END}")
            return False
    
    def _print_failure_details(self, result: unittest.TestResult):
        """Print detailed failure information."""
        if result.failures or result.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}Failure Details:{Colors.END}")
            print(f"{'═' * 60}")
            
            for test, traceback in result.failures:
                print(f"\n{Colors.RED}FAIL: {test}{Colors.END}")
                print(f"{Colors.YELLOW}{traceback}{Colors.END}")
            
            for test, traceback in result.errors:
                print(f"\n{Colors.RED}ERROR: {test}{Colors.END}")
                print(f"{Colors.YELLOW}{traceback}{Colors.END}")
    
    def run_single_module(self, module_name: str, verbosity: int = 1, 
                         failfast: bool = False) -> bool:
        """
        Run tests from a single module.
        
        Args:
            module_name: Name of the test module to run
            verbosity: Test output verbosity level
            failfast: Stop on first failure
            
        Returns:
            True if all tests passed, False otherwise
        """
        if module_name not in self.available_modules:
            print(f"{Colors.RED}Error: Module '{module_name}' not found{Colors.END}")
            print(f"Available modules: {', '.join(self.available_modules)}")
            return False
        
        self._print_module_info(module_name)
        
        try:
            # Import the test module
            test_module = importlib.import_module(module_name)
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            
            # Run tests
            runner = unittest.TextTestRunner(
                verbosity=verbosity,
                failfast=failfast,
                stream=sys.stdout
            )
            
            start_time = time.time()
            result = runner.run(suite)
            duration = time.time() - start_time
            
            # Print results
            success = self._print_results(result, duration)
            if not success:
                self._print_failure_details(result)
            
            return success
            
        except ImportError as e:
            print(f"{Colors.RED}Error importing module '{module_name}': {e}{Colors.END}")
            return False
        except Exception as e:
            print(f"{Colors.RED}Error running tests for '{module_name}': {e}{Colors.END}")
            return False
    
    def run_all_modules(self, verbosity: int = 1, failfast: bool = False) -> bool:
        """
        Run tests from all available modules.
        
        Args:
            verbosity: Test output verbosity level
            failfast: Stop on first failure
            
        Returns:
            True if all tests passed, False otherwise
        """
        self._print_header("Running All Test Modules")
        
        all_success = True
        total_duration = 0
        module_results = []
        
        for module_name in self.available_modules:
            print(f"\n{Colors.MAGENTA}[{self.available_modules.index(module_name) + 1}/{len(self.available_modules)}]{Colors.END}")
            
            start_time = time.time()
            success = self.run_single_module(module_name, verbosity, failfast)
            duration = time.time() - start_time
            
            total_duration += duration
            module_results.append((module_name, success, duration))
            
            if not success:
                all_success = False
                if failfast:
                    break
        
        # Print overall summary
        self._print_overall_summary(module_results, total_duration, all_success)
        
        return all_success
    
    def run_pattern_matching(self, pattern: str, verbosity: int = 1, 
                           failfast: bool = False) -> bool:
        """
        Run tests matching a specific pattern.
        
        Args:
            pattern: Pattern to match test names against
            verbosity: Test output verbosity level
            failfast: Stop on first failure
            
        Returns:
            True if all tests passed, False otherwise
        """
        self._print_header(f"Running Tests Matching Pattern: '{pattern}'")
        
        # Find matching modules
        matching_modules = [m for m in self.available_modules if pattern in m]
        
        if not matching_modules:
            print(f"{Colors.YELLOW}No modules found matching pattern '{pattern}'{Colors.END}")
            return True
        
        print(f"Found {len(matching_modules)} matching modules:")
        for module in matching_modules:
            print(f"  • {module}")
        
        all_success = True
        for module_name in matching_modules:
            success = self.run_single_module(module_name, verbosity, failfast)
            if not success:
                all_success = False
                if failfast:
                    break
        
        return all_success
    
    def _print_overall_summary(self, module_results: List[tuple], 
                             total_duration: float, all_success: bool):
        """Print overall test execution summary."""
        print(f"\n{Colors.BOLD}Overall Test Summary:{Colors.END}")
        print(f"{'═' * 60}")
        
        passed_count = sum(1 for _, success, _ in module_results if success)
        failed_count = len(module_results) - passed_count
        
        print(f"Total Modules:    {Colors.CYAN}{len(module_results)}{Colors.END}")
        print(f"Modules Passed:   {Colors.GREEN}{passed_count}{Colors.END}")
        print(f"Modules Failed:   {Colors.RED}{failed_count}{Colors.END}")
        print(f"Total Duration:   {Colors.MAGENTA}{total_duration:.2f}s{Colors.END}")
        
        # Module-by-module breakdown
        print(f"\n{Colors.BOLD}Module Results:{Colors.END}")
        for module_name, success, duration in module_results:
            status = f"{Colors.GREEN}✓{Colors.END}" if success else f"{Colors.RED}✗{Colors.END}"
            print(f"  {status} {module_name:<30} ({duration:.2f}s)")
        
        # Final status
        if all_success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL MODULES PASSED! 🎉{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME MODULES FAILED ❌{Colors.END}")
    
    def run_with_coverage(self, verbosity: int = 1) -> bool:
        """
        Run tests with coverage reporting.
        
        Args:
            verbosity: Test output verbosity level
            
        Returns:
            True if all tests passed, False otherwise
        """
        try:
            import coverage
        except ImportError:
            print(f"{Colors.RED}Coverage.py not installed. Install with: pip install coverage{Colors.END}")
            return False
        
        self._print_header("Running Tests with Coverage Analysis")
        
        # Initialize coverage
        cov = coverage.Coverage()
        cov.start()
        
        # Run all tests
        success = self.run_all_modules(verbosity)
        
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print(f"\n{Colors.BOLD}Coverage Report:{Colors.END}")
        print(f"{'─' * 40}")
        cov.report(show_missing=True)
        
        # Generate HTML report
        try:
            html_dir = self.test_dir / 'coverage_html'
            cov.html_report(directory=str(html_dir))
            print(f"\n{Colors.GREEN}HTML coverage report generated: {html_dir}/index.html{Colors.END}")
        except Exception as e:
            print(f"{Colors.YELLOW}Could not generate HTML report: {e}{Colors.END}")
        
        return success
    
    def list_modules(self):
        """List all available test modules."""
        print(f"{Colors.BOLD}Available Test Modules:{Colors.END}")
        print(f"{'─' * 40}")
        
        for i, module in enumerate(self.available_modules, 1):
            print(f"{Colors.CYAN}{i:2d}.{Colors.END} {module}")
        
        print(f"\nTotal: {Colors.GREEN}{len(self.available_modules)}{Colors.END} test modules")


def main():
    """Main function to handle command line arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Test Runner for Legal QA Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py                           # Run all tests
  python test_runner.py --module test_json_to_tables  # Run specific module
  python test_runner.py --coverage               # Run with coverage
  python test_runner.py --pattern "json"         # Run tests matching pattern
  python test_runner.py --verbose --failfast     # Verbose output, stop on first failure
  python test_runner.py --list                   # List available test modules
        """
    )
    
    parser.add_argument(
        '--module', '-m',
        help='Run tests from a specific module'
    )
    
    parser.add_argument(
        '--pattern', '-p',
        help='Run tests from modules matching the pattern'
    )
    
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Run tests with coverage analysis'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Run tests with verbose output'
    )
    
    parser.add_argument(
        '--failfast', '-f',
        action='store_true',
        help='Stop running tests on first failure'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available test modules'
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner()
    
    # Handle list command
    if args.list:
        runner.list_modules()
        return
    
    # Set verbosity level
    verbosity = 2 if args.verbose else 1
    
    # Run tests based on arguments
    success = True
    
    if args.coverage:
        success = runner.run_with_coverage(verbosity)
    elif args.module:
        success = runner.run_single_module(args.module, verbosity, args.failfast)
    elif args.pattern:
        success = runner.run_pattern_matching(args.pattern, verbosity, args.failfast)
    else:
        success = runner.run_all_modules(verbosity, args.failfast)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
