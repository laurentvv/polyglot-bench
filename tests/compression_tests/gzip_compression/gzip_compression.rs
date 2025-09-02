use std::env;
use std::fs;
use std::time::Instant;
use serde::{Deserialize, Serialize};
use serde_json;
use rand::Rng;
use flate2::write::GzEncoder;
use flate2::Compression;
use std::io::Write;

#[derive(Debug, Serialize)]
struct CompressionResult {
    success: bool,
    original_size: Option<usize>,
    compressed_size: Option<usize>,
    compression_ratio: Option<f64>,
    compression_time: f64,
    throughput_mb_s: Option<f64>,
    error: Option<String>,
}

#[derive(Debug, Serialize)]
struct IterationResult {
    iteration: u32,
    compression: CompressionResult,
}

#[derive(Debug, Serialize)]
struct TestCase {
    input_size: usize,
    data_type: String,
    compression_level: u32,
    iterations: Vec<IterationResult>,
    avg_compression_ratio: f64,
    avg_compression_time: f64,
    avg_decompression_time: f64,
    avg_compression_throughput: f64,
    avg_decompression_throughput: f64,
}

#[derive(Debug, Serialize)]
struct Summary {
    total_tests: u32,
    successful_tests: u32,
    failed_tests: u32,
    avg_compression_ratio: f64,
    avg_compression_time: f64,
    avg_decompression_time: f64,
    avg_compression_throughput: f64,
    avg_decompression_throughput: f64,
}

#[derive(Debug, Serialize)]
struct BenchmarkResults {
    start_time: f64,
    test_cases: Vec<TestCase>,
    summary: Summary,
    end_time: Option<f64>,
    total_execution_time: Option<f64>,
}

#[derive(Debug, Deserialize)]
struct Config {
    parameters: Parameters,
}

#[derive(Debug, Deserialize)]
struct Parameters {
    input_sizes: Option<Vec<usize>>,
    data_types: Option<Vec<String>>,
    compression_levels: Option<Vec<u32>>,
    iterations: Option<u32>,
}

fn generate_test_data(size: usize, data_type: &str) -> Result<Vec<u8>, String> {
    let mut rng = rand::thread_rng();
    
    match data_type {
        "text" => {
            let chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n";
            let result: String = (0..size)
                .map(|_| chars.chars().nth(rng.gen_range(0..chars.len())).unwrap())
                .collect();
            Ok(result.into_bytes())
        }
        "binary" => {
            let result: Vec<u8> = (0..size)
                .map(|_| rng.gen_range(0..256) as u8)
                .collect();
            Ok(result)
        }
        "json" => {
            let mut data = Vec::new();
            let mut current_size = 0;
            
            while current_size < size {
                let record = serde_json::json!({
                    "id": data.len(),
                    "name": (0..10).map(|_| rng.gen_range(b'a'..=b'z') as char).collect::<String>(),
                    "value": rng.gen_range(1..=1000),
                    "active": rng.gen_bool(0.5),
                    "data": (0..50).map(|_| {
                        let chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
                        chars.chars().nth(rng.gen_range(0..chars.len())).unwrap()
                    }).collect::<String>()
                });
                data.push(record);
                current_size = serde_json::to_string(&data).unwrap().len();
            }
            
            let json_str = serde_json::to_string(&data).unwrap();
            let bytes = json_str.into_bytes();
            Ok(bytes[..size.min(bytes.len())].to_vec())
        }
        _ => Err(format!("Unknown data type: {}", data_type))
    }
}

fn compress_data(data: &[u8], compression_level: u32) -> CompressionResult {
    let start = Instant::now();
    let original_size = data.len();
    
    match try_compress_gzip(data, compression_level) {
        Ok(compressed) => {
            let compression_time = start.elapsed().as_secs_f64() * 1000.0;
            let compressed_size = compressed.len();
            let compression_ratio = if compressed_size > 0 {
                original_size as f64 / compressed_size as f64
            } else {
                0.0
            };
            let throughput = original_size as f64 / (compression_time / 1000.0) / (1024.0 * 1024.0);
            
            CompressionResult {
                success: true,
                original_size: Some(original_size),
                compressed_size: Some(compressed_size),
                compression_ratio: Some((compression_ratio * 1000.0).round() / 1000.0),
                compression_time: (compression_time * 100.0).round() / 100.0,
                throughput_mb_s: Some((throughput * 100.0).round() / 100.0),
                error: None,
            }
        }
        Err(e) => {
            let compression_time = start.elapsed().as_secs_f64() * 1000.0;
            CompressionResult {
                success: false,
                original_size: Some(original_size),
                compressed_size: None,
                compression_ratio: None,
                compression_time: (compression_time * 100.0).round() / 100.0,
                throughput_mb_s: None,
                error: Some(e.to_string()),
            }
        }
    }
}

fn try_compress_gzip(data: &[u8], compression_level: u32) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let compression = match compression_level {
        1 => Compression::fast(),
        2..=5 => Compression::new(compression_level),
        6 => Compression::default(),
        7..=9 => Compression::new(compression_level),
        _ => Compression::default(),
    };
    
    let mut encoder = GzEncoder::new(Vec::new(), compression);
    encoder.write_all(data)?;
    Ok(encoder.finish()?)
}

fn run_compression_benchmark(config: Parameters) -> BenchmarkResults {
    let input_sizes = config.input_sizes.unwrap_or_else(|| vec![1024]);
    let data_types = config.data_types.unwrap_or_else(|| vec!["text".to_string()]);
    let compression_levels = config.compression_levels.unwrap_or_else(|| vec![6]);
    let iterations = config.iterations.unwrap_or(5);
    
    let mut results = BenchmarkResults {
        start_time: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs_f64(),
        test_cases: Vec::new(),
        summary: Summary {
            total_tests: 0,
            successful_tests: 0,
            failed_tests: 0,
            avg_compression_ratio: 0.0,
            avg_compression_time: 0.0,
            avg_decompression_time: 0.0,
            avg_compression_throughput: 0.0,
            avg_decompression_throughput: 0.0,
        },
        end_time: None,
        total_execution_time: None,
    };
    
    let mut total_compression_ratios = Vec::new();
    let mut total_compression_times = Vec::new();
    let mut total_compression_throughputs = Vec::new();
    
    for size in input_sizes {
        for data_type in &data_types {
            for level in &compression_levels {
                eprintln!("Testing {} data, size: {} bytes, level: {}...", data_type, size, level);
                
                let mut test_case = TestCase {
                    input_size: size,
                    data_type: data_type.clone(),
                    compression_level: *level,
                    iterations: Vec::new(),
                    avg_compression_ratio: 0.0,
                    avg_compression_time: 0.0,
                    avg_decompression_time: 0.0,
                    avg_compression_throughput: 0.0,
                    avg_decompression_throughput: 0.0,
                };
                
                let mut iteration_compression_ratios = Vec::new();
                let mut iteration_compression_times = Vec::new();
                let mut iteration_compression_throughputs = Vec::new();
                
                for i in 0..iterations {
                    eprintln!("  Iteration {}/{}...", i + 1, iterations);
                    
                    let test_data = match generate_test_data(size, data_type) {
                        Ok(data) => data,
                        Err(e) => {
                            eprintln!("Error generating test data: {}", e);
                            continue;
                        }
                    };
                    
                    let compression_result = compress_data(&test_data, *level);
                    
                    let iteration_result = IterationResult {
                        iteration: i + 1,
                        compression: compression_result,
                    };
                    
                    results.summary.total_tests += 1;
                    
                    if iteration_result.compression.success {
                        results.summary.successful_tests += 1;
                        
                        if let Some(ratio) = iteration_result.compression.compression_ratio {
                            iteration_compression_ratios.push(ratio);
                        }
                        iteration_compression_times.push(iteration_result.compression.compression_time);
                        if let Some(throughput) = iteration_result.compression.throughput_mb_s {
                            iteration_compression_throughputs.push(throughput);
                        }
                    } else {
                        results.summary.failed_tests += 1;
                    }
                    
                    test_case.iterations.push(iteration_result);
                }
                
                // Calculate averages for this test case
                if !iteration_compression_ratios.is_empty() {
                    test_case.avg_compression_ratio = iteration_compression_ratios.iter().sum::<f64>() / iteration_compression_ratios.len() as f64;
                    test_case.avg_compression_time = iteration_compression_times.iter().sum::<f64>() / iteration_compression_times.len() as f64;
                    test_case.avg_compression_throughput = iteration_compression_throughputs.iter().sum::<f64>() / iteration_compression_throughputs.len() as f64;
                    
                    total_compression_ratios.extend(iteration_compression_ratios);
                    total_compression_times.extend(iteration_compression_times);
                    total_compression_throughputs.extend(iteration_compression_throughputs);
                }
                
                results.test_cases.push(test_case);
            }
        }
    }
    
    // Calculate overall summary
    if !total_compression_ratios.is_empty() {
        results.summary.avg_compression_ratio = total_compression_ratios.iter().sum::<f64>() / total_compression_ratios.len() as f64;
        results.summary.avg_compression_time = total_compression_times.iter().sum::<f64>() / total_compression_times.len() as f64;
        results.summary.avg_compression_throughput = total_compression_throughputs.iter().sum::<f64>() / total_compression_throughputs.len() as f64;
    }
    
    let end_time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs_f64();
    results.end_time = Some(end_time);
    results.total_execution_time = Some(end_time - results.start_time);
    
    results
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
            eprintln!("Error: Cannot read config file '{}': {}", config_file, e);
            std::process::exit(1);
        }
    };
    
    let config: Config = match serde_json::from_str(&config_content) {
        Ok(config) => config,
        Err(e) => {
            eprintln!("Error: Invalid JSON in config file: {}", e);
            std::process::exit(1);
        }
    };
    
    let results = run_compression_benchmark(config.parameters);
    
    match serde_json::to_string_pretty(&results) {
        Ok(json) => println!("{}", json),
        Err(e) => {
            eprintln!("Error: Failed to serialize results: {}", e);
            std::process::exit(1);
        }
    }
}