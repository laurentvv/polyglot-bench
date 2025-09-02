use std::env;
use std::fs;
use std::time::Instant;
use std::collections::HashMap;
use serde_json::{json, Value};
use rand::Rng;
use rand::seq::SliceRandom;

// Optimized structures for better performance
#[derive(Debug, Clone)]
enum OptimizedValue {
    String(String),
    Number(f64),
    Bool(bool),
    Object(HashMap<String, OptimizedValue>),
    Array(Vec<OptimizedValue>),
}

fn generate_flat_json(size: usize) -> Value {
    let mut data = HashMap::new();
    let mut rng = rand::thread_rng();
    
    for i in 0..size {
        let key = format!("key_{}", i);
        let value_type = rng.gen_range(0..3);
        
        let value = match value_type {
            0 => Value::String(format!("value_{}", rng.gen_range(0..1000))),
            1 => Value::Number(serde_json::Number::from(rng.gen_range(1..1000))),
            _ => Value::Bool(rng.gen_bool(0.5)),
        };
        
        data.insert(key, value);
    }
    
    json!(data)
}

fn generate_nested_json(size: usize, max_depth: usize) -> Value {
    fn create_nested_object(remaining_size: usize, current_depth: usize, max_depth: usize, rng: &mut rand::rngs::ThreadRng) -> Value {
        if remaining_size == 0 || current_depth >= max_depth {
            let choice = rng.gen_range(0..3);
            return match choice {
                0 => Value::String(format!("leaf_{}", rng.gen_range(0..100))),
                1 => Value::Number(serde_json::Number::from(rng.gen_range(1..100))),
                _ => Value::Bool(rng.gen_bool(0.5)),
            };
        }
        
        if rng.gen_bool(0.6) {
            // Create object
            let mut obj = HashMap::new();
            let keys_count = std::cmp::min(rng.gen_range(2..6), remaining_size);
            let remaining_per_key = remaining_size / keys_count;
            
            for i in 0..keys_count {
                let key = format!("nested_key_{}", i);
                obj.insert(key, create_nested_object(remaining_per_key, current_depth + 1, max_depth, rng));
            }
            json!(obj)
        } else {
            // Create array
            let items_count = std::cmp::min(rng.gen_range(2..5), remaining_size);
            let remaining_per_item = remaining_size / items_count;
            
            let mut arr = Vec::new();
            for _ in 0..items_count {
                arr.push(create_nested_object(remaining_per_item, current_depth + 1, max_depth, rng));
            }
            json!(arr)
        }
    }
    
    let mut rng = rand::thread_rng();
    json!({
        "root": create_nested_object(size, 0, max_depth, &mut rng)
    })
}

fn generate_array_heavy_json(size: usize) -> Value {
    let mut rng = rand::thread_rng();
    let items_per_array = size / 3;
    
    let mut users = Vec::new();
    let mut products = Vec::new();
    let mut orders = Vec::new();
    
    // Users array
    for i in 0..items_per_array {
        users.push(json!({
            "id": i,
            "name": format!("User_{}", i),
            "email": format!("user{}@example.com", i),
            "active": rng.gen_bool(0.5)
        }));
    }
    
    // Products array
    let categories = ["electronics", "clothing", "books", "home"];
    for i in 0..items_per_array {
        products.push(json!({
            "id": i,
            "name": format!("Product_{}", i),
            "price": (rng.gen::<f64>() * 490.0 + 10.0).round() / 100.0,
            "category": categories.choose(&mut rng).unwrap()
        }));
    }
    
    // Orders array
    for i in 0..items_per_array {
        let product_count = rng.gen_range(1..6);
        let mut product_ids = Vec::new();
        for _ in 0..product_count {
            product_ids.push(rng.gen_range(0..items_per_array));
        }
        
        orders.push(json!({
            "id": i,
            "user_id": rng.gen_range(0..items_per_array),
            "product_ids": product_ids,
            "total": (rng.gen::<f64>() * 980.0 + 20.0).round() / 100.0,
            "timestamp": format!("2024-{:02}-{:02}", rng.gen_range(1..13), rng.gen_range(1..29))
        }));
    }
    
    json!({
        "users": users,
        "products": products,
        "orders": orders
    })
}

fn generate_mixed_json(size: usize) -> Value {
    let mut rng = rand::thread_rng();
    let mut data = Vec::new();
    
    for i in 0..size {
        let record_type = ["A", "B", "C"].choose(&mut rng).unwrap();
        let tags = ["urgent", "normal", "low", "critical"];
        let tag_count = rng.gen_range(1..3);
        let selected_tags: Vec<&str> = tags.choose_multiple(&mut rng, tag_count).cloned().collect();
        
        let mut relationships = Vec::new();
        for _ in 0..rng.gen_range(0..4) {
            relationships.push(json!({
                "id": rng.gen_range(0..size),
                "type": "related"
            }));
        }
        
        data.push(json!({
            "id": i,
            "type": record_type,
            "attributes": {
                "name": format!("Item_{}", i),
                "value": rng.gen_range(1..1001),
                "tags": selected_tags
            },
            "relationships": relationships
        }));
    }
    
    json!({
        "metadata": {
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "total_records": size
        },
        "config": {
            "settings": {
                "debug": true,
                "cache_enabled": false,
                "timeout": 30
            }
        },
        "data": data
    })
}

// Optimized traversal function that avoids recursion overhead
fn traverse_json(data: &Value) -> usize {
    let mut count = 0;
    let mut stack = vec![data];
    
    while let Some(current) = stack.pop() {
        count += 1;
        
        match current {
            Value::Object(map) => {
                for (_, value) in map {
                    stack.push(value);
                }
            }
            Value::Array(arr) => {
                for item in arr {
                    stack.push(item);
                }
            }
            _ => {}
        }
    }
    
    count
}

fn run_json_parsing_benchmark(config: &Value) -> Value {
    let parameters = &config["parameters"];
    
    let json_sizes: Vec<usize> = parameters["json_sizes"]
        .as_array()
        .unwrap_or(&vec![json!(1000)])
        .iter()
        .map(|v| v.as_u64().unwrap() as usize)
        .collect();
    
    let structures: Vec<String> = parameters["json_structures"]
        .as_array()
        .unwrap_or(&vec![json!("flat")])
        .iter()
        .map(|v| v.as_str().unwrap().to_string())
        .collect();
    
    let operations: Vec<String> = parameters["operations"]
        .as_array()
        .unwrap_or(&vec![json!("parse")])
        .iter()
        .map(|v| v.as_str().unwrap().to_string())
        .collect();
    
    let iterations = parameters["iterations"].as_u64().unwrap_or(5) as usize;
    
    let start_time = Instant::now();
    let mut test_cases = Vec::new();
    let mut all_parse_times = Vec::new();
    let mut all_stringify_times = Vec::new();
    let mut all_traverse_times = Vec::new();
    let mut total_tests = 0;
    let mut successful_tests = 0;
    let mut failed_tests = 0;
    
    // Pre-allocate vectors for better performance
    all_parse_times.reserve(json_sizes.len() * structures.len() * iterations);
    all_stringify_times.reserve(json_sizes.len() * structures.len() * iterations);
    all_traverse_times.reserve(json_sizes.len() * structures.len() * iterations);
    
    for size in &json_sizes {
        for structure in &structures {
            eprintln!("Testing {} JSON, size: {}...", structure, size);
            
            let mut parse_times = Vec::new();
            let mut stringify_times = Vec::new();
            let mut traverse_times = Vec::new();
            let mut iterations_data = Vec::new();
            
            // Pre-allocate vectors for better performance
            parse_times.reserve(iterations);
            stringify_times.reserve(iterations);
            traverse_times.reserve(iterations);
            iterations_data.reserve(iterations);
            
            for i in 0..iterations {
                eprintln!("  Iteration {}/{}...", i + 1, iterations);
                
                // Generate test data
                let json_data = match structure.as_str() {
                    "flat" => generate_flat_json(*size),
                    "nested" => generate_nested_json(*size, 5),
                    "array_heavy" => generate_array_heavy_json(*size),
                    "mixed" => generate_mixed_json(*size),
                    _ => {
                        eprintln!("Warning: Structure {} not implemented, using flat", structure);
                        generate_flat_json(*size)
                    }
                };
                
                // Optimize data size calculation by avoiding repeated serialization
                let json_string = serde_json::to_string(&json_data).unwrap();
                let data_size = json_string.len();
                
                let mut iteration_result = json!({
                    "iteration": i + 1,
                    "data_size": data_size,
                    "operations": {}
                });
                
                total_tests += 1;
                let mut success = true;
                
                // Parse operation
                if operations.contains(&"parse".to_string()) {
                    let start = Instant::now();
                    match serde_json::from_str::<Value>(&json_string) {
                        Ok(_) => {
                            let parse_time = start.elapsed().as_secs_f64() * 1000.0;
                            parse_times.push(parse_time);
                            all_parse_times.push(parse_time);
                            
                            iteration_result["operations"]["parse"] = json!({
                                "success": true,
                                "time_ms": parse_time,
                                "json_string_length": json_string.len()
                            });
                        }
                        Err(e) => {
                            success = false;
                            iteration_result["operations"]["parse"] = json!({
                                "success": false,
                                "error": e.to_string()
                            });
                        }
                    }
                }
                
                // Stringify operation
                if operations.contains(&"stringify".to_string()) {
                    let start = Instant::now();
                    match serde_json::to_string(&json_data) {
                        Ok(json_string) => {
                            let stringify_time = start.elapsed().as_secs_f64() * 1000.0;
                            stringify_times.push(stringify_time);
                            all_stringify_times.push(stringify_time);
                            
                            iteration_result["operations"]["stringify"] = json!({
                                "success": true,
                                "time_ms": stringify_time,
                                "output_length": json_string.len()
                            });
                        }
                        Err(e) => {
                            success = false;
                            iteration_result["operations"]["stringify"] = json!({
                                "success": false,
                                "error": e.to_string()
                            });
                        }
                    }
                }
                
                // Traverse operation
                if operations.contains(&"traverse".to_string()) {
                    let start = Instant::now();
                    let operation_count = traverse_json(&json_data);
                    let traverse_time = start.elapsed().as_secs_f64() * 1000.0;
                    
                    traverse_times.push(traverse_time);
                    all_traverse_times.push(traverse_time);
                    
                    iteration_result["operations"]["traverse"] = json!({
                        "success": true,
                        "time_ms": traverse_time,
                        "operations_count": operation_count
                    });
                }
                
                if success {
                    successful_tests += 1;
                } else {
                    failed_tests += 1;
                }
                
                iterations_data.push(iteration_result);
            }
            
            // Calculate averages for this test case
            let avg_parse_time = if !parse_times.is_empty() {
                parse_times.iter().sum::<f64>() / parse_times.len() as f64
            } else { 0.0 };
            
            let avg_stringify_time = if !stringify_times.is_empty() {
                stringify_times.iter().sum::<f64>() / stringify_times.len() as f64
            } else { 0.0 };
            
            let avg_traverse_time = if !traverse_times.is_empty() {
                traverse_times.iter().sum::<f64>() / traverse_times.len() as f64
            } else { 0.0 };
            
            let test_case = json!({
                "json_size": size,
                "structure_type": structure,
                "operations": operations,
                "iterations": iterations_data,
                "avg_parse_time": avg_parse_time,
                "avg_stringify_time": avg_stringify_time,
                "avg_traverse_time": avg_traverse_time
            });
            
            test_cases.push(test_case);
        }
    }
    
    // Calculate overall summary
    let avg_parse_time = if !all_parse_times.is_empty() {
        all_parse_times.iter().sum::<f64>() / all_parse_times.len() as f64
    } else { 0.0 };
    
    let avg_stringify_time = if !all_stringify_times.is_empty() {
        all_stringify_times.iter().sum::<f64>() / all_stringify_times.len() as f64
    } else { 0.0 };
    
    let avg_traverse_time = if !all_traverse_times.is_empty() {
        all_traverse_times.iter().sum::<f64>() / all_traverse_times.len() as f64
    } else { 0.0 };
    
    let total_execution_time = start_time.elapsed().as_secs_f64();
    
    json!({
        "start_time": 0, // Placeholder
        "test_cases": test_cases,
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "avg_parse_time": avg_parse_time,
            "avg_stringify_time": avg_stringify_time,
            "avg_traverse_time": avg_traverse_time
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
    
    let results = run_json_parsing_benchmark(&config);
    println!("{}", serde_json::to_string_pretty(&results).unwrap());
}