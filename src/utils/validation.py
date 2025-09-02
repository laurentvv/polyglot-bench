"""
Environment validation for language runtimes.
Checks if required compilers and interpreters are available.
"""

import os
import sys
import subprocess
import shutil
import socket
import urllib.request
import urllib.error
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.config import BenchmarkConfig, LanguageConfig


class EnvironmentValidator:
    """Validates language runtime environments."""
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.validation_cache: Dict[str, bool] = {}
        self.version_cache: Dict[str, str] = {}
    
    def validate_all_languages(self) -> Dict[str, bool]:
        """Validate all configured languages."""
        results = {}
        
        for language in self.config.get_enabled_languages():
            results[language] = self.validate_language(language)
        
        return results
    
    def validate_language(self, language: str) -> bool:
        """Validate a specific language environment."""
        if language in self.validation_cache:
            return self.validation_cache[language]
        
        lang_config = self.config.get_language_config(language)
        if not lang_config:
            self.validation_cache[language] = False
            return False
        
        # Check if executable exists
        if not self._check_executable_exists(lang_config.executable):
            self.validation_cache[language] = False
            return False
        
        # Check if executable works
        if not self._check_executable_works(language, lang_config):
            self.validation_cache[language] = False
            return False
        
        # For compiled languages, check compilation tools
        if lang_config.compile_required:
            if not self._check_compilation_tools(language, lang_config):
                self.validation_cache[language] = False
                return False
        
        self.validation_cache[language] = True
        return True
    
    def get_language_version(self, language: str) -> str:
        """Get version string for a language."""
        if language in self.version_cache:
            return self.version_cache[language]
        
        lang_config = self.config.get_language_config(language)
        if not lang_config:
            return "Unknown"
        
        try:
            result = subprocess.run(
                [lang_config.executable, lang_config.version_check],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract version from output
                version = self._extract_version(language, result.stdout + result.stderr)
                self.version_cache[language] = version
                return version
            else:
                return "Error getting version"
                
        except Exception as e:
            return f"Error: {e}"
    
    def get_validation_report(self) -> Dict[str, Dict[str, str]]:
        """Get detailed validation report for all languages."""
        report = {}
        
        for language in self.config.get_enabled_languages():
            lang_config = self.config.get_language_config(language)
            
            report[language] = {
                'executable': lang_config.executable,
                'executable_found': self._check_executable_exists(lang_config.executable),
                'version': self.get_language_version(language),
                'compile_required': lang_config.compile_required,
                'validation_status': 'Valid' if self.validate_language(language) else 'Invalid'
            }
            
            if lang_config.compile_required:
                report[language]['compile_cmd'] = lang_config.compile_cmd or 'Not configured'
        
        return report
    
    def _check_executable_exists(self, executable: str) -> bool:
        """Check if an executable exists in PATH."""
        return shutil.which(executable) is not None
    
    def _check_executable_works(self, language: str, lang_config: LanguageConfig) -> bool:
        """Check if executable actually works."""
        try:
            result = subprocess.run(
                [lang_config.executable, lang_config.version_check],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_compilation_tools(self, language: str, lang_config: LanguageConfig) -> bool:
        """Check if compilation tools are available."""
        if not lang_config.compile_cmd:
            return False
        
        # Extract the compiler command (first word)
        compiler = lang_config.compile_cmd.split()[0]
        
        # Special handling for TypeScript
        if language == 'typescript' and compiler == 'tsc':
            # Check if TypeScript compiler is available globally
            if self._check_executable_exists('tsc'):
                return True
            # Check if npx is available as fallback
            elif self._check_executable_exists('npx'):
                # Test if TypeScript can be run via npx
                try:
                    result = subprocess.run(
                        ['npx', 'tsc', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    return result.returncode == 0
                except Exception:
                    return False
            return False
        
        # Special handling for Rust - check for Cargo
        if language == 'rust' and compiler == 'rustc':
            # Ensure Cargo is also available for dependency management
            return self._check_executable_exists('rustc') and self._check_executable_exists('cargo')
        
        return self._check_executable_exists(compiler)
    
    def _extract_version(self, language: str, version_output: str) -> str:
        """Extract version number from version command output."""
        lines = version_output.strip().split('\\n')
        
        if language == 'python':
            for line in lines:
                if 'Python' in line:
                    return line.strip()
        
        elif language == 'rust':
            for line in lines:
                if 'rustc' in line:
                    return line.strip()
        
        elif language == 'go':
            for line in lines:
                if 'go version' in line:
                    return line.strip()
        
        elif language == 'typescript':
            # Node.js version for TypeScript
            for line in lines:
                if 'v' in line and '.' in line:
                    return f"Node.js {line.strip()}"
        
        # Fallback: return first non-empty line
        for line in lines:
            if line.strip():
                return line.strip()
        
        return "Version unknown"
    
    def suggest_installation(self, language: str) -> List[str]:
        """Suggest installation commands for missing languages."""
        suggestions = {
            'python': [
                "Install Python 3.8+ from https://python.org",
                "Or use your package manager:",
                "  Ubuntu/Debian: sudo apt install python3",
                "  macOS: brew install python3",
                "  Windows: Download from python.org or use winget install Python.Python.3"
            ],
            'rust': [
                "Install Rust from https://rustup.rs",
                "Run: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh",
                "Or on Windows: Download from https://rustup.rs and run the installer",
                "Verify installation: rustc --version && cargo --version"
            ],
            'go': [
                "Install Go from https://golang.org/dl/",
                "Or use your package manager:",
                "  Ubuntu/Debian: sudo apt install golang-go",
                "  macOS: brew install go",
                "  Windows: Download from golang.org or use winget install GoLang.Go",
                "Verify installation: go version"
            ],
            'typescript': [
                "Install Node.js from https://nodejs.org (required for TypeScript)",
                "Then install TypeScript using one of these methods:",
                "  1. Global: npm install -g typescript",
                "  2. Local: npm install typescript (in project directory)",
                "  3. Via npx: npx tsc --version (to test)",
                "Verification commands:",
                "  - node --version",
                "  - tsc --version (if installed globally)",
                "  - npx tsc --version (if using npx)",
                "Package manager options:",
                "  Ubuntu/Debian: sudo apt install nodejs npm && npm install -g typescript",
                "  macOS: brew install node && npm install -g typescript",
                "  Windows: Download from nodejs.org or use winget install OpenJS.NodeJS"
            ]
        }
        
        return suggestions.get(language, [f"Please install {language} runtime"])
    
    def comprehensive_diagnostic(self) -> Dict[str, Any]:
        """Run comprehensive diagnostic checks and return detailed report."""
        diagnostic_report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'platform': os.name,
                'python_version': sys.version,
            },
            'language_status': {},
            'compilation_status': {},
            'recommendations': []
        }
        
        for language in self.config.get_enabled_languages():
            lang_config = self.config.get_language_config(language)
            if not lang_config:
                continue
                
            # Basic validation
            is_valid = self.validate_language(language)
            version = self.get_language_version(language)
            
            diagnostic_report['language_status'][language] = {
                'valid': is_valid,
                'version': version,
                'executable': lang_config.executable,
                'executable_found': self._check_executable_exists(lang_config.executable),
                'compile_required': lang_config.compile_required
            }
            
            # Compilation tools check
            if lang_config.compile_required:
                compile_available = self._check_compilation_tools(language, lang_config)
                diagnostic_report['compilation_status'][language] = {
                    'available': compile_available,
                    'compile_cmd': lang_config.compile_cmd,
                }
                
                # Special TypeScript diagnostics
                if language == 'typescript':
                    diagnostic_report['compilation_status'][language].update({
                        'global_tsc': self._check_executable_exists('tsc'),
                        'npx_available': self._check_executable_exists('npx'),
                        'local_tsc': os.path.exists('node_modules/.bin/tsc'),
                        'node_version': self._get_node_version()
                    })
            
            # Add recommendations for failed validations
            if not is_valid:
                diagnostic_report['recommendations'].extend(
                    self.suggest_installation(language)
                )
        
        return diagnostic_report
    
    def _get_node_version(self) -> str:
        """Get Node.js version if available."""
        try:
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "Not found"
    
    def check_dependencies(self) -> Dict[str, List[str]]:
        """Check for additional dependencies that might be needed."""
        dependencies = {}
        
        # Check for Python packages
        if self.validate_language('python'):
            python_deps = self._check_python_dependencies()
            if python_deps:
                dependencies['python'] = python_deps
        
        return dependencies
    
    def _check_python_dependencies(self) -> List[str]:
        """Check if required Python packages are available."""
        required_packages = ['psutil', 'pandas', 'numpy']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        return missing_packages
    
    def validate_network_connectivity(self) -> Dict[str, Any]:
        """Validate network connectivity for network tests."""
        network_status = {
            'internet_connectivity': False,
            'dns_resolution': False,
            'http_access': False,
            'ping_capability': False,
            'test_endpoints': []
        }
        
        # Test basic internet connectivity
        network_status['internet_connectivity'] = self._test_internet_connectivity()
        
        # Test DNS resolution
        network_status['dns_resolution'] = self._test_dns_resolution()
        
        # Test HTTP access
        network_status['http_access'] = self._test_http_access()
        
        # Test ping capability
        network_status['ping_capability'] = self._test_ping_capability()
        
        # Test specific endpoints
        test_urls = [
            'https://httpbin.org/get',
            'https://jsonplaceholder.typicode.com/posts/1',
            'https://api.github.com/zen'
        ]
        
        for url in test_urls:
            status = self._test_endpoint(url)
            network_status['test_endpoints'].append({
                'url': url,
                'accessible': status['accessible'],
                'response_time': status['response_time'],
                'error': status.get('error')
            })
        
        return network_status
    
    def _test_internet_connectivity(self) -> bool:
        """Test basic internet connectivity."""
        try:
            # Try to connect to a reliable host
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False
    
    def _test_dns_resolution(self) -> bool:
        """Test DNS resolution capability."""
        try:
            socket.gethostbyname('google.com')
            return True
        except socket.gaierror:
            return False
    
    def _test_http_access(self) -> bool:
        """Test HTTP/HTTPS access capability."""
        try:
            with urllib.request.urlopen('https://httpbin.org/get', timeout=10) as response:
                return response.status == 200
        except (urllib.error.URLError, socket.timeout):
            return False
    
    def _test_ping_capability(self) -> bool:
        """Test if ping command is available."""
        ping_cmd = 'ping' if os.name == 'nt' else 'ping'
        
        try:
            # Test with a single ping to a reliable host
            cmd = [ping_cmd, '-c', '1', '8.8.8.8'] if os.name != 'nt' else [ping_cmd, '-n', '1', '8.8.8.8']
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _test_endpoint(self, url: str) -> Dict[str, Any]:
        """Test accessibility of a specific endpoint."""
        import time
        
        try:
            start_time = time.time()
            with urllib.request.urlopen(url, timeout=10) as response:
                response_time = time.time() - start_time
                return {
                    'accessible': True,
                    'response_time': round(response_time * 1000, 2),  # Convert to ms
                    'status_code': response.status
                }
        except Exception as e:
            return {
                'accessible': False,
                'response_time': None,
                'error': str(e)
            }
    
    def validate_network_requirements(self, test_suite: str) -> bool:
        """Validate network requirements for a specific test suite."""
        if test_suite != 'network_operations':
            return True  # Non-network tests don't need network validation
        
        network_status = self.validate_network_connectivity()
        
        # For network tests, we need basic connectivity and HTTP access
        required_capabilities = [
            network_status['internet_connectivity'],
            network_status['dns_resolution'],
            network_status['http_access']
        ]
        
        return all(required_capabilities)


def validate_environment_interactive():
    """Interactive environment validation."""
    print(" Interactive Environment Validation")
    print("=" * 50)
    
    try:
        config = BenchmarkConfig()
        validator = EnvironmentValidator(config)
        
        print("\\nChecking language environments...")
        validation_results = validator.validate_all_languages()
        
        all_valid = True
        for language, is_valid in validation_results.items():
            status = "" if is_valid else ""
            version = validator.get_language_version(language) if is_valid else "Not available"
            print(f"  {language}: {status} {version}")
            
            if not is_valid:
                all_valid = False
                print("    Installation suggestions:")
                suggestions = validator.suggest_installation(language)
                for suggestion in suggestions:
                    print(f"    {suggestion}")
                print()
        
        # Check dependencies
        deps = validator.check_dependencies()
        if deps:
            print("\\n Dependency Check:")
            for language, missing_deps in deps.items():
                if missing_deps:
                    print(f"  {language}: Missing packages: {', '.join(missing_deps)}")
                    print(f"    Install with: pip install {' '.join(missing_deps)}")
        
        # Check network connectivity for network tests
        print("\\n Network Connectivity Check:")
        network_status = validator.validate_network_connectivity()
        
        connectivity_items = [
            ("Internet connectivity", network_status['internet_connectivity']),
            ("DNS resolution", network_status['dns_resolution']),
            ("HTTP access", network_status['http_access']),
            ("Ping capability", network_status['ping_capability'])
        ]
        
        for item_name, status in connectivity_items:
            status_icon = "" if status else ""
            print(f"  {item_name}: {status_icon}")
        
        if network_status['test_endpoints']:
            print("  Test endpoints:")
            for endpoint in network_status['test_endpoints']:
                status_icon = "" if endpoint['accessible'] else ""
                if endpoint['accessible']:
                    print(f"    {endpoint['url']}: {status_icon} ({endpoint['response_time']}ms)")
                else:
                    print(f"    {endpoint['url']}: {status_icon} ({endpoint.get('error', 'Unknown error')})")
        
        if all_valid:
            print("\\n All environments are ready for benchmarking!")
            return True
        else:
            print("\\n  Some environments need attention before running benchmarks.")
            return False
            
    except Exception as e:
        print(f"\\n Validation failed: {e}")
        return False


if __name__ == "__main__":
    # Run interactive validation
    validate_environment_interactive()