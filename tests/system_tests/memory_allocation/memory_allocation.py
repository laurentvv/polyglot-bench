#!/usr/bin/env python3
"""
Memory allocation test implementation in Python.
Measures memory allocation, deallocation, and management performance.
"""

import json
import sys
import time
import random
import gc
import psutil
import os
from typing import Dict, List, Any, Optional
import numpy as np


def get_memory_usage() -> int:
    """Get current memory usage in bytes."""
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss
    except:
        return 0


def allocate_array(size: int, count: int) -> List[np.ndarray]:
    """Allocate arrays of specified size using NumPy for performance."""
    arrays = []
    for i in range(count):
        # Use NumPy's optimized random integer generation
        array = np.random.randint(0, 1001, size=size)
        arrays.append(array)
    return arrays


def allocate_linked_list(size: int, count: int) -> List[List[Dict]]:
    """Allocate linked list structures."""
    class ListNode:
        def __init__(self, value: int, next_node=None):
            self.value = value
            self.next = next_node
    
    lists = []
    for i in range(count):
        head = None
        for j in range(size):
            new_node = ListNode(random.randint(0, 1000))
            new_node.next = head
            head = new_node
        lists.append(head)
    
    return lists


def allocate_hash_map(size: int, count: int) -> List[Dict[int, int]]:
    """Allocate hash map/dictionary structures."""
    maps = []
    for i in range(count):
        hash_map = {}
        for j in range(size):
            key = random.randint(0, size * 2)
            value = random.randint(0, 1000)
            hash_map[key] = value
        maps.append(hash_map)
    return maps


def allocate_sequential(allocator_func, size: int, count: int) -> Any:
    """Sequential allocation pattern."""
    return allocator_func(size, count)


def allocate_random(allocator_func, size: int, count: int) -> List[Any]:
    """Random allocation pattern."""
    # Allocate in random order with random delays
    allocated = []
    indices = list(range(count))
    random.shuffle(indices)
    
    for i in indices:
        # Allocate one item at a time
        item = allocator_func(size, 1)[0]
        allocated.append(item)
        
        # Random micro-delay to simulate real-world patterns
        if random.random() < 0.1:
            time.sleep(0.0001)
    
    return allocated


def allocate_fragmented(allocator_func, size: int, count: int) -> List[Any]:
    """Fragmented allocation pattern - allocate, deallocate some, allocate more."""
    allocated = []
    
    # First wave - allocate half
    first_half = count // 2
    first_batch = allocator_func(size, first_half)
    allocated.extend(first_batch)
    
    # Deallocate every other item to create fragmentation
    for i in range(len(allocated) - 1, -1, -2):
        del allocated[i]
    
    # Force garbage collection
    gc.collect()
    
    # Second wave - allocate remaining
    remaining = count - len(allocated)
    second_batch = allocator_func(size, remaining)
    allocated.extend(second_batch)
    
    return allocated


def run_memory_allocation_benchmark(config: Dict) -> Dict:
    """Run memory allocation benchmark."""
    allocation_sizes = config.get("allocation_sizes", [1024])
    patterns = config.get("allocation_patterns", ["sequential"])
    allocation_counts = config.get("allocation_counts", [100])
    data_structures = config.get("data_structures", ["array"])
    iterations = config.get("iterations", 3)
    
    # Structure allocators
    allocators = {
        "array": allocate_array,
        "linked_list": allocate_linked_list,
        "hash_map": allocate_hash_map
    }
    
    # Pattern functions
    pattern_funcs = {
        "sequential": allocate_sequential,
        "random": allocate_random,
        "fragmented": allocate_fragmented
    }
    
    results = {
        "start_time": time.time(),
        "test_cases": [],
        "summary": {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "avg_allocation_time": 0.0,
            "avg_deallocation_time": 0.0,
            "avg_memory_efficiency": 0.0
        }
    }
    
    all_allocation_times = []
    all_deallocation_times = []
    all_memory_efficiencies = []
    
    for size in allocation_sizes:
        for count in allocation_counts:
            for structure in data_structures:
                for pattern in patterns:
                    if structure not in allocators or pattern not in pattern_funcs:
                        continue
                    
                    print(f"Testing {structure} allocation: size={size}, count={count}, pattern={pattern}...", file=sys.stderr)
                    
                    test_case = {
                        "allocation_size": size,
                        "allocation_count": count,
                        "data_structure": structure,
                        "allocation_pattern": pattern,
                        "iterations": [],
                        "avg_allocation_time": 0.0,
                        "avg_deallocation_time": 0.0,
                        "avg_memory_efficiency": 0.0
                    }
                    
                    allocation_times = []
                    deallocation_times = []
                    memory_efficiencies = []
                    
                    for i in range(iterations):
                        print(f"  Iteration {i+1}/{iterations}...", file=sys.stderr)
                        
                        # Force garbage collection before test
                        gc.collect()
                        initial_memory = get_memory_usage()
                        
                        iteration_result = {
                            "iteration": i + 1,
                            "initial_memory": initial_memory,
                            "allocation": {},
                            "deallocation": {}
                        }
                        
                        results["summary"]["total_tests"] += 1
                        success = True
                        
                        try:
                            # Allocation phase
                            allocator = allocators[structure]
                            pattern_func = pattern_funcs[pattern]
                            
                            start_time = time.time()
                            
                            if pattern == "sequential":
                                allocated_data = pattern_func(allocator, size, count)
                            else:
                                allocated_data = pattern_func(allocator, size, count)
                            
                            allocation_time = (time.time() - start_time) * 1000  # ms
                            
                            # Measure memory after allocation
                            peak_memory = get_memory_usage()
                            memory_used = peak_memory - initial_memory
                            
                            # Calculate theoretical vs actual memory usage
                            if structure == "array":
                                # For NumPy, we can get the exact byte size
                                theoretical_size = sum(arr.nbytes for arr in allocated_data)
                            elif structure == "hash_map":
                                theoretical_size = size * count * 16  # Key-value pairs
                            else:  # linked_list
                                theoretical_size = size * count * 24  # Node overhead
                            
                            memory_efficiency = (theoretical_size / memory_used * 100) if memory_used > 0 else 0
                            
                            allocation_times.append(allocation_time)
                            all_allocation_times.append(allocation_time)
                            memory_efficiencies.append(memory_efficiency)
                            all_memory_efficiencies.append(memory_efficiency)
                            
                            iteration_result["allocation"] = {
                                "success": True,
                                "time_ms": allocation_time,
                                "memory_used": memory_used,
                                "peak_memory": peak_memory,
                                "memory_efficiency": memory_efficiency,
                                "items_allocated": count
                            }
                            
                            # Deallocation phase
                            start_time = time.time()
                            
                            # Clear references to trigger deallocation
                            if isinstance(allocated_data, list):
                                allocated_data.clear()
                            del allocated_data
                            
                            # Force garbage collection
                            gc.collect()
                            
                            deallocation_time = (time.time() - start_time) * 1000  # ms
                            final_memory = get_memory_usage()
                            
                            deallocation_times.append(deallocation_time)
                            all_deallocation_times.append(deallocation_time)
                            
                            iteration_result["deallocation"] = {
                                "success": True,
                                "time_ms": deallocation_time,
                                "final_memory": final_memory,
                                "memory_freed": peak_memory - final_memory
                            }
                            
                        except Exception as e:
                            success = False
                            iteration_result["allocation"]["success"] = False
                            iteration_result["allocation"]["error"] = str(e)
                        
                        if success:
                            results["summary"]["successful_tests"] += 1
                        else:
                            results["summary"]["failed_tests"] += 1
                        
                        test_case["iterations"].append(iteration_result)
                    
                    # Calculate averages for this test case
                    if allocation_times:
                        test_case["avg_allocation_time"] = sum(allocation_times) / len(allocation_times)
                    if deallocation_times:
                        test_case["avg_deallocation_time"] = sum(deallocation_times) / len(deallocation_times)
                    if memory_efficiencies:
                        test_case["avg_memory_efficiency"] = sum(memory_efficiencies) / len(memory_efficiencies)
                    
                    results["test_cases"].append(test_case)
    
    # Calculate overall summary
    if all_allocation_times:
        results["summary"]["avg_allocation_time"] = sum(all_allocation_times) / len(all_allocation_times)
    if all_deallocation_times:
        results["summary"]["avg_deallocation_time"] = sum(all_deallocation_times) / len(all_deallocation_times)
    if all_memory_efficiencies:
        results["summary"]["avg_memory_efficiency"] = sum(all_memory_efficiencies) / len(all_memory_efficiencies)
    
    results["end_time"] = time.time()
    results["total_execution_time"] = results["end_time"] - results["start_time"]
    
    return results


def main():
    """Main entry point for memory allocation test."""
    if len(sys.argv) < 2:
        print("Usage: python memory_allocation.py <config_file>", file=sys.stderr)
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        parameters = config.get("parameters", {})
        results = run_memory_allocation_benchmark(parameters)
        
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