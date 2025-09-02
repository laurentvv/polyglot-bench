"""
Configuration management for the multi-language benchmark tool.
Handles loading, validation, and access to benchmark configuration.
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class LanguageConfig:
    """Configuration for a specific programming language."""
    executable: str
    version_check: str
    timeout: int
    file_extension: str
    compile_required: bool = False
    compile_cmd: Optional[str] = None
    binary_extension: Optional[str] = None
    runtime_args: List[str] = field(default_factory=list)


@dataclass
class TestSuiteConfig:
    """Configuration for a test suite category."""
    enabled: bool
    timeout: int
    iterations: int
    tests: List[str] = field(default_factory=list)
    requires_network: bool = False
    test_data_size: Optional[str] = None
    test_file_size: Optional[str] = None


@dataclass
class PerformanceConfig:
    """Performance measurement configuration."""
    iterations: int = 10
    warmup_runs: int = 2
    timeout_per_test: int = 120
    memory_sampling_interval: float = 0.1


@dataclass
class OutputConfig:
    """Output and reporting configuration."""
    format: str = "all"
    directory: str = "./results"
    timestamp: bool = True
    include_metadata: bool = True


@dataclass
class SystemConfig:
    """System monitoring configuration."""
    collect_system_info: bool = True
    monitor_resources: bool = True
    cleanup_binaries: bool = False


class BenchmarkConfig:
    """Main configuration manager for the benchmark tool."""
    
    def __init__(self, config_path: str = "bench.config.json"):
        self.config_path = config_path
        self.raw_config: Dict[str, Any] = {}
        self.languages: Dict[str, LanguageConfig] = {}
        self.test_suites: Dict[str, TestSuiteConfig] = {}
        self.performance: PerformanceConfig = PerformanceConfig()
        self.output: OutputConfig = OutputConfig()
        self.system: SystemConfig = SystemConfig()
        
        self.load_configuration()
    
    def load_configuration(self) -> None:
        """Load and parse the configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.raw_config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        
        self._parse_languages()
        self._parse_test_suites()
        self._parse_performance()
        self._parse_output()
        self._parse_system()
        
        self._validate_configuration()
    
    def _parse_languages(self) -> None:
        """Parse language configurations."""
        languages_config = self.raw_config.get('languages', {})
        
        for lang_name, lang_config in languages_config.items():
            self.languages[lang_name] = LanguageConfig(
                executable=lang_config.get('executable', ''),
                version_check=lang_config.get('version_check', '--version'),
                timeout=lang_config.get('timeout', 60),
                file_extension=lang_config.get('file_extension', ''),
                compile_required=lang_config.get('compile_required', False),
                compile_cmd=lang_config.get('compile_cmd'),
                binary_extension=lang_config.get('binary_extension', ''),
                runtime_args=lang_config.get('runtime_args', [])
            )
    
    def _parse_test_suites(self) -> None:
        """Parse test suite configurations."""
        suites_config = self.raw_config.get('test_suites', {})
        
        for suite_name, suite_config in suites_config.items():
            self.test_suites[suite_name] = TestSuiteConfig(
                enabled=suite_config.get('enabled', True),
                timeout=suite_config.get('timeout', 30),
                iterations=suite_config.get('iterations', 10),
                tests=suite_config.get('tests', []),
                requires_network=suite_config.get('requires_network', False),
                test_data_size=suite_config.get('test_data_size'),
                test_file_size=suite_config.get('test_file_size')
            )
    
    def _parse_performance(self) -> None:
        """Parse performance configuration."""
        perf_config = self.raw_config.get('performance', {})
        
        self.performance = PerformanceConfig(
            iterations=perf_config.get('iterations', 10),
            warmup_runs=perf_config.get('warmup_runs', 2),
            timeout_per_test=perf_config.get('timeout_per_test', 120),
            memory_sampling_interval=perf_config.get('memory_sampling_interval', 0.1)
        )
    
    def _parse_output(self) -> None:
        """Parse output configuration."""
        output_config = self.raw_config.get('output', {})
        
        self.output = OutputConfig(
            format=output_config.get('format', 'all'),
            directory=output_config.get('directory', './results'),
            timestamp=output_config.get('timestamp', True),
            include_metadata=output_config.get('include_metadata', True)
        )
    
    def _parse_system(self) -> None:
        """Parse system configuration."""
        system_config = self.raw_config.get('system', {})
        
        self.system = SystemConfig(
            collect_system_info=system_config.get('collect_system_info', True),
            monitor_resources=system_config.get('monitor_resources', True),
            cleanup_binaries=system_config.get('cleanup_binaries', False)
        )
    
    def _validate_configuration(self) -> None:
        """Validate the loaded configuration."""
        # Validate languages
        if not self.languages:
            raise ValueError("No languages configured")
        
        for lang_name, lang_config in self.languages.items():
            if not lang_config.executable:
                raise ValueError(f"No executable specified for language: {lang_name}")
            
            if lang_config.compile_required and not lang_config.compile_cmd:
                raise ValueError(f"Compile command required for language: {lang_name}")
        
        # Validate test suites
        if not any(suite.enabled for suite in self.test_suites.values()):
            raise ValueError("No test suites enabled")
        
        # Validate output directory
        try:
            os.makedirs(self.output.directory, exist_ok=True)
        except OSError as e:
            raise ValueError(f"Cannot create output directory: {e}")
    
    def get_enabled_languages(self) -> List[str]:
        """Get list of configured language names."""
        return list(self.languages.keys())
    
    def get_enabled_test_suites(self) -> List[str]:
        """Get list of enabled test suite names."""
        return [name for name, suite in self.test_suites.items() if suite.enabled]
    
    def get_language_config(self, language: str) -> Optional[LanguageConfig]:
        """Get configuration for a specific language."""
        return self.languages.get(language)
    
    def get_test_suite_config(self, suite_name: str) -> Optional[TestSuiteConfig]:
        """Get configuration for a specific test suite."""
        return self.test_suites.get(suite_name)
    
    def get_all_tests(self) -> List[str]:
        """Get all test names from enabled test suites."""
        all_tests = []
        for suite in self.test_suites.values():
            if suite.enabled:
                all_tests.extend(suite.tests)
        return list(set(all_tests))  # Remove duplicates
    
    def update_config(self, section: str, key: str, value: Any) -> None:
        """Update a configuration value and save to file."""
        if section not in self.raw_config:
            self.raw_config[section] = {}
        
        self.raw_config[section][key] = value
        
        # Save to file
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.raw_config, f, indent=2)
        
        # Reload configuration
        self.load_configuration()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        return {
            'languages': {name: {
                'executable': config.executable,
                'version_check': config.version_check,
                'timeout': config.timeout,
                'file_extension': config.file_extension,
                'compile_required': config.compile_required,
                'compile_cmd': config.compile_cmd,
                'binary_extension': config.binary_extension,
                'runtime_args': config.runtime_args
            } for name, config in self.languages.items()},
            'test_suites': {name: {
                'enabled': config.enabled,
                'timeout': config.timeout,
                'iterations': config.iterations,
                'tests': config.tests
            } for name, config in self.test_suites.items()},
            'performance': {
                'iterations': self.performance.iterations,
                'warmup_runs': self.performance.warmup_runs,
                'timeout_per_test': self.performance.timeout_per_test,
                'memory_sampling_interval': self.performance.memory_sampling_interval
            },
            'output': {
                'format': self.output.format,
                'directory': self.output.directory,
                'timestamp': self.output.timestamp,
                'include_metadata': self.output.include_metadata
            },
            'system': {
                'collect_system_info': self.system.collect_system_info,
                'monitor_resources': self.system.monitor_resources,
                'cleanup_binaries': self.system.cleanup_binaries
            }
        }


def load_config(config_path: str = "bench.config.json") -> BenchmarkConfig:
    """Convenience function to load configuration."""
    return BenchmarkConfig(config_path)


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        print("Configuration loaded successfully!")
        print(f"Languages: {config.get_enabled_languages()}")
        print(f"Test suites: {config.get_enabled_test_suites()}")
        print(f"All tests: {config.get_all_tests()}")
    except Exception as e:
        print(f"Configuration error: {e}")