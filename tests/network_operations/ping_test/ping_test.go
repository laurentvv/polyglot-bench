package main

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"sync"
	"time"
)

type Config struct {
	Parameters Parameters `json:"parameters"`
}

type Parameters struct {
	Targets     []string `json:"targets"`
	PacketCount *int     `json:"packet_count,omitempty"`
	Timeout     *int     `json:"timeout,omitempty"`
}

type PingResult struct {
	AvgLatency    float64 `json:"avg_latency"`
	MinLatency    float64 `json:"min_latency"`
	MaxLatency    float64 `json:"max_latency"`
	PacketLoss    float64 `json:"packet_loss"`
	ExecutionTime float64 `json:"execution_time"`
	Error         *string `json:"error,omitempty"`
}

type Summary struct {
	TotalTargets      int     `json:"total_targets"`
	SuccessfulTargets int     `json:"successful_targets"`
	FailedTargets     int     `json:"failed_targets"`
	OverallAvgLatency float64 `json:"overall_avg_latency"`
}

type Results struct {
	StartTime          float64               `json:"start_time"`
	Targets            map[string]PingResult `json:"targets"`
	Summary            Summary               `json:"summary"`
	EndTime            float64               `json:"end_time"`
	TotalExecutionTime float64               `json:"total_execution_time"`
}

// Mock pingHost function that simulates ping without using system commands
// In a real implementation, we would use a native Go ping library like github.com/go-ping/ping
// For this implementation, we'll simulate ping by making a quick TCP connection to common ports
func pingHost(host string, count int, timeout int) PingResult {
	start := time.Now()
	
	var latencies []float64
	packetLoss := 0.0
	totalLost := 0
	
	for i := 0; i < count; i++ {
		// Try to connect to common ports as a simple "ping" simulation
		// First try port 80 (HTTP)
		conn, err := net.DialTimeout("tcp", host+":80", time.Duration(timeout)*time.Millisecond)
		if err != nil {
			// Try port 443 (HTTPS) if 80 fails
			conn, err = net.DialTimeout("tcp", host+":443", time.Duration(timeout)*time.Millisecond)
		}
		
		if err != nil {
			// Try DNS port if ports 80/443 fail
			conn, err = net.DialTimeout("tcp", host+":53", time.Duration(timeout)*time.Millisecond)
		}
		
		if err != nil {
			// If no port is reachable, count as packet loss
			totalLost++
		} else {
			// Calculate latency as the time it took to establish the connection
			conn.Close()
			latency := time.Since(start).Seconds() * 1000 // Convert to milliseconds
			latencies = append(latencies, latency)
		}
	}
	
	packetLoss = float64(totalLost) / float64(count) * 100.0
	
	result := PingResult{
		AvgLatency:    0.0,
		MinLatency:    float64(^uint(0) >> 1),
		MaxLatency:    0.0,
		PacketLoss:    packetLoss,
		ExecutionTime: time.Since(start).Seconds(),
		Error:         nil,
	}
	
	if len(latencies) > 0 {
		var sum float64
		for _, latency := range latencies {
			sum += latency
			if latency < result.MinLatency {
				result.MinLatency = latency
			}
			if latency > result.MaxLatency {
				result.MaxLatency = latency
			}
		}
		result.AvgLatency = sum / float64(len(latencies))
	} else {
		// If no packets returned, set to max value
		result.MinLatency = float64(^uint(0) >> 1)
		result.MaxLatency = float64(^uint(0) >> 1)
		result.AvgLatency = float64(^uint(0) >> 1)
		errMsg := "All packets lost"
		result.Error = &errMsg
	}
	
	return result
}



func runPingBenchmark(params Parameters) Results {
	startTime := float64(time.Now().UnixNano()) / 1e9

	packetCount := 3 // Reduced for better performance
	if params.PacketCount != nil {
		packetCount = *params.PacketCount
	}

	timeout := 3000 // Reduced for better performance
	if params.Timeout != nil {
		timeout = *params.Timeout
	}

	targets := make(map[string]PingResult)
	successfulTargets := 0
	failedTargets := 0
	totalLatency := 0.0
	successfulCount := 0

	// Use WaitGroup and channels for concurrent execution
	var wg sync.WaitGroup
	resultsChan := make(chan struct {
		target string
		result PingResult
	}, len(params.Targets))

	// Execute pings concurrently for better performance
	for _, target := range params.Targets {
		wg.Add(1)
		go func(t string) {
			defer wg.Done()
			fmt.Fprintf(os.Stderr, "Pinging %s...\n", t)
			pingResult := pingHost(t, packetCount, timeout)
			resultsChan <- struct {
				target string
				result PingResult
			}{target: t, result: pingResult}
		}(target)
	}

	// Close the channel once all goroutines are done
	go func() {
		wg.Wait()
		close(resultsChan)
	}()

	// Collect results
	for res := range resultsChan {
		targets[res.target] = res.result

		if res.result.Error == nil && res.result.PacketLoss < 100.0 {
			successfulTargets++
			if res.result.AvgLatency < float64(^uint(0)>>1) { // Check if not infinity
				totalLatency += res.result.AvgLatency
				successfulCount++
			}
		} else {
			failedTargets++
		}
	}

	overallAvgLatency := 0.0
	if successfulCount > 0 {
		overallAvgLatency = totalLatency / float64(successfulCount)
	}

	endTime := float64(time.Now().UnixNano()) / 1e9

	return Results{
		StartTime: startTime,
		Targets:   targets,
		Summary: Summary{
			TotalTargets:      len(params.Targets),
			SuccessfulTargets: successfulTargets,
			FailedTargets:     failedTargets,
			OverallAvgLatency: overallAvgLatency,
		},
		EndTime:            endTime,
		TotalExecutionTime: endTime - startTime,
	}
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <config_file>\n", os.Args[0])
		os.Exit(1)
	}

	configFile := os.Args[1]

	configData, err := os.ReadFile(configFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading config file: %v\n", err)
		os.Exit(1)
	}

	var config Config
	if err := json.Unmarshal(configData, &config); err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing config JSON: %v\n", err)
		os.Exit(1)
	}

	results := runPingBenchmark(config.Parameters)

	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling results: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(output))
}
