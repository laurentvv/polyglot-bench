use std::env;
use std::fs;
use std::process::Command;
use std::time::{Duration, Instant};
use serde::{Deserialize, Serialize};
use serde_json;
use regex::Regex;

#[derive(Deserialize)]
struct Config {
    parameters: Parameters,
}

#[derive(Deserialize)]
struct Parameters {
    targets: Vec<String>,
    packet_count: Option<u32>,
    timeout: Option<u32>,
}

#[derive(Serialize)]
struct PingResult {
    avg_latency: f64,
    min_latency: f64,
    max_latency: f64,
    packet_loss: f64,
    execution_time: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[derive(Serialize)]
struct Summary {
    total_targets: usize,
    successful_targets: usize,
    failed_targets: usize,
    overall_avg_latency: f64,
}

#[derive(Serialize)]
struct Results {
    start_time: f64,
    targets: std::collections::HashMap<String, PingResult>,
    summary: Summary,
    end_time: f64,
    total_execution_time: f64,
}

fn ping_host(host: &str, count: u32, timeout: u32) -> PingResult {
    let start_time = Instant::now();
    
    let cmd = if cfg!(target_os = "windows") {
        Command::new("ping")
            .args(&["-n", &count.to_string(), "-w", &timeout.to_string(), host])
            .output()
    } else {
        let timeout_sec = timeout / 1000;
        Command::new("ping")
            .args(&["-c", &count.to_string(), "-W", &timeout_sec.to_string(), host])
            .output()
    };

    let execution_time = start_time.elapsed().as_secs_f64();

    match cmd {
        Ok(output) => {
            if output.status.success() {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let mut result = parse_ping_output(&stdout);
                result.execution_time = execution_time;
                result
            } else {
                let stderr = String::from_utf8_lossy(&output.stderr);
                PingResult {
                    avg_latency: f64::INFINITY,
                    min_latency: f64::INFINITY,
                    max_latency: f64::INFINITY,
                    packet_loss: 100.0,
                    execution_time,
                    error: Some(if stderr.is_empty() { "Ping failed".to_string() } else { stderr.to_string() }),
                }
            }
        }
        Err(e) => PingResult {
            avg_latency: f64::INFINITY,
            min_latency: f64::INFINITY,
            max_latency: f64::INFINITY,
            packet_loss: 100.0,
            execution_time,
            error: Some(e.to_string()),
        },
    }
}

fn parse_ping_output(output: &str) -> PingResult {
    let mut result = PingResult {
        avg_latency: 0.0,
        min_latency: 0.0,
        max_latency: 0.0,
        packet_loss: 0.0,
        execution_time: 0.0,
        error: None,
    };

    if cfg!(target_os = "windows") {
        // Parse Windows ping output (supports both English and French)
        // Look for packet loss percentage in multiple languages
        if let Some(captures) = Regex::new(r"(\d+)%\s*(?:loss|perte)").unwrap().captures(output) {
            if let Ok(loss) = captures[1].parse::<f64>() {
                result.packet_loss = loss;
            }
        }

        // Extract individual ping times (supports both English and French)
        let time_regex = Regex::new(r"(?:time[<>=]|temps[<>=])\s*(\d+)\s*ms").unwrap();
        let times: Vec<f64> = time_regex
            .captures_iter(output)
            .filter_map(|cap| cap[1].parse().ok())
            .collect();

        if !times.is_empty() {
            result.min_latency = times.iter().cloned().fold(f64::INFINITY, f64::min);
            result.max_latency = times.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
            result.avg_latency = times.iter().sum::<f64>() / times.len() as f64;
        }

        // Try to get statistics from summary lines (supports English and French)
        // English: "Average = 10ms"
        if let Some(captures) = Regex::new(r"Average = (\d+)ms").unwrap().captures(output) {
            if let Ok(avg) = captures[1].parse::<f64>() {
                result.avg_latency = avg;
            }
        }
        
        // French: "Minimum = 9ms, Maximum = 11ms, Moyenne = 10ms"
        if let Some(captures) = Regex::new(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Moyenne = (\d+)ms").unwrap().captures(output) {
            if let (Ok(min), Ok(max), Ok(avg)) = (
                captures[1].parse::<f64>(),
                captures[2].parse::<f64>(),
                captures[3].parse::<f64>(),
            ) {
                result.min_latency = min;
                result.max_latency = max;
                result.avg_latency = avg;
            }
        }
    } else {
        // Parse Unix/Linux ping output
        if let Some(captures) = Regex::new(r"(\d+(?:\.\d+)?)% packet loss").unwrap().captures(output) {
            if let Ok(loss) = captures[1].parse::<f64>() {
                result.packet_loss = loss;
            }
        }

        // Parse rtt statistics
        if let Some(captures) = Regex::new(r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms").unwrap().captures(output) {
            if let (Ok(min), Ok(avg), Ok(max)) = (
                captures[1].parse::<f64>(),
                captures[2].parse::<f64>(),
                captures[3].parse::<f64>(),
            ) {
                result.min_latency = min;
                result.avg_latency = avg;
                result.max_latency = max;
            }
        }
    }

    // If no valid latency was parsed, mark as error
    if result.avg_latency == 0.0 && result.packet_loss == 100.0 {
        result.error = Some("Failed to parse ping output".to_string());
    }

    result
}

fn run_ping_benchmark(params: &Parameters) -> Results {
    let start_time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs_f64();

    let packet_count = params.packet_count.unwrap_or(5);
    let timeout = params.timeout.unwrap_or(5000);

    let mut targets = std::collections::HashMap::new();
    let mut successful_targets = 0;
    let mut failed_targets = 0;
    let mut total_latency = 0.0;
    let mut successful_count = 0;

    for target in &params.targets {
        eprintln!("Pinging {}...", target);
        
        let ping_result = ping_host(target, packet_count, timeout);
        
        if ping_result.error.is_none() && ping_result.packet_loss < 100.0 {
            successful_targets += 1;
            if ping_result.avg_latency.is_finite() {
                total_latency += ping_result.avg_latency;
                successful_count += 1;
            }
        } else {
            failed_targets += 1;
        }
        
        targets.insert(target.clone(), ping_result);
    }

    let overall_avg_latency = if successful_count > 0 {
        total_latency / successful_count as f64
    } else {
        0.0
    };

    let end_time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs_f64();

    Results {
        start_time,
        targets,
        summary: Summary {
            total_targets: params.targets.len(),
            successful_targets,
            failed_targets,
            overall_avg_latency,
        },
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
    let config_content = fs::read_to_string(config_file)?;
    let config: Config = serde_json::from_str(&config_content)?;

    let results = run_ping_benchmark(&config.parameters);
    println!("{}", serde_json::to_string_pretty(&results)?);

    Ok(())
}