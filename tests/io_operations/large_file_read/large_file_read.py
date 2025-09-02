#!/usr/bin/env python3
"""
Large file reading test implementation in Python.
Measures file I/O performance with different file sizes, buffer sizes, and read patterns.
"""

import json
import sys
import time
import os
import tempfile
import random
import string
from typing import Dict, List, Any


def generate_test_file(file_path: str, size_bytes: int) -> None:
    """Generate a test file with specified size."""
    print(f"Generating test file: {size_bytes} bytes...", file=sys.stderr)
    
    # Generate data in chunks to avoid memory issues
    chunk_size = 8192
    data_chunk = ''.join(random.choices(string.ascii_letters + string.digits + '\n', k=chunk_size))
    
    with open(file_path, 'w', encoding='utf-8') as f:
        bytes_written = 0
        while bytes_written < size_bytes:
            remaining = size_bytes - bytes_written
            if remaining < chunk_size:
                f.write(data_chunk[:remaining])
                bytes_written += remaining
            else:
                f.write(data_chunk)
                bytes_written += chunk_size


def read_file_sequential(file_path: str, buffer_size: int) -> Dict[str, Any]:
    """Read file sequentially with specified buffer size."""
    start_time = time.time()
    total_bytes = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            total_bytes += len(data.encode('utf-8'))
    
    read_time = time.time() - start_time
    
    return {
        "read_time": read_time * 1000,  # ms
        "bytes_read": total_bytes,
        "throughput_mbps": (total_bytes / (1024 * 1024)) / read_time if read_time > 0 else 0
    }


def read_file_chunked(file_path: str, buffer_size: int) -> Dict[str, Any]:
    """Read file in chunks with specified buffer size."""
    start_time = time.time()
    total_bytes = 0
    chunk_count = 0
    
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            total_bytes += len(data)
            chunk_count += 1
    
    read_time = time.time() - start_time
    
    return {
        "read_time": read_time * 1000,  # ms
        "bytes_read": total_bytes,
        "chunk_count": chunk_count,
        "avg_chunk_size": total_bytes / chunk_count if chunk_count > 0 else 0,
        "throughput_mbps": (total_bytes / (1024 * 1024)) / read_time if read_time > 0 else 0
    }


def measure_memory_usage():
    """Measure current memory usage."""
    import psutil
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)  # MB


def run_large_file_read_benchmark(config: Dict) -> Dict:
    """Run large file reading benchmark."""
    file_sizes = config.get("file_sizes", [1048576])  # Default 1MB
    buffer_sizes = config.get("buffer_sizes", [4096])
    read_patterns = config.get("read_patterns", ["sequential"])
    iterations = config.get("iterations", 3)
    generate_test_files = config.get("generate_test_files", True)
    
    results = {
        "start_time": time.time(),
        "test_cases": [],
        "summary": {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "avg_read_time": 0.0,
            "avg_throughput": 0.0,
            "peak_memory_usage": 0.0
        }
    }
    
    all_read_times = []
    all_throughputs = []
    peak_memory = 0.0
    
    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp(prefix="large_file_read_test_")
    
    try:
        for file_size in file_sizes:
            for buffer_size in buffer_sizes:
                for pattern in read_patterns:
                    print(f"Testing file size: {file_size} bytes, buffer: {buffer_size}, pattern: {pattern}...", file=sys.stderr)
                    
                    test_case = {
                        "file_size": file_size,
                        "buffer_size": buffer_size,
                        "read_pattern": pattern,
                        "iterations": [],
                        "avg_read_time": 0.0,
                        "avg_throughput": 0.0,
                        "memory_efficiency": 0.0
                    }
                    
                    # Generate test file if needed
                    test_file_path = os.path.join(temp_dir, f"test_file_{file_size}_{buffer_size}.txt")
                    if generate_test_files and not os.path.exists(test_file_path):
                        generate_test_file(test_file_path, file_size)
                    
                    read_times = []
                    throughputs = []
                    
                    for i in range(iterations):
                        print(f"  Iteration {i+1}/{iterations}...", file=sys.stderr)
                        
                        results["summary"]["total_tests"] += 1
                        
                        try:
                            # Measure memory before test
                            try:
                                memory_before = measure_memory_usage()
                            except ImportError:
                                memory_before = 0.0
                            
                            # Perform read operation
                            if pattern == "sequential":
                                read_result = read_file_sequential(test_file_path, buffer_size)
                            elif pattern == "chunked":
                                read_result = read_file_chunked(test_file_path, buffer_size)
                            else:
                                raise ValueError(f"Unknown read pattern: {pattern}")
                            
                            # Measure memory after test
                            try:
                                memory_after = measure_memory_usage()
                                memory_used = memory_after - memory_before
                                peak_memory = max(peak_memory, memory_after)
                            except ImportError:
                                memory_used = 0.0
                            
                            iteration_result = {
                                "iteration": i + 1,
                                "read_time": read_result["read_time"],
                                "bytes_read": read_result["bytes_read"],
                                "throughput_mbps": read_result["throughput_mbps"],
                                "memory_used": memory_used,
                                "io_wait_time": read_result["read_time"]  # Approximation
                            }
                            
                            if pattern == "chunked":
                                iteration_result["chunk_count"] = read_result["chunk_count"]
                                iteration_result["avg_chunk_size"] = read_result["avg_chunk_size"]
                            
                            test_case["iterations"].append(iteration_result)
                            read_times.append(read_result["read_time"])
                            throughputs.append(read_result["throughput_mbps"])
                            
                            results["summary"]["successful_tests"] += 1
                            
                        except Exception as e:
                            print(f"Error in iteration {i+1}: {e}", file=sys.stderr)
                            results["summary"]["failed_tests"] += 1
                            test_case["iterations"].append({
                                "iteration": i + 1,
                                "error": str(e),
                                "read_time": 0.0,
                                "throughput_mbps": 0.0
                            })
                    
                    # Calculate averages for this test case
                    if read_times:
                        test_case["avg_read_time"] = sum(read_times) / len(read_times)
                        test_case["avg_throughput"] = sum(throughputs) / len(throughputs)
                        test_case["memory_efficiency"] = file_size / (1024 * 1024) / max(1, peak_memory)
                        
                        all_read_times.extend(read_times)
                        all_throughputs.extend(throughputs)
                    
                    results["test_cases"].append(test_case)
    
    finally:
        # Clean up temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}", file=sys.stderr)
    
    # Calculate overall summary
    if all_read_times:
        results["summary"]["avg_read_time"] = sum(all_read_times) / len(all_read_times)
        results["summary"]["avg_throughput"] = sum(all_throughputs) / len(all_throughputs)
        results["summary"]["peak_memory_usage"] = peak_memory
    
    results["end_time"] = time.time()
    results["total_duration"] = results["end_time"] - results["start_time"]
    
    return results


def main():
    """Main function to run the benchmark."""
    if len(sys.argv) != 2:
        print("Usage: python large_file_read.py <input_file>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        with open(input_file, 'r') as f:
            config = json.load(f)
        
        parameters = config.get("parameters", {})
        result = run_large_file_read_benchmark(parameters)
        
        # Output results as JSON
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()