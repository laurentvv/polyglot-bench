#!/usr/bin/env python3
"""
Ping test implementation in Python.
Measures network latency and packet loss to specified targets.
Optimized version for better performance using concurrent execution.
"""

import json
import sys
import time
import subprocess
import platform
import re
import concurrent.futures
from typing import Dict, List, Optional


def ping_host(host: str, count: int = 3, timeout: int = 3000) -> Dict[str, float]:
    """
    Ping a host and return latency statistics.
    
    Args:
        host: Target host to ping
        count: Number of ping packets to send (reduced for better performance)
        timeout: Timeout in milliseconds (reduced for better performance)
        
    Returns:
        Dictionary with latency statistics
    """
    system = platform.system().lower()
    
    if system == "windows":
        cmd = ["ping", "-n", str(count), "-w", str(timeout), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(timeout // 1000), host]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return {
                "avg_latency": float('inf'),
                "min_latency": float('inf'),
                "max_latency": float('inf'),
                "packet_loss": 100.0,
                "error": result.stderr or "Ping failed"
            }
        
        return parse_ping_output(result.stdout, system)
        
    except subprocess.TimeoutExpired:
        return {
            "avg_latency": float('inf'),
            "min_latency": float('inf'),
            "max_latency": float('inf'),
            "packet_loss": 100.0,
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "avg_latency": float('inf'),
            "min_latency": float('inf'),
            "max_latency": float('inf'),
            "packet_loss": 100.0,
            "error": str(e)
        }


def parse_ping_output(output: str, system: str) -> Dict[str, float]:
    """Parse ping command output and extract statistics."""
    stats = {
        "avg_latency": 0.0,
        "min_latency": 0.0,
        "max_latency": 0.0,
        "packet_loss": 0.0
    }
    
    try:
        if system == "windows":
            # Parse Windows ping output
            # Look for packet loss percentage
            loss_match = re.search(r'(\d+)% loss', output)
            if loss_match:
                stats["packet_loss"] = float(loss_match.group(1))
            
            # Look for latency statistics
            # Find all time values in ms
            time_matches = re.findall(r'time[<>=]\s*(\d+)ms', output)
            if time_matches:
                times = [float(t) for t in time_matches]
                stats["min_latency"] = min(times)
                stats["max_latency"] = max(times)
                stats["avg_latency"] = sum(times) / len(times)
            
            # Alternative: look for Average line
            avg_match = re.search(r'Average = (\d+)ms', output)
            if avg_match:
                stats["avg_latency"] = float(avg_match.group(1))
                
        else:
            # Parse Unix/Linux ping output
            # Look for packet loss
            loss_match = re.search(r'(\d+(?:\.\d+)?)% packet loss', output)
            if loss_match:
                stats["packet_loss"] = float(loss_match.group(1))
            
            # Look for rtt statistics line
            rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', output)
            if rtt_match:
                stats["min_latency"] = float(rtt_match.group(1))
                stats["avg_latency"] = float(rtt_match.group(2))
                stats["max_latency"] = float(rtt_match.group(3))
    
    except Exception:
        # If parsing fails, set default values
        stats = {
            "avg_latency": float('inf'),
            "min_latency": float('inf'),
            "max_latency": float('inf'),
            "packet_loss": 100.0,
            "error": "Failed to parse ping output"
        }
    
    return stats


def run_ping_benchmark(config: Dict) -> Dict:
    """Run ping benchmark with given configuration using concurrent execution."""
    targets = config.get("targets", ["8.8.8.8"])
    packet_count = config.get("packet_count", 3)  # Reduced for better performance
    timeout = config.get("timeout", 3000)  # Reduced for better performance
    
    results = {
        "start_time": time.time(),
        "targets": {},
        "summary": {
            "total_targets": len(targets),
            "successful_targets": 0,
            "failed_targets": 0,
            "overall_avg_latency": 0.0
        }
    }
    
    total_latency = 0.0
    successful_count = 0
    
    # Execute pings concurrently for better performance
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(targets))) as executor:
        # Submit all ping tasks
        future_to_target = {
            executor.submit(ping_host, target, packet_count, timeout): target 
            for target in targets
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_target):
            target = future_to_target[future]
            print(f"Pinging {target}...", file=sys.stderr)
            
            try:
                ping_result = future.result()
                results["targets"][target] = ping_result
                
                if ping_result.get("error") is None and ping_result["packet_loss"] < 100:
                    results["summary"]["successful_targets"] += 1
                    if ping_result["avg_latency"] != float('inf'):
                        total_latency += ping_result["avg_latency"]
                        successful_count += 1
                else:
                    results["summary"]["failed_targets"] += 1
            except Exception as e:
                results["targets"][target] = {
                    "avg_latency": float('inf'),
                    "min_latency": float('inf'),
                    "max_latency": float('inf'),
                    "packet_loss": 100.0,
                    "error": str(e)
                }
                results["summary"]["failed_targets"] += 1
    
    if successful_count > 0:
        results["summary"]["overall_avg_latency"] = total_latency / successful_count
    
    results["end_time"] = time.time()
    results["total_execution_time"] = results["end_time"] - results["start_time"]
    
    return results


def main():
    """Main entry point for ping test."""
    if len(sys.argv) < 2:
        print("Usage: python ping_test.py <config_file>", file=sys.stderr)
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Extract parameters from config
        parameters = config.get("parameters", {})
        
        # Run the benchmark
        results = run_ping_benchmark(parameters)
        
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