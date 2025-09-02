#!/usr/bin/env python3
"""
Prime sieve benchmark implementation in Python.
Finds all prime numbers up to n using the Sieve of Eratosthenes.
"""

import sys
import time
import math


def sieve_of_eratosthenes(n):
    """Find all prime numbers up to n using the Sieve of Eratosthenes."""
    if n < 2:
        return []
    
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    
    for i in range(2, int(math.sqrt(n)) + 1):
        if is_prime[i]:
            for j in range(i * i, n + 1, i):
                is_prime[j] = False
    
    return [i for i in range(2, n + 1) if is_prime[i]]


def main():
    """Main execution function."""
    n = 100000
    
    print(f"Finding all primes up to {n}...")
    start_time = time.perf_counter()
    
    primes = sieve_of_eratosthenes(n)
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    print(f"Result: Found {len(primes)} primes")
    print(f"Largest prime: {max(primes) if primes else 'None'}")
    print(f"Execution time: {execution_time:.6f} seconds")


if __name__ == "__main__":
    main()