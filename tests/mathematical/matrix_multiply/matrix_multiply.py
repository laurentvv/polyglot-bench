#!/usr/bin/env python3
"""
Matrix multiplication benchmark implementation in Python.
Performs matrix multiplication on randomly generated matrices.
"""

import sys
import time
import random
import numpy as np


def create_matrix(rows, cols):
    """Create a matrix filled with random values using NumPy."""
    return np.random.rand(rows, cols) * 100


def multiply_matrices(a, b):
    """Multiply two matrices using NumPy's optimized multiplication."""
    if a.shape[1] != b.shape[0]:
        raise ValueError("Matrices cannot be multiplied")
    # Use the @ operator for matrix multiplication in NumPy
    return a @ b


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
    result_rows, result_cols = result.shape
    
    print(f"Result: {result_rows}x{result_cols} matrix")
    print(f"Sample result[0][0]: {result[0][0]:.6f}")
    print(f"Timing:")
    print(f"  Matrix creation: {create_time:.6f} seconds")
    print(f"  Matrix multiplication: {multiply_time:.6f} seconds")
    print(f"  Total time: {total_time:.6f} seconds")


if __name__ == "__main__":
    main()