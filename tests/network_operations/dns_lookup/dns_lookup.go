package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"sort"
	"sync"
	"time"
)

type DnsResult struct {
	Domain         string   `json:"domain"`
	Success        bool     `json:"success"`
	ResponseTimeMs float64  `json:"response_time_ms"`
	IPAddresses    []string `json:"ip_addresses"`
	Error          *string  `json:"error,omitempty"`
}

type IterationResult struct {
	Iteration             int         `json:"iteration"`
	TotalTimeMs           float64     `json:"total_time_ms"`
	DomainsResolved       int         `json:"domains_resolved"`
	SuccessfulResolutions int         `json:"successful_resolutions"`
	FailedResolutions     int         `json:"failed_resolutions"`
	AvgResolutionTimeMs   float64     `json:"avg_resolution_time_ms"`
	DomainResults         []DnsResult `json:"domain_results"`
}

type TestCase struct {
	ResolutionMode    string            `json:"resolution_mode"`
	DomainsCount      int               `json:"domains_count"`
	Iterations        []IterationResult `json:"iterations"`
	AvgResolutionTime float64           `json:"avg_resolution_time"`
	FastestResolution float64           `json:"fastest_resolution"`
	SlowestResolution float64           `json:"slowest_resolution"`
	SuccessRate       float64           `json:"success_rate"`
	TotalSuccessful   int               `json:"total_successful"`
	TotalAttempts     int               `json:"total_attempts"`
}

type Summary struct {
	TotalDomains          int     `json:"total_domains"`
	TotalIterations       int     `json:"total_iterations"`
	SuccessfulResolutions int     `json:"successful_resolutions"`
	FailedResolutions     int     `json:"failed_resolutions"`
	AvgResolutionTime     float64 `json:"avg_resolution_time"`
	FastestResolution     float64 `json:"fastest_resolution"`
	SlowestResolution     float64 `json:"slowest_resolution"`
}

type BenchmarkResult struct {
	StartTime          int64      `json:"start_time"`
	TestCases          []TestCase `json:"test_cases"`
	Summary            Summary    `json:"summary"`
	EndTime            int64      `json:"end_time"`
	TotalExecutionTime float64    `json:"total_execution_time"`
}

type Config struct {
	Parameters struct {
		Domains           []string `json:"domains"`
		ResolutionModes   []string `json:"resolution_modes"`
		Iterations        int      `json:"iterations"`
		TimeoutSeconds    int      `json:"timeout_seconds"`
		ConcurrentWorkers int      `json:"concurrent_workers"`
	} `json:"parameters"`
}

func resolveDomain(domain string, timeoutSecs int) DnsResult {
	start := time.Now()
	result := DnsResult{
		Domain:         domain,
		Success:        false,
		ResponseTimeMs: 0.0,
		IPAddresses:    []string{},
	}

	// Create context with timeout for DNS resolution
	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeoutSecs)*time.Second)
	defer cancel()

	// Set timeout for DNS resolution
	resolver := &net.Resolver{
		PreferGo: true,
		Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
			d := net.Dialer{
				Timeout: time.Duration(timeoutSecs) * time.Second,
			}
			return d.DialContext(ctx, network, address)
		},
	}

	ips, err := resolver.LookupIPAddr(ctx, domain)
	elapsed := time.Since(start)
	result.ResponseTimeMs = float64(elapsed.Nanoseconds()) / 1e6

	if err != nil {
		errMsg := fmt.Sprintf("DNS resolution failed: %v", err)
		result.Error = &errMsg
	} else {
		result.Success = true
		for _, ip := range ips {
			result.IPAddresses = append(result.IPAddresses, ip.IP.String())
		}
	}

	return result
}

func resolveDomainsSequential(domains []string, timeoutSecs int) []DnsResult {
	var results []DnsResult

	for _, domain := range domains {
		result := resolveDomain(domain, timeoutSecs)
		status := "✗"
		if result.Success {
			status = "✓"
		}
		fmt.Fprintf(os.Stderr, "  Resolved %s: %s (%.2fms)\n",
			domain, status, result.ResponseTimeMs)
		results = append(results, result)
	}

	return results
}

func resolveDomainsConcurrent(domains []string, maxWorkers, timeoutSecs int) []DnsResult {
	var wg sync.WaitGroup
	resultsChan := make(chan DnsResult, len(domains))
	semaphore := make(chan struct{}, maxWorkers)

	for _, domain := range domains {
		wg.Add(1)
		go func(d string) {
			defer wg.Done()
			semaphore <- struct{}{} // acquire

			result := resolveDomain(d, timeoutSecs)
			status := "✗"
			if result.Success {
				status = "✓"
			}
			fmt.Fprintf(os.Stderr, "  Resolved %s: %s (%.2fms)\n",
				d, status, result.ResponseTimeMs)

			resultsChan <- result
			<-semaphore // release
		}(domain)
	}

	wg.Wait()
	close(resultsChan)

	var results []DnsResult
	for result := range resultsChan {
		results = append(results, result)
	}

	// Sort by domain name for consistent ordering
	sort.Slice(results, func(i, j int) bool {
		return results[i].Domain < results[j].Domain
	})

	return results
}

func runDnsBenchmark(config Config) BenchmarkResult {
	params := config.Parameters

	// Set defaults
	if len(params.Domains) == 0 {
		params.Domains = []string{"google.com", "github.com", "stackoverflow.com"}
	}
	if len(params.ResolutionModes) == 0 {
		params.ResolutionModes = []string{"sequential"}
	}
	if params.Iterations == 0 {
		params.Iterations = 3
	}
	if params.TimeoutSeconds == 0 {
		params.TimeoutSeconds = 5
	}
	if params.ConcurrentWorkers == 0 {
		params.ConcurrentWorkers = 5
	}

	startTime := time.Now()
	var testCases []TestCase
	var allResolutionTimes []float64
	totalIterations := 0

	for _, mode := range params.ResolutionModes {
		fmt.Fprintf(os.Stderr, "Testing DNS resolution mode: %s...\n", mode)

		var modeResolutionTimes []float64
		modeSuccessful := 0
		modeTotal := 0
		var iterationsData []IterationResult

		for i := 0; i < params.Iterations; i++ {
			fmt.Fprintf(os.Stderr, "  Iteration %d/%d...\n", i+1, params.Iterations)

			iterationStart := time.Now()

			var domainResults []DnsResult
			switch mode {
			case "sequential":
				domainResults = resolveDomainsSequential(params.Domains, params.TimeoutSeconds)
			case "concurrent":
				domainResults = resolveDomainsConcurrent(params.Domains, params.ConcurrentWorkers, params.TimeoutSeconds)
			default:
				fmt.Fprintf(os.Stderr, "Warning: Unknown resolution mode '%s', using sequential\n", mode)
				domainResults = resolveDomainsSequential(params.Domains, params.TimeoutSeconds)
			}

			iterationTotalTime := float64(time.Since(iterationStart).Nanoseconds()) / 1e6

			iterationSuccessful := 0
			var iterationTimes []float64
			for _, result := range domainResults {
				if result.Success {
					iterationSuccessful++
					iterationTimes = append(iterationTimes, result.ResponseTimeMs)
					modeResolutionTimes = append(modeResolutionTimes, result.ResponseTimeMs)
					allResolutionTimes = append(allResolutionTimes, result.ResponseTimeMs)
				}
			}

			iterationFailed := len(domainResults) - iterationSuccessful

			var iterationAvgTime float64
			if len(iterationTimes) > 0 {
				sum := 0.0
				for _, t := range iterationTimes {
					sum += t
				}
				iterationAvgTime = sum / float64(len(iterationTimes))
			}

			modeSuccessful += iterationSuccessful
			modeTotal += len(domainResults)
			totalIterations++

			iterationResult := IterationResult{
				Iteration:             i + 1,
				TotalTimeMs:           iterationTotalTime,
				DomainsResolved:       len(domainResults),
				SuccessfulResolutions: iterationSuccessful,
				FailedResolutions:     iterationFailed,
				AvgResolutionTimeMs:   iterationAvgTime,
				DomainResults:         domainResults,
			}

			iterationsData = append(iterationsData, iterationResult)
		}

		// Calculate test case averages
		var avgResolutionTime, fastestResolution, slowestResolution float64
		if len(modeResolutionTimes) > 0 {
			sum := 0.0
			fastestResolution = modeResolutionTimes[0]
			slowestResolution = modeResolutionTimes[0]

			for _, t := range modeResolutionTimes {
				sum += t
				if t < fastestResolution {
					fastestResolution = t
				}
				if t > slowestResolution {
					slowestResolution = t
				}
			}
			avgResolutionTime = sum / float64(len(modeResolutionTimes))
		}

		var successRate float64
		if modeTotal > 0 {
			successRate = (float64(modeSuccessful) / float64(modeTotal)) * 100.0
		}

		testCase := TestCase{
			ResolutionMode:    mode,
			DomainsCount:      len(params.Domains),
			Iterations:        iterationsData,
			AvgResolutionTime: avgResolutionTime,
			FastestResolution: fastestResolution,
			SlowestResolution: slowestResolution,
			SuccessRate:       successRate,
			TotalSuccessful:   modeSuccessful,
			TotalAttempts:     modeTotal,
		}

		testCases = append(testCases, testCase)
	}

	// Calculate overall summary
	successfulResolutions := len(allResolutionTimes)
	failedResolutions := (totalIterations * len(params.Domains)) - successfulResolutions

	var avgResolutionTime, fastestResolution, slowestResolution float64
	if len(allResolutionTimes) > 0 {
		sum := 0.0
		fastestResolution = allResolutionTimes[0]
		slowestResolution = allResolutionTimes[0]

		for _, t := range allResolutionTimes {
			sum += t
			if t < fastestResolution {
				fastestResolution = t
			}
			if t > slowestResolution {
				slowestResolution = t
			}
		}
		avgResolutionTime = sum / float64(len(allResolutionTimes))
	}

	endTime := time.Now()
	executionTime := endTime.Sub(startTime).Seconds()

	return BenchmarkResult{
		StartTime: startTime.Unix(),
		TestCases: testCases,
		Summary: Summary{
			TotalDomains:          len(params.Domains),
			TotalIterations:       totalIterations,
			SuccessfulResolutions: successfulResolutions,
			FailedResolutions:     failedResolutions,
			AvgResolutionTime:     avgResolutionTime,
			FastestResolution:     fastestResolution,
			SlowestResolution:     slowestResolution,
		},
		EndTime:            endTime.Unix(),
		TotalExecutionTime: executionTime,
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
		fmt.Fprintf(os.Stderr, "Error: Cannot read config file '%s': %v\n", configFile, err)
		os.Exit(1)
	}

	var config Config
	if err := json.Unmarshal(configData, &config); err != nil {
		fmt.Fprintf(os.Stderr, "Error: Invalid JSON in config file: %v\n", err)
		os.Exit(1)
	}

	results := runDnsBenchmark(config)

	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Failed to marshal results: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(output))
}
