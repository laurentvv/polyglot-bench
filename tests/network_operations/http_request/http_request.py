#!/usr/bin/env python3
"""
HTTP request test implementation in Python.
Measures HTTP request/response performance to specified endpoints.
"""

import json
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, List, Optional, Any
import ssl


def make_http_request(url: str, method: str = "GET", timeout: int = 10) -> Dict[str, Any]:
    """
    Make an HTTP request and measure performance metrics.
    
    Args:
        url: Target URL to request
        method: HTTP method (GET, POST, etc.)
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with request performance metrics
    """
    start_time = time.time()
    
    try:
        # Create request
        request = urllib.request.Request(url, method=method)
        request.add_header('User-Agent', 'BenchmarkTool/1.0')
        
        # Handle HTTPS certificates
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Make the request
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            response_time = time.time() - start_time
            content = response.read()
            
            return {
                "success": True,
                "response_time": round(response_time * 1000, 2),  # Convert to ms
                "status_code": response.status,
                "content_length": len(content),
                "headers": dict(response.headers),
                "url": response.url
            }
            
    except urllib.error.HTTPError as e:
        response_time = time.time() - start_time
        return {
            "success": False,
            "response_time": round(response_time * 1000, 2),
            "status_code": e.code,
            "content_length": 0,
            "error": f"HTTP Error {e.code}: {e.reason}"
        }
        
    except urllib.error.URLError as e:
        response_time = time.time() - start_time
        return {
            "success": False,
            "response_time": round(response_time * 1000, 2),
            "status_code": 0,
            "content_length": 0,
            "error": f"URL Error: {e.reason}"
        }
        
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "success": False,
            "response_time": round(response_time * 1000, 2),
            "status_code": 0,
            "content_length": 0,
            "error": str(e)
        }


def run_http_benchmark(config: Dict) -> Dict:
    """Run HTTP request benchmark with given configuration."""
    urls = config.get("urls", ["https://httpbin.org/get"])
    request_count = config.get("request_count", 5)
    timeout = config.get("timeout", 10000) / 1000  # Convert to seconds
    methods = config.get("methods", ["GET"])
    concurrent_requests = config.get("concurrent_requests", 1)
    
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
                
                request_result = make_http_request(url, method, timeout)
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