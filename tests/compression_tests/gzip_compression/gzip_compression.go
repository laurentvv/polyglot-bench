package main

import (
	"bytes"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"strings"
	"time"
)

type CompressionResult struct {
	Success          bool     `json:"success"`
	OriginalSize     *int     `json:"original_size,omitempty"`
	CompressedSize   *int     `json:"compressed_size,omitempty"`
	CompressionRatio *float64 `json:"compression_ratio,omitempty"`
	CompressionTime  float64  `json:"compression_time"`
	ThroughputMbS    *float64 `json:"throughput_mb_s,omitempty"`
	Error            *string  `json:"error,omitempty"`
}

type IterationResult struct {
	Iteration   int               `json:"iteration"`
	Compression CompressionResult `json:"compression"`
}

type TestCase struct {
	InputSize                  int               `json:"input_size"`
	DataType                   string            `json:"data_type"`
	CompressionLevel           int               `json:"compression_level"`
	Iterations                 []IterationResult `json:"iterations"`
	AvgCompressionRatio        float64           `json:"avg_compression_ratio"`
	AvgCompressionTime         float64           `json:"avg_compression_time"`
	AvgDecompressionTime       float64           `json:"avg_decompression_time"`
	AvgCompressionThroughput   float64           `json:"avg_compression_throughput"`
	AvgDecompressionThroughput float64           `json:"avg_decompression_throughput"`
}

type Summary struct {
	TotalTests                 int     `json:"total_tests"`
	SuccessfulTests            int     `json:"successful_tests"`
	FailedTests                int     `json:"failed_tests"`
	AvgCompressionRatio        float64 `json:"avg_compression_ratio"`
	AvgCompressionTime         float64 `json:"avg_compression_time"`
	AvgDecompressionTime       float64 `json:"avg_decompression_time"`
	AvgCompressionThroughput   float64 `json:"avg_compression_throughput"`
	AvgDecompressionThroughput float64 `json:"avg_decompression_throughput"`
}

type BenchmarkResults struct {
	StartTime          float64    `json:"start_time"`
	TestCases          []TestCase `json:"test_cases"`
	Summary            Summary    `json:"summary"`
	EndTime            *float64   `json:"end_time,omitempty"`
	TotalExecutionTime *float64   `json:"total_execution_time,omitempty"`
}

type Config struct {
	Parameters Parameters `json:"parameters"`
}

type Parameters struct {
	InputSizes        []int    `json:"input_sizes"`
	DataTypes         []string `json:"data_types"`
	CompressionLevels []int    `json:"compression_levels"`
	Iterations        int      `json:"iterations"`
}

func generateTestData(size int, dataType string) ([]byte, error) {
	rand.Seed(time.Now().UnixNano())

	switch dataType {
	case "text":
		chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n"
		result := make([]byte, size)
		for i := 0; i < size; i++ {
			result[i] = chars[rand.Intn(len(chars))]
		}
		return result, nil

	case "binary":
		result := make([]byte, size)
		for i := 0; i < size; i++ {
			result[i] = byte(rand.Intn(256))
		}
		return result, nil

	case "json":
		var data []map[string]interface{}
		currentSize := 0

		for currentSize < size {
			record := map[string]interface{}{
				"id":     len(data),
				"name":   generateRandomString(10),
				"value":  rand.Intn(1000) + 1,
				"active": rand.Intn(2) == 1,
				"data":   generateRandomString(50),
			}
			data = append(data, record)

			jsonBytes, _ := json.Marshal(data)
			currentSize = len(jsonBytes)
		}

		jsonBytes, err := json.Marshal(data)
		if err != nil {
			return nil, err
		}

		if len(jsonBytes) > size {
			return jsonBytes[:size], nil
		}
		return jsonBytes, nil

	default:
		return nil, fmt.Errorf("unknown data type: %s", dataType)
	}
}

func generateRandomString(length int) string {
	chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
	var result strings.Builder
	for i := 0; i < length; i++ {
		result.WriteByte(chars[rand.Intn(len(chars))])
	}
	return result.String()
}

func compressData(data []byte, compressionLevel int) CompressionResult {
	start := time.Now()
	originalSize := len(data)

	var buf bytes.Buffer
	var writer *gzip.Writer

	switch compressionLevel {
	case 1:
		writer, _ = gzip.NewWriterLevel(&buf, gzip.BestSpeed)
	case 2, 3, 4, 5:
		writer, _ = gzip.NewWriterLevel(&buf, compressionLevel)
	case 6:
		writer = gzip.NewWriter(&buf)
	case 7, 8, 9:
		writer, _ = gzip.NewWriterLevel(&buf, compressionLevel)
	default:
		writer = gzip.NewWriter(&buf)
	}

	_, err := writer.Write(data)
	if err != nil {
		compressionTime := float64(time.Since(start).Nanoseconds()) / 1e6
		compressionTime = float64(int(compressionTime*100)) / 100
		errStr := err.Error()
		return CompressionResult{
			Success:         false,
			OriginalSize:    &originalSize,
			CompressionTime: compressionTime,
			Error:           &errStr,
		}
	}

	err = writer.Close()
	if err != nil {
		compressionTime := float64(time.Since(start).Nanoseconds()) / 1e6
		compressionTime = float64(int(compressionTime*100)) / 100
		errStr := err.Error()
		return CompressionResult{
			Success:         false,
			OriginalSize:    &originalSize,
			CompressionTime: compressionTime,
			Error:           &errStr,
		}
	}

	compressed := buf.Bytes()
	compressedSize := len(compressed)
	compressionTime := float64(time.Since(start).Nanoseconds()) / 1e6
	compressionTime = float64(int(compressionTime*100)) / 100

	var compressionRatio float64
	if compressedSize > 0 {
		compressionRatio = float64(originalSize) / float64(compressedSize)
		compressionRatio = float64(int(compressionRatio*1000)) / 1000
	}

	throughput := float64(originalSize) / (compressionTime / 1000.0) / (1024.0 * 1024.0)
	throughput = float64(int(throughput*100)) / 100

	return CompressionResult{
		Success:          true,
		OriginalSize:     &originalSize,
		CompressedSize:   &compressedSize,
		CompressionRatio: &compressionRatio,
		CompressionTime:  compressionTime,
		ThroughputMbS:    &throughput,
	}
}

func runCompressionBenchmark(config Parameters) BenchmarkResults {
	inputSizes := config.InputSizes
	if inputSizes == nil {
		inputSizes = []int{1024}
	}

	dataTypes := config.DataTypes
	if dataTypes == nil {
		dataTypes = []string{"text"}
	}

	compressionLevels := config.CompressionLevels
	if compressionLevels == nil {
		compressionLevels = []int{6}
	}

	iterations := config.Iterations
	if iterations == 0 {
		iterations = 5
	}

	results := BenchmarkResults{
		StartTime: float64(time.Now().Unix()),
		TestCases: []TestCase{},
		Summary: Summary{
			TotalTests:                 0,
			SuccessfulTests:            0,
			FailedTests:                0,
			AvgCompressionRatio:        0.0,
			AvgCompressionTime:         0.0,
			AvgDecompressionTime:       0.0,
			AvgCompressionThroughput:   0.0,
			AvgDecompressionThroughput: 0.0,
		},
	}

	var totalCompressionRatios []float64
	var totalCompressionTimes []float64
	var totalCompressionThroughputs []float64

	for _, size := range inputSizes {
		for _, dataType := range dataTypes {
			for _, level := range compressionLevels {
				fmt.Fprintf(os.Stderr, "Testing %s data, size: %d bytes, level: %d...\n", dataType, size, level)

				testCase := TestCase{
					InputSize:                  size,
					DataType:                   dataType,
					CompressionLevel:           level,
					Iterations:                 []IterationResult{},
					AvgCompressionRatio:        0.0,
					AvgCompressionTime:         0.0,
					AvgDecompressionTime:       0.0,
					AvgCompressionThroughput:   0.0,
					AvgDecompressionThroughput: 0.0,
				}

				var iterationCompressionRatios []float64
				var iterationCompressionTimes []float64
				var iterationCompressionThroughputs []float64

				for i := 0; i < iterations; i++ {
					fmt.Fprintf(os.Stderr, "  Iteration %d/%d...\n", i+1, iterations)

					testData, err := generateTestData(size, dataType)
					if err != nil {
						fmt.Fprintf(os.Stderr, "Error generating test data: %v\n", err)
						continue
					}

					compressionResult := compressData(testData, level)

					iterationResult := IterationResult{
						Iteration:   i + 1,
						Compression: compressionResult,
					}

					results.Summary.TotalTests++

					if compressionResult.Success {
						results.Summary.SuccessfulTests++

						if compressionResult.CompressionRatio != nil {
							iterationCompressionRatios = append(iterationCompressionRatios, *compressionResult.CompressionRatio)
						}
						iterationCompressionTimes = append(iterationCompressionTimes, compressionResult.CompressionTime)
						if compressionResult.ThroughputMbS != nil {
							iterationCompressionThroughputs = append(iterationCompressionThroughputs, *compressionResult.ThroughputMbS)
						}
					} else {
						results.Summary.FailedTests++
					}

					testCase.Iterations = append(testCase.Iterations, iterationResult)
				}

				// Calculate averages for this test case
				if len(iterationCompressionRatios) > 0 {
					testCase.AvgCompressionRatio = average(iterationCompressionRatios)
					testCase.AvgCompressionTime = average(iterationCompressionTimes)
					testCase.AvgCompressionThroughput = average(iterationCompressionThroughputs)

					totalCompressionRatios = append(totalCompressionRatios, iterationCompressionRatios...)
					totalCompressionTimes = append(totalCompressionTimes, iterationCompressionTimes...)
					totalCompressionThroughputs = append(totalCompressionThroughputs, iterationCompressionThroughputs...)
				}

				results.TestCases = append(results.TestCases, testCase)
			}
		}
	}

	// Calculate overall summary
	if len(totalCompressionRatios) > 0 {
		results.Summary.AvgCompressionRatio = average(totalCompressionRatios)
		results.Summary.AvgCompressionTime = average(totalCompressionTimes)
		results.Summary.AvgCompressionThroughput = average(totalCompressionThroughputs)
	}

	endTime := float64(time.Now().Unix())
	results.EndTime = &endTime
	totalExecutionTime := endTime - results.StartTime
	results.TotalExecutionTime = &totalExecutionTime

	return results
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

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <config_file>\n", os.Args[0])
		os.Exit(1)
	}

	configFile := os.Args[1]

	configContent, err := os.ReadFile(configFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Cannot read config file '%s': %v\n", configFile, err)
		os.Exit(1)
	}

	var config Config
	err = json.Unmarshal(configContent, &config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Invalid JSON in config file: %v\n", err)
		os.Exit(1)
	}

	results := runCompressionBenchmark(config.Parameters)

	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Failed to serialize results: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(output))
}
