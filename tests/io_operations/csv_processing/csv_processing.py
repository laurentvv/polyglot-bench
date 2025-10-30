#!/usr/bin/env python3
"""
CSV processing test implementation in Python.
Measures CSV file read, write, filtering, and aggregation performance.
Optimized version for better performance.
"""

import json
import sys
import time
import random
import string
from typing import Dict, List, Any, Union


def load_test_data() -> List[List[str]]:
    """Load standardized test data from JSON file."""
    import os
    test_data_path = os.path.join(os.path.dirname(__file__), 'test_data.json')
    with open(test_data_path, 'r') as f:
        test_data = json.load(f)
    
    csv_data = test_data['csv_data']
    data = [csv_data['headers']]
    data.extend(csv_data['rows'])
    return data

def generate_csv_data(rows: int, cols: int, data_type: str) -> List[List[str]]:
    """Generate CSV data using standardized test data - replicated to match size."""
    base_data = load_test_data()
    
    # Use the headers from test data
    headers = base_data[0][:cols] if cols <= len(base_data[0]) else base_data[0] + [f"col_{i+1}" for i in range(len(base_data[0]), cols)]
    data = [headers]
    
    # Replicate base rows to match requested size
    base_rows = base_data[1:]
    for row_idx in range(rows):
        source_row = base_rows[row_idx % len(base_rows)]
        row_data = source_row[:cols] if cols <= len(source_row) else source_row + [f"extra_{row_idx}_{i}" for i in range(len(source_row), cols)]
        data.append(row_data)
    
    return data


def write_csv_to_string(data: List[List[str]]) -> str:
    """Write CSV data to string format using optimized string operations."""
    # Use more efficient string building
    result = []
    for row in data:
        result.append(','.join(row))
    return '\n'.join(result) + '\n'


def read_csv_from_string(csv_string: str) -> List[List[str]]:
    """Read CSV data from string format using optimized string operations."""
    # More efficient parsing
    lines = csv_string.strip().split('\n')
    return [line.split(',') for line in lines if line]


def filter_csv_data(data: List[List[str]], filter_column: int = 0) -> List[List[str]]:
    """Filter CSV data based on a condition - optimized."""
    if not data or len(data) < 2:
        return data
    
    filtered_data = [data[0]]  # Headers
    
    for row in data[1:]:
        if len(row) > filter_column:
            cell_value = row[filter_column]
            # Quick numeric check without exception handling
            if cell_value.replace('.', '').replace('-', '').isdigit():
                if float(cell_value) > 500:
                    filtered_data.append(row)
            elif len(cell_value) > 5:
                filtered_data.append(row)
    return filtered_data


def aggregate_csv_data(data: List[List[str]]) -> Dict[str, Any]:
    """Perform aggregation operations on CSV data - optimized."""
    if not data or len(data) < 2:
        return {}
    
    headers = data[0]
    numeric_columns = []
    
    # Quick numeric column detection
    for col_idx in range(len(headers)):
        is_numeric = True
        check_rows = min(3, len(data) - 1)  # Check fewer rows
        for row_idx in range(1, check_rows + 1):
            if len(data[row_idx]) > col_idx:
                cell = data[row_idx][col_idx]
                if not (cell.replace('.', '').replace('-', '').isdigit()):
                    is_numeric = False
                    break
        if is_numeric:
            numeric_columns.append(col_idx)
    
    aggregations = {}
    
    for col_idx in numeric_columns:
        col_name = headers[col_idx]
        values = []
        
        for row in data[1:]:
            if len(row) > col_idx:
                cell = row[col_idx]
                if cell.replace('.', '').replace('-', '').isdigit():
                    values.append(float(cell))
        
        if values:
            total = sum(values)
            aggregations[col_name] = {
                "sum": total,
                "avg": total / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            }
    
    return aggregations


def run_csv_processing_benchmark(config: Dict) -> Dict:
    """Run CSV processing benchmark."""
    row_counts = config.get("row_counts", [1000])
    column_counts = config.get("column_counts", [5])
    operations = config.get("operations", ["read", "write"])
    data_types = config.get("data_types", ["mixed"])
    iterations = config.get("iterations", 3)
    
    results = {
        "start_time": time.time(),
        "test_cases": [],
        "summary": {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "avg_read_time": 0.0,
            "avg_write_time": 0.0,
            "avg_filter_time": 0.0,
            "avg_aggregate_time": 0.0
        }
    }
    
    all_read_times = []
    all_write_times = []
    all_filter_times = []
    all_aggregate_times = []
    
    for rows in row_counts:
        for cols in column_counts:
            for data_type in data_types:
                print(f"Testing CSV: {rows} rows x {cols} cols, type: {data_type}...", file=sys.stderr)
                
                test_case = {
                    "row_count": rows,
                    "column_count": cols,
                    "data_type": data_type,
                    "operations": operations,
                    "iterations": [],
                    "avg_read_time": 0.0,
                    "avg_write_time": 0.0,
                    "avg_filter_time": 0.0,
                    "avg_aggregate_time": 0.0
                }
                
                read_times = []
                write_times = []
                filter_times = []
                aggregate_times = []
                
                for i in range(iterations):
                    print(f"  Iteration {i+1}/{iterations}...", file=sys.stderr)
                    
                    # Generate test data
                    csv_data = generate_csv_data(rows, cols, data_type)
                    
                    iteration_result = {
                        "iteration": i + 1,
                        "data_size": len(csv_data),
                        "operations": {}
                    }
                    
                    results["summary"]["total_tests"] += 1
                    success = True
                    
                    # Write operation
                    if "write" in operations:
                        try:
                            start_time = time.time()
                            csv_string = write_csv_to_string(csv_data)
                            write_time = (time.time() - start_time) * 1000  # ms
                            
                            write_times.append(write_time)
                            all_write_times.append(write_time)
                            
                            iteration_result["operations"]["write"] = {
                                "success": True,
                                "time_ms": write_time,
                                "output_size": len(csv_string)
                            }
                            
                        except Exception as e:
                            success = False
                            iteration_result["operations"]["write"] = {
                                "success": False,
                                "error": str(e)
                            }
                    
                    # Read operation
                    if "read" in operations:
                        try:
                            # First write to get string representation
                            csv_string = write_csv_to_string(csv_data)
                            
                            start_time = time.time()
                            read_data = read_csv_from_string(csv_string)
                            read_time = (time.time() - start_time) * 1000  # ms
                            
                            read_times.append(read_time)
                            all_read_times.append(read_time)
                            
                            iteration_result["operations"]["read"] = {
                                "success": True,
                                "time_ms": read_time,
                                "rows_read": len(read_data)
                            }
                            
                        except Exception as e:
                            success = False
                            iteration_result["operations"]["read"] = {
                                "success": False,
                                "error": str(e)
                            }
                    
                    # Filter operation
                    if "filter" in operations:
                        try:
                            start_time = time.time()
                            filtered_data = filter_csv_data(csv_data)
                            filter_time = (time.time() - start_time) * 1000  # ms
                            
                            filter_times.append(filter_time)
                            all_filter_times.append(filter_time)
                            
                            iteration_result["operations"]["filter"] = {
                                "success": True,
                                "time_ms": filter_time,
                                "original_rows": len(csv_data),
                                "filtered_rows": len(filtered_data)
                            }
                            
                        except Exception as e:
                            success = False
                            iteration_result["operations"]["filter"] = {
                                "success": False,
                                "error": str(e)
                            }
                    
                    # Aggregate operation
                    if "aggregate" in operations:
                        try:
                            start_time = time.time()
                            aggregations = aggregate_csv_data(csv_data)
                            aggregate_time = (time.time() - start_time) * 1000  # ms
                            
                            aggregate_times.append(aggregate_time)
                            all_aggregate_times.append(aggregate_time)
                            
                            iteration_result["operations"]["aggregate"] = {
                                "success": True,
                                "time_ms": aggregate_time,
                                "aggregated_columns": len(aggregations)
                            }
                            
                        except Exception as e:
                            success = False
                            iteration_result["operations"]["aggregate"] = {
                                "success": False,
                                "error": str(e)
                            }
                    
                    if success:
                        results["summary"]["successful_tests"] += 1
                    else:
                        results["summary"]["failed_tests"] += 1
                    
                    test_case["iterations"].append(iteration_result)
                
                # Calculate averages for this test case
                if read_times:
                    test_case["avg_read_time"] = sum(read_times) / len(read_times)
                if write_times:
                    test_case["avg_write_time"] = sum(write_times) / len(write_times)
                if filter_times:
                    test_case["avg_filter_time"] = sum(filter_times) / len(filter_times)
                if aggregate_times:
                    test_case["avg_aggregate_time"] = sum(aggregate_times) / len(aggregate_times)
                
                results["test_cases"].append(test_case)
    
    # Calculate overall summary
    if all_read_times:
        results["summary"]["avg_read_time"] = sum(all_read_times) / len(all_read_times)
    if all_write_times:
        results["summary"]["avg_write_time"] = sum(all_write_times) / len(all_write_times)
    if all_filter_times:
        results["summary"]["avg_filter_time"] = sum(all_filter_times) / len(all_filter_times)
    if all_aggregate_times:
        results["summary"]["avg_aggregate_time"] = sum(all_aggregate_times) / len(all_aggregate_times)
    
    results["end_time"] = time.time()
    results["total_execution_time"] = results["end_time"] - results["start_time"]
    
    return results


def main():
    """Main entry point for CSV processing test."""
    if len(sys.argv) < 2:
        print("Usage: python csv_processing.py <config_file>", file=sys.stderr)
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        parameters = config.get("parameters", {})
        results = run_csv_processing_benchmark(parameters)
        
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