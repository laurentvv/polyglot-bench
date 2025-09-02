#!/usr/bin/env python3
"""
Matrix multiplication benchmark implementation in Python.
Performs matrix multiplication on randomly generated matrices.
"""

import sys
import time
import random


def create_matrix(rows, cols):
    """Create a matrix filled with random values."""
    return [[random.uniform(0, 100) for _ in range(cols)] for _ in range(rows)]


def multiply_matrices(a, b):
    """Multiply two matrices."""
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])
    
    if cols_a != rows_b:
        raise ValueError("Matrices cannot be multiplied")
    
    result = [[0 for _ in range(cols_b)] for _ in range(rows_a)]
    
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    
    return result


def main():
    """Main execution function."""
    size = 200  # Matrix size (200x200)
    
    print(f"Multiplying two {size}x{size} matrices...")
    
    # Create matrices
    create_start = time.perf_counter()
    matrix_a = create_matrix(size, size)
    matrix_b = create_matrix(size, size)
    create_time = time.perf_counter() - create_start
    
    # Multiply matrices
    multiply_start = time.perf_counter()
    result = multiply_matrices(matrix_a, matrix_b)
    multiply_time = time.perf_counter() - multiply_start
    
    total_time = create_time + multiply_time
    
    # Verify result dimensions
    result_rows, result_cols = len(result), len(result[0])
    
    print(f"Result: {result_rows}x{result_cols} matrix")
    print(f"Sample result[0][0]: {result[0][0]:.6f}")
    print(f"Timing:")
    print(f"  Matrix creation: {create_time:.6f} seconds")
    print(f"  Matrix multiplication: {multiply_time:.6f} seconds")
    print(f"  Total time: {total_time:.6f} seconds")


if __name__ == "__main__":
    main()