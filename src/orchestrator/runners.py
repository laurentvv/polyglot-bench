"""
Language-specific runners for executing benchmark tests.
Each runner handles compilation (if needed) and execution for a specific language.
"""

import os
import sys
import subprocess
import tempfile
import time
import psutil
import shlex
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Any
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.config import BenchmarkConfig, LanguageConfig


class TestResult:
    """Test execution result with performance metrics."""
    def __init__(self, execution_time: float, memory_usage: int, cpu_usage: float,
                 output: str, error: str, success: bool, language: str, 
                 test_name: str, iteration: int):
        self.execution_time = execution_time
        self.memory_usage = memory_usage
        self.cpu_usage = cpu_usage
        self.output = output
        self.error = error
        self.success = success
        self.language = language
        self.test_name = test_name
        self.iteration = iteration
        self.timestamp = datetime.now()


class BaseLanguageRunner(ABC):
    """Abstract base class for language runners."""
    
    def __init__(self, language: str, config: LanguageConfig):
        self.language = language
        self.config = config
        self.binaries_dir = "binaries"
        os.makedirs(self.binaries_dir, exist_ok=True)
    
    @abstractmethod
    def compile_test(self, source_file: str) -> Optional[str]:
        """Compile test if needed, return executable path."""
        pass
    
    @abstractmethod
    def execute_test(self, executable_file: str, input_data: str, 
                    test_name: str, iteration: int) -> TestResult:
        """Execute test and collect performance metrics."""
        pass
    
    def _run_command(self, command: List[str], input_data: str = "", 
                    timeout: int = None) -> subprocess.CompletedProcess:
        """Run a command with timeout and input data."""
        timeout = timeout or self.config.timeout
        
        try:
            # For Windows, ensure proper shell handling
            shell = False
            if os.name == 'nt' and (command[0] in ['npx', 'npm', 'node', 'tsc'] or command[0].endswith('.cmd')):
                shell = True
            
            result = subprocess.run(
                command,
                input=input_data,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                shell=shell,
                cwd=os.getcwd()  # Explicitly set working directory
            )
            return result
        except subprocess.TimeoutExpired as e:
            return subprocess.CompletedProcess(
                args=command,
                returncode=-1,
                stdout="",
                stderr=f"Timeout after {timeout}s"
            )
        except FileNotFoundError as e:
            return subprocess.CompletedProcess(
                args=command,
                returncode=-1,
                stdout="",
                stderr=f"Command not found: {command[0]} - {str(e)}"
            )
        except Exception as e:
            return subprocess.CompletedProcess(
                args=command,
                returncode=-1,
                stdout="",
                stderr=str(e)
            )
    
    def _monitor_process_metrics(self, process: subprocess.Popen, 
                               duration: float) -> Dict[str, float]:
        """Monitor process metrics during execution."""
        try:
            psutil_process = psutil.Process(process.pid)
            initial_memory = psutil_process.memory_info().rss
            peak_memory = initial_memory
            cpu_samples = []
            
            start_time = time.time()
            sample_interval = 0.1  # 100ms intervals
            
            while time.time() - start_time < duration and process.poll() is None:
                try:
                    memory_info = psutil_process.memory_info()
                    peak_memory = max(peak_memory, memory_info.rss)
                    
                    cpu_percent = psutil_process.cpu_percent()
                    if cpu_percent > 0:  # Valid CPU reading
                        cpu_samples.append(cpu_percent)
                    
                    time.sleep(sample_interval)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
            
            avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0
            
            return {
                'peak_memory': peak_memory - initial_memory,
                'avg_cpu': avg_cpu
            }
        except Exception:
            return {'peak_memory': 0, 'avg_cpu': 0.0}


class PythonRunner(BaseLanguageRunner):
    """Runner for Python tests."""
    
    def compile_test(self, source_file: str) -> Optional[str]:
        """Python doesn't need compilation, return source file."""
        if os.path.exists(source_file):
            return source_file
        return None
    
    def execute_test(self, executable_file: str, input_data: str, 
                    test_name: str, iteration: int) -> TestResult:
        """Execute Python test."""
        # Use the same Python interpreter that's running the orchestrator
        import sys
        command = [sys.executable, executable_file]
        if input_data:  # input_data is file path for Python tests
            command.append(input_data)
        
        start_time = time.perf_counter()
        start_memory = 0
        
        try:
            # For Python tests, we don't need stdin input
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=self.config.timeout)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            
            # For Python, get basic memory info
            memory_usage = len(stdout.encode()) + len(stderr.encode())  # Rough estimate
            
            return TestResult(
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=0.0,  # CPU monitoring requires more complex setup
                output=stdout,
                error=stderr,
                success=process.returncode == 0,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                execution_time=self.config.timeout,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Timeout after {self.config.timeout}s",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
        except Exception as e:
            return TestResult(
                execution_time=0.0,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=str(e),
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )


class RustRunner(BaseLanguageRunner):
    """Runner for Rust tests with Cargo dependency management."""
    
    def __init__(self, language: str, config: LanguageConfig):
        super().__init__(language, config)
        self.temp_dirs = []  # Track temporary directories for cleanup
    
    def _analyze_rust_dependencies(self, source_file: str) -> List[str]:
        """Analyze Rust source file for external crate dependencies."""
        dependencies = []
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for common external crate usage
            if 'use rand::' in content or 'rand::' in content:
                dependencies.append('rand = "0.8"')
            if 'use serde::' in content or 'serde::' in content:
                dependencies.append('serde = { version = "1.0", features = ["derive"] }')
            if 'use serde_json::' in content or 'serde_json::' in content:
                dependencies.append('serde_json = "1.0"')
            if 'use regex::' in content or 'regex::' in content:
                dependencies.append('regex = "1.0"')
            if 'use reqwest::' in content or 'reqwest::' in content:
                dependencies.append('reqwest = { version = "0.11", features = ["blocking", "json"] }')
            if 'use clap::' in content or 'clap::' in content:
                dependencies.append('clap = { version = "4.0", features = ["derive"] }')
            if 'use flate2::' in content or 'flate2::' in content:
                dependencies.append('flate2 = "1.0"')
            if 'use tokio::' in content or 'tokio::' in content:
                dependencies.append('tokio = { version = "1.0", features = ["full"] }')
            if 'use tempfile::' in content or 'tempfile::' in content:
                dependencies.append('tempfile = "3.0"')
            
        except Exception as e:
            print(f"    Warning: Could not analyze dependencies in {source_file}: {e}")
        
        return dependencies
    
    def _create_cargo_project(self, source_file: str, dependencies: List[str]) -> str:
        """Create a temporary Cargo project for compilation."""
        import tempfile
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='benchmark_rust_')
        self.temp_dirs.append(temp_dir)
        
        # Create Cargo.toml
        cargo_toml_content = f"""[package]
name = "benchmark_test"
version = "0.1.0"
edition = "2021"

[dependencies]
"""
        
        # Add dependencies
        if dependencies:
            for dep in dependencies:
                cargo_toml_content += dep + "\n"
        
        # Add optimization profile
        cargo_toml_content += """
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
debug = false
"""
        
        cargo_toml_path = os.path.join(temp_dir, 'Cargo.toml')
        with open(cargo_toml_path, 'w', encoding='utf-8') as f:
            f.write(cargo_toml_content)
        
        # Create src directory and copy source file as main.rs
        src_dir = os.path.join(temp_dir, 'src')
        os.makedirs(src_dir, exist_ok=True)
        
        main_rs_path = os.path.join(src_dir, 'main.rs')
        import shutil
        shutil.copy2(source_file, main_rs_path)
        
        return temp_dir
    
    def _compile_with_cargo(self, cargo_dir: str, base_name: str = None) -> Optional[str]:
        """Compile Rust project using Cargo."""
        # Get the source file name for the output binary
        if not base_name:
            source_files = [f for f in os.listdir(os.path.join(cargo_dir, 'src')) if f.endswith('.rs')]
            if not source_files:
                print(f"    Rust compilation failed: No source file found")
                return None
            
            base_name = os.path.splitext(source_files[0])[0]
            if base_name == 'main':
                # Try to extract from temp directory name
                temp_name = os.path.basename(cargo_dir)
                if temp_name.startswith('benchmark_rust_'):
                    base_name = temp_name.replace('benchmark_rust_', '') or 'test'
                else:
                    base_name = 'test'
        
        # Change to cargo directory for compilation
        original_cwd = os.getcwd()
        
        try:
            os.chdir(cargo_dir)
            
            # Run cargo build --release
            result = self._run_command(['cargo', 'build', '--release'], timeout=120)
            
            if result.returncode == 0:
                # Find the compiled binary
                target_dir = os.path.join(cargo_dir, 'target', 'release')
                
                # Look for the binary (name should be "benchmark_test")
                binary_name = 'benchmark_test'
                if os.name == 'nt':  # Windows
                    binary_name += '.exe'
                
                binary_path = os.path.join(target_dir, binary_name)
                
                if os.path.exists(binary_path):
                    # Define final output path relative to original working directory
                    output_file = os.path.join(original_cwd, self.binaries_dir, f"{base_name}_rust")
                    if os.name == 'nt':
                        output_file += '.exe'
                    
                    # Ensure binaries directory exists
                    os.makedirs(os.path.join(original_cwd, self.binaries_dir), exist_ok=True)
                    
                    # Copy binary
                    import shutil
                    shutil.copy2(binary_path, output_file)
                    
                    # Verify the copy was successful
                    if os.path.exists(output_file):
                        return output_file
                    else:
                        print(f"    Rust compilation: Failed to copy binary to {output_file}")
                        return None
                else:
                    print(f"    Rust compilation succeeded but binary not found at {binary_path}")
                    return None
            else:
                print(f"    Rust compilation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"    Rust compilation error: {e}")
            return None
        finally:
            os.chdir(original_cwd)
    
    def compile_test(self, source_file: str) -> Optional[str]:
        """Compile Rust source using Cargo with dependency management."""
        if not os.path.exists(source_file):
            return None
        
        # Check if Cargo is available
        import shutil
        if not shutil.which('cargo'):
            print(f"    Rust compilation failed: Cargo not found. Install Rust toolchain from https://rustup.rs")
            return None
        
        # Extract base name for the output binary
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        
        # Analyze dependencies
        dependencies = self._analyze_rust_dependencies(source_file)
        
        # Create Cargo project
        cargo_dir = self._create_cargo_project(source_file, dependencies)
        
        try:
            # Compile with Cargo
            result_binary = self._compile_with_cargo(cargo_dir, base_name)
            
            return result_binary
        finally:
            # Always cleanup temporary directory
            self._cleanup_temp_dir(cargo_dir)
    
    def _cleanup_temp_dir(self, temp_dir: str):
        """Clean up temporary directory."""
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if temp_dir in self.temp_dirs:
                self.temp_dirs.remove(temp_dir)
        except Exception as e:
            print(f"    Warning: Could not clean up temporary directory {temp_dir}: {e}")
    
    def execute_test(self, executable_file: str, input_data: str, 
                    test_name: str, iteration: int) -> TestResult:
        """Execute compiled Rust binary."""
        if not os.path.exists(executable_file):
            return TestResult(
                execution_time=0.0,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Executable not found: {executable_file}",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
        
        # Check if binary is executable
        if not os.access(executable_file, os.X_OK):
            return TestResult(
                execution_time=0.0,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Binary not executable: {executable_file}",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
        
        command = [executable_file]
        if input_data:  # input_data is now file path
            command.append(input_data)
        
        start_time = time.perf_counter()
        
        try:
            # Skip the preliminary test for network operations that may take longer
            # Just run the actual test directly
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=self.config.timeout)  # Removed input=input_data since file path is passed as arg
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            
            # Get binary size as a proxy for memory efficiency
            binary_size = os.path.getsize(executable_file)
            
            return TestResult(
                execution_time=execution_time,
                memory_usage=binary_size,  # Using binary size as memory metric
                cpu_usage=0.0,
                output=stdout,
                error=stderr,
                success=process.returncode == 0,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                execution_time=self.config.timeout,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Timeout after {self.config.timeout}s",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
        except Exception as e:
            return TestResult(
                execution_time=0.0,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Execution error: {str(e)}",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )


class GoRunner(BaseLanguageRunner):
    """Runner for Go tests with module management."""
    
    def __init__(self, language: str, config: LanguageConfig):
        super().__init__(language, config)
        self.temp_dirs = []  # Track temporary directories for cleanup
    
    def _analyze_go_imports(self, source_file: str) -> List[str]:
        """Analyze Go source file for external imports."""
        imports = []
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for import statements
            import re
            
            # Find import blocks
            import_blocks = re.findall(r'import\s*\((.*?)\)', content, re.DOTALL)
            single_imports = re.findall(r'import\s+"([^"]+)"', content)
            
            all_imports = single_imports
            for block in import_blocks:
                block_imports = re.findall(r'"([^"]+)"', block)
                all_imports.extend(block_imports)
            
            # Filter for external packages (not standard library)
            external_imports = []
            standard_packages = {'fmt', 'math', 'os', 'time', 'strings', 'sort', 'strconv', 'math/rand'}
            
            for imp in all_imports:
                if '.' in imp or '/' in imp:  # Likely external package
                    if not any(imp.startswith(std) for std in standard_packages):
                        external_imports.append(imp)
            
            return external_imports
            
        except Exception as e:
            print(f"    Warning: Could not analyze imports in {source_file}: {e}")
        
        return []
    
    def _setup_go_module(self, source_file: str, imports: List[str]) -> str:
        """Set up a temporary Go module for compilation."""
        import tempfile
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='benchmark_go_')
        self.temp_dirs.append(temp_dir)
        
        # Copy source file - rename if it ends with _test.go
        import shutil
        base_name = os.path.basename(source_file)
        if base_name.endswith('_test.go'):
            # Rename to avoid Go thinking it's a test file
            new_name = base_name.replace('_test.go', '_benchmark.go')
        else:
            new_name = base_name
            
        go_file_path = os.path.join(temp_dir, new_name)
        shutil.copy2(source_file, go_file_path)
        
        # Create go.mod - always create one for proper module support
        go_mod_content = """module benchmark_test

go 1.19
"""
        go_mod_path = os.path.join(temp_dir, 'go.mod')
        with open(go_mod_path, 'w', encoding='utf-8') as f:
            f.write(go_mod_content)
        
        return temp_dir
    
    def _compile_with_modules(self, module_dir: str) -> Optional[str]:
        """Compile Go source with proper module context."""
        original_cwd = os.getcwd()
        
        try:
            os.chdir(module_dir)
            
            # Find the Go source file
            go_files = [f for f in os.listdir('.') if f.endswith('.go') and not f.endswith('_test.go')]
            if not go_files:
                # Fallback: look for any .go files including renamed ones
                go_files = [f for f in os.listdir('.') if f.endswith('.go')]
                if not go_files:
                    print(f"    Go compilation failed: No Go source file found in {module_dir}")
                    return None
            
            source_file = go_files[0]
            base_name = os.path.splitext(source_file)[0]
            # Remove _benchmark suffix if present to get original test name
            if base_name.endswith('_benchmark'):
                base_name = base_name.replace('_benchmark', '_test')
            
            # Initialize module if go.mod exists
            if os.path.exists('go.mod'):
                # Run go mod tidy to resolve dependencies
                tidy_result = self._run_command(['go', 'mod', 'tidy'], timeout=60)
                if tidy_result.returncode != 0:
                    print(f"    Go mod tidy failed: {tidy_result.stderr}")
                    # Continue anyway, might still compile
            
            # Generate output path relative to original working directory
            output_file = os.path.join(original_cwd, self.binaries_dir, f"{base_name}_go")
            if os.name == 'nt':  # Windows
                output_file += '.exe'
            
            # Ensure binaries directory exists
            os.makedirs(os.path.join(original_cwd, self.binaries_dir), exist_ok=True)
            
            # Compile with go build - handle renamed files properly
            compile_cmd = ['go', 'build', '-ldflags', '-s -w', '-o', output_file, source_file]
            
            result = self._run_command(compile_cmd, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_file):
                return output_file
            else:
                error_msg = result.stderr or result.stdout or "Unknown compilation error"
                print(f"    Go compilation failed: {error_msg}")
                return None
                
        except Exception as e:
            print(f"    Go compilation error: {e}")
            return None
        finally:
            os.chdir(original_cwd)
    
    def compile_test(self, source_file: str) -> Optional[str]:
        """Compile Go source with module management."""
        if not os.path.exists(source_file):
            return None
        
        # Check if Go is available
        import shutil
        if not shutil.which('go'):
            print(f"    Go compilation failed: Go compiler not found. Install Go from https://golang.org")
            return None
        
        # Analyze imports
        imports = self._analyze_go_imports(source_file)
        
        # Setup Go module
        module_dir = self._setup_go_module(source_file, imports)
        
        # Compile with modules
        result_binary = self._compile_with_modules(module_dir)
        
        # Cleanup temporary directory
        self._cleanup_temp_dir(module_dir)
        
        return result_binary
    
    def _cleanup_temp_dir(self, temp_dir: str):
        """Clean up temporary directory."""
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if temp_dir in self.temp_dirs:
                self.temp_dirs.remove(temp_dir)
        except Exception as e:
            print(f"    Warning: Could not clean up temporary directory {temp_dir}: {e}")
    
    def execute_test(self, executable_file: str, input_data: str, 
                    test_name: str, iteration: int) -> TestResult:
        """Execute compiled Go binary."""
        if not os.path.exists(executable_file):
            return TestResult(
                execution_time=0.0,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Executable not found: {executable_file}",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
        
        # Check if binary is executable
        if not os.access(executable_file, os.X_OK):
            return TestResult(
                execution_time=0.0,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Binary not executable: {executable_file}",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
        
        command = [executable_file]
        if input_data:  # input_data is now file path
            # Ensure proper path format for the current OS
            normalized_path = os.path.normpath(input_data)
            command.append(normalized_path)
        
        start_time = time.perf_counter()
        
        try:
            # For Windows, ensure proper shell handling for binaries
            shell = False
            if os.name == 'nt':
                shell = True
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=shell
            )
            
            stdout, stderr = process.communicate(timeout=self.config.timeout)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            
            # Get binary size
            binary_size = os.path.getsize(executable_file)
            
            # Log execution details for debugging
            if process.returncode != 0:
                print(f"    Go execution failed with return code {process.returncode}")
                print(f"    Command: {' '.join(command)}")
                print(f"    Stdout: {stdout[:200]}..." if len(stdout) > 200 else f"    Stdout: {stdout}")
                print(f"    Stderr: {stderr[:200]}..." if len(stderr) > 200 else f"    Stderr: {stderr}")
            
            return TestResult(
                execution_time=execution_time,
                memory_usage=binary_size,
                cpu_usage=0.0,
                output=stdout,
                error=stderr,
                success=process.returncode == 0,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                execution_time=self.config.timeout,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Timeout after {self.config.timeout}s",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
        except Exception as e:
            return TestResult(
                execution_time=0.0,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Execution error: {str(e)}",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )


class TypeScriptRunner(BaseLanguageRunner):
    """Runner for TypeScript tests."""
    
    def __init__(self, language: str, config: LanguageConfig):
        super().__init__(language, config)
        self.tsc_available = self._check_tsc_availability()
    
    def _check_tsc_availability(self) -> str:
        """Check which TypeScript compilation method is available."""
        import shutil
        
        # Check for global tsc installation
        if shutil.which('tsc'):
            try:
                result = subprocess.run(
                    ['tsc', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return 'global_tsc'
            except Exception:
                pass
        
        # Check for npx availability
        if shutil.which('npx'):
            try:
                result = subprocess.run(
                    ['npx', 'tsc', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                if result.returncode == 0:
                    return 'npx_tsc'
            except Exception:
                pass
        
        # Check for local node_modules TypeScript
        if os.path.exists('node_modules/.bin/tsc'):
            try:
                tsc_path = os.path.join('node_modules', '.bin', 'tsc')
                if os.name == 'nt':  # Windows
                    tsc_path += '.cmd'
                result = subprocess.run(
                    [tsc_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return 'local_tsc'
            except Exception:
                pass
        
        return 'none'
    
    def compile_test(self, source_file: str) -> Optional[str]:
        """Compile TypeScript to JavaScript with multiple fallback methods."""
        if not os.path.exists(source_file):
            return None
        
        if self.tsc_available == 'none':
            print(f"    TypeScript compilation failed: No TypeScript compiler found")
            print(f"    Please install TypeScript using one of these methods:")
            print(f"      1. Global: npm install -g typescript")
            print(f"      2. Local: npm install typescript")
            print(f"      3. Via npx: Ensure Node.js is installed")
            return None
        
        # Generate output directory
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        output_dir = os.path.join(self.binaries_dir, f"{base_name}_ts")
        os.makedirs(output_dir, exist_ok=True)
        
        # Try compilation with available method
        js_file = None
        if self.tsc_available == 'global_tsc':
            js_file = self._compile_with_global_tsc(source_file, output_dir, base_name)
        elif self.tsc_available == 'npx_tsc':
            js_file = self._compile_with_npx_tsc(source_file, output_dir, base_name)
        elif self.tsc_available == 'local_tsc':
            js_file = self._compile_with_local_tsc(source_file, output_dir, base_name)
        
        if js_file and os.path.exists(js_file):
            return js_file
        else:
            return None
    
    def _compile_with_global_tsc(self, source_file: str, output_dir: str, base_name: str) -> Optional[str]:
        """Compile using global tsc command."""
        js_file = os.path.join(output_dir, f"{base_name}.js")
        
        # Change to project directory to ensure @types/node is available
        original_cwd = os.getcwd()
        
        try:
            # Use more specific TypeScript compilation flags
            compile_cmd = [
                'tsc', source_file,
                '--outDir', output_dir,
                '--target', 'ES2020',
                '--module', 'commonjs',
                '--strict',
                '--noEmitOnError',
                '--moduleResolution', 'node'
            ]
            
            result = self._run_command(compile_cmd)
            
            if result.returncode == 0 and os.path.exists(js_file):
                return js_file
            else:
                print(f"    TypeScript compilation failed: {result.stderr}")
                return None
        finally:
            os.chdir(original_cwd)
    
    def _compile_with_npx_tsc(self, source_file: str, output_dir: str, base_name: str) -> Optional[str]:
        """Compile using npx tsc command."""
        js_file = os.path.join(output_dir, f"{base_name}.js")
        
        # Change to project directory to ensure @types/node is available
        original_cwd = os.getcwd()
        
        try:
            # Use npx to run TypeScript compiler
            compile_cmd = [
                'npx', 'tsc', source_file,
                '--outDir', output_dir,
                '--target', 'ES2020',
                '--module', 'commonjs',
                '--strict',
                '--noEmitOnError',
                '--moduleResolution', 'node'
            ]
            
            result = self._run_command(compile_cmd, timeout=60)
            
            if result.returncode == 0 and os.path.exists(js_file):
                return js_file
            else:
                print(f"    TypeScript compilation failed: {result.stderr}")
                return None
        finally:
            os.chdir(original_cwd)
    
    def _compile_with_local_tsc(self, source_file: str, output_dir: str, base_name: str) -> Optional[str]:
        """Compile using local node_modules tsc command."""
        js_file = os.path.join(output_dir, f"{base_name}.js")
        
        # Change to project directory to ensure @types/node is available
        original_cwd = os.getcwd()
        
        try:
            # Use local TypeScript compiler
            tsc_path = os.path.join('node_modules', '.bin', 'tsc')
            if os.name == 'nt':  # Windows
                tsc_path += '.cmd'
            
            compile_cmd = [
                tsc_path, source_file,
                '--outDir', output_dir,
                '--target', 'ES2020',
                '--module', 'commonjs',
                '--strict',
                '--noEmitOnError',
                '--moduleResolution', 'node'
            ]
            
            result = self._run_command(compile_cmd, timeout=60)
            
            if result.returncode == 0 and os.path.exists(js_file):
                return js_file
            else:
                print(f"    TypeScript compilation failed: {result.stderr}")
                return None
        finally:
            os.chdir(original_cwd)
    
    def execute_test(self, executable_file: str, input_data: str, 
                    test_name: str, iteration: int) -> TestResult:
        """Execute compiled JavaScript via Node.js."""
        if not os.path.exists(executable_file):
            return TestResult(
                execution_time=0.0,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error="JavaScript file not found",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
        
        command = [self.config.executable, executable_file]
        command.extend(self.config.runtime_args)
        if input_data:  # input_data is now file path
            command.append(input_data)
        
        start_time = time.perf_counter()
        
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=self.config.timeout)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            
            # Get file size
            file_size = os.path.getsize(executable_file)
            
            return TestResult(
                execution_time=execution_time,
                memory_usage=file_size,
                cpu_usage=0.0,
                output=stdout,
                error=stderr,
                success=process.returncode == 0,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                execution_time=self.config.timeout,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=f"Timeout after {self.config.timeout}s",
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )
        except Exception as e:
            return TestResult(
                execution_time=0.0,
                memory_usage=0,
                cpu_usage=0.0,
                output="",
                error=str(e),
                success=False,
                language=self.language,
                test_name=test_name,
                iteration=iteration
            )


def create_language_runners(config: BenchmarkConfig, 
                          target_languages: List[str]) -> Dict[str, BaseLanguageRunner]:
    """Factory function to create language runners."""
    runners = {}
    
    runner_classes = {
        'python': PythonRunner,
        'rust': RustRunner,
        'go': GoRunner,
        'typescript': TypeScriptRunner
    }
    
    for language in target_languages:
        lang_config = config.get_language_config(language)
        if not lang_config:
            continue
        
        runner_class = runner_classes.get(language)
        if runner_class:
            runners[language] = runner_class(language, lang_config)
    
    return runners


if __name__ == "__main__":
    # Test runner creation
    from utils.config import BenchmarkConfig
    
    try:
        config = BenchmarkConfig()
        runners = create_language_runners(config, ['python', 'rust', 'go', 'typescript'])
        print(f"Created {len(runners)} runners: {list(runners.keys())}")
        
        # Test Python runner if available
        if 'python' in runners:
            python_runner = runners['python']
            print(f"Python runner: {python_runner.language}")
    except Exception as e:
        print(f"Runner creation failed: {e}")