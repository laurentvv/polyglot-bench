#!/usr/bin/env python3
"""
Performance comparison script for CSV processing implementations.
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
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, script_path, config_path],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout
        )
        execution_time = time.time() - start_time
        
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
                "avg_read_time": output["summary"]["avg_read_time"],
                "avg_write_time": output["summary"]["avg_write_time"],
                "avg_filter_time": output["summary"]["avg_filter_time"],
                "avg_aggregate_time": output["summary"]["avg_aggregate_time"]
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
    
    # Test optimized Python implementation
    python_script = os.path.join(os.path.dirname(__file__), "csv_processing.py")
    result = run_performance_test("Python (Optimized)", python_script, config_path)
    results.append(result)
    
    # Print summary
    print("\n" + "="*50)
    print("PERFORMANCE COMPARISON SUMMARY")
    print("="*50)
    
    for result in results:
        if "error" in result:
            print(f"{result['implementation']}: ERROR - {result['error']}")
        else:
            print(f"{result['implementation']}: {result['execution_time']:.2f}s")
            print(f"  Read time: {result['avg_read_time']:.2f}ms")
            print(f"  Write time: {result['avg_write_time']:.2f}ms")
            print(f"  Filter time: {result['avg_filter_time']:.2f}ms")
            print(f"  Aggregate time: {result['avg_aggregate_time']:.2f}ms")

if __name__ == "__main__":
    main()