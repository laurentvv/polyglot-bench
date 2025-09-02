#!/usr/bin/env python3
"""
DNS lookup performance test implementation in Python.
Measures DNS resolution performance for various domain types.
"""

import json
import sys
import time
import socket
import concurrent.futures
from typing import Dict, List, Any
import threading


def resolve_domain(domain: str, timeout: float = 5.0) -> Dict[str, Any]:
    """Resolve a single domain and measure timing."""
    start_time = time.time()
    result = {
        "domain": domain,
        "success": False,
        "response_time_ms": 0.0,
        "ip_addresses": [],
        "error": None
    }
    
    try:
        # Resolve domain to IP addresses
        ip_addresses = socket.gethostbyname_ex(domain)[2]
        end_time = time.time()
        
        result.update({
            "success": True,
            "response_time_ms": (end_time - start_time) * 1000,
            "ip_addresses": ip_addresses
        })
        
    except socket.gaierror as e:
        end_time = time.time()
        result.update({
            "response_time_ms": (end_time - start_time) * 1000,
            "error": f"DNS resolution failed: {str(e)}"
        })
    except Exception as e:
        end_time = time.time()
        result.update({
            "response_time_ms": (end_time - start_time) * 1000,
            "error": f"Unexpected error: {str(e)}"
        })
    
    return result


def resolve_domains_sequential(domains: List[str], timeout: float = 5.0) -> List[Dict[str, Any]]:
    """Resolve domains sequentially."""
    results = []
    for domain in domains:
        result = resolve_domain(domain, timeout)
        results.append(result)
        print(f"  Resolved {domain}: {'✓' if result['success'] else '✗'} ({result['response_time_ms']:.2f}ms)", file=sys.stderr)
    return results


def resolve_domains_concurrent(domains: List[str], max_workers: int = 5, timeout: float = 5.0) -> List[Dict[str, Any]]:
    """Resolve domains concurrently using thread pool."""
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_domain = {
            executor.submit(resolve_domain, domain, timeout): domain 
            for domain in domains
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_domain):
            domain = future_to_domain[future]
            try:
                result = future.result()
                results.append(result)
                print(f"  Resolved {domain}: {'✓' if result['success'] else '✗'} ({result['response_time_ms']:.2f}ms)", file=sys.stderr)
            except Exception as e:
                error_result = {
                    "domain": domain,
                    "success": False,
                    "response_time_ms": 0.0,
                    "ip_addresses": [],
                    "error": f"Future execution failed: {str(e)}"
                }
                results.append(error_result)
                print(f"  Resolved {domain}: ✗ (future failed)", file=sys.stderr)
    
    # Sort results by domain name to maintain consistent order
    results.sort(key=lambda x: x["domain"])
    return results


def run_dns_benchmark(config: Dict) -> Dict:
    """Run DNS lookup benchmark."""
    domains = config.get("domains", ["google.com", "github.com", "stackoverflow.com"])
    resolution_modes = config.get("resolution_modes", ["sequential"])
    iterations = config.get("iterations", 3)
    timeout = config.get("timeout_seconds", 5.0)
    concurrent_workers = config.get("concurrent_workers", 5)
    
    results = {
        "start_time": time.time(),
        "test_cases": [],
        "summary": {
            "total_domains": len(domains),
            "total_iterations": 0,
            "successful_resolutions": 0,
            "failed_resolutions": 0,
            "avg_resolution_time": 0.0,
            "fastest_resolution": float('inf'),
            "slowest_resolution": 0.0
        }
    }
    
    all_resolution_times = []
    
    for mode in resolution_modes:
        print(f"Testing DNS resolution mode: {mode}...", file=sys.stderr)
        
        test_case = {
            "resolution_mode": mode,
            "domains_count": len(domains),
            "iterations": [],
            "avg_resolution_time": 0.0,
            "success_rate": 0.0,
            "total_time": 0.0
        }
        
        mode_resolution_times = []
        mode_successful = 0
        mode_total = 0
        
        for i in range(iterations):
            print(f"  Iteration {i+1}/{iterations}...", file=sys.stderr)
            
            iteration_start = time.time()
            
            if mode == "sequential":
                domain_results = resolve_domains_sequential(domains, timeout)
            elif mode == "concurrent":
                domain_results = resolve_domains_concurrent(domains, concurrent_workers, timeout)
            else:
                print(f"Warning: Unknown resolution mode '{mode}', using sequential", file=sys.stderr)
                domain_results = resolve_domains_sequential(domains, timeout)
            
            iteration_end = time.time()
            iteration_total_time = (iteration_end - iteration_start) * 1000  # ms
            
            # Calculate iteration statistics
            iteration_successful = sum(1 for r in domain_results if r["success"])
            iteration_failed = len(domain_results) - iteration_successful
            iteration_avg_time = sum(r["response_time_ms"] for r in domain_results if r["success"])
            if iteration_successful > 0:
                iteration_avg_time /= iteration_successful
            
            # Collect timing data
            for result in domain_results:
                if result["success"]:
                    mode_resolution_times.append(result["response_time_ms"])
                    all_resolution_times.append(result["response_time_ms"])
            
            mode_successful += iteration_successful
            mode_total += len(domain_results)
            results["summary"]["total_iterations"] += 1
            
            iteration_result = {
                "iteration": i + 1,
                "total_time_ms": iteration_total_time,
                "domains_resolved": len(domain_results),
                "successful_resolutions": iteration_successful,
                "failed_resolutions": iteration_failed,
                "avg_resolution_time_ms": iteration_avg_time,
                "domain_results": domain_results
            }
            
            test_case["iterations"].append(iteration_result)
        
        # Calculate test case averages
        if mode_resolution_times:
            test_case["avg_resolution_time"] = sum(mode_resolution_times) / len(mode_resolution_times)
            test_case["fastest_resolution"] = min(mode_resolution_times)
            test_case["slowest_resolution"] = max(mode_resolution_times)
        
        test_case["success_rate"] = (mode_successful / mode_total) * 100 if mode_total > 0 else 0
        test_case["total_successful"] = mode_successful
        test_case["total_attempts"] = mode_total
        
        results["test_cases"].append(test_case)
    
    # Calculate overall summary
    results["summary"]["successful_resolutions"] = sum(1 for t in all_resolution_times)
    results["summary"]["failed_resolutions"] = (
        results["summary"]["total_iterations"] * len(domains) - results["summary"]["successful_resolutions"]
    )
    
    if all_resolution_times:
        results["summary"]["avg_resolution_time"] = sum(all_resolution_times) / len(all_resolution_times)
        results["summary"]["fastest_resolution"] = min(all_resolution_times)
        results["summary"]["slowest_resolution"] = max(all_resolution_times)
    else:
        results["summary"]["fastest_resolution"] = 0.0
    
    results["end_time"] = time.time()
    results["total_execution_time"] = results["end_time"] - results["start_time"]
    
    return results


def main():
    """Main entry point for DNS lookup test."""
    if len(sys.argv) < 2:
        print("Usage: python dns_lookup.py <config_file>", file=sys.stderr)
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        parameters = config.get("parameters", {})
        results = run_dns_benchmark(parameters)
        
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