#!/usr/bin/env python3
"""
Performance comparison script for JSON parsing implementations.
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
            timeout=120  # 2 minutes timeout
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
            print(f"  Successful tests: {output['summary']['successful_tests']}")
            print(f"  Failed tests: {output['summary']['failed_tests']}")
            
            return {
                "implementation": implementation_name,
                "execution_time": total_time,
                "successful_tests": output["summary"]["successful_tests"],
                "failed_tests": output["summary"]["failed_tests"],
                "avg_parse_time": output["summary"]["avg_parse_time"],
                "avg_stringify_time": output["summary"]["avg_stringify_time"],
                "avg_traverse_time": output["summary"]["avg_traverse_time"]
            }
        else:
            print(f"  Error: {result.stderr}")
            return {
                "implementation": implementation_name,
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        print(f"  Error: Test timed out after 120 seconds")
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
    python_script = os.path.join(os.path.dirname(__file__), "json_parsing.py")
    result = run_performance_test("Python", python_script, config_path)
    results.append(result)
    
    # Test Go implementation
    go_script = os.path.join(os.path.dirname(__file__), "json_parsing.go")
    result = run_performance_test("Go", go_script, config_path)
    results.append(result)
    
    # Test Rust implementation
    rust_script = os.path.join(os.path.dirname(__file__), "json_parsing.rs")
    result = run_performance_test("Rust", rust_script, config_path)
    results.append(result)
    
    # Test TypeScript implementation
    ts_script = os.path.join(os.path.dirname(__file__), "json_parsing.ts")
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
        print(f"  Parse time: {result['avg_parse_time']:.2f}ms")
        print(f"  Stringify time: {result['avg_stringify_time']:.2f}ms")
        print(f"  Traverse time: {result['avg_traverse_time']:.2f}ms")
        print(f"  Successful tests: {result['successful_tests']}")
    
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