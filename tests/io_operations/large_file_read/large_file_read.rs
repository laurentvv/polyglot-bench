use serde_json::{json, Value};
use std::env;
use std::fs::File;
use std::io::{Read, Write};
use std::path::Path;
use std::time::Instant;

use rand::prelude::*;
use tempfile::TempDir;

#[derive(Debug)]
struct ReadResult {
    read_time: f64,
    bytes_read: u64,
    throughput_mbps: f64,
    chunk_count: Option<u32>,
    avg_chunk_size: Option<f64>,
}

fn generate_test_file(file_path: &Path, size_bytes: u64) -> Result<(), Box<dyn std::error::Error>> {
    eprintln!("Generating test file: {} bytes...", size_bytes);
    
    let mut file = File::create(file_path)?;
    let mut rng = thread_rng();
    let chunk_size = 8192;
    
    let mut bytes_written = 0u64;
    while bytes_written < size_bytes {
        let remaining = size_bytes - bytes_written;
        let current_chunk_size = if remaining < chunk_size { remaining } else { chunk_size } as usize;
        
        // Generate random text data
        let data: String = (0..current_chunk_size)
            .map(|_| {
                let chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n";
                chars.chars().choose(&mut rng).unwrap()
            })
            .collect();
        
        file.write_all(data.as_bytes())?;
        bytes_written += current_chunk_size as u64;
    }
    
    file.flush()?;
    Ok(())
}

fn read_file_sequential(file_path: &Path, buffer_size: usize) -> Result<ReadResult, Box<dyn std::error::Error>> {
    let start_time = Instant::now();
    let mut file = File::open(file_path)?;
    let mut buffer = vec![0u8; buffer_size];
    let mut total_bytes = 0u64;
    
    loop {
        let bytes_read = file.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }
        total_bytes += bytes_read as u64;
    }
    
    let read_time = start_time.elapsed().as_secs_f64();
    let throughput_mbps = if read_time > 0.0 {
        (total_bytes as f64 / (1024.0 * 1024.0)) / read_time
    } else {
        0.0
    };
    
    Ok(ReadResult {
        read_time: read_time * 1000.0, // Convert to milliseconds
        bytes_read: total_bytes,
        throughput_mbps,
        chunk_count: None,
        avg_chunk_size: None,
    })
}

fn read_file_chunked(file_path: &Path, buffer_size: usize) -> Result<ReadResult, Box<dyn std::error::Error>> {
    let start_time = Instant::now();
    let mut file = File::open(file_path)?;
    let mut buffer = vec![0u8; buffer_size];
    let mut total_bytes = 0u64;
    let mut chunk_count = 0u32;
    
    loop {
        let bytes_read = file.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }
        total_bytes += bytes_read as u64;
        chunk_count += 1;
    }
    
    let read_time = start_time.elapsed().as_secs_f64();
    let throughput_mbps = if read_time > 0.0 {
        (total_bytes as f64 / (1024.0 * 1024.0)) / read_time
    } else {
        0.0
    };
    
    let avg_chunk_size = if chunk_count > 0 {
        total_bytes as f64 / chunk_count as f64
    } else {
        0.0
    };
    
    Ok(ReadResult {
        read_time: read_time * 1000.0, // Convert to milliseconds
        bytes_read: total_bytes,
        throughput_mbps,
        chunk_count: Some(chunk_count),
        avg_chunk_size: Some(avg_chunk_size),
    })
}

fn get_memory_usage() -> f64 {
    // Simple memory usage approximation for Rust
    // In a real implementation, you might use external crates for more accurate measurement
    0.0
}

fn run_large_file_read_benchmark(config: &Value) -> Result<Value, Box<dyn std::error::Error>> {
    let parameters = config.as_object().unwrap();
    
    let file_sizes: Vec<u64> = parameters
        .get("file_sizes")
        .and_then(|v| v.as_array())
        .map(|arr| arr.iter().filter_map(|v| v.as_u64()).collect())
        .unwrap_or_else(|| vec![1048576]); // Default 1MB
    
    let buffer_sizes: Vec<usize> = parameters
        .get("buffer_sizes")
        .and_then(|v| v.as_array())
        .map(|arr| arr.iter().filter_map(|v| v.as_u64().map(|u| u as usize)).collect())
        .unwrap_or_else(|| vec![4096]);
    
    let read_patterns: Vec<String> = parameters
        .get("read_patterns")
        .and_then(|v| v.as_array())
        .map(|arr| arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect())
        .unwrap_or_else(|| vec!["sequential".to_string()]);
    
    let iterations = parameters
        .get("iterations")
        .and_then(|v| v.as_u64())
        .unwrap_or(3) as u32;
    
    let generate_test_files = parameters
        .get("generate_test_files")
        .and_then(|v| v.as_bool())
        .unwrap_or(true);
    
    let start_time = Instant::now();
    let mut test_cases = Vec::new();
    let mut total_tests = 0u32;
    let mut successful_tests = 0u32;
    let mut failed_tests = 0u32;
    let mut all_read_times = Vec::new();
    let mut all_throughputs = Vec::new();
    let mut peak_memory = 0.0f64;
    
    // Create temporary directory for test files
    let temp_dir = TempDir::new()?;
    
    for file_size in &file_sizes {
        for buffer_size in &buffer_sizes {
            for pattern in &read_patterns {
                eprintln!("Testing file size: {} bytes, buffer: {}, pattern: {}...", file_size, buffer_size, pattern);
                
                let mut test_case = json!({
                    "file_size": file_size,
                    "buffer_size": buffer_size,
                    "read_pattern": pattern,
                    "iterations": [],
                    "avg_read_time": 0.0,
                    "avg_throughput": 0.0,
                    "memory_efficiency": 0.0
                });
                
                // Generate test file if needed
                let test_file_path = temp_dir.path().join(format!("test_file_{}_{}.txt", file_size, buffer_size));
                if generate_test_files && !test_file_path.exists() {
                    generate_test_file(&test_file_path, *file_size)?;
                }
                
                let mut read_times = Vec::new();
                let mut throughputs = Vec::new();
                let mut iterations_array = Vec::new();
                
                for i in 0..iterations {
                    eprintln!("  Iteration {}/{}...", i + 1, iterations);
                    total_tests += 1;
                    
                    match perform_read_test(&test_file_path, *buffer_size, pattern) {
                        Ok(read_result) => {
                            let memory_usage = get_memory_usage();
                            peak_memory = peak_memory.max(memory_usage);
                            
                            let mut iteration_result = json!({
                                "iteration": i + 1,
                                "read_time": read_result.read_time,
                                "bytes_read": read_result.bytes_read,
                                "throughput_mbps": read_result.throughput_mbps,
                                "memory_used": memory_usage,
                                "io_wait_time": read_result.read_time
                            });
                            
                            if let (Some(chunk_count), Some(avg_chunk_size)) = (read_result.chunk_count, read_result.avg_chunk_size) {
                                iteration_result["chunk_count"] = json!(chunk_count);
                                iteration_result["avg_chunk_size"] = json!(avg_chunk_size);
                            }
                            
                            iterations_array.push(iteration_result);
                            read_times.push(read_result.read_time);
                            throughputs.push(read_result.throughput_mbps);
                            successful_tests += 1;
                        }
                        Err(e) => {
                            eprintln!("Error in iteration {}: {}", i + 1, e);
                            failed_tests += 1;
                            iterations_array.push(json!({
                                "iteration": i + 1,
                                "error": e.to_string(),
                                "read_time": 0.0,
                                "throughput_mbps": 0.0
                            }));
                        }
                    }
                }
                
                // Calculate averages for this test case
                if !read_times.is_empty() {
                    let avg_read_time = read_times.iter().sum::<f64>() / read_times.len() as f64;
                    let avg_throughput = throughputs.iter().sum::<f64>() / throughputs.len() as f64;
                    let memory_efficiency = (*file_size as f64 / (1024.0 * 1024.0)) / peak_memory.max(1.0);
                    
                    test_case["avg_read_time"] = json!(avg_read_time);
                    test_case["avg_throughput"] = json!(avg_throughput);
                    test_case["memory_efficiency"] = json!(memory_efficiency);
                    
                    all_read_times.extend(&read_times);
                    all_throughputs.extend(&throughputs);
                }
                
                test_case["iterations"] = json!(iterations_array);
                test_cases.push(test_case);
            }
        }
    }
    
    let end_time = Instant::now();
    let total_duration = (end_time - start_time).as_secs_f64();
    
    let avg_read_time = if !all_read_times.is_empty() {
        all_read_times.iter().sum::<f64>() / all_read_times.len() as f64
    } else {
        0.0
    };
    
    let avg_throughput = if !all_throughputs.is_empty() {
        all_throughputs.iter().sum::<f64>() / all_throughputs.len() as f64
    } else {
        0.0
    };
    
    Ok(json!({
        "start_time": start_time.elapsed().as_secs_f64(),
        "end_time": end_time.elapsed().as_secs_f64(),
        "total_duration": total_duration,
        "test_cases": test_cases,
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "avg_read_time": avg_read_time,
            "avg_throughput": avg_throughput,
            "peak_memory_usage": peak_memory
        }
    }))
}

fn perform_read_test(file_path: &Path, buffer_size: usize, pattern: &str) -> Result<ReadResult, Box<dyn std::error::Error>> {
    match pattern {
        "sequential" => read_file_sequential(file_path, buffer_size),
        "chunked" => read_file_chunked(file_path, buffer_size),
        _ => Err(format!("Unknown read pattern: {}", pattern).into()),
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    
    if args.len() != 2 {
        eprintln!("Usage: {} <input_file>", args[0]);
        std::process::exit(1);
    }
    
    let input_file = &args[1];
    
    // Read and parse input configuration
    let config_content = std::fs::read_to_string(input_file)?;
    let config: Value = serde_json::from_str(&config_content)?;
    
    let parameters = config.get("parameters")
        .ok_or("Missing 'parameters' in configuration")?;
    
    let result = run_large_file_read_benchmark(parameters)?;
    
    // Output results as JSON
    println!("{}", serde_json::to_string_pretty(&result)?);
    
    Ok(())
}