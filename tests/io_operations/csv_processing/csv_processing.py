#!/usr/bin/env python3
"""
CSV processing test implementation in Python.
Measures CSV file read, write, filtering, and aggregation performance.
"""

import json
import sys
import time
import csv
import random
import string
import tempfile
import os
from typing import Dict, List, Any, Union
from io import StringIO


def generate_csv_data(rows: int, cols: int, data_type: str) -> List[List[str]]:
    """Generate CSV data with specified dimensions and data types."""
    headers = [f"col_{i+1}" for i in range(cols)]
    data = [headers]
    
    for row in range(rows):
        row_data = []
        for col in range(cols):
            if data_type == "numeric":
                value = str(round(random.uniform(0, 1000), 2))
            elif data_type == "text":
                value = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 15)))
            else:  # mixed
                if col % 3 == 0:
                    value = str(random.randint(1, 10000))
                elif col % 3 == 1:
                    value = ''.join(random.choices(string.ascii_letters, k=10))
                else:
                    value = str(round(random.uniform(0, 1000), 2))
            
            row_data.append(value)
        data.append(row_data)
    
    return data


def write_csv_to_string(data: List[List[str]]) -> str:
    """Write CSV data to string format."""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue()


def read_csv_from_string(csv_string: str) -> List[List[str]]:
    """Read CSV data from string format."""
    input_stream = StringIO(csv_string)
    reader = csv.reader(input_stream)
    return list(reader)


def filter_csv_data(data: List[List[str]], filter_column: int = 0) -> List[List[str]]:
    """Filter CSV data based on a condition."""
    if not data or len(data) < 2:
        return data
    
    headers = data[0]
    filtered_data = [headers]
    
    for row in data[1:]:
        if len(row) > filter_column:
            try:
                # Try to convert to number for filtering
                value = float(row[filter_column])
                if value > 500:  # Simple filter condition
                    filtered_data.append(row)
            except ValueError:
                # If not numeric, filter by string length
                if len(row[filter_column]) > 5:
                    filtered_data.append(row)
    
    return filtered_data


def aggregate_csv_data(data: List[List[str]]) -> Dict[str, Any]:
    """Perform aggregation operations on CSV data."""
    if not data or len(data) < 2:
        return {}
    
    headers = data[0]
    numeric_columns = []
    
    # Find numeric columns
    for col_idx in range(len(headers)):
        is_numeric = True
        for row in data[1:6]:  # Check first 5 rows
            if len(row) > col_idx:
                try:
                    float(row[col_idx])
                except ValueError:
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
                try:
                    values.append(float(row[col_idx]))
                except ValueError:
                    continue
        
        if values:
            aggregations[col_name] = {
                "sum": sum(values),
                "avg": sum(values) / len(values),
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