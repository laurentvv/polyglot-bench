use serde_json::{json, Value};
use std::env;
use std::fs::File;
use std::io::{BufReader, Read, Write};
use std::time::Instant;
use std::path::Path;
use rand::prelude::*;

fn generate_test_file(file_path: &Path, size_bytes: usize) -> Result<(), Box<dyn std::error::Error>> {
    eprintln!("Generating test file: {} bytes...", size_bytes);
    
    let mut file = File::create(file_path)?;
    let chunk_size = 8192;
    let chars = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n";
    
    let mut bytes_written = 0;
    let mut rng = thread_rng();
    
    while bytes_written < size_bytes {
        let remaining = size_bytes - bytes_written;
        let current_chunk_size = std::cmp::min(chunk_size, remaining);
        
        let mut data = vec![0u8; current_chunk_size];
        for byte in &mut data {
            *byte = chars[rng.gen_range(0..chars.len())];
        }
        
        file.write_all(&data)?;
        bytes_written += current_chunk_size;
    }
    
    file.sync_all()?;
    Ok(())
}

fn read_file_sequential(file_path: &Path, buffer_size: usize) -> Result<Value, Box<dyn std::error::Error>> {
    let start_time = Instant::now();
    
    let file = File::open(file_path)?;
    let mut reader = BufReader::with_capacity(buffer_size, file);
    let mut buffer = vec![0u8; buffer_size];
    let mut total_bytes = 0;
    
    loop {
        let bytes_read = reader.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }
        total_bytes += bytes_read;
    }
    
    let read_time = start_time.elapsed().as_secs_f64() * 1000.0; // ms
    let throughput_mbps = if read_time > 0.0 {
        (total_bytes as f64 / (1024.0 * 1024.0)) / (read_time / 1000.0)
    } else {
        0.0
    };
    
    Ok(json!({
        "read_time": read_time,
        "bytes_read": total_bytes,
        "throughput_mbps": throughput_mbps
    }))
}

fn read_file_chunked(file_path: &Path, buffer_size: usize) -> Result<Value, Box<dyn std::error::Error>> {
    let start_time = Instant::now();
    
    let file = File::open(file_path)?;
    let mut reader = BufReader::with_capacity(buffer_size, file);
    let mut buffer = vec![0u8; buffer_size];
    let mut total_bytes = 0;
    let mut chunk_count = 0;
    
    loop {
        let bytes_read = reader.read(&mut buffer)?;
        if bytes_read == 0 {
            break;
        }
        total_bytes += bytes_read;
        chunk_count += 1;
    }
    
    let read_time = start_time.elapsed().as_secs_f64() * 1000.0; // ms
    let throughput_mbps = if read_time > 0.0 {
        (total_bytes as f64 / (1024.0 * 1024.0)) / (read_time / 1000.0)
    } else {
        0.0
    };
    
    let avg_chunk_size = if chunk_count > 0 {
        total_bytes as f64 / chunk_count as f64
    } else {
        0.0
    };
    
    Ok(json!({
        "read_time": read_time,
        "bytes_read": total_bytes,
        "throughput_mbps": throughput_mbps,
        "chunk_count": chunk_count,
        "avg_chunk_size": avg_chunk_size
    }))
}

fn run_large_file_read_benchmark() -> Result<Value, Box<dyn std::error::Error>> {
    let file_sizes = vec![1048576, 10485760]; // 1MB, 10MB
    let buffer_sizes = vec![4096, 65536];
    let read_patterns = vec!["sequential", "chunked"];
    let iterations = 3;
    
    let start_time = Instant::now();
    let mut test_cases = Vec::new();
    let mut all_read_times = Vec::new();
    let mut all_throughputs = Vec::new();
    let mut total_tests = 0;
    let mut successful_tests = 0;
    
    let temp_dir = std::env::temp_dir().join("rust_large_file_test");
    std::fs::create_dir_all(&temp_dir)?;
    
    for file_size in &file_sizes {
        for buffer_size in &buffer_sizes {
            for pattern in &read_patterns {
                eprintln!("Testing file size: {} bytes, buffer: {}, pattern: {}...", file_size, buffer_size, pattern);
                
                let test_file_path = temp_dir.join(format!("test_file_{}_{}.txt", file_size, buffer_size));
                
                // Generate test file if needed
                if !test_file_path.exists() {
                    generate_test_file(&test_file_path, *file_size)?;
                }
                
                let mut iteration_results = Vec::new();
                let mut read_times = Vec::new();
                let mut throughputs = Vec::new();
                
                for i in 0..iterations {
                    eprintln!("  Iteration {}/{}...", i + 1, iterations);
                    total_tests += 1;
                    
                    let read_result = match pattern.as_str() {
                        "sequential" => read_file_sequential(&test_file_path, *buffer_size)?,
                        "chunked" => read_file_chunked(&test_file_path, *buffer_size)?,
                        _ => return Err("Unknown read pattern".into()),
                    };
                    
                    let read_time = read_result["read_time"].as_f64().unwrap_or(0.0);
                    let throughput = read_result["throughput_mbps"].as_f64().unwrap_or(0.0);
                    
                    read_times.push(read_time);
                    throughputs.push(throughput);
                    all_read_times.push(read_time);
                    all_throughputs.push(throughput);
                    successful_tests += 1;
                    
                    let mut iteration_result = json!({
                        "iteration": i + 1,
                        "read_time": read_time,
                        "bytes_read": read_result["bytes_read"],
                        "throughput_mbps": throughput,
                        "memory_used": 1.0,
                        "io_wait_time": read_time
                    });
                    
                    if pattern == "chunked" {
                        iteration_result["chunk_count"] = read_result["chunk_count"].clone();
                        iteration_result["avg_chunk_size"] = read_result["avg_chunk_size"].clone();
                    }
                    
                    iteration_results.push(iteration_result);
                }
                
                let avg_read_time = read_times.iter().sum::<f64>() / read_times.len() as f64;
                let avg_throughput = throughputs.iter().sum::<f64>() / throughputs.len() as f64;
                
                let test_case = json!({
                    "file_size": file_size,
                    "buffer_size": buffer_size,
                    "read_pattern": pattern,
                    "iterations": iteration_results,
                    "avg_read_time": avg_read_time,
                    "avg_throughput": avg_throughput,
                    "memory_efficiency": (*file_size as f64 / (1024.0 * 1024.0)) / 1.0
                });
                
                test_cases.push(test_case);
            }
        }
    }
    
    // Cleanup
    let _ = std::fs::remove_dir_all(&temp_dir);
    
    let total_duration = start_time.elapsed().as_secs_f64();
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
        "start_time": 0.0,
        "end_time": total_duration,
        "total_duration": total_duration,
        "test_cases": test_cases,
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "avg_read_time": avg_read_time,
            "avg_throughput": avg_throughput,
            "peak_memory_usage": 1.0
        }
    }))
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let result = run_large_file_read_benchmark()?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}