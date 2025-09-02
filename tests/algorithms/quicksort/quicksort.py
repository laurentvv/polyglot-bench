#!/usr/bin/env python3
"""
Quicksort benchmark implementation in Python.
Sorts an array using the quicksort algorithm.
"""

import sys
import time
import random


def quicksort(arr):
    """Sort array using quicksort algorithm."""
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)


def main():
    """Main execution function."""
    # Generate test data
    size = 10000
    arr = list(range(size))
    random.shuffle(arr)
    
    print(f"Sorting array of size {size}...")
    start_time = time.perf_counter()
    
    sorted_arr = quicksort(arr.copy())
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    # Verify correctness
    is_sorted = sorted_arr == sorted(arr)
    
    print(f"Result: {'Sorted correctly' if is_sorted else 'Sort failed'}")
    print(f"Execution time: {execution_time:.6f} seconds")


if __name__ == "__main__":
    main()