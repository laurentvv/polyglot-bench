#!/usr/bin/env python3
"""
Fibonacci benchmark implementation in Python.
Calculates the nth Fibonacci number using recursive algorithm.
"""

import sys
import time


def fibonacci(n):
    """Calculate the nth Fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)


def main():
    """Main execution function."""
    # Test parameter
    n = 35  # Adjusted for reasonable execution time
    
    print(f"Calculating fibonacci({n})...")
    start_time = time.perf_counter()
    
    result = fibonacci(n)
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    print(f"Result: {result}")
    print(f"Execution time: {execution_time:.6f} seconds")


if __name__ == "__main__":
    main()