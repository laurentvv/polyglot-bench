package main

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

type Config struct {
	Parameters Parameters `json:"parameters"`
}

type Parameters struct {
	URLs               []string  `json:"urls"`
	RequestCount       *int      `json:"request_count,omitempty"`
	Timeout            *int      `json:"timeout,omitempty"`
	Methods            *[]string `json:"methods,omitempty"`
	ConcurrentRequests *int      `json:"concurrent_requests,omitempty"`
}

type RequestResult struct {
	Success       bool    `json:"success"`
	ResponseTime  float64 `json:"response_time"`
	StatusCode    int     `json:"status_code"`
	ContentLength int     `json:"content_length"`
	Error         *string `json:"error,omitempty"`
}

type URLResults struct {
	Requests           []RequestResult `json:"requests"`
	AvgResponseTime    float64         `json:"avg_response_time"`
	SuccessRate        float64         `json:"success_rate"`
	TotalRequests      int             `json:"total_requests"`
	SuccessfulRequests int             `json:"successful_requests"`
}

type Summary struct {
	TotalRequests      int     `json:"total_requests"`
	SuccessfulRequests int     `json:"successful_requests"`
	FailedRequests     int     `json:"failed_requests"`
	AvgResponseTime    float64 `json:"avg_response_time"`
	MinResponseTime    float64 `json:"min_response_time"`
	MaxResponseTime    float64 `json:"max_response_time"`
	SuccessRate        float64 `json:"success_rate"`
}

type Results struct {
	StartTime           float64                `json:"start_time"`
	URLs                map[string]URLResults  `json:"urls"`
	Summary             Summary                `json:"summary"`
	EndTime             float64                `json:"end_time"`
	TotalExecutionTime  float64                `json:"total_execution_time"`
}

func makeHTTPRequest(client *http.Client, url, method string) RequestResult {
	start := time.Now()

	// Create request
	req, err := http.NewRequest(strings.ToUpper(method), url, nil)
	if err != nil {
		responseTime := float64(time.Since(start).Nanoseconds()) / 1e6
		errMsg := fmt.Sprintf("Request creation error: %v", err)
		return RequestResult{
			Success:       false,
			ResponseTime:  responseTime,
			StatusCode:    0,
			ContentLength: 0,
			Error:         &errMsg,
		}
	}

	req.Header.Set("User-Agent", "BenchmarkTool/1.0")

	// Make the request
	resp, err := client.Do(req)
	responseTime := float64(time.Since(start).Nanoseconds()) / 1e6

	if err != nil {
		errMsg := err.Error()
		return RequestResult{
			Success:       false,
			ResponseTime:  responseTime,
			StatusCode:    0,
			ContentLength: 0,
			Error:         &errMsg,
		}
	}
	defer resp.Body.Close()

	// Read response body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		errMsg := fmt.Sprintf("Content read error: %v", err)
		return RequestResult{
			Success:       false,
			ResponseTime:  responseTime,
			StatusCode:    resp.StatusCode,
			ContentLength: 0,
			Error:         &errMsg,
		}
	}

	isSuccess := resp.StatusCode >= 200 && resp.StatusCode < 300
	var errorMsg *string
	if !isSuccess {
		msg := fmt.Sprintf("HTTP Error %d", resp.StatusCode)
		errorMsg = &msg
	}

	return RequestResult{
		Success:       isSuccess,
		ResponseTime:  responseTime,
		StatusCode:    resp.StatusCode,
		ContentLength: len(body),
		Error:         errorMsg,
	}
}

func runHTTPBenchmark(params Parameters) Results {
	startTime := float64(time.Now().UnixNano()) / 1e9

	requestCount := 5
	if params.RequestCount != nil {
		requestCount = *params.RequestCount
	}

	timeout := 10000
	if params.Timeout != nil {
		timeout = *params.Timeout
	}

	methods := []string{"GET"}
	if params.Methods != nil {
		methods = *params.Methods
	}

	urlsResults := make(map[string]URLResults)
	totalRequests := 0
	successfulRequests := 0
	var totalResponseTime float64
	minResponseTime := float64(^uint(0) >> 1) // Max float64
	var maxResponseTime float64

	client := &http.Client{
		Timeout: time.Duration(timeout) * time.Millisecond,
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		},
	}

	for _, url := range params.URLs {
		fmt.Fprintf(os.Stderr, "Testing %s...\n", url)

		urlResults := URLResults{
			Requests: make([]RequestResult, 0),
		}

		var urlResponseTimes []float64
		urlSuccessful := 0

		for _, method := range methods {
			for i := 0; i < requestCount; i++ {
				fmt.Fprintf(os.Stderr, "  Request %d/%d (%s)...\n", i+1, requestCount, method)

				requestResult := makeHTTPRequest(client, url, method)

				totalRequests++
				urlResults.TotalRequests++

				if requestResult.Success {
					successfulRequests++
					urlSuccessful++

					responseTime := requestResult.ResponseTime
					urlResponseTimes = append(urlResponseTimes, responseTime)
					totalResponseTime += responseTime

					if responseTime < minResponseTime {
						minResponseTime = responseTime
					}
					if responseTime > maxResponseTime {
						maxResponseTime = responseTime
					}
				}

				urlResults.Requests = append(urlResults.Requests, requestResult)
			}
		}

		urlResults.SuccessfulRequests = urlSuccessful
		if urlResults.TotalRequests > 0 {
			urlResults.SuccessRate = float64(urlSuccessful) / float64(urlResults.TotalRequests) * 100.0
		}

		if len(urlResponseTimes) > 0 {
			sum := 0.0
			for _, rt := range urlResponseTimes {
				sum += rt
			}
			urlResults.AvgResponseTime = sum / float64(len(urlResponseTimes))
		}

		urlsResults[url] = urlResults
	}

	successRate := 0.0
	if totalRequests > 0 {
		successRate = float64(successfulRequests) / float64(totalRequests) * 100.0
	}

	avgResponseTime := 0.0
	if successfulRequests > 0 {
		avgResponseTime = totalResponseTime / float64(successfulRequests)
	}

	if minResponseTime == float64(^uint(0)>>1) {
		minResponseTime = 0.0
	}

	endTime := float64(time.Now().UnixNano()) / 1e9

	return Results{
		StartTime: startTime,
		URLs:      urlsResults,
		Summary: Summary{
			TotalRequests:      totalRequests,
			SuccessfulRequests: successfulRequests,
			FailedRequests:     totalRequests - successfulRequests,
			AvgResponseTime:    avgResponseTime,
			MinResponseTime:    minResponseTime,
			MaxResponseTime:    maxResponseTime,
			SuccessRate:        successRate,
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

	results := runHTTPBenchmark(config.Parameters)

	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling results: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(output))
}