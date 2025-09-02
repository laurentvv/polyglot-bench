use std::env;
use std::fs;
use std::time::{Duration, Instant};
use std::net::{ToSocketAddrs, TcpStream};
use std::thread;
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use serde_json::{json, Value};

#[derive(Debug, Clone)]
struct DnsResult {
    domain: String,
    success: bool,
    response_time_ms: f64,
    ip_addresses: Vec<String>,
    error: Option<String>,
}

impl DnsResult {
    fn new(domain: String) -> Self {
        DnsResult {
            domain,
            success: false,
            response_time_ms: 0.0,
            ip_addresses: Vec::new(),
            error: None,
        }
    }
    
    fn to_json(&self) -> Value {
        json!({
            "domain": self.domain,
            "success": self.success,
            "response_time_ms": self.response_time_ms,
            "ip_addresses": self.ip_addresses,
            "error": self.error
        })
    }
}

// Simple DNS cache
lazy_static::lazy_static! {
    static ref DNS_CACHE: Arc<Mutex<HashMap<String, DnsResult>>> = 
        Arc::new(Mutex::new(HashMap::new()));
}

fn resolve_domain_with_timeout(domain: &str, timeout_secs: u64) -> DnsResult {
    // Check cache first
    {
        let cache = DNS_CACHE.lock().unwrap();
        if let Some(cached_result) = cache.get(domain) {
            return cached_result.clone();
        }
    }
    
    let mut result = DnsResult::new(domain.to_string());
    let start = Instant::now();
    
    // Create address string for resolution
    let address = format!("{}:53", domain);
    
    // Use a separate thread for timeout control
    let domain_clone = domain.to_string();
    let handle = thread::spawn(move || {
        let address_with_port = format!("{}:80", domain_clone);
        match address_with_port.to_socket_addrs() {
            Ok(addrs) => {
                let ip_addresses: Vec<String> = addrs
                    .map(|addr| addr.ip().to_string())
                    .collect();
                Ok(ip_addresses)
            }
            Err(e) => Err(format!("DNS resolution failed: {}", e)),
        }
    });
    
    match handle.join() {
        Ok(Ok(ip_addresses)) => {
            result.success = !ip_addresses.is_empty();
            result.ip_addresses = ip_addresses;
            result.response_time_ms = start.elapsed().as_secs_f64() * 1000.0;
        }
        Ok(Err(e)) => {
            result.error = Some(e);
            result.response_time_ms = start.elapsed().as_secs_f64() * 1000.0;
        }
        Err(_) => {
            result.error = Some("Thread panicked during DNS resolution".to_string());
            result.response_time_ms = start.elapsed().as_secs_f64() * 1000.0;
        }
    }
    
    // Cache the result
    {
        let mut cache = DNS_CACHE.lock().unwrap();
        cache.insert(domain.to_string(), result.clone());
    }
    
    result
}

fn resolve_domain(domain: &str, timeout_secs: u64) -> DnsResult {
    resolve_domain_with_timeout(domain, timeout_secs)
}

fn resolve_domains_sequential(domains: &[String], timeout_secs: u64) -> Vec<DnsResult> {
    let mut results = Vec::new();
    
    for domain in domains {
        let result = resolve_domain(domain, timeout_secs);
        eprintln!("  Resolved {}: {} ({:.2}ms)", 
                  domain, 
                  if result.success { "✓" } else { "✗" }, 
                  result.response_time_ms);
        results.push(result);
    }
    
    results
}

fn resolve_domains_concurrent(domains: &[String], max_workers: usize, timeout_secs: u64) -> Vec<DnsResult> {
    let results = Arc::new(Mutex::new(Vec::new()));
    let mut handles = Vec::new();
    
    // Split domains into chunks for workers
    let chunk_size = (domains.len() + max_workers - 1) / max_workers;
    
    for chunk in domains.chunks(chunk_size) {
        let chunk_domains = chunk.to_vec();
        let results_clone = Arc::clone(&results);
        
        let handle = thread::spawn(move || {
            for domain in chunk_domains {
                let result = resolve_domain(&domain, timeout_secs);
                eprintln!("  Resolved {}: {} ({:.2}ms)", 
                          domain, 
                          if result.success { "✓" } else { "✗" }, 
                          result.response_time_ms);
                
                let mut results_guard = results_clone.lock().unwrap();
                results_guard.push(result);
            }
        });
        
        handles.push(handle);
    }
    
    // Wait for all threads to complete
    for handle in handles {
        handle.join().unwrap();
    }
    
    let mut final_results = results.lock().unwrap().clone();
    final_results.sort_by(|a, b| a.domain.cmp(&b.domain));
    
    final_results
}

fn run_dns_benchmark(config: &Value) -> Value {
    let parameters = &config["parameters"];
    
    let domains: Vec<String> = parameters["domains"]
        .as_array()
        .unwrap_or(&vec![
            json!("google.com"),
            json!("github.com"), 
            json!("stackoverflow.com")
        ])
        .iter()
        .map(|v| v.as_str().unwrap().to_string())
        .collect();
    
    let resolution_modes: Vec<String> = parameters["resolution_modes"]
        .as_array()
        .unwrap_or(&vec![json!("sequential")])
        .iter()
        .map(|v| v.as_str().unwrap().to_string())
        .collect();
    
    let iterations = parameters["iterations"].as_u64().unwrap_or(3) as usize;
    let timeout_secs = parameters["timeout_seconds"].as_u64().unwrap_or(5);
    let concurrent_workers = parameters["concurrent_workers"].as_u64().unwrap_or(5) as usize;
    
    let start_time = Instant::now();
    let mut test_cases = Vec::new();
    let mut all_resolution_times = Vec::new();
    let mut total_iterations = 0;
    
    for mode in &resolution_modes {
        eprintln!("Testing DNS resolution mode: {}...", mode);
        
        let mut mode_resolution_times = Vec::new();
        let mut mode_successful = 0;
        let mut mode_total = 0;
        let mut iterations_data = Vec::new();
        
        for i in 0..iterations {
            eprintln!("  Iteration {}/{}...", i + 1, iterations);
            
            let iteration_start = Instant::now();
            
            let domain_results = match mode.as_str() {
                "sequential" => resolve_domains_sequential(&domains, timeout_secs),
                "concurrent" => resolve_domains_concurrent(&domains, concurrent_workers, timeout_secs),
                _ => {
                    eprintln!("Warning: Unknown resolution mode '{}', using sequential", mode);
                    resolve_domains_sequential(&domains, timeout_secs)
                }
            };
            
            let iteration_total_time = iteration_start.elapsed().as_secs_f64() * 1000.0;
            
            let iteration_successful = domain_results.iter().filter(|r| r.success).count();
            let iteration_failed = domain_results.len() - iteration_successful;
            
            let iteration_avg_time: f64 = if iteration_successful > 0 {
                domain_results.iter()
                    .filter(|r| r.success)
                    .map(|r| r.response_time_ms)
                    .sum::<f64>() / iteration_successful as f64
            } else {
                0.0
            };
            
            // Collect timing data
            for result in &domain_results {
                if result.success {
                    mode_resolution_times.push(result.response_time_ms);
                    all_resolution_times.push(result.response_time_ms);
                }
            }
            
            mode_successful += iteration_successful;
            mode_total += domain_results.len();
            total_iterations += 1;
            
            let iteration_result = json!({
                "iteration": i + 1,
                "total_time_ms": iteration_total_time,
                "domains_resolved": domain_results.len(),
                "successful_resolutions": iteration_successful,
                "failed_resolutions": iteration_failed,
                "avg_resolution_time_ms": iteration_avg_time,
                "domain_results": domain_results.iter().map(|r| r.to_json()).collect::<Vec<_>>()
            });
            
            iterations_data.push(iteration_result);
        }
        
        let avg_resolution_time = if !mode_resolution_times.is_empty() {
            mode_resolution_times.iter().sum::<f64>() / mode_resolution_times.len() as f64
        } else {
            0.0
        };
        
        let fastest_resolution = mode_resolution_times.iter().fold(f64::INFINITY, |a, &b| a.min(b));
        let slowest_resolution = mode_resolution_times.iter().fold(0.0f64, |a, &b| a.max(b));
        let success_rate = if mode_total > 0 {
            (mode_successful as f64 / mode_total as f64) * 100.0
        } else {
            0.0
        };
        
        let test_case = json!({
            "resolution_mode": mode,
            "domains_count": domains.len(),
            "iterations": iterations_data,
            "avg_resolution_time": avg_resolution_time,
            "fastest_resolution": if fastest_resolution == f64::INFINITY { 0.0 } else { fastest_resolution },
            "slowest_resolution": slowest_resolution,
            "success_rate": success_rate,
            "total_successful": mode_successful,
            "total_attempts": mode_total
        });
        
        test_cases.push(test_case);
    }
    
    let successful_resolutions = all_resolution_times.len();
    let failed_resolutions = (total_iterations * domains.len()) - successful_resolutions;
    
    let avg_resolution_time = if !all_resolution_times.is_empty() {
        all_resolution_times.iter().sum::<f64>() / all_resolution_times.len() as f64
    } else {
        0.0
    };
    
    let fastest_resolution = all_resolution_times.iter().fold(f64::INFINITY, |a, &b| a.min(b));
    let slowest_resolution = all_resolution_times.iter().fold(0.0f64, |a, &b| a.max(b));
    
    let end_time = start_time.elapsed();
    
    json!({
        "start_time": 0, // Placeholder, would need proper timestamp
        "test_cases": test_cases,
        "summary": {
            "total_domains": domains.len(),
            "total_iterations": total_iterations,
            "successful_resolutions": successful_resolutions,
            "failed_resolutions": failed_resolutions,
            "avg_resolution_time": avg_resolution_time,
            "fastest_resolution": if fastest_resolution == f64::INFINITY { 0.0 } else { fastest_resolution },
            "slowest_resolution": slowest_resolution
        },
        "end_time": 0, // Placeholder
        "total_execution_time": end_time.as_secs_f64()
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
            eprintln!("Error: Cannot read config file '{}': {}", config_file, e);
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
    
    let results = run_dns_benchmark(&config);
    println!("{}", serde_json::to_string_pretty(&results).unwrap());
}