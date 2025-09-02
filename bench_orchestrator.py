#!/usr/bin/env python3
"""
Multi-Language Performance Benchmark Tool

Main orchestrator script that coordinates benchmark execution across
Python, Rust, Go, and TypeScript implementations.

Usage:
    python bench_orchestrator.py run [options]
    python bench_orchestrator.py validate
    python bench_orchestrator.py list [--tests|--languages]
"""

import os
import sys
import argparse
import time
from typing import List, Optional

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from orchestrator.core import BenchmarkOrchestrator
    from utils.config import BenchmarkConfig
    from utils.validation import EnvironmentValidator
except ImportError as e:
    print(f" Import error: {e}")
    print("Please ensure you're running from the project root directory.")
    sys.exit(1)


def print_banner():
    """Print tool banner."""
    banner = """
+==============================================================+
|               Multi-Language Performance Benchmark           |
|                                                              |
|           Compare Python * Rust * Go * TypeScript            |
+==============================================================+
    """
    print(banner)


def command_run(args) -> int:
    """Execute benchmark runs."""
    try:
        print("[*] Initializing benchmark orchestrator...")
        
        # Create orchestrator
        orchestrator = BenchmarkOrchestrator(args.config)
        
        # Configure execution parameters
        if args.languages:
            orchestrator.set_target_languages(args.languages)
        
        if args.tests:
            orchestrator.set_target_tests(args.tests)
        
        if args.iterations:
            orchestrator.set_iterations(args.iterations)
        
        print(f"[*] Configuration:")
        print(f"  Languages: {', '.join(orchestrator.target_languages)}")
        print(f"  Tests: {len(orchestrator.target_tests)} tests")
        print(f"  Iterations: {orchestrator.iterations} per test")
        print()
        
        # Execute benchmark suite
        performance_summary = orchestrator.execute_benchmark_suite()
        
        # Generate reports
        output_formats = [args.output] if args.output != 'all' else ['json', 'html', 'csv']
        orchestrator.generate_reports(output_formats)
        
        # Print summary
        print_execution_summary(performance_summary)
        
        # Cleanup if requested
        orchestrator.cleanup()
        
        print(f"\n[OK] Benchmark completed successfully!")
        print(f"[*] Results saved in: ./results/")
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n[!] Benchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[X] Benchmark failed: {e}")
        return 1


def command_validate(args) -> int:
    """Validate language environments."""
    try:
        print("[*] Validating language environments...")
        
        config = BenchmarkConfig(args.config)
        validator = EnvironmentValidator(config)
        
        languages_to_check = args.languages if args.languages else config.get_enabled_languages()
        
        validation_results = {}
        all_valid = True
        
        for language in languages_to_check:
            print(f"  Checking {language}...", end=" ")
            
            is_valid = validator.validate_language(language)
            validation_results[language] = is_valid
            
            if is_valid:
                version = validator.get_language_version(language)
                print(f"  [OK] {version}")
            else:
                print("[X] Not available")
                all_valid = False
        
        if all_valid:
            print(f"\n[OK] All environments validated successfully!")
            return 0
        else:
            failed_languages = [lang for lang, valid in validation_results.items() if not valid]
            print(f"\n[!] Validation failed for: {', '.join(failed_languages)}")
            print("Please install missing language runtimes.")
            return 1
            
    except Exception as e:
        print(f"\n[X] Validation failed: {e}")
        return 1


def command_list(args) -> int:
    """List available tests and languages."""
    try:
        config = BenchmarkConfig(args.config)
        
        if args.tests:
            print("[*] Available test suites:")
            for suite_name, suite_config in config.test_suites.items():
                status = "[OK] enabled" if suite_config.enabled else "[X] disabled"
                print(f"  {suite_name}: {len(suite_config.tests)} tests ({status})")
                for test in suite_config.tests:
                    print(f"    - {test}")
            
        elif args.languages:
            print("[*] Available languages:")
            for lang_name, lang_config in config.languages.items():
                print(f"  {lang_name}:")
                print(f"    Executable: {lang_config.executable}")
                print(f"    File extension: {lang_config.file_extension}")
                print(f"    Compilation required: {lang_config.compile_required}")
                
        else:
            # Show both
            print("[*] Available test suites:")
            all_tests = config.get_all_tests()
            enabled_suites = config.get_enabled_test_suites()
            
            print(f"  Total tests: {len(all_tests)}")
            print(f"  Enabled suites: {', '.join(enabled_suites)}")
            
            print(f"\n Available languages:")
            languages = config.get_enabled_languages()
            print(f"  Languages: {', '.join(languages)}")
        
        return 0
        
    except Exception as e:
        print(f" List failed: {e}")
        return 1


def print_execution_summary(performance_summary):
    """Print execution summary to terminal."""
    print(f"\n BENCHMARK SUMMARY")
    print("=" * 60)
    
    print(f"Benchmark ID: {performance_summary.benchmark_id}")
    print(f"Execution time: {performance_summary.execution_time:.2f}s")
    print(f"Total tests: {performance_summary.total_tests}")
    print(f"Total languages: {performance_summary.total_languages}")
    print(f"Total executions: {performance_summary.total_executions}")
    
    if performance_summary.overall_rankings.by_overall:
        print(f"\n[*] OVERALL PERFORMANCE RANKING:")
        for i, (language, score) in enumerate(performance_summary.overall_rankings.by_overall[:5], 1):
            print(f"  {i}. {language}: {score:.2f}")
    
    if performance_summary.results:
        print(f"\n TEST RESULTS:")
        for test_name, analysis in performance_summary.results.items():
            fastest = analysis.fastest_language
            most_efficient = analysis.most_memory_efficient
            most_reliable = analysis.most_reliable
            
            print(f"  {test_name}:")
            print(f"    Fastest: {fastest}")
            print(f"    Most memory efficient: {most_efficient}")
            print(f"    Most reliable: {most_reliable}")


def create_sample_tests():
    """Create sample test files to demonstrate the tool."""
    print(" Creating sample test files...")
    
    # Sample Fibonacci test
    fibonacci_tests = {
        'python': '''#!/usr/bin/env python3
import sys

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

if __name__ == "__main__":
    n = 30  # Default test value
    result = fibonacci(n)
    print(f"fibonacci({n}) = {result}")
''',
        'rust': '''fn fibonacci(n: u32) -> u64 {
    if n <= 1 {
        return n as u64;
    }
    fibonacci(n - 1) + fibonacci(n - 2)
}

fn main() {
    let n = 30;
    let result = fibonacci(n);
    println!("fibonacci({}) = {}", n, result);
}
''',
        'go': '''package main

import "fmt"

func fibonacci(n int) int {
    if n <= 1 {
        return n
    }
    return fibonacci(n-1) + fibonacci(n-2)
}

func main() {
    n := 30
    result := fibonacci(n)
    fmt.Printf("fibonacci(%d) = %d\\n", n, result)
}
''',
        'typescript': '''function fibonacci(n: number): number {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

const n = 30;
const result = fibonacci(n);
console.log(`fibonacci(${n}) = ${result}`);
'''
    }
    
    # Create test directories and files
    extensions = {'python': '.py', 'rust': '.rs', 'go': '.go', 'typescript': '.ts'}
    
    for language, code in fibonacci_tests.items():
        test_dir = f"tests/algorithms/fibonacci"
        os.makedirs(test_dir, exist_ok=True)
        
        file_path = os.path.join(test_dir, f"fibonacci{extensions[language]}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        print(f"  Created: {file_path}")
    
    # Create input file
    input_file = "tests/algorithms/fibonacci/input.json"
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write('{"n": 30}')
    
    print("  Created: {input_file}")
    print("[OK] Sample tests created!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Multi-Language Performance Benchmark Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s run                          # Run all benchmarks
  %(prog)s run -l python,rust           # Test only Python and Rust
  %(prog)s run -t fibonacci,quicksort   # Run specific tests
  %(prog)s run --iterations 20          # Run 20 iterations per test
  %(prog)s validate                     # Check language environments
  %(prog)s list --tests                 # List available tests
        """
    )
    
    # Global options
    parser.add_argument('--config', '-c', default='bench.config.json',
                       help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Execute benchmark suite')
    run_parser.add_argument('--languages', '-l', 
                           choices=['python', 'rust', 'go', 'typescript'],
                           nargs='+', default=None,
                           help='Languages to benchmark')
    run_parser.add_argument('--tests', '-t', nargs='+', default=None,
                           help='Specific tests to run')
    run_parser.add_argument('--iterations', '-i', type=int, default=None,
                           help='Number of iterations per test')
    run_parser.add_argument('--output', '-o',
                           choices=['json', 'html', 'csv', 'all'], default='all',
                           help='Output format')
    run_parser.add_argument('--timeout', type=int, default=None,
                           help='Timeout per test in seconds')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate language environments')
    validate_parser.add_argument('--languages', '-l',
                                choices=['python', 'rust', 'go', 'typescript'],
                                nargs='+', default=None,
                                help='Languages to validate')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available tests and languages')
    list_parser.add_argument('--tests', action='store_true',
                            help='List available test suites')
    list_parser.add_argument('--languages', action='store_true',
                            help='List available languages')
    
    # Setup command (hidden)
    setup_parser = subparsers.add_parser('setup', help='Create sample test files')
    
    args = parser.parse_args()
    
    # Show banner
    print_banner()
    
    # Handle no command
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        if args.command == 'run':
            return command_run(args)
        elif args.command == 'validate':
            return command_validate(args)
        elif args.command == 'list':
            return command_list(args)
        elif args.command == 'setup':
            create_sample_tests()
            return 0
        else:
            print(f"[X] Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n[!] Operation interrupted by user")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)