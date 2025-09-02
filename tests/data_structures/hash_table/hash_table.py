#!/usr/bin/env python3
"""
Hash table benchmark implementation in Python.
Tests hash table operations (insert, lookup, delete).
"""

import sys
import time
import random
import string


def random_string(length=10):
    """Generate a random string of given length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def main():
    """Main execution function."""
    num_operations = 100000
    
    # Generate test data
    keys = [random_string() for _ in range(num_operations)]
    values = [random.randint(1, 1000000) for _ in range(num_operations)]
    
    print(f"Testing hash table with {num_operations} operations...")
    start_time = time.perf_counter()
    
    # Create hash table (dictionary in Python)
    hash_table = {}
    
    # Insert operations
    insert_start = time.perf_counter()
    for i in range(num_operations):
        hash_table[keys[i]] = values[i]
    insert_time = time.perf_counter() - insert_start
    
    # Lookup operations
    lookup_start = time.perf_counter()
    found_count = 0
    for key in keys:
        if key in hash_table:
            found_count += 1
    lookup_time = time.perf_counter() - lookup_start
    
    # Delete operations
    delete_start = time.perf_counter()
    deleted_count = 0
    for i in range(0, num_operations, 2):  # Delete every other key
        if keys[i] in hash_table:
            del hash_table[keys[i]]
            deleted_count += 1
    delete_time = time.perf_counter() - delete_start
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    print(f"Result:")
    print(f"  Inserted: {num_operations} items")
    print(f"  Found: {found_count}/{num_operations} items")
    print(f"  Deleted: {deleted_count} items")
    print(f"  Remaining: {len(hash_table)} items")
    print(f"Timing:")
    print(f"  Insert time: {insert_time:.6f} seconds")
    print(f"  Lookup time: {lookup_time:.6f} seconds") 
    print(f"  Delete time: {delete_time:.6f} seconds")
    print(f"  Total time: {total_time:.6f} seconds")


if __name__ == "__main__":
    main()
