use std::env;
use std::fs;
use std::time::Instant;
use std::collections::HashMap;
use serde_json::{json, Value};
use rand::Rng;

fn generate_csv_data(rows: usize, cols: usize, data_type: &str) -> Vec<Vec<String>> {
    let mut rng = rand::thread_rng();
    let mut data = Vec::new();
    
    // Generate headers
    let headers: Vec<String> = (1..=cols).map(|i| format!("col_{}", i)).collect();
    data.push(headers);
    
    // Generate data rows
    for _row in 0..rows {
        let mut row_data = Vec::new();
        for col in 0..cols {
            let value = match data_type {
                "numeric" => format!("{:.2}", rng.gen::<f64>() * 1000.0),
                "text" => {
                    let len = rng.gen_range(5..=15);
                    (0..len).map(|_| rng.gen_range(b'a'..=b'z') as char).collect()
                }
                _ => { // mixed
                    match col % 3 {
                        0 => rng.gen_range(1..=10000).to_string(),
                        1 => (0..10).map(|_| rng.gen_range(b'a'..=b'z') as char).collect(),
                        _ => format!("{:.2}", rng.gen::<f64>() * 1000.0),
                    }
                }
            };
            row_data.push(value);
        }
        data.push(row_data);
    }
    
    data
}

fn write_csv_to_string(data: &Vec<Vec<String>>) -> String {
    let mut result = String::new();
    for row in data {
        let row_str = row.join(",");
        result.push_str(&row_str);
        result.push('\n');
    }
    result
}

fn read_csv_from_string(csv_string: &str) -> Vec<Vec<String>> {
    csv_string
        .lines()
        .filter(|line| !line.is_empty())
        .map(|line| line.split(',').map(|s| s.to_string()).collect())
        .collect()
}

fn filter_csv_data(data: &Vec<Vec<String>>, filter_column: usize) -> Vec<Vec<String>> {
    if data.is_empty() || data.len() < 2 {
        return data.clone();
    }
    
    let mut filtered_data = vec![data[0].clone()]; // Keep headers
    
    for row in &data[1..] {
        if row.len() > filter_column {
            if let Ok(value) = row[filter_column].parse::<f64>() {
                if value > 500.0 {
                    filtered_data.push(row.clone());
                }
            } else if row[filter_column].len() > 5 {
                filtered_data.push(row.clone());
            }
        }
    }
    
    filtered_data
}

fn aggregate_csv_data(data: &Vec<Vec<String>>) -> HashMap<String, HashMap<String, f64>> {
    if data.is_empty() || data.len() < 2 {
        return HashMap::new();
    }
    
    let headers = &data[0];
    let mut numeric_columns = Vec::new();
    
    // Find numeric columns
    for col_idx in 0..headers.len() {
        let mut is_numeric = true;
        for row in &data[1..std::cmp::min(6, data.len())] {
            if col_idx < row.len() {
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
    
    let mut aggregations = HashMap::new();
    
    for &col_idx in &numeric_columns {
        let col_name = &headers[col_idx];
        let mut values = Vec::new();
        
        for row in &data[1..] {
            if col_idx < row.len() {
                if let Ok(value) = row[col_idx].parse::<f64>() {
                    values.push(value);
                }
            }
        }
        
        if !values.is_empty() {
            let mut stats = HashMap::new();
            stats.insert("sum".to_string(), values.iter().sum());
            stats.insert("avg".to_string(), values.iter().sum::<f64>() / values.len() as f64);
            stats.insert("min".to_string(), *values.iter().min_by(|a, b| a.partial_cmp(b).unwrap()).unwrap());
            stats.insert("max".to_string(), *values.iter().max_by(|a, b| a.partial_cmp(b).unwrap()).unwrap());
            stats.insert("count".to_string(), values.len() as f64);
            
            aggregations.insert(col_name.clone(), stats);
        }
    }
    
    aggregations
}

fn run_csv_processing_benchmark(config: &Value) -> Value {
    let parameters = &config["parameters"];
    
    let row_counts: Vec<usize> = parameters["row_counts"]
        .as_array()
        .unwrap_or(&vec![json!(1000)])
        .iter()
        .map(|v| v.as_u64().unwrap() as usize)
        .collect();
    
    let column_counts: Vec<usize> = parameters["column_counts"]
        .as_array()
        .unwrap_or(&vec![json!(5)])
        .iter()
        .map(|v| v.as_u64().unwrap() as usize)
        .collect();
    
    let operations: Vec<String> = parameters["operations"]
        .as_array()
        .unwrap_or(&vec![json!("read"), json!("write")])
        .iter()
        .map(|v| v.as_str().unwrap().to_string())
        .collect();
    
    let data_types: Vec<String> = parameters["data_types"]
        .as_array()
        .unwrap_or(&vec![json!("mixed")])
        .iter()
        .map(|v| v.as_str().unwrap().to_string())
        .collect();
    
    let iterations = parameters["iterations"].as_u64().unwrap_or(3) as usize;
    
    let start_time = Instant::now();
    let mut test_cases = Vec::new();
    let mut all_read_times = Vec::new();
    let mut all_write_times = Vec::new();
    let mut all_filter_times = Vec::new();
    let mut all_aggregate_times = Vec::new();
    let mut total_tests = 0;
    let mut successful_tests = 0;
    let mut failed_tests = 0;
    
    for &rows in &row_counts {
        for &cols in &column_counts {
            for data_type in &data_types {
                eprintln!("Testing CSV: {} rows x {} cols, type: {}...", rows, cols, data_type);
                
                let mut read_times = Vec::new();
                let mut write_times = Vec::new();
                let mut filter_times = Vec::new();
                let mut aggregate_times = Vec::new();
                let mut iterations_data = Vec::new();
                
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
                    if operations.contains(&"write".to_string()) {
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
                    if operations.contains(&"read".to_string()) {
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
                    if operations.contains(&"filter".to_string()) {
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
                    if operations.contains(&"aggregate".to_string()) {
                        let start = Instant::now();
                        let aggregations = aggregate_csv_data(&csv_data);
                        let aggregate_time = start.elapsed().as_secs_f64() * 1000.0;
                        
                        aggregate_times.push(aggregate_time);
                        all_aggregate_times.push(aggregate_time);
                        
                        iteration_result["operations"]["aggregate"] = json!({
                            "success": true,
                            "time_ms": aggregate_time,
                            "aggregated_columns": aggregations.len()
                        });
                    }
                    
                    if success {
                        successful_tests += 1;
                    } else {
                        failed_tests += 1;
                    }
                    
                    iterations_data.push(iteration_result);
                }
                
                let test_case = json!({
                    "row_count": rows,
                    "column_count": cols,
                    "data_type": data_type,
                    "operations": operations,
                    "iterations": iterations_data,
                    "avg_read_time": if read_times.is_empty() { 0.0 } else { read_times.iter().sum::<f64>() / read_times.len() as f64 },
                    "avg_write_time": if write_times.is_empty() { 0.0 } else { write_times.iter().sum::<f64>() / write_times.len() as f64 },
                    "avg_filter_time": if filter_times.is_empty() { 0.0 } else { filter_times.iter().sum::<f64>() / filter_times.len() as f64 },
                    "avg_aggregate_time": if aggregate_times.is_empty() { 0.0 } else { aggregate_times.iter().sum::<f64>() / aggregate_times.len() as f64 }
                });
                
                test_cases.push(test_case);
            }
        }
    }
    
    let total_execution_time = start_time.elapsed().as_secs_f64();
    
    json!({
        "start_time": 0, // Placeholder
        "test_cases": test_cases,
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "avg_read_time": if all_read_times.is_empty() { 0.0 } else { all_read_times.iter().sum::<f64>() / all_read_times.len() as f64 },
            "avg_write_time": if all_write_times.is_empty() { 0.0 } else { all_write_times.iter().sum::<f64>() / all_write_times.len() as f64 },
            "avg_filter_time": if all_filter_times.is_empty() { 0.0 } else { all_filter_times.iter().sum::<f64>() / all_filter_times.len() as f64 },
            "avg_aggregate_time": if all_aggregate_times.is_empty() { 0.0 } else { all_aggregate_times.iter().sum::<f64>() / all_aggregate_times.len() as f64 }
        },
        "end_time": 0, // Placeholder
        "total_execution_time": total_execution_time
    })
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <config_file>", args[0]);
        std::process::exit(1);
    }
    
    let config_file = &args[1];
    
    let config_content = match fs::read_to_string(config_file) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Error: Config file '{}' not found: {}", config_file, e);
            std::process::exit(1);
        }
    };
    
    let config: Value = match serde_json::from_str(&config_content) {
        Ok(config) => config,
        Err(e) => {
            eprintln!("Error: Invalid JSON in config file: {}", e);
            std::process::exit(1);
        }
    };
    
    let results = run_csv_processing_benchmark(&config);
    println!("{}", serde_json::to_string_pretty(&results).unwrap());
}