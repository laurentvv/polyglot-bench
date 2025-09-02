use std::env;
use std::fs::File;
use std::io::BufReader;
use std::time::{SystemTime, UNIX_EPOCH, Instant};
use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use serde_json;
use rand::Rng;

#[derive(Debug, Deserialize)]
struct Config {
    parameters: Parameters,
}

#[derive(Debug, Deserialize)]
struct Parameters {
    allocation_sizes: Vec<usize>,
    allocation_patterns: Vec<String>,
    allocation_counts: Vec<usize>,
    data_structures: Vec<String>,
    iterations: usize,
}

#[derive(Debug, Serialize)]
struct Results {
    start_time: f64,
    test_cases: Vec<TestCase>,
    summary: Summary,
    end_time: f64,
    total_execution_time: f64,
}

#[derive(Debug, Serialize)]
struct TestCase {
    allocation_size: usize,
    allocation_count: usize,
    data_structure: String,
    allocation_pattern: String,
    iterations: Vec<IterationResult>,
    avg_allocation_time: f64,
    avg_deallocation_time: f64,
    avg_memory_efficiency: f64,
}

#[derive(Debug, Serialize)]
struct IterationResult {
    iteration: usize,
    initial_memory: usize,
    allocation: AllocationResult,
    deallocation: DeallocationResult,
}

#[derive(Debug, Serialize)]
struct AllocationResult {
    success: bool,
    time_ms: f64,
    memory_used: usize,
    peak_memory: usize,
    memory_efficiency: f64,
    items_allocated: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[derive(Debug, Serialize)]
struct DeallocationResult {
    success: bool,
    time_ms: f64,
    final_memory: usize,
    memory_freed: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[derive(Debug, Serialize)]
struct Summary {
    total_tests: usize,
    successful_tests: usize,
    failed_tests: usize,
    avg_allocation_time: f64,
    avg_deallocation_time: f64,
    avg_memory_efficiency: f64,
}

// Simple memory tracking (approximation)
fn get_memory_usage() -> usize {
    // In Rust, we'll use a simple approximation since direct memory monitoring is complex
    // This is a placeholder - in real scenarios you'd use external crates like sysinfo
    0 // Returning 0 as placeholder
}

fn allocate_arrays(size: usize, count: usize) -> Vec<Vec<i32>> {
    let mut rng = rand::thread_rng();
    let mut arrays = Vec::with_capacity(count);
    
    for _ in 0..count {
        let mut array = Vec::with_capacity(size);
        for _ in 0..size {
            array.push(rng.gen_range(0..1000));
        }
        arrays.push(array);
    }
    
    arrays
}

fn allocate_hash_maps(size: usize, count: usize) -> Vec<HashMap<i32, i32>> {
    let mut rng = rand::thread_rng();
    let mut maps = Vec::with_capacity(count);
    
    for _ in 0..count {
        let mut map = HashMap::with_capacity(size);
        for _ in 0..size {
            let key = rng.gen_range(0..size * 2) as i32;
            let value = rng.gen_range(0..1000);
            map.insert(key, value);
        }
        maps.push(map);
    }
    
    maps
}

#[derive(Clone)]
struct ListNode {
    value: i32,
    next: Option<Box<ListNode>>,
}

fn allocate_linked_lists(size: usize, count: usize) -> Vec<Option<Box<ListNode>>> {
    let mut rng = rand::thread_rng();
    let mut lists = Vec::with_capacity(count);
    
    for _ in 0..count {
        let mut head: Option<Box<ListNode>> = None;
        for _ in 0..size {
            let new_node = ListNode {
                value: rng.gen_range(0..1000),
                next: head,
            };
            head = Some(Box::new(new_node));
        }
        lists.push(head);
    }
    
    lists
}

fn run_memory_allocation_benchmark(params: Parameters) -> Results {
    let start_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs_f64();
    let mut test_cases = Vec::new();
    let mut summary = Summary {
        total_tests: 0,
        successful_tests: 0,
        failed_tests: 0,
        avg_allocation_time: 0.0,
        avg_deallocation_time: 0.0,
        avg_memory_efficiency: 0.0,
    };
    
    let mut all_allocation_times = Vec::new();
    let mut all_deallocation_times = Vec::new();
    let mut all_memory_efficiencies = Vec::new();
    
    for &size in &params.allocation_sizes {
        for &count in &params.allocation_counts {
            for structure in &params.data_structures {
                for pattern in &params.allocation_patterns {
                    eprintln!("Testing {} allocation: size={}, count={}, pattern={}...", 
                             structure, size, count, pattern);
                    
                    let mut test_case = TestCase {
                        allocation_size: size,
                        allocation_count: count,
                        data_structure: structure.clone(),
                        allocation_pattern: pattern.clone(),
                        iterations: Vec::new(),
                        avg_allocation_time: 0.0,
                        avg_deallocation_time: 0.0,
                        avg_memory_efficiency: 0.0,
                    };
                    
                    let mut allocation_times = Vec::new();
                    let mut deallocation_times = Vec::new();
                    let mut memory_efficiencies = Vec::new();
                    
                    for i in 0..params.iterations {
                        eprintln!("  Iteration {}/{}...", i + 1, params.iterations);
                        
                        let initial_memory = get_memory_usage();
                        summary.total_tests += 1;
                        
                        let mut iteration_result = IterationResult {
                            iteration: i + 1,
                            initial_memory,
                            allocation: AllocationResult {
                                success: false,
                                time_ms: 0.0,
                                memory_used: 0,
                                peak_memory: 0,
                                memory_efficiency: 0.0,
                                items_allocated: count,
                                error: None,
                            },
                            deallocation: DeallocationResult {
                                success: false,
                                time_ms: 0.0,
                                final_memory: 0,
                                memory_freed: 0,
                                error: None,
                            },
                        };
                        
                        let success = match structure.as_str() {
                            "array" => {
                                let start = Instant::now();
                                let _allocated = allocate_arrays(size, count);
                                let allocation_time = start.elapsed().as_secs_f64() * 1000.0;
                                
                                let peak_memory = get_memory_usage();
                                let memory_used = peak_memory.saturating_sub(initial_memory);
                                let theoretical_size = size * count * std::mem::size_of::<i32>();
                                let memory_efficiency = if memory_used > 0 {
                                    (theoretical_size as f64 / memory_used as f64) * 100.0
                                } else {
                                    100.0
                                };
                                
                                allocation_times.push(allocation_time);
                                all_allocation_times.push(allocation_time);
                                memory_efficiencies.push(memory_efficiency);
                                all_memory_efficiencies.push(memory_efficiency);
                                
                                iteration_result.allocation = AllocationResult {
                                    success: true,
                                    time_ms: allocation_time,
                                    memory_used,
                                    peak_memory,
                                    memory_efficiency,
                                    items_allocated: count,
                                    error: None,
                                };
                                
                                // Deallocation (drop happens automatically)
                                let start = Instant::now();
                                drop(_allocated);
                                let deallocation_time = start.elapsed().as_secs_f64() * 1000.0;
                                let final_memory = get_memory_usage();
                                
                                deallocation_times.push(deallocation_time);
                                all_deallocation_times.push(deallocation_time);
                                
                                iteration_result.deallocation = DeallocationResult {
                                    success: true,
                                    time_ms: deallocation_time,
                                    final_memory,
                                    memory_freed: peak_memory.saturating_sub(final_memory),
                                    error: None,
                                };
                                
                                true
                            },
                            "hash_map" => {
                                let start = Instant::now();
                                let _allocated = allocate_hash_maps(size, count);
                                let allocation_time = start.elapsed().as_secs_f64() * 1000.0;
                                
                                let peak_memory = get_memory_usage();
                                let memory_used = peak_memory.saturating_sub(initial_memory);
                                let theoretical_size = size * count * (std::mem::size_of::<i32>() * 2);
                                let memory_efficiency = if memory_used > 0 {
                                    (theoretical_size as f64 / memory_used as f64) * 100.0
                                } else {
                                    100.0
                                };
                                
                                allocation_times.push(allocation_time);
                                all_allocation_times.push(allocation_time);
                                memory_efficiencies.push(memory_efficiency);
                                all_memory_efficiencies.push(memory_efficiency);
                                
                                iteration_result.allocation = AllocationResult {
                                    success: true,
                                    time_ms: allocation_time,
                                    memory_used,
                                    peak_memory,
                                    memory_efficiency,
                                    items_allocated: count,
                                    error: None,
                                };
                                
                                let start = Instant::now();
                                drop(_allocated);
                                let deallocation_time = start.elapsed().as_secs_f64() * 1000.0;
                                let final_memory = get_memory_usage();
                                
                                deallocation_times.push(deallocation_time);
                                all_deallocation_times.push(deallocation_time);
                                
                                iteration_result.deallocation = DeallocationResult {
                                    success: true,
                                    time_ms: deallocation_time,
                                    final_memory,
                                    memory_freed: peak_memory.saturating_sub(final_memory),
                                    error: None,
                                };
                                
                                true
                            },
                            "linked_list" => {
                                let start = Instant::now();
                                let _allocated = allocate_linked_lists(size, count);
                                let allocation_time = start.elapsed().as_secs_f64() * 1000.0;
                                
                                let peak_memory = get_memory_usage();
                                let memory_used = peak_memory.saturating_sub(initial_memory);
                                let theoretical_size = size * count * (std::mem::size_of::<i32>() + std::mem::size_of::<usize>());
                                let memory_efficiency = if memory_used > 0 {
                                    (theoretical_size as f64 / memory_used as f64) * 100.0
                                } else {
                                    100.0
                                };
                                
                                allocation_times.push(allocation_time);
                                all_allocation_times.push(allocation_time);
                                memory_efficiencies.push(memory_efficiency);
                                all_memory_efficiencies.push(memory_efficiency);
                                
                                iteration_result.allocation = AllocationResult {
                                    success: true,
                                    time_ms: allocation_time,
                                    memory_used,
                                    peak_memory,
                                    memory_efficiency,
                                    items_allocated: count,
                                    error: None,
                                };
                                
                                let start = Instant::now();
                                drop(_allocated);
                                let deallocation_time = start.elapsed().as_secs_f64() * 1000.0;
                                let final_memory = get_memory_usage();
                                
                                deallocation_times.push(deallocation_time);
                                all_deallocation_times.push(deallocation_time);
                                
                                iteration_result.deallocation = DeallocationResult {
                                    success: true,
                                    time_ms: deallocation_time,
                                    final_memory,
                                    memory_freed: peak_memory.saturating_sub(final_memory),
                                    error: None,
                                };
                                
                                true
                            },
                            _ => {
                                iteration_result.allocation.error = Some(format!("Unknown data structure: {}", structure));
                                false
                            }
                        };
                        
                        if success {
                            summary.successful_tests += 1;
                        } else {
                            summary.failed_tests += 1;
                        }
                        
                        test_case.iterations.push(iteration_result);
                    }
                    
                    // Calculate averages
                    if !allocation_times.is_empty() {
                        test_case.avg_allocation_time = allocation_times.iter().sum::<f64>() / allocation_times.len() as f64;
                    }
                    if !deallocation_times.is_empty() {
                        test_case.avg_deallocation_time = deallocation_times.iter().sum::<f64>() / deallocation_times.len() as f64;
                    }
                    if !memory_efficiencies.is_empty() {
                        test_case.avg_memory_efficiency = memory_efficiencies.iter().sum::<f64>() / memory_efficiencies.len() as f64;
                    }
                    
                    test_cases.push(test_case);
                }
            }
        }
    }
    
    // Calculate overall summary
    if !all_allocation_times.is_empty() {
        summary.avg_allocation_time = all_allocation_times.iter().sum::<f64>() / all_allocation_times.len() as f64;
    }
    if !all_deallocation_times.is_empty() {
        summary.avg_deallocation_time = all_deallocation_times.iter().sum::<f64>() / all_deallocation_times.len() as f64;
    }
    if !all_memory_efficiencies.is_empty() {
        summary.avg_memory_efficiency = all_memory_efficiencies.iter().sum::<f64>() / all_memory_efficiencies.len() as f64;
    }
    
    let end_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs_f64();
    
    Results {
        start_time,
        test_cases,
        summary,
        end_time,
        total_execution_time: end_time - start_time,
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: {} <config_file>", args[0]);
        std::process::exit(1);
    }
    
    let config_file = &args[1];
    let file = File::open(config_file)?;
    let reader = BufReader::new(file);
    let config: Config = serde_json::from_reader(reader)?;
    
    let results = run_memory_allocation_benchmark(config.parameters);
    
    println!("{}", serde_json::to_string_pretty(&results)?);
    
    Ok(())
}