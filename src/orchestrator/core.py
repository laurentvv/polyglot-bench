"""
Core orchestrator for the multi-language benchmark tool.
Coordinates test execution, metrics collection, and report generation.
"""

import os
import sys
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config import BenchmarkConfig, LanguageConfig, TestSuiteConfig


@dataclass
class TestResult:
    """Single test execution result."""
    execution_time: float
    memory_usage: int
    cpu_usage: float
    output: str
    error: str
    success: bool
    language: str
    test_name: str
    iteration: int
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LanguagePerformance:
    """Aggregated performance metrics for a language on a specific test."""
    avg_time: float
    min_time: float
    max_time: float
    std_time: float
    avg_memory: float
    peak_memory: int
    avg_cpu: float
    success_rate: float
    total_iterations: int


@dataclass
class TestAnalysis:
    """Analysis results for a specific test across all languages."""
    test_name: str
    language_performances: Dict[str, LanguagePerformance]
    fastest_language: str
    most_memory_efficient: str
    most_reliable: str


@dataclass
class PerformanceSummary:
    """Complete benchmark performance summary."""
    benchmark_id: str
    timestamp: datetime
    total_tests: int
    total_languages: int
    total_executions: int
    results: Dict[str, TestAnalysis]
    overall_rankings: Any  # Can be OverallRankings object
    execution_time: float
    system_info: Dict[str, Any]
    configuration: Dict[str, Any]
    summary_statistics: Dict[str, Any]
    language_versions: Dict[str, str] = field(default_factory=dict)


class BenchmarkOrchestrator:
    """Main orchestrator for multi-language performance benchmarks."""
    
    def __init__(self, config_path: str = "bench.config.json"):
        """Initialize the benchmark orchestrator."""
        self.config = BenchmarkConfig(config_path)
        self.benchmark_id = f"bench_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Execution state
        self.target_languages: List[str] = self.config.get_enabled_languages()
        self.target_tests: List[str] = self.config.get_all_tests()
        self.iterations: int = self.config.performance.iterations
        
        # Results storage
        self.raw_results: Dict[str, Dict[str, List[TestResult]]] = {}
        self.performance_summary: Optional[PerformanceSummary] = None
        
        # Runtime components (to be initialized)
        self.runners: Dict[str, Any] = {}
        self.metrics_collector: Optional[Any] = None
        self.results_compiler: Optional[Any] = None
        self.report_generator: Optional[Any] = None
        
        # State tracking
        self.execution_start_time: Optional[float] = None
        self.current_test: Optional[str] = None
        self.current_language: Optional[str] = None
        
        print(f" Benchmark Orchestrator initialized (ID: {self.benchmark_id})")
        print(f" Target languages: {', '.join(self.target_languages)}")
        print(f" Target tests: {len(self.target_tests)} tests")
    
    def set_target_languages(self, languages: List[str]) -> None:
        """Set specific languages to benchmark."""
        valid_languages = self.config.get_enabled_languages()
        invalid_languages = [lang for lang in languages if lang not in valid_languages]
        
        if invalid_languages:
            raise ValueError(f"Invalid languages: {invalid_languages}. "
                           f"Available: {valid_languages}")
        
        self.target_languages = languages
        print(f" Target languages set to: {', '.join(languages)}")
    
    def set_target_tests(self, tests: List[str]) -> None:
        """Set specific tests to run."""
        all_tests = self.config.get_all_tests()
        invalid_tests = [test for test in tests if test not in all_tests]
        
        if invalid_tests:
            raise ValueError(f"Invalid tests: {invalid_tests}. "
                           f"Available: {all_tests}")
        
        self.target_tests = tests
        print(f" Target tests set to: {', '.join(tests)}")
    
    def set_iterations(self, iterations: int) -> None:
        """Set number of iterations per test."""
        if iterations < 1:
            raise ValueError("Iterations must be at least 1")
        
        self.iterations = iterations
        print(f" Iterations set to: {iterations}")
    
    def validate_environments(self) -> Dict[str, str]:
        """
        Validate environments and return a dictionary of language versions.
        Raises EnvironmentError if validation fails.
        """
        from utils.validation import EnvironmentValidator
        
        validator = EnvironmentValidator(self.config)
        versions = {}
        failed_languages = []

        print(" Validating language environments...")
        
        for language in self.target_languages:
            print(f"  Checking {language}...", end="")
            if validator.validate_language(language):
                version = validator.get_language_version(language)
                versions[language] = version
                print(f" [OK] {version}")
            else:
                failed_languages.append(language)
                print(" [FAILED]")

        # Network validation (existing logic)
        network_tests = self._get_network_tests()
        if network_tests:
            print(" Validating network connectivity for network tests...")
            for test_suite in network_tests:
                if not validator.validate_network_requirements(test_suite):
                    print(f"  Warning: Network connectivity for {test_suite} might be limited.")

        if failed_languages:
            raise EnvironmentError(f"Environment validation failed for: {', '.join(failed_languages)}")
        
        print(" All environments validated successfully!")
        return versions
    
    def _get_network_tests(self) -> List[str]:
        """Get list of network-dependent test suites."""
        network_suites = []
        enabled_test_suites = self.config.get_enabled_test_suites()
        
        for suite_name, suite_config in self.config.test_suites.items():
            if hasattr(suite_config, 'requires_network') and suite_config.requires_network:
                if suite_name in enabled_test_suites:
                    network_suites.append(suite_name)
        return network_suites
    
    def initialize_components(self) -> None:
        """Initialize runtime components (runners, collectors, etc.)."""
        from orchestrator.runners import create_language_runners
        from orchestrator.metrics import MetricsCollector
        from orchestrator.results import ResultsCompiler
        from orchestrator.reports import ReportGenerator
        
        print(" Initializing runtime components...")
        
        # Initialize language runners
        self.runners = create_language_runners(self.config, self.target_languages)
        print(f"   Language runners: {len(self.runners)} initialized")
        
        # Initialize metrics collector
        self.metrics_collector = MetricsCollector(self.config.system)
        print("   Metrics collector initialized")
        
        # Initialize results compiler
        self.results_compiler = ResultsCompiler()
        print("   Results compiler initialized")
        
        # Initialize report generator
        self.report_generator = ReportGenerator(self.config.output)
        print("   Report generator initialized")
    
    def discover_tests(self) -> Dict[str, Dict[str, str]]:
        """Discover available test files for each language."""
        test_files = {}
        
        for test_name in self.target_tests:
            test_files[test_name] = {}
            
            for language in self.target_languages:
                lang_config = self.config.get_language_config(language)
                if not lang_config:
                    continue
                
                # Look for test file in expected location
                test_file = self._find_test_file(test_name, language, lang_config)
                if test_file:
                    test_files[test_name][language] = test_file
                else:
                    print(f"  Test file not found: {test_name}{lang_config.file_extension}")
        
        return test_files
    
    def _find_test_file(self, test_name: str, language: str, lang_config: LanguageConfig) -> Optional[str]:
        """Find test file for a specific test and language."""
        # Search in multiple possible locations
        search_paths = [
            f"tests/algorithms/{test_name}/{test_name}{lang_config.file_extension}",
            f"tests/data_structures/{test_name}/{test_name}{lang_config.file_extension}",
            f"tests/mathematical/{test_name}/{test_name}{lang_config.file_extension}",
            f"tests/io_operations/{test_name}/{test_name}{lang_config.file_extension}",
            f"tests/network_operations/{test_name}/{test_name}{lang_config.file_extension}",
            f"tests/compression_tests/{test_name}/{test_name}{lang_config.file_extension}",
            f"tests/system_tests/{test_name}/{test_name}{lang_config.file_extension}"
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def compile_tests(self, test_files: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """Compile tests for compiled languages."""
        compiled_files = {}
        
        print(" Compiling tests for compiled languages...")
        
        for test_name, language_files in test_files.items():
            compiled_files[test_name] = {}
            
            for language, source_file in language_files.items():
                runner = self.runners.get(language)
                if not runner:
                    continue
                
                print(f"  Compiling {test_name}.{language}...", end=" ")
                
                try:
                    compiled_file = runner.compile_test(source_file)
                    if compiled_file:
                        compiled_files[test_name][language] = compiled_file
                        print("")
                    else:
                        print("")
                        # For interpreted languages, use source file directly
                        compiled_files[test_name][language] = source_file
                except Exception as e:
                    print(f" ({e})")
        
        return compiled_files
    
    def execute_benchmark_suite(self) -> PerformanceSummary:
        """Execute the complete benchmark suite."""
        print(f"\n Starting Multi-Language Performance Benchmark")
        print(f" Benchmark ID: {self.benchmark_id}")
        print("=" * 60)
        
        self.execution_start_time = time.perf_counter()
        
        # Phase 1: Environment validation
        language_versions = self.validate_environments()
        
        # Phase 2: Component initialization
        self.initialize_components()
        
        # Phase 3: Test discovery
        print("\n Discovering test files...")
        test_files = self.discover_tests()
        
        if not test_files:
            raise ValueError("No test files found")
        
        print(f"   Found {len(test_files)} tests")
        
        # Phase 4: Compilation
        compiled_files = self.compile_tests(test_files)
        
        # Phase 5: Benchmark execution
        print(f"\n Executing benchmarks ({self.iterations} iterations each)...")
        self._execute_all_tests(compiled_files)
        
        # Phase 6: Results compilation
        print("\n Compiling results...")
        self.performance_summary = self.results_compiler.compile_results(
            raw_results=self.raw_results,
            benchmark_id=self.benchmark_id,
            execution_time=self._get_execution_time(),
            language_versions=language_versions
        )
        
        print(f" Benchmark suite completed in {self._get_execution_time():.2f}s")
        return self.performance_summary
    
    def _execute_all_tests(self, compiled_files: Dict[str, Dict[str, str]]) -> None:
        """Execute all tests across all languages."""
        total_executions = len(compiled_files) * len(self.target_languages) * self.iterations
        current_execution = 0
        
        for test_name, language_files in compiled_files.items():
            self.current_test = test_name
            print(f"\n   Running test: {test_name}")
            
            if test_name not in self.raw_results:
                self.raw_results[test_name] = {}
            
            for language in self.target_languages:
                self.current_language = language
                executable_file = language_files.get(language)
                
                if not executable_file:
                    print(f"      {language}: No executable found")
                    continue
                
                print(f"     {language}: ", end="")
                
                # Initialize results list for this test-language combination
                if language not in self.raw_results[test_name]:
                    self.raw_results[test_name][language] = []
                
                # Execute multiple iterations
                for iteration in range(self.iterations):
                    current_execution += 1
                    progress = (current_execution / total_executions) * 100
                    
                    try:
                        result = self._execute_single_test(
                            test_name, language, executable_file, iteration
                        )
                        self.raw_results[test_name][language].append(result)
                        
                        if iteration == 0:  # Print status after first iteration
                            print(f"[{progress:.1f}%] ", end="")
                    
                    except Exception as e:
                        # Create failed result
                        failed_result = TestResult(
                            execution_time=0.0,
                            memory_usage=0,
                            cpu_usage=0.0,
                            output="",
                            error=str(e),
                            success=False,
                            language=language,
                            test_name=test_name,
                            iteration=iteration
                        )
                        self.raw_results[test_name][language].append(failed_result)
                
                # Calculate and display summary for this language
                language_results = self.raw_results[test_name][language]
                successful_runs = [r for r in language_results if r.success]
                
                if successful_runs:
                    avg_time = sum(r.execution_time for r in successful_runs) / len(successful_runs)
                    print(f" ({len(successful_runs)}/{self.iterations} success, avg: {avg_time*1000:.2f}ms)")
                else:
                    print(f" (0/{self.iterations} success)")
    
    def _execute_single_test(self, test_name: str, language: str, 
                           executable_file: str, iteration: int) -> TestResult:
        """Execute a single test iteration."""
        runner = self.runners[language]
        
        # Load input data if available
        input_data = self._load_test_input(test_name)
        
        # Execute with metrics collection
        return runner.execute_test(executable_file, input_data, test_name, iteration)
    
    def _load_test_input(self, test_name: str) -> str:
        """Load input data for a test if available."""
        input_paths = [
            f"tests/algorithms/{test_name}/input.json",
            f"tests/data_structures/{test_name}/input.json",
            f"tests/mathematical/{test_name}/input.json",
            f"tests/io_operations/{test_name}/input.json",
            f"tests/network_operations/{test_name}/input.json",
            f"tests/compression_tests/{test_name}/input.json",
            f"tests/system_tests/{test_name}/input.json"
        ]
        
        for input_path in input_paths:
            if os.path.exists(input_path):
                return input_path  # Return file path, not content
        
        return ""  # No input data
    
    def _get_execution_time(self) -> float:
        """Get total execution time."""
        if self.execution_start_time:
            return time.perf_counter() - self.execution_start_time
        return 0.0
    
    def generate_reports(self, formats: List[str] = None) -> None:
        """Generate reports in specified formats."""
        if not self.performance_summary:
            raise ValueError("No benchmark results available. Run benchmark first.")
        
        if not self.report_generator:
            raise ValueError("Report generator not initialized")
        
        print("\n Generating reports...")
        self.report_generator.generate_all_reports(self.performance_summary, formats)
    
    def cleanup(self) -> None:
        """Clean up temporary files and resources."""
        if self.config.system.cleanup_binaries:
            print(" Cleaning up temporary files...")
            
            binaries_dir = "binaries"
            if os.path.exists(binaries_dir):
                import shutil
                shutil.rmtree(binaries_dir)
                print("   Cleaned up binaries directory")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        return {
            'benchmark_id': self.benchmark_id,
            'current_test': self.current_test,
            'current_language': self.current_language,
            'target_languages': self.target_languages,
            'target_tests': self.target_tests,
            'iterations': self.iterations,
            'execution_time': self._get_execution_time(),
            'results_available': self.performance_summary is not None
        }


def create_orchestrator(config_path: str = "bench.config.json") -> BenchmarkOrchestrator:
    """Factory function to create a benchmark orchestrator."""
    return BenchmarkOrchestrator(config_path)


if __name__ == "__main__":
    # Test orchestrator initialization
    try:
        orchestrator = create_orchestrator()
        print("Orchestrator created successfully!")
        status = orchestrator.get_status()
        print(f"Status: {status}")
    except Exception as e:
        print(f"Orchestrator initialization failed: {e}")