#!/usr/bin/env python3
"""
Performance comparison script for DNS lookup implementations.
"""

import json
import time
import subprocess
import sys
import os

def run_performance_test(implementation_name, script_path, config_path):
    """Run a performance test for a specific implementation."""
    print(f"Testing {implementation_name} implementation...")
    
    try:
        # Determine the command to run based on the implementation
        if implementation_name == "Python":
            cmd = [sys.executable, script_path, config_path]
        elif implementation_name == "Go":
            # For Go, we need to run "go run" on the .go file
            cmd = ["go", "run", script_path, config_path]
        elif implementation_name == "Rust":
            # For Rust, we need to compile and run
            binary_path = script_path.replace(".rs", "")
            # Compile the Rust program first
            compile_result = subprocess.run(
                ["rustc", script_path, "-o", binary_path],
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                print(f"  Compilation error: {compile_result.stderr}")
                return {
                    "implementation": implementation_name,
                    "error": f"Compilation failed: {compile_result.stderr}"
                }
            cmd = [binary_path, config_path]
        elif implementation_name == "TypeScript":
            # For TypeScript, we need to run with node
            cmd = ["node", script_path, config_path]
        else:
            print(f"  Error: Unknown implementation {implementation_name}")
            return {
                "implementation": implementation_name,
                "error": f"Unknown implementation {implementation_name}"
            }
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )
        execution_time = time.time() - start_time
        
        # Clean up Rust binary if it exists
        if implementation_name == "Rust":
            try:
                os.remove(binary_path)
            except:
                pass
        
        if result.returncode == 0:
            # Parse the JSON output to get detailed metrics
            output = json.loads(result.stdout)
            total_time = output.get("total_execution_time", execution_time)
            
            print(f"  Execution time: {total_time:.2f} seconds")
            print(f"  Successful resolutions: {output['summary']['successful_resolutions']}")
            print(f"  Failed resolutions: {output['summary']['failed_resolutions']}")
            print(f"  Avg resolution time: {output['summary']['avg_resolution_time']:.2f}ms")
            
            return {
                "implementation": implementation_name,
                "execution_time": total_time,
                "successful_resolutions": output["summary"]["successful_resolutions"],
                "failed_resolutions": output["summary"]["failed_resolutions"],
                "avg_resolution_time": output["summary"]["avg_resolution_time"]
            }
        else:
            print(f"  Error: {result.stderr}")
            return {
                "implementation": implementation_name,
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        print(f"  Error: Test timed out after 60 seconds")
        return {
            "implementation": implementation_name,
            "error": "Timeout"
        }
    except Exception as e:
        print(f"  Error: {str(e)}")
        return {
            "implementation": implementation_name,
            "error": str(e)
        }

def main():
    """Main function to run performance comparisons."""
    # Define paths
    config_path = os.path.join(os.path.dirname(__file__), "input.json")
    
    # Test implementations
    results = []
    
    # Test Python implementation
    python_script = os.path.join(os.path.dirname(__file__), "dns_lookup.py")
    result = run_performance_test("Python", python_script, config_path)
    results.append(result)
    
    # Test Go implementation
    go_script = os.path.join(os.path.dirname(__file__), "dns_lookup.go")
    result = run_performance_test("Go", go_script, config_path)
    results.append(result)
    
    # Test Rust implementation
    rust_script = os.path.join(os.path.dirname(__file__), "dns_lookup.rs")
    result = run_performance_test("Rust", rust_script, config_path)
    results.append(result)
    
    # Test TypeScript implementation
    ts_script = os.path.join(os.path.dirname(__file__), "dns_lookup.ts")
    result = run_performance_test("TypeScript", ts_script, config_path)
    results.append(result)
    
    # Print summary
    print("\n" + "="*50)
    print("PERFORMANCE COMPARISON SUMMARY")
    print("="*50)
    
    # Sort results by execution time
    valid_results = [r for r in results if "error" not in r]
    valid_results.sort(key=lambda x: x["execution_time"])
    
    for result in valid_results:
        print(f"{result['implementation']}: {result['execution_time']:.2f}s")
        print(f"  Successful resolutions: {result['successful_resolutions']}")
        print(f"  Failed resolutions: {result['failed_resolutions']}")
        print(f"  Avg resolution time: {result['avg_resolution_time']:.2f}ms")
    
    # Print errors
    error_results = [r for r in results if "error" in r]
    if error_results:
        print("\n" + "="*50)
        print("ERRORS")
        print("="*50)
        for result in error_results:
            print(f"{result['implementation']}: {result['error']}")

if __name__ == "__main__":
    main()