use std::env;
use std::fs;
use std::time::Instant;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use serde_json;
use rand::Rng;
use rand::seq::SliceRandom;
use flate2::write::GzEncoder;
use flate2::write::ZlibEncoder;
use flate2::Compression;
use std::io::Write;

#[derive(Debug, Serialize)]
struct CompressionResult {
    success: bool,
    compressed_size: Option<usize>,
    compression_time: f64,
    error: Option<String>,
}

#[derive(Debug, Serialize)]
struct DecompressionResult {
    success: bool,
    decompressed_size: Option<usize>,
    decompression_time: f64,
    error: Option<String>,
}

#[derive(Debug, Serialize)]
struct IterationResult {
    iteration: u32,
    original_size: usize,
    compression: CompressionResult,
    decompression: Option<DecompressionResult>,
}

#[derive(Debug, Serialize)]
struct TestCase {
    input_size: usize,
    text_type: String,
    algorithm: String,
    iterations: Vec<IterationResult>,
    avg_compression_ratio: f64,
    avg_compression_time: f64,
    avg_decompression_time: f64,
}

#[derive(Debug, Serialize)]
struct AlgorithmPerformance {
    avg_compression_ratio: f64,
    max_compression_ratio: f64,
    min_compression_ratio: f64,
}

#[derive(Debug, Serialize)]
struct Summary {
    total_tests: u32,
    successful_compressions: u32,
    failed_compressions: u32,
    best_compression_ratios: HashMap<String, f64>,
    algorithm_performance: HashMap<String, AlgorithmPerformance>,
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
    text_types: Option<Vec<String>>,
    compression_algorithms: Option<Vec<String>>,
    iterations: Option<u32>,
}

fn generate_text_data(size: usize, text_type: &str) -> Result<String, String> {
    let mut rng = rand::thread_rng();
    
    match text_type {
        "ascii" => {
            let chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n";
            let result: String = (0..size)
                .map(|_| chars.chars().nth(rng.gen_range(0..chars.len())).unwrap())
                .collect();
            Ok(result)
        }
        "unicode" => {
            let chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789àáâãäåæçèéêëìíîïñòóôõöøùúûüý你好世界🌟🚀📊 \n";
            let result: String = (0..size)
                .map(|_| chars.chars().nth(rng.gen_range(0..chars.chars().count())).unwrap())
                .collect();
            Ok(result)
        }
        "code" => {
            let keywords = vec!["fn", "let", "mut", "if", "else", "for", "while", "return", "match", "impl"];
            let operators = vec!["=", "+", "-", "*", "/", "(", ")", "{", "}", "[", "]", ";", ":"];
            let mut text = String::new();
            
            while text.len() < size {
                if rng.gen::<f64>() < 0.3 {
                    text.push_str(keywords.choose(&mut rng).unwrap());
                } else {
                    let word_len = rng.gen_range(3..10);
                    for _ in 0..word_len {
                        text.push((b'a' + rng.gen_range(0..26)) as char);
                    }
                }
                
                if rng.gen::<f64>() < 0.2 {
                    text.push_str(operators.choose(&mut rng).unwrap());
                }
                
                if rng.gen::<f64>() < 0.1 {
                    text.push('\n');
                } else {
                    text.push(' ');
                }
            }
            
            Ok(text.chars().take(size).collect())
        }
        "natural_language" => {
            let words = vec!["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "and", "runs", "through",
                           "forest", "meadow", "river", "mountain", "valley", "beautiful", "magnificent", "wonderful"];
            let mut text = String::new();
            
            while text.len() < size {
                text.push_str(words.choose(&mut rng).unwrap());
                
                if rng.gen::<f64>() < 0.1 {
                    text.push_str(". ");
                } else if rng.gen::<f64>() < 0.05 {
                    text.push_str(", ");
                } else {
                    text.push(' ');
                }
                
                if rng.gen::<f64>() < 0.05 {
                    text.push('\n');
                }
            }
            
            Ok(text.chars().take(size).collect())
        }
        _ => Err(format!("Unknown text type: {}", text_type))
    }
}

fn compress_with_gzip(data: &[u8]) -> CompressionResult {
    let start = Instant::now();
    
    match try_compress_gzip(data) {
        Ok(compressed) => {
            let compression_time = start.elapsed().as_secs_f64() * 1000.0;
            CompressionResult {
                success: true,
                compressed_size: Some(compressed.len()),
                compression_time,
                error: None,
            }
        }
        Err(e) => {
            let compression_time = start.elapsed().as_secs_f64() * 1000.0;
            CompressionResult {
                success: false,
                compressed_size: None,
                compression_time,
                error: Some(e.to_string()),
            }
        }
    }
}

fn try_compress_gzip(data: &[u8]) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let mut encoder = GzEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(data)?;
    Ok(encoder.finish()?)
}

fn compress_with_zlib(data: &[u8]) -> CompressionResult {
    let start = Instant::now();
    
    match try_compress_zlib(data) {
        Ok(compressed) => {
            let compression_time = start.elapsed().as_secs_f64() * 1000.0;
            CompressionResult {
                success: true,
                compressed_size: Some(compressed.len()),
                compression_time,
                error: None,
            }
        }
        Err(e) => {
            let compression_time = start.elapsed().as_secs_f64() * 1000.0;
            CompressionResult {
                success: false,
                compressed_size: None,
                compression_time,
                error: Some(e.to_string()),
            }
        }
    }
}

fn try_compress_zlib(data: &[u8]) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(data)?;
    Ok(encoder.finish()?)
}

fn run_text_compression_benchmark(config: &Parameters) -> Result<BenchmarkResults, Box<dyn std::error::Error>> {
    let default_sizes = vec![1024];
    let default_types = vec!["ascii".to_string()];
    let default_algorithms = vec!["gzip".to_string()];
    
    let input_sizes = config.input_sizes.as_ref().unwrap_or(&default_sizes);
    let text_types = config.text_types.as_ref().unwrap_or(&default_types);
    let algorithms = config.compression_algorithms.as_ref().unwrap_or(&default_algorithms);
    let iterations = config.iterations.unwrap_or(3);
    
    let mut results = BenchmarkResults {
        start_time: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)?
            .as_secs_f64(),
        test_cases: Vec::new(),
        summary: Summary {
            total_tests: 0,
            successful_compressions: 0,
            failed_compressions: 0,
            best_compression_ratios: HashMap::new(),
            algorithm_performance: HashMap::new(),
        },
        end_time: None,
        total_execution_time: None,
    };
    
    let mut algorithm_stats: HashMap<String, Vec<f64>> = HashMap::new();
    
    for &size in input_sizes {
        for text_type in text_types {
            for algorithm in algorithms {
                eprintln!("Testing {} text, size: {}, algorithm: {}...", text_type, size, algorithm);
                
                let mut test_case = TestCase {
                    input_size: size,
                    text_type: text_type.clone(),
                    algorithm: algorithm.clone(),
                    iterations: Vec::new(),
                    avg_compression_ratio: 0.0,
                    avg_compression_time: 0.0,
                    avg_decompression_time: 0.0,
                };
                
                let mut compression_ratios = Vec::new();
                let mut compression_times = Vec::new();
                
                for i in 0..iterations {
                    eprintln!("  Iteration {}/{}...", i + 1, iterations);
                    
                    let text_data = generate_text_data(size, text_type)?;
                    let data_bytes = text_data.as_bytes();
                    let original_size = data_bytes.len();
                    
                    let compress_result = match algorithm.as_str() {
                        "gzip" => compress_with_gzip(data_bytes),
                        "zlib" => compress_with_zlib(data_bytes),
                        _ => {
                            eprintln!("Warning: Algorithm {} not implemented, skipping", algorithm);
                            continue;
                        }
                    };
                    
                    let iteration_result = IterationResult {
                        iteration: i + 1,
                        original_size,
                        compression: compress_result,
                        decompression: None,
                    };
                    
                    results.summary.total_tests += 1;
                    
                    if iteration_result.compression.success {
                        results.summary.successful_compressions += 1;
                        
                        if let Some(compressed_size) = iteration_result.compression.compressed_size {
                            let compression_ratio = if compressed_size > 0 {
                                original_size as f64 / compressed_size as f64
                            } else {
                                0.0
                            };
                            
                            compression_ratios.push(compression_ratio);
                            compression_times.push(iteration_result.compression.compression_time);
                            
                            algorithm_stats.entry(algorithm.clone()).or_insert_with(Vec::new).push(compression_ratio);
                        }
                    } else {
                        results.summary.failed_compressions += 1;
                    }
                    
                    test_case.iterations.push(iteration_result);
                }
                
                if !compression_ratios.is_empty() {
                    test_case.avg_compression_ratio = compression_ratios.iter().sum::<f64>() / compression_ratios.len() as f64;
                    test_case.avg_compression_time = compression_times.iter().sum::<f64>() / compression_times.len() as f64;
                }
                
                results.test_cases.push(test_case);
            }
        }
    }
    
    // Calculate summary statistics
    for (algorithm, ratios) in algorithm_stats {
        if !ratios.is_empty() {
            let avg = ratios.iter().sum::<f64>() / ratios.len() as f64;
            let max = ratios.iter().fold(f64::NEG_INFINITY, |a, &b| a.max(b));
            let min = ratios.iter().fold(f64::INFINITY, |a, &b| a.min(b));
            
            results.summary.algorithm_performance.insert(algorithm, AlgorithmPerformance {
                avg_compression_ratio: avg,
                max_compression_ratio: max,
                min_compression_ratio: min,
            });
        }
    }
    
    results.end_time = Some(
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)?
            .as_secs_f64()
    );
    
    if let Some(end_time) = results.end_time {
        results.total_execution_time = Some(end_time - results.start_time);
    }
    
    Ok(results)
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <config_file>", args[0]);
        std::process::exit(1);
    }
    
    let config_file = &args[1];
    
    let config_data = fs::read_to_string(config_file)
        .map_err(|_| format!("Error: Config file '{}' not found", config_file))?;
    
    let config: Config = serde_json::from_str(&config_data)
        .map_err(|e| format!("Error: Invalid JSON in config file: {}", e))?;
    
    let results = run_text_compression_benchmark(&config.parameters)?;
    
    println!("{}", serde_json::to_string_pretty(&results)?);
    
    Ok(())
}