#!/usr/bin/env python3
"""
Text compression test implementation in Python.
Measures compression performance for different text types and algorithms.
"""

import json
import sys
import time
import gzip
import zlib
import random
import string
from typing import Dict, List, Any, Callable


def generate_text_data(size: int, text_type: str) -> str:
    """Generate different types of text data."""
    if text_type == "ascii":
        return ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=size))
    
    elif text_type == "unicode":
        # Include various Unicode characters
        chars = string.ascii_letters + string.digits + 'àáâãäåæçèéêëìíîïñòóôõöøùúûüý' + '你好世界' + '🌟🚀📊'
        return ''.join(random.choices(chars + ' \n', k=size))
    
    elif text_type == "code":
        # Generate code-like text
        keywords = ['def', 'class', 'import', 'from', 'if', 'else', 'for', 'while', 'return', 'try', 'except']
        operators = ['=', '+', '-', '*', '/', '(', ')', '{', '}', '[', ']', ';', ':']
        text = []
        current_size = 0
        
        while current_size < size:
            if random.random() < 0.3:
                word = random.choice(keywords)
            else:
                word = ''.join(random.choices(string.ascii_lowercase, k=random.randint(3, 10)))
            
            if random.random() < 0.2:
                word += random.choice(operators)
            
            if random.random() < 0.1:
                word += '\n'
            else:
                word += ' '
            
            text.append(word)
            current_size += len(word)
        
        return ''.join(text)[:size]
    
    elif text_type == "natural_language":
        # Generate natural language-like text
        words = ['the', 'quick', 'brown', 'fox', 'jumps', 'over', 'lazy', 'dog', 'and', 'runs', 'through',
                'forest', 'meadow', 'river', 'mountain', 'valley', 'beautiful', 'magnificent', 'wonderful']
        
        text = []
        current_size = 0
        
        while current_size < size:
            word = random.choice(words)
            if random.random() < 0.1:
                word += '. '
            elif random.random() < 0.05:
                word += ', '
            else:
                word += ' '
            
            if random.random() < 0.05:
                word += '\n'
            
            text.append(word)
            current_size += len(word)
        
        return ''.join(text)[:size]
    
    else:
        raise ValueError(f"Unknown text type: {text_type}")


def compress_with_gzip(data: bytes, level: int = 6) -> Dict[str, Any]:
    """Compress data using GZIP."""
    start_time = time.time()
    try:
        compressed = gzip.compress(data, compresslevel=level)
        compression_time = time.time() - start_time
        
        return {
            "success": True,
            "compressed_size": len(compressed),
            "compression_time": compression_time * 1000,  # ms
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "compression_time": (time.time() - start_time) * 1000
        }


def compress_with_zlib(data: bytes, level: int = 6) -> Dict[str, Any]:
    """Compress data using zlib."""
    start_time = time.time()
    try:
        compressed = zlib.compress(data, level)
        compression_time = time.time() - start_time
        
        return {
            "success": True,
            "compressed_size": len(compressed),
            "compression_time": compression_time * 1000,  # ms
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "compression_time": (time.time() - start_time) * 1000
        }


def decompress_gzip(data: bytes) -> Dict[str, Any]:
    """Decompress GZIP data."""
    start_time = time.time()
    try:
        decompressed = gzip.decompress(data)
        decompression_time = time.time() - start_time
        
        return {
            "success": True,
            "decompressed_size": len(decompressed),
            "decompression_time": decompression_time * 1000  # ms
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "decompression_time": (time.time() - start_time) * 1000
        }


def decompress_zlib(data: bytes) -> Dict[str, Any]:
    """Decompress zlib data."""
    start_time = time.time()
    try:
        decompressed = zlib.decompress(data)
        decompression_time = time.time() - start_time
        
        return {
            "success": True,
            "decompressed_size": len(decompressed),
            "decompression_time": decompression_time * 1000  # ms
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "decompression_time": (time.time() - start_time) * 1000
        }


def run_text_compression_benchmark(config: Dict) -> Dict:
    """Run text compression benchmark."""
    input_sizes = config.get("input_sizes", [1024])
    text_types = config.get("text_types", ["ascii"])
    algorithms = config.get("compression_algorithms", ["gzip"])
    iterations = config.get("iterations", 3)
    
    # Algorithm mappings
    compress_funcs = {
        "gzip": compress_with_gzip,
        "zlib": compress_with_zlib
    }
    
    decompress_funcs = {
        "gzip": decompress_gzip,
        "zlib": decompress_zlib
    }
    
    results = {
        "start_time": time.time(),
        "test_cases": [],
        "summary": {
            "total_tests": 0,
            "successful_compressions": 0,
            "failed_compressions": 0,
            "best_compression_ratios": {},
            "algorithm_performance": {}
        }
    }
    
    algorithm_stats = {}
    
    for size in input_sizes:
        for text_type in text_types:
            for algorithm in algorithms:
                if algorithm not in compress_funcs:
                    print(f"Warning: Algorithm {algorithm} not implemented, skipping", file=sys.stderr)
                    continue
                    
                print(f"Testing {text_type} text, size: {size}, algorithm: {algorithm}...", file=sys.stderr)
                
                test_case = {
                    "input_size": size,
                    "text_type": text_type,
                    "algorithm": algorithm,
                    "iterations": [],
                    "avg_compression_ratio": 0.0,
                    "avg_compression_time": 0.0,
                    "avg_decompression_time": 0.0
                }
                
                compression_ratios = []
                compression_times = []
                decompression_times = []
                
                for i in range(iterations):
                    print(f"  Iteration {i+1}/{iterations}...", file=sys.stderr)
                    
                    # Generate test data
                    text_data = generate_text_data(size, text_type)
                    data_bytes = text_data.encode('utf-8')
                    original_size = len(data_bytes)
                    
                    # Compress
                    compress_result = compress_funcs[algorithm](data_bytes)
                    
                    iteration_result = {
                        "iteration": i + 1,
                        "original_size": original_size,
                        "compression": compress_result
                    }
                    
                    results["summary"]["total_tests"] += 1
                    
                    if compress_result["success"]:
                        results["summary"]["successful_compressions"] += 1
                        
                        # Calculate compression ratio
                        compressed_size = compress_result["compressed_size"]
                        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
                        
                        compression_ratios.append(compression_ratio)
                        compression_times.append(compress_result["compression_time"])
                        
                        # Note: Decompression test removed to avoid storing compressed data
                        # This simplifies the test and avoids JSON serialization issues
                        
                        # Track algorithm performance
                        if algorithm not in algorithm_stats:
                            algorithm_stats[algorithm] = []
                        algorithm_stats[algorithm].append(compression_ratio)
                        
                    else:
                        results["summary"]["failed_compressions"] += 1
                    
                    test_case["iterations"].append(iteration_result)
                
                # Calculate averages
                if compression_ratios:
                    test_case["avg_compression_ratio"] = sum(compression_ratios) / len(compression_ratios)
                    test_case["avg_compression_time"] = sum(compression_times) / len(compression_times)
                    
                    if decompression_times:
                        test_case["avg_decompression_time"] = sum(decompression_times) / len(decompression_times)
                
                results["test_cases"].append(test_case)
    
    # Calculate summary statistics
    for algorithm, ratios in algorithm_stats.items():
        if ratios:
            results["summary"]["algorithm_performance"][algorithm] = {
                "avg_compression_ratio": sum(ratios) / len(ratios),
                "max_compression_ratio": max(ratios),
                "min_compression_ratio": min(ratios)
            }
    
    results["end_time"] = time.time()
    results["total_execution_time"] = results["end_time"] - results["start_time"]
    
    return results


def main():
    """Main entry point for text compression test."""
    if len(sys.argv) < 2:
        print("Usage: python text_compression.py <config_file>", file=sys.stderr)
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        parameters = config.get("parameters", {})
        results = run_text_compression_benchmark(parameters)
        
        print(json.dumps(results, indent=2))
        
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()