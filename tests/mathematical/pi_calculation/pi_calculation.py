#!/usr/bin/env python3
"""
Pi calculation benchmark implementation in Python.
Calculates pi using the Monte Carlo method.
"""

import sys
import time
import random
import math
import numpy as np


def calculate_pi_monte_carlo(num_samples):
    """Calculate pi using Monte Carlo method with NumPy for vectorization."""
    # Generate random coordinates in a vectorized manner
    x = np.random.rand(num_samples)
    y = np.random.rand(num_samples)
    
    # Use vectorized operations to find points inside the circle
    inside_circle = np.sum(x*x + y*y <= 1)
    
    return 4.0 * inside_circle / num_samples


def main():
    """Main execution function."""
    num_samples = 1000000
    
    print(f"Calculating pi with {num_samples} samples...")
    start_time = time.perf_counter()
    
    pi_estimate = calculate_pi_monte_carlo(num_samples)
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    error = abs(pi_estimate - math.pi)
    
    print(f"Result: {pi_estimate:.6f}")
    print(f"Actual pi: {math.pi:.6f}")
    print(f"Error: {error:.6f}")
    print(f"Execution time: {execution_time:.6f} seconds")


if __name__ == "__main__":
    main()