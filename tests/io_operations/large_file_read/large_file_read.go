package main

import (
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"time"
)

type ReadResult struct {
	ReadTime       float64  `json:"read_time"`
	BytesRead      int64    `json:"bytes_read"`
	ThroughputMbps float64  `json:"throughput_mbps"`
	ChunkCount     *int     `json:"chunk_count,omitempty"`
	AvgChunkSize   *float64 `json:"avg_chunk_size,omitempty"`
}

type IterationResult struct {
	Iteration      int      `json:"iteration"`
	ReadTime       float64  `json:"read_time"`
	BytesRead      int64    `json:"bytes_read"`
	ThroughputMbps float64  `json:"throughput_mbps"`
	MemoryUsed     float64  `json:"memory_used"`
	IOWaitTime     float64  `json:"io_wait_time"`
	ChunkCount     *int     `json:"chunk_count,omitempty"`
	AvgChunkSize   *float64 `json:"avg_chunk_size,omitempty"`
	Error          *string  `json:"error,omitempty"`
}

type TestCase struct {
	FileSize         int64             `json:"file_size"`
	BufferSize       int               `json:"buffer_size"`
	ReadPattern      string            `json:"read_pattern"`
	Iterations       []IterationResult `json:"iterations"`
	AvgReadTime      float64           `json:"avg_read_time"`
	AvgThroughput    float64           `json:"avg_throughput"`
	MemoryEfficiency float64           `json:"memory_efficiency"`
}

type Summary struct {
	TotalTests      int     `json:"total_tests"`
	SuccessfulTests int     `json:"successful_tests"`
	FailedTests     int     `json:"failed_tests"`
	AvgReadTime     float64 `json:"avg_read_time"`
	AvgThroughput   float64 `json:"avg_throughput"`
	PeakMemoryUsage float64 `json:"peak_memory_usage"`
}

type BenchmarkResult struct {
	StartTime     float64    `json:"start_time"`
	EndTime       float64    `json:"end_time"`
	TotalDuration float64    `json:"total_duration"`
	TestCases     []TestCase `json:"test_cases"`
	Summary       Summary    `json:"summary"`
}

type Config struct {
	Parameters map[string]interface{} `json:"parameters"`
}

func generateTestFile(filePath string, sizeBytes int64) error {
	fmt.Fprintf(os.Stderr, "Generating test file: %d bytes...\n", sizeBytes)

	file, err := os.Create(filePath)
	if err != nil {
		return err
	}
	defer file.Close()

	const chunkSize = 8192
	chars := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n"

	var bytesWritten int64
	for bytesWritten < sizeBytes {
		remaining := sizeBytes - bytesWritten
		currentChunkSize := chunkSize
		if remaining < chunkSize {
			currentChunkSize = int(remaining)
		}

		// Generate random text data
		data := make([]byte, currentChunkSize)
		for i := 0; i < currentChunkSize; i++ {
			data[i] = chars[rand.Intn(len(chars))]
		}

		n, err := file.Write(data)
		if err != nil {
			return err
		}
		bytesWritten += int64(n)
	}

	return file.Sync()
}

func readFileSequential(filePath string, bufferSize int) (*ReadResult, error) {
	startTime := time.Now()

	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	buffer := make([]byte, bufferSize)
	var totalBytes int64

	for {
		n, err := file.Read(buffer)
		if err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}
		totalBytes += int64(n)
	}

	readTime := time.Since(startTime)
	readTimeMs := float64(readTime.Nanoseconds()) / 1e6 // Convert to milliseconds

	var throughputMbps float64
	if readTime.Seconds() > 0 {
		throughputMbps = (float64(totalBytes) / (1024 * 1024)) / readTime.Seconds()
	}

	return &ReadResult{
		ReadTime:       readTimeMs,
		BytesRead:      totalBytes,
		ThroughputMbps: throughputMbps,
		ChunkCount:     nil,
		AvgChunkSize:   nil,
	}, nil
}

func readFileChunked(filePath string, bufferSize int) (*ReadResult, error) {
	startTime := time.Now()

	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	buffer := make([]byte, bufferSize)
	var totalBytes int64
	var chunkCount int

	for {
		n, err := file.Read(buffer)
		if err != nil {
			if err == io.EOF {
				break
			}
			return nil, err
		}
		totalBytes += int64(n)
		chunkCount++
	}

	readTime := time.Since(startTime)
	readTimeMs := float64(readTime.Nanoseconds()) / 1e6 // Convert to milliseconds

	var throughputMbps float64
	if readTime.Seconds() > 0 {
		throughputMbps = (float64(totalBytes) / (1024 * 1024)) / readTime.Seconds()
	}

	var avgChunkSize float64
	if chunkCount > 0 {
		avgChunkSize = float64(totalBytes) / float64(chunkCount)
	}

	return &ReadResult{
		ReadTime:       readTimeMs,
		BytesRead:      totalBytes,
		ThroughputMbps: throughputMbps,
		ChunkCount:     &chunkCount,
		AvgChunkSize:   &avgChunkSize,
	}, nil
}

func getMemoryUsage() float64 {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return float64(m.Alloc) / (1024 * 1024) // Convert to MB
}

func performReadTest(filePath string, bufferSize int, pattern string) (*ReadResult, error) {
	switch pattern {
	case "sequential":
		return readFileSequential(filePath, bufferSize)
	case "chunked":
		return readFileChunked(filePath, bufferSize)
	default:
		return nil, fmt.Errorf("unknown read pattern: %s", pattern)
	}
}

func getIntSlice(data interface{}, defaultVal []int64) []int64 {
	if arr, ok := data.([]interface{}); ok {
		result := make([]int64, 0, len(arr))
		for _, v := range arr {
			if num, ok := v.(float64); ok {
				result = append(result, int64(num))
			}
		}
		if len(result) > 0 {
			return result
		}
	}
	return defaultVal
}

func getStringSlice(data interface{}, defaultVal []string) []string {
	if arr, ok := data.([]interface{}); ok {
		result := make([]string, 0, len(arr))
		for _, v := range arr {
			if str, ok := v.(string); ok {
				result = append(result, str)
			}
		}
		if len(result) > 0 {
			return result
		}
	}
	return defaultVal
}

func runLargeFileReadBenchmark(parameters map[string]interface{}) (*BenchmarkResult, error) {
	// Parse configuration with defaults
	fileSizes := getIntSlice(parameters["file_sizes"], []int64{1048576}) // Default 1MB

	bufferSizesInt64 := getIntSlice(parameters["buffer_sizes"], []int64{4096})
	bufferSizes := make([]int, len(bufferSizesInt64))
	for i, v := range bufferSizesInt64 {
		bufferSizes[i] = int(v)
	}

	readPatterns := getStringSlice(parameters["read_patterns"], []string{"sequential"})

	iterations := 3
	if val, ok := parameters["iterations"].(float64); ok {
		iterations = int(val)
	}

	generateTestFiles := true
	if val, ok := parameters["generate_test_files"].(bool); ok {
		generateTestFiles = val
	}

	startTime := time.Now()
	var testCases []TestCase
	var totalTests, successfulTests, failedTests int
	var allReadTimes, allThroughputs []float64
	var peakMemory float64

	// Create temporary directory for test files
	tempDir := filepath.Join(os.TempDir(), fmt.Sprintf("large_file_read_test_%d", time.Now().Unix()))
	err := os.MkdirAll(tempDir, 0755)
	if err != nil {
		return nil, fmt.Errorf("failed to create temp directory: %v", err)
	}
	defer os.RemoveAll(tempDir)

	for _, fileSize := range fileSizes {
		for _, bufferSize := range bufferSizes {
			for _, pattern := range readPatterns {
				fmt.Fprintf(os.Stderr, "Testing file size: %d bytes, buffer: %d, pattern: %s...\n", fileSize, bufferSize, pattern)

				testCase := TestCase{
					FileSize:    fileSize,
					BufferSize:  bufferSize,
					ReadPattern: pattern,
					Iterations:  []IterationResult{},
				}

				// Generate test file if needed
				testFilePath := filepath.Join(tempDir, fmt.Sprintf("test_file_%d_%d.txt", fileSize, bufferSize))
				if generateTestFiles {
					if _, err := os.Stat(testFilePath); os.IsNotExist(err) {
						if err := generateTestFile(testFilePath, fileSize); err != nil {
							return nil, fmt.Errorf("failed to generate test file: %v", err)
						}
					}
				}

				var readTimes, throughputs []float64

				for i := 0; i < iterations; i++ {
					fmt.Fprintf(os.Stderr, "  Iteration %d/%d...\n", i+1, iterations)
					totalTests++

					memoryBefore := getMemoryUsage()

					readResult, err := performReadTest(testFilePath, bufferSize, pattern)
					if err != nil {
						fmt.Fprintf(os.Stderr, "Error in iteration %d: %v\n", i+1, err)
						failedTests++
						errMsg := err.Error()
						iteration := IterationResult{
							Iteration:      i + 1,
							ReadTime:       0.0,
							ThroughputMbps: 0.0,
							Error:          &errMsg,
						}
						testCase.Iterations = append(testCase.Iterations, iteration)
						continue
					}

					memoryAfter := getMemoryUsage()
					memoryUsed := memoryAfter - memoryBefore
					peakMemory = max(peakMemory, memoryAfter)

					iteration := IterationResult{
						Iteration:      i + 1,
						ReadTime:       readResult.ReadTime,
						BytesRead:      readResult.BytesRead,
						ThroughputMbps: readResult.ThroughputMbps,
						MemoryUsed:     memoryUsed,
						IOWaitTime:     readResult.ReadTime, // Approximation
						ChunkCount:     readResult.ChunkCount,
						AvgChunkSize:   readResult.AvgChunkSize,
					}

					testCase.Iterations = append(testCase.Iterations, iteration)
					readTimes = append(readTimes, readResult.ReadTime)
					throughputs = append(throughputs, readResult.ThroughputMbps)
					successfulTests++
				}

				// Calculate averages for this test case
				if len(readTimes) > 0 {
					testCase.AvgReadTime = average(readTimes)
					testCase.AvgThroughput = average(throughputs)
					testCase.MemoryEfficiency = (float64(fileSize) / (1024 * 1024)) / max(1.0, peakMemory)

					allReadTimes = append(allReadTimes, readTimes...)
					allThroughputs = append(allThroughputs, throughputs...)
				}

				testCases = append(testCases, testCase)
			}
		}
	}

	endTime := time.Now()
	totalDuration := endTime.Sub(startTime).Seconds()

	// Calculate overall summary
	var avgReadTime, avgThroughput float64
	if len(allReadTimes) > 0 {
		avgReadTime = average(allReadTimes)
		avgThroughput = average(allThroughputs)
	}

	return &BenchmarkResult{
		StartTime:     float64(startTime.Unix()),
		EndTime:       float64(endTime.Unix()),
		TotalDuration: totalDuration,
		TestCases:     testCases,
		Summary: Summary{
			TotalTests:      totalTests,
			SuccessfulTests: successfulTests,
			FailedTests:     failedTests,
			AvgReadTime:     avgReadTime,
			AvgThroughput:   avgThroughput,
			PeakMemoryUsage: peakMemory,
		},
	}, nil
}

func average(values []float64) float64 {
	if len(values) == 0 {
		return 0.0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <input_file>\n", os.Args[0])
		os.Exit(1)
	}

	inputFile := os.Args[1]

	// Read and parse input configuration
	configData, err := os.ReadFile(inputFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading config file: %v\n", err)
		os.Exit(1)
	}

	var config Config
	if err := json.Unmarshal(configData, &config); err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing config JSON: %v\n", err)
		os.Exit(1)
	}

	// Initialize random seed
	rand.Seed(time.Now().UnixNano())

	result, err := runLargeFileReadBenchmark(config.Parameters)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error running benchmark: %v\n", err)
		os.Exit(1)
	}

	// Output results as JSON
	jsonOutput, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling results: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(jsonOutput))
}
