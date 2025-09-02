use std::env;
use std::fs;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use serde_json;

#[derive(Deserialize)]
struct Config {
    parameters: Parameters,
}

#[derive(Deserialize)]
struct Parameters {
    urls: Vec<String>,
    request_count: Option<u32>,
    timeout: Option<u64>,
    methods: Option<Vec<String>>,
    concurrent_requests: Option<u32>,
}

#[derive(Serialize)]
struct RequestResult {
    success: bool,
    response_time: f64,
    status_code: u16,
    content_length: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

#[derive(Serialize)]
struct UrlResults {
    requests: Vec<RequestResult>,
    avg_response_time: f64,
    success_rate: f64,
    total_requests: u32,
    successful_requests: u32,
}

#[derive(Serialize)]
struct Summary {
    total_requests: u32,
    successful_requests: u32,
    failed_requests: u32,
    avg_response_time: f64,
    min_response_time: f64,
    max_response_time: f64,
    success_rate: f64,
}

#[derive(Serialize)]
struct Results {
    start_time: f64,
    urls: HashMap<String, UrlResults>,
    summary: Summary,
    end_time: f64,
    total_execution_time: f64,
}

fn make_http_request(url: &str, method: &str, timeout_ms: u64) -> RequestResult {
    let start_time = Instant::now();
    
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_millis(timeout_ms))
        .danger_accept_invalid_certs(true)
        .build();

    let client = match client {
        Ok(c) => c,
        Err(e) => {
            let response_time = start_time.elapsed().as_millis() as f64;
            return RequestResult {
                success: false,
                response_time,
                status_code: 0,
                content_length: 0,
                error: Some(format!("Client creation error: {}", e)),
            };
        }
    };

    let request_builder = match method.to_uppercase().as_str() {
        "GET" => client.get(url),
        "POST" => client.post(url),
        "PUT" => client.put(url),
        "DELETE" => client.delete(url),
        _ => client.get(url), // Default to GET
    };

    let request = request_builder.header("User-Agent", "BenchmarkTool/1.0");

    match request.send() {
        Ok(response) => {
            let response_time = start_time.elapsed().as_millis() as f64;
            let status_code = response.status().as_u16();
            let is_success = response.status().is_success();
            
            match response.text() {
                Ok(content) => RequestResult {
                    success: is_success,
                    response_time,
                    status_code,
                    content_length: content.len(),
                    error: if is_success { None } else { Some(format!("HTTP Error {}", status_code)) },
                },
                Err(e) => RequestResult {
                    success: false,
                    response_time,
                    status_code,
                    content_length: 0,
                    error: Some(format!("Content read error: {}", e)),
                },
            }
        }
        Err(e) => {
            let response_time = start_time.elapsed().as_millis() as f64;
            RequestResult {
                success: false,
                response_time,
                status_code: 0,
                content_length: 0,
                error: Some(e.to_string()),
            }
        }
    }
}

fn run_http_benchmark(params: &Parameters) -> Results {
    let start_time = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs_f64();

    let request_count = params.request_count.unwrap_or(5);
    let timeout = params.timeout.unwrap_or(10000);
    let methods = params.methods.as_ref().map(|m| m.clone()).unwrap_or_else(|| vec!["GET".to_string()]);

    let mut urls_results = HashMap::new();
    let mut total_requests = 0u32;
    let mut successful_requests = 0u32;
    let mut total_response_time = 0.0;
    let mut min_response_time = f64::INFINITY;
    let mut max_response_time: f64 = 0.0;

    for url in &params.urls {
        eprintln!("Testing {}...", url);

        let mut url_results = UrlResults {
            requests: Vec::new(),
            avg_response_time: 0.0,
            success_rate: 0.0,
            total_requests: 0,
            successful_requests: 0,
        };

        let mut url_response_times = Vec::new();
        let mut url_successful = 0u32;

        for method in &methods {
            for i in 0..request_count {
                eprintln!("  Request {}/{} ({})...", i + 1, request_count, method);

                let request_result = make_http_request(url, method, timeout);
                
                total_requests += 1;
                url_results.total_requests += 1;

                if request_result.success {
                    successful_requests += 1;
                    url_successful += 1;

                    let response_time = request_result.response_time;
                    url_response_times.push(response_time);
                    total_response_time += response_time;
                    min_response_time = min_response_time.min(response_time);
                    max_response_time = max_response_time.max(response_time);
                }

                url_results.requests.push(request_result);
            }
        }

        url_results.successful_requests = url_successful;
        url_results.success_rate = if url_results.total_requests > 0 {
            (url_successful as f64 / url_results.total_requests as f64) * 100.0
        } else {
            0.0
        };

        if !url_response_times.is_empty() {
            url_results.avg_response_time = url_response_times.iter().sum::<f64>() / url_response_times.len() as f64;
        }

        urls_results.insert(url.clone(), url_results);
    }

    let success_rate = if total_requests > 0 {
        (successful_requests as f64 / total_requests as f64) * 100.0
    } else {
        0.0
    };

    let avg_response_time = if successful_requests > 0 {
        total_response_time / successful_requests as f64
    } else {
        0.0
    };

    if min_response_time == f64::INFINITY {
        min_response_time = 0.0;
    }

    let end_time = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs_f64();

    Results {
        start_time,
        urls: urls_results,
        summary: Summary {
            total_requests,
            successful_requests,
            failed_requests: total_requests - successful_requests,
            avg_response_time,
            min_response_time,
            max_response_time,
            success_rate,
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

    let results = run_http_benchmark(&config.parameters);
    println!("{}", serde_json::to_string_pretty(&results)?);

    Ok(())
}