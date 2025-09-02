package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"runtime"
	"strconv"
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

func pingHost(host string, count int, timeout int) PingResult {
	start := time.Now()

	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("ping", "-n", strconv.Itoa(count), "-w", strconv.Itoa(timeout), host)
	} else {
		timeoutSec := timeout / 1000
		cmd = exec.Command("ping", "-c", strconv.Itoa(count), "-W", strconv.Itoa(timeoutSec), host)
	}

	output, err := cmd.CombinedOutput()
	executionTime := time.Since(start).Seconds()

	if err != nil {
		errMsg := err.Error()
		return PingResult{
			AvgLatency:    float64(^uint(0) >> 1), // Max float64
			MinLatency:    float64(^uint(0) >> 1),
			MaxLatency:    float64(^uint(0) >> 1),
			PacketLoss:    100.0,
			ExecutionTime: executionTime,
			Error:         &errMsg,
		}
	}

	result := parsePingOutput(string(output))
	result.ExecutionTime = executionTime
	return result
}

func parsePingOutput(output string) PingResult {
	result := PingResult{
		AvgLatency: 0.0,
		MinLatency: 0.0,
		MaxLatency: 0.0,
		PacketLoss: 0.0,
	}

	if runtime.GOOS == "windows" {
		// Parse Windows ping output (supports both English and French)
		// Look for packet loss percentage
		lossRegex := regexp.MustCompile(`(\d+)%\s*(?:loss|perte)`)
		if matches := lossRegex.FindStringSubmatch(output); matches != nil {
			if loss, err := strconv.ParseFloat(matches[1], 64); err == nil {
				result.PacketLoss = loss
			}
		}

		// Extract individual ping times (supports both English and French)
		timeRegex := regexp.MustCompile(`(?:time[<>=]|temps[<>=])\s*(\d+)\s*ms`)
		timeMatches := timeRegex.FindAllStringSubmatch(output, -1)

		var times []float64
		for _, match := range timeMatches {
			if time, err := strconv.ParseFloat(match[1], 64); err == nil {
				times = append(times, time)
			}
		}

		if len(times) > 0 {
			result.MinLatency = times[0]
			result.MaxLatency = times[0]
			sum := 0.0

			for _, t := range times {
				if t < result.MinLatency {
					result.MinLatency = t
				}
				if t > result.MaxLatency {
					result.MaxLatency = t
				}
				sum += t
			}
			result.AvgLatency = sum / float64(len(times))
		}

		// Try to get average from summary line (English)
		avgRegex := regexp.MustCompile(`Average = (\d+)ms`)
		if matches := avgRegex.FindStringSubmatch(output); matches != nil {
			if avg, err := strconv.ParseFloat(matches[1], 64); err == nil {
				result.AvgLatency = avg
			}
		}

		// Try to get statistics from French summary line
		// "Minimum = 9ms, Maximum = 11ms, Moyenne = 10ms"
		frenchStatsRegex := regexp.MustCompile(`Minimum = (\d+)ms, Maximum = (\d+)ms, Moyenne = (\d+)ms`)
		if matches := frenchStatsRegex.FindStringSubmatch(output); matches != nil {
			if min, err := strconv.ParseFloat(matches[1], 64); err == nil {
				result.MinLatency = min
			}
			if max, err := strconv.ParseFloat(matches[2], 64); err == nil {
				result.MaxLatency = max
			}
			if avg, err := strconv.ParseFloat(matches[3], 64); err == nil {
				result.AvgLatency = avg
			}
		}
	} else {
		// Parse Unix/Linux ping output
		lossRegex := regexp.MustCompile(`(\d+(?:\.\d+)?)% packet loss`)
		if matches := lossRegex.FindStringSubmatch(output); matches != nil {
			if loss, err := strconv.ParseFloat(matches[1], 64); err == nil {
				result.PacketLoss = loss
			}
		}

		// Parse rtt statistics
		rttRegex := regexp.MustCompile(`rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms`)
		if matches := rttRegex.FindStringSubmatch(output); matches != nil {
			if min, err := strconv.ParseFloat(matches[1], 64); err == nil {
				result.MinLatency = min
			}
			if avg, err := strconv.ParseFloat(matches[2], 64); err == nil {
				result.AvgLatency = avg
			}
			if max, err := strconv.ParseFloat(matches[3], 64); err == nil {
				result.MaxLatency = max
			}
		}
	}

	// If no valid latency was parsed, mark as error
	if result.AvgLatency == 0.0 && result.PacketLoss == 100.0 {
		errMsg := "Failed to parse ping output"
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
