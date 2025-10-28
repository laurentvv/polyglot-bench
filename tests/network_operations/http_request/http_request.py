#!/usr/bin/env python3
"""
HTTP request test implementation in Python.
Measures HTTP request/response performance to specified endpoints.
"""

import json
import sys
import time
from typing import Dict, List, Optional, Any

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    import ssl
    HAS_REQUESTS = False


def create_session():
    """Create optimized session with connection pooling if available."""
    if HAS_REQUESTS:
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({'User-Agent': 'BenchmarkTool/1.0'})
        
        return session
    else:
        return None

def make_http_request(session, url: str, method: str = "GET", timeout: int = 10) -> Dict[str, Any]:
    """Make an HTTP request using optimized session or fallback."""
    start_time = time.perf_counter()
    
    if HAS_REQUESTS and session:
        try:
            response = session.request(
                method=method,
                url=url,
                timeout=timeout,
                verify=False  # Skip SSL verification for benchmarking
            )
            
            response_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
            
            return {
                "success": response.status_code < 400,
                "response_time": round(response_time, 2),
                "status_code": response.status_code,
                "content_length": len(response.content),
                "url": str(response.url)
            }
            
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "response_time": round(response_time, 2),
                "status_code": 0,
                "content_length": 0,
                "error": str(e)
            }
    else:
        # Fallback to urllib
        try:
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'BenchmarkTool/1.0')
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
                response_time = (time.perf_counter() - start_time) * 1000
                content = response.read()
                
                return {
                    "success": True,
                    "response_time": round(response_time, 2),
                    "status_code": response.status,
                    "content_length": len(content),
                    "url": response.url
                }
                
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "response_time": round(response_time, 2),
                "status_code": 0,
                "content_length": 0,
                "error": str(e)
            }


def run_http_benchmark(config: Dict) -> Dict:
    """Run HTTP request benchmark with given configuration."""
    urls = config.get("urls", ["http://httpbin.org/get"])  # Use HTTP for faster benchmarking
    request_count = config.get("request_count", 3)  # Reduce for faster benchmarking
    timeout = config.get("timeout", 5000) / 1000  # Shorter timeout
    methods = config.get("methods", ["GET"])
    concurrent_requests = config.get("concurrent_requests", 1)
    
    # Create optimized session
    session = create_session()
    
    results = {
        "start_time": time.time(),
        "urls": {},
        "summary": {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "min_response_time": float('inf'),
            "max_response_time": 0.0,
            "success_rate": 0.0
        }
    }
    
    total_response_time = 0.0
    min_response_time = float('inf')
    max_response_time = 0.0
    total_requests = 0
    successful_requests = 0
    
    for url in urls:
        print(f"Testing {url}...", file=sys.stderr)
        
        url_results = {
            "requests": [],
            "avg_response_time": 0.0,
            "success_rate": 0.0,
            "total_requests": 0,
            "successful_requests": 0
        }
        
        url_response_times = []
        url_successful = 0
        
        for method in methods:
            for i in range(request_count):
                print(f"  Request {i+1}/{request_count} ({method})...", file=sys.stderr)
                
                request_result = make_http_request(session, url, method, timeout)
                url_results["requests"].append(request_result)
                
                total_requests += 1
                url_results["total_requests"] += 1
                
                if request_result["success"]:
                    successful_requests += 1
                    url_successful += 1
                    
                    response_time = request_result["response_time"]
                    url_response_times.append(response_time)
                    total_response_time += response_time
                    min_response_time = min(min_response_time, response_time)
                    max_response_time = max(max_response_time, response_time)
        
        # Calculate URL-specific metrics
        url_results["successful_requests"] = url_successful
        url_results["success_rate"] = (url_successful / url_results["total_requests"]) * 100
        
        if url_response_times:
            url_results["avg_response_time"] = sum(url_response_times) / len(url_response_times)
        
        results["urls"][url] = url_results
    
    # Calculate overall summary
    results["summary"]["total_requests"] = total_requests
    results["summary"]["successful_requests"] = successful_requests
    results["summary"]["failed_requests"] = total_requests - successful_requests
    results["summary"]["success_rate"] = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
    
    if successful_requests > 0:
        results["summary"]["avg_response_time"] = total_response_time / successful_requests
        results["summary"]["min_response_time"] = min_response_time
        results["summary"]["max_response_time"] = max_response_time
    else:
        results["summary"]["min_response_time"] = 0.0
    
    results["end_time"] = time.time()
    results["total_execution_time"] = results["end_time"] - results["start_time"]
    
    return results


def main():
    """Main entry point for HTTP request test."""
    if len(sys.argv) < 2:
        print("Usage: python http_request.py <config_file>", file=sys.stderr)
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Extract parameters from config
        parameters = config.get("parameters", {})
        
        # Run the benchmark
        results = run_http_benchmark(parameters)
        
        # Output results as JSON
        print(json.dumps(results, indent=2))
        
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()