#!/usr/bin/env python3
"""
JSON parsing test implementation in Python.
Measures JSON parsing, stringification, and traversal performance.
Optimized version for better performance.
"""

import json
import sys
import time
import random
import string
from typing import Dict, List, Any, Union


def generate_flat_json(size: int) -> Dict[str, Any]:
    """Generate flat JSON structure."""
    data = {}
    for i in range(size):
        key = f"key_{i}"
        value_type = random.randrange(3)
        
        if value_type == 0:
            data[key] = ''.join(random.choices(string.ascii_letters, k=10))
        elif value_type == 1:
            data[key] = random.randint(1, 1000)
        else:
            data[key] = bool(random.getrandbits(1))
    
    return data


def generate_nested_json(size: int, max_depth: int = 5) -> Dict[str, Any]:
    """Generate nested JSON structure."""
    def create_nested_object(remaining_size: int, current_depth: int) -> Union[Dict, List, str, int, bool]:
        if remaining_size <= 0 or current_depth >= max_depth:
            choice = random.randrange(3)
            if choice == 0:
                return ''.join(random.choices(string.ascii_letters, k=5))
            elif choice == 1:
                return random.randint(1, 100)
            else:
                return bool(random.getrandbits(1))
        
        if bool(random.getrandbits(1)):  # Create object
            obj = {}
            keys_count = min(random.randint(2, 5), remaining_size)
            remaining_per_key = remaining_size // keys_count
            
            for i in range(keys_count):
                key = f"nested_key_{i}"
                obj[key] = create_nested_object(remaining_per_key, current_depth + 1)
            return obj
        else:  # Create array
            arr = []
            items_count = min(random.randint(2, 4), remaining_size)
            remaining_per_item = remaining_size // items_count
            
            for _ in range(items_count):
                arr.append(create_nested_object(remaining_per_item, current_depth + 1))
            return arr
    
    return {"root": create_nested_object(size, 0)}


def generate_array_heavy_json(size: int) -> Dict[str, Any]:
    """Generate JSON with large arrays."""
    data = {
        "users": [],
        "products": [],
        "orders": []
    }
    
    items_per_array = size // 3
    
    # Users array
    for i in range(items_per_array):
        data["users"].append({
            "id": i,
            "name": f"User_{i}",
            "email": f"user{i}@example.com",
            "active": bool(random.getrandbits(1))
        })
    
    # Products array
    categories = ["electronics", "clothing", "books", "home"]
    for i in range(items_per_array):
        data["products"].append({
            "id": i,
            "name": f"Product_{i}",
            "price": round(random.uniform(10.0, 500.0), 2),
            "category": random.choice(categories)
        })
    
    # Orders array
    for i in range(items_per_array):
        product_ids = [random.randrange(items_per_array) for _ in range(random.randint(1, 5))]
        data["orders"].append({
            "id": i,
            "user_id": random.randrange(items_per_array),
            "product_ids": product_ids,
            "total": round(random.uniform(20.0, 1000.0), 2),
            "timestamp": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        })
    
    return data


def generate_mixed_json(size: int) -> Dict[str, Any]:
    """Generate mixed structure JSON."""
    data = {
        "metadata": {
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "total_records": size
        },
        "config": {
            "settings": {
                "debug": True,
                "cache_enabled": False,
                "timeout": 30
            }
        },
        "data": []
    }
    
    types = ["A", "B", "C"]
    tags = ["urgent", "normal", "low", "critical"]
    
    for i in range(size):
        selected_tags = random.sample(tags, k=min(random.randint(1, 2), len(tags)))
        relationships = [
            {"id": random.randrange(size), "type": "related"}
            for _ in range(random.randint(0, 3))
        ]
        
        data["data"].append({
            "id": i,
            "type": random.choice(types),
            "attributes": {
                "name": f"Item_{i}",
                "value": random.randint(1, 1000),
                "tags": selected_tags
            },
            "relationships": relationships
        })
    
    return data


# Optimized traversal function using iterative approach to avoid recursion limit issues
def traverse_json(data: Any) -> int:
    """Traverse JSON structure and count operations."""
    count = 0
    stack = [data]
    
    while stack:
        current = stack.pop()
        count += 1
        
        if isinstance(current, dict):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    
    return count


def run_json_parsing_benchmark(config: Dict) -> Dict:
    """Run JSON parsing benchmark."""
    json_sizes = config.get("json_sizes", [1000])
    structures = config.get("json_structures", ["flat"])
    operations = config.get("operations", ["parse"])
    iterations = config.get("iterations", 5)
    
    # Structure generators
    generators = {
        "flat": generate_flat_json,
        "nested": generate_nested_json,
        "array_heavy": generate_array_heavy_json,
        "mixed": generate_mixed_json
    }
    
    results = {
        "start_time": time.time(),
        "test_cases": [],
        "summary": {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "avg_parse_time": 0.0,
            "avg_stringify_time": 0.0,
            "avg_traverse_time": 0.0
        }
    }
    
    all_parse_times = []
    all_stringify_times = []
    all_traverse_times = []
    
    # Pre-allocate lists for better performance
    all_parse_times = [0.0] * (len(json_sizes) * len(structures) * iterations)
    all_stringify_times = [0.0] * (len(json_sizes) * len(structures) * iterations)
    all_traverse_times = [0.0] * (len(json_sizes) * len(structures) * iterations)
    
    parse_idx = 0
    stringify_idx = 0
    traverse_idx = 0
    
    for size in json_sizes:
        for structure in structures:
            if structure not in generators:
                print(f"Warning: Structure {structure} not implemented, skipping", file=sys.stderr)
                continue
            
            print(f"Testing {structure} JSON, size: {size}...", file=sys.stderr)
            
            test_case = {
                "json_size": size,
                "structure_type": structure,
                "operations": operations,
                "iterations": [],
                "avg_parse_time": 0.0,
                "avg_stringify_time": 0.0,
                "avg_traverse_time": 0.0
            }
            
            parse_times = []
            stringify_times = []
            traverse_times = []
            
            for i in range(iterations):
                print(f"  Iteration {i+1}/{iterations}...", file=sys.stderr)
                
                # Generate test data
                json_data = generators[structure](size)
                
                # Optimize data size calculation
                json_string = json.dumps(json_data)
                data_size = len(json_string)
                
                iteration_result = {
                    "iteration": i + 1,
                    "data_size": data_size,
                    "operations": {}
                }
                
                results["summary"]["total_tests"] += 1
                success = True
                
                # Parse operation (stringify then parse)
                if "parse" in operations:
                    try:
                        start_time = time.perf_counter()
                        parsed_data = json.loads(json_string)
                        parse_time = (time.perf_counter() - start_time) * 1000  # ms
                        
                        parse_times.append(parse_time)
                        all_parse_times[parse_idx] = parse_time
                        parse_idx += 1
                        
                        iteration_result["operations"]["parse"] = {
                            "success": True,
                            "time_ms": parse_time,
                            "json_string_length": len(json_string)
                        }
                        
                    except Exception as e:
                        success = False
                        iteration_result["operations"]["parse"] = {
                            "success": False,
                            "error": str(e)
                        }
                
                # Stringify operation
                if "stringify" in operations:
                    try:
                        start_time = time.perf_counter()
                        json_string = json.dumps(json_data)
                        stringify_time = (time.perf_counter() - start_time) * 1000  # ms
                        
                        stringify_times.append(stringify_time)
                        all_stringify_times[stringify_idx] = stringify_time
                        stringify_idx += 1
                        
                        iteration_result["operations"]["stringify"] = {
                            "success": True,
                            "time_ms": stringify_time,
                            "output_length": len(json_string)
                        }
                        
                    except Exception as e:
                        success = False
                        iteration_result["operations"]["stringify"] = {
                            "success": False,
                            "error": str(e)
                        }
                
                # Traverse operation
                if "traverse" in operations:
                    try:
                        start_time = time.perf_counter()
                        operation_count = traverse_json(json_data)
                        traverse_time = (time.perf_counter() - start_time) * 1000  # ms
                        
                        traverse_times.append(traverse_time)
                        all_traverse_times[traverse_idx] = traverse_time
                        traverse_idx += 1
                        
                        iteration_result["operations"]["traverse"] = {
                            "success": True,
                            "time_ms": traverse_time,
                            "operations_count": operation_count
                        }
                        
                    except Exception as e:
                        success = False
                        iteration_result["operations"]["traverse"] = {
                            "success": False,
                            "error": str(e)
                        }
                
                if success:
                    results["summary"]["successful_tests"] += 1
                else:
                    results["summary"]["failed_tests"] += 1
                
                test_case["iterations"].append(iteration_result)
            
            # Calculate averages for this test case
            if parse_times:
                test_case["avg_parse_time"] = sum(parse_times) / len(parse_times)
            if stringify_times:
                test_case["avg_stringify_time"] = sum(stringify_times) / len(stringify_times)
            if traverse_times:
                test_case["avg_traverse_time"] = sum(traverse_times) / len(traverse_times)
            
            results["test_cases"].append(test_case)
    
    # Filter out unused slots and calculate overall summary
    all_parse_times = [t for t in all_parse_times if t > 0]
    all_stringify_times = [t for t in all_stringify_times if t > 0]
    all_traverse_times = [t for t in all_traverse_times if t > 0]
    
    if all_parse_times:
        results["summary"]["avg_parse_time"] = sum(all_parse_times) / len(all_parse_times)
    if all_stringify_times:
        results["summary"]["avg_stringify_time"] = sum(all_stringify_times) / len(all_stringify_times)
    if all_traverse_times:
        results["summary"]["avg_traverse_time"] = sum(all_traverse_times) / len(all_traverse_times)
    
    results["end_time"] = time.time()
    results["total_execution_time"] = results["end_time"] - results["start_time"]
    
    return results


def main():
    """Main entry point for JSON parsing test."""
    if len(sys.argv) < 2:
        print("Usage: python json_parsing.py <config_file>", file=sys.stderr)
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        parameters = config.get("parameters", {})
        results = run_json_parsing_benchmark(parameters)
        
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