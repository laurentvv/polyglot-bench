#!/usr/bin/env python3
"""
Binary search benchmark implementation in Python.
Performs binary search on a sorted array.
"""

import sys
import time
import random


def binary_search(arr, target):
    """Perform binary search on sorted array."""
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1


def main():
    """Main execution function."""
    size = 1000000
    arr = list(range(size))
    num_searches = 1000
    
    # Generate random targets
    targets = [random.randint(0, size-1) for _ in range(num_searches)]
    
    print(f"Performing {num_searches} binary searches on array of size {size}...")
    start_time = time.perf_counter()
    
    found_count = 0
    for target in targets:
        result = binary_search(arr, target)
        if result != -1:
            found_count += 1
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    print(f"Result: Found {found_count}/{num_searches} targets")
    print(f"Execution time: {execution_time:.6f} seconds")


if __name__ == "__main__":
    main()