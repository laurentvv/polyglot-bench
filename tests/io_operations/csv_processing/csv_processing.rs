use std::env;
use std::time::Instant;
use serde_json::{json, Value};
use rand::Rng;
use rand::seq::SliceRandom;

fn generate_csv_data(rows: usize, cols: usize, data_type: &str) -> Vec<Vec<String>> {
    let mut rng = rand::thread_rng();
    let mut data = Vec::new();
    
    // Headers
    let headers: Vec<String> = (0..cols).map(|i| format!("col_{}", i + 1)).collect();
    data.push(headers);
    
    // Data rows
    for _ in 0..rows {
        let mut row = Vec::new();
        for col in 0..cols {
            let value = match data_type {
                "numeric" => format!("{:.2}", rng.gen_range(0.0..1000.0)),
                "text" => {
                    let len = rng.gen_range(5..16);
                    (0..len).map(|_| (b'a' + rng.gen_range(0..26)) as char).collect()
                },
                "mixed" => {
                    match col % 3 {
                        0 => rng.gen_range(1..10001).to_string(),
                        1 => (0..10).map(|_| (b'a' + rng.gen_range(0..26)) as char).collect(),
                        _ => format!("{:.2}", rng.gen_range(0.0..1000.0)),
                    }
                },
                _ => "default".to_string(),
            };
            row.push(value);
        }
        data.push(row);
    }
    
    data
}

fn write_csv_to_string(data: &[Vec<String>]) -> String {
    data.iter()
        .map(|row| row.join(","))
        .collect::<Vec<String>>()
        .join("\n") + "\n"
}

fn read_csv_from_string(csv_string: &str) -> Vec<Vec<String>> {
    csv_string
        .trim()
        .lines()
        .map(|line| line.split(',').map(|s| s.to_string()).collect())
        .collect()
}

fn filter_csv_data(data: &[Vec<String>], filter_column: usize) -> Vec<Vec<String>> {
    if data.is_empty() || data.len() < 2 {
        return data.to_vec();
    }
    
    let mut filtered_data = vec![data[0].clone()]; // Headers
    
    for row in &data[1..] {
        if row.len() > filter_column {
            // Try numeric filter
            if let Ok(value) = row[filter_column].parse::<f64>() {
                if value > 500.0 {
                    filtered_data.push(row.clone());
                }
            } else if row[filter_column].len() > 5 {
                // String length filter
                filtered_data.push(row.clone());
            }
        }
    }
    
    filtered_data
}

fn aggregate_csv_data(data: &[Vec<String>]) -> Value {
    if data.is_empty() || data.len() < 2 {
        return json!({});
    }
    
    let headers = &data[0];
    let mut numeric_columns = Vec::new();
    
    // Find numeric columns
    for (col_idx, _) in headers.iter().enumerate() {
        let mut is_numeric = true;
        for row in data.iter().take(6).skip(1) { // Check first 5 rows
            if row.len() > col_idx {
                if row[col_idx].parse::<f64>().is_err() {
                    is_numeric = false;
                    break;
                }
            }
        }
        if is_numeric {
            numeric_columns.push(col_idx);
        }
    }
    
    let mut aggregations = serde_json::Map::new();
    
    for &col_idx in &numeric_columns {
        let col_name = &headers[col_idx];
        let mut values = Vec::new();
        
        for row in &data[1..] {
            if row.len() > col_idx {
                if let Ok(value) = row[col_idx].parse::<f64>() {
                    values.push(value);
                }
            }
        }
        
        if !values.is_empty() {
            let sum: f64 = values.iter().sum();
            let avg = sum / values.len() as f64;
            let min = values.iter().fold(f64::INFINITY, |a, &b| a.min(b));
            let max = values.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
            
            aggregations.insert(col_name.clone(), json!({
                "sum": sum,
                "avg": avg,
                "min": min,
                "max": max,
                "count": values.len()
            }));
        }
    }
    
    json!(aggregations)
}

fn run_csv_processing_benchmark() -> Value {
    let start_time = Instant::now();
    
    let row_counts = vec![1000];
    let column_counts = vec![5];
    let data_types = vec!["mixed"];
    let operations = vec!["read", "write", "filter", "aggregate"];
    let iterations = 3;
    
    let mut test_cases = Vec::new();
    let mut total_tests = 0;
    let mut successful_tests = 0;
    let mut all_read_times = Vec::new();
    let mut all_write_times = Vec::new();
    let mut all_filter_times = Vec::new();
    let mut all_aggregate_times = Vec::new();
    
    for &rows in &row_counts {
        for &cols in &column_counts {
            for data_type in &data_types {
                eprintln!("Testing CSV: {} rows x {} cols, type: {}...", rows, cols, data_type);
                
                let mut iteration_results = Vec::new();
                let mut read_times = Vec::new();
                let mut write_times = Vec::new();
                let mut filter_times = Vec::new();
                let mut aggregate_times = Vec::new();
                
                for i in 0..iterations {
                    eprintln!("  Iteration {}/{}...", i + 1, iterations);
                    
                    // Generate test data
                    let csv_data = generate_csv_data(rows, cols, data_type);
                    
                    let mut iteration_result = json!({
                        "iteration": i + 1,
                        "data_size": csv_data.len(),
                        "operations": {}
                    });
                    
                    total_tests += 1;
                    let mut success = true;
                    
                    // Write operation
                    if operations.contains(&"write") {
                        let start = Instant::now();
                        let csv_string = write_csv_to_string(&csv_data);
                        let write_time = start.elapsed().as_secs_f64() * 1000.0;
                        
                        write_times.push(write_time);
                        all_write_times.push(write_time);
                        
                        iteration_result["operations"]["write"] = json!({
                            "success": true,
                            "time_ms": write_time,
                            "output_size": csv_string.len()
                        });
                    }
                    
                    // Read operation
                    if operations.contains(&"read") {
                        let csv_string = write_csv_to_string(&csv_data);
                        
                        let start = Instant::now();
                        let read_data = read_csv_from_string(&csv_string);
                        let read_time = start.elapsed().as_secs_f64() * 1000.0;
                        
                        read_times.push(read_time);
                        all_read_times.push(read_time);
                        
                        iteration_result["operations"]["read"] = json!({
                            "success": true,
                            "time_ms": read_time,
                            "rows_read": read_data.len()
                        });
                    }
                    
                    // Filter operation
                    if operations.contains(&"filter") {
                        let start = Instant::now();
                        let filtered_data = filter_csv_data(&csv_data, 0);
                        let filter_time = start.elapsed().as_secs_f64() * 1000.0;
                        
                        filter_times.push(filter_time);
                        all_filter_times.push(filter_time);
                        
                        iteration_result["operations"]["filter"] = json!({
                            "success": true,
                            "time_ms": filter_time,
                            "original_rows": csv_data.len(),
                            "filtered_rows": filtered_data.len()
                        });
                    }
                    
                    // Aggregate operation
                    if operations.contains(&"aggregate") {
                        let start = Instant::now();
                        let aggregations = aggregate_csv_data(&csv_data);
                        let aggregate_time = start.elapsed().as_secs_f64() * 1000.0;
                        
                        aggregate_times.push(aggregate_time);
                        all_aggregate_times.push(aggregate_time);
                        
                        let aggregated_columns = if let Some(obj) = aggregations.as_object() {
                            obj.len()
                        } else {
                            0
                        };
                        
                        iteration_result["operations"]["aggregate"] = json!({
                            "success": true,
                            "time_ms": aggregate_time,
                            "aggregated_columns": aggregated_columns
                        });
                    }
                    
                    if success {
                        successful_tests += 1;
                    }
                    
                    iteration_results.push(iteration_result);
                }
                
                // Calculate averages
                let avg_read_time = if !read_times.is_empty() {
                    read_times.iter().sum::<f64>() / read_times.len() as f64
                } else { 0.0 };
                
                let avg_write_time = if !write_times.is_empty() {
                    write_times.iter().sum::<f64>() / write_times.len() as f64
                } else { 0.0 };
                
                let avg_filter_time = if !filter_times.is_empty() {
                    filter_times.iter().sum::<f64>() / filter_times.len() as f64
                } else { 0.0 };
                
                let avg_aggregate_time = if !aggregate_times.is_empty() {
                    aggregate_times.iter().sum::<f64>() / aggregate_times.len() as f64
                } else { 0.0 };
                
                let test_case = json!({
                    "row_count": rows,
                    "column_count": cols,
                    "data_type": data_type,
                    "operations": operations,
                    "iterations": iteration_results,
                    "avg_read_time": avg_read_time,
                    "avg_write_time": avg_write_time,
                    "avg_filter_time": avg_filter_time,
                    "avg_aggregate_time": avg_aggregate_time
                });
                
                test_cases.push(test_case);
            }
        }
    }
    
    // Calculate overall summary
    let avg_read_time = if !all_read_times.is_empty() {
        all_read_times.iter().sum::<f64>() / all_read_times.len() as f64
    } else { 0.0 };
    
    let avg_write_time = if !all_write_times.is_empty() {
        all_write_times.iter().sum::<f64>() / all_write_times.len() as f64
    } else { 0.0 };
    
    let avg_filter_time = if !all_filter_times.is_empty() {
        all_filter_times.iter().sum::<f64>() / all_filter_times.len() as f64
    } else { 0.0 };
    
    let avg_aggregate_time = if !all_aggregate_times.is_empty() {
        all_aggregate_times.iter().sum::<f64>() / all_aggregate_times.len() as f64
    } else { 0.0 };
    
    let total_duration = start_time.elapsed().as_secs_f64();
    
    json!({
        "start_time": 0.0,
        "test_cases": test_cases,
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "avg_read_time": avg_read_time,
            "avg_write_time": avg_write_time,
            "avg_filter_time": avg_filter_time,
            "avg_aggregate_time": avg_aggregate_time
        },
        "end_time": total_duration,
        "total_execution_time": total_duration
    })
}

fn main() {
    let results = run_csv_processing_benchmark();
    println!("{}", serde_json::to_string_pretty(&results).unwrap());
}