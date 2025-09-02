package main

import (
	"bytes"
	"compress/gzip"
	"compress/zlib"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"os"
	"strings"
	"time"
)

type CompressionResult struct {
	Success         bool    `json:"success"`
	CompressedSize  *int    `json:"compressed_size,omitempty"`
	CompressionTime float64 `json:"compression_time"`
	Error           *string `json:"error,omitempty"`
}

type DecompressionResult struct {
	Success           bool    `json:"success"`
	DecompressedSize  *int    `json:"decompressed_size,omitempty"`
	DecompressionTime float64 `json:"decompression_time"`
	Error             *string `json:"error,omitempty"`
}

type IterationResult struct {
	Iteration     int                  `json:"iteration"`
	OriginalSize  int                  `json:"original_size"`
	Compression   CompressionResult    `json:"compression"`
	Decompression *DecompressionResult `json:"decompression,omitempty"`
}

type TestCase struct {
	InputSize            int               `json:"input_size"`
	TextType             string            `json:"text_type"`
	Algorithm            string            `json:"algorithm"`
	Iterations           []IterationResult `json:"iterations"`
	AvgCompressionRatio  float64           `json:"avg_compression_ratio"`
	AvgCompressionTime   float64           `json:"avg_compression_time"`
	AvgDecompressionTime float64           `json:"avg_decompression_time"`
}

type AlgorithmPerformance struct {
	AvgCompressionRatio float64 `json:"avg_compression_ratio"`
	MaxCompressionRatio float64 `json:"max_compression_ratio"`
	MinCompressionRatio float64 `json:"min_compression_ratio"`
}

type Summary struct {
	TotalTests             int                             `json:"total_tests"`
	SuccessfulCompressions int                             `json:"successful_compressions"`
	FailedCompressions     int                             `json:"failed_compressions"`
	BestCompressionRatios  map[string]float64              `json:"best_compression_ratios"`
	AlgorithmPerformance   map[string]AlgorithmPerformance `json:"algorithm_performance"`
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
	InputSizes            []int    `json:"input_sizes"`
	TextTypes             []string `json:"text_types"`
	CompressionAlgorithms []string `json:"compression_algorithms"`
	Iterations            int      `json:"iterations"`
}

func generateTextData(size int, textType string) (string, error) {
	rand.Seed(time.Now().UnixNano())

	switch textType {
	case "ascii":
		chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n"
		result := make([]byte, size)
		for i := 0; i < size; i++ {
			result[i] = chars[rand.Intn(len(chars))]
		}
		return string(result), nil

	case "unicode":
		chars := "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789àáâãäåæçèéêëìíîïñòóôõöøùúûüý你好世界🌟🚀📊 \n"
		runes := []rune(chars)
		result := make([]rune, 0, size)
		for len(string(result)) < size {
			result = append(result, runes[rand.Intn(len(runes))])
		}
		resultStr := string(result)
		if len(resultStr) > size {
			// Truncate to exact size, being careful with UTF-8
			return resultStr[:size], nil
		}
		return resultStr, nil

	case "code":
		keywords := []string{"package", "func", "var", "if", "else", "for", "range", "return", "struct", "interface"}
		operators := []string{"=", "+", "-", "*", "/", "(", ")", "{", "}", "[", "]", ";", ":"}
		var text strings.Builder

		for text.Len() < size {
			if rand.Float64() < 0.3 {
				text.WriteString(keywords[rand.Intn(len(keywords))])
			} else {
				wordLen := rand.Intn(8) + 3
				for i := 0; i < wordLen; i++ {
					text.WriteByte(byte('a' + rand.Intn(26)))
				}
			}

			if rand.Float64() < 0.2 {
				text.WriteString(operators[rand.Intn(len(operators))])
			}

			if rand.Float64() < 0.1 {
				text.WriteString("\n")
			} else {
				text.WriteString(" ")
			}
		}

		result := text.String()
		if len(result) > size {
			return result[:size], nil
		}
		return result, nil

	case "natural_language":
		words := []string{"the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "and", "runs", "through",
			"forest", "meadow", "river", "mountain", "valley", "beautiful", "magnificent", "wonderful"}
		var text strings.Builder

		for text.Len() < size {
			text.WriteString(words[rand.Intn(len(words))])

			if rand.Float64() < 0.1 {
				text.WriteString(". ")
			} else if rand.Float64() < 0.05 {
				text.WriteString(", ")
			} else {
				text.WriteString(" ")
			}

			if rand.Float64() < 0.05 {
				text.WriteString("\n")
			}
		}

		result := text.String()
		if len(result) > size {
			return result[:size], nil
		}
		return result, nil

	default:
		return "", fmt.Errorf("unknown text type: %s", textType)
	}
}

func compressWithGzip(data []byte) CompressionResult {
	start := time.Now()

	var buf bytes.Buffer
	writer := gzip.NewWriter(&buf)

	_, err := writer.Write(data)
	if err != nil {
		errStr := err.Error()
		return CompressionResult{
			Success:         false,
			CompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
			Error:           &errStr,
		}
	}

	err = writer.Close()
	if err != nil {
		errStr := err.Error()
		return CompressionResult{
			Success:         false,
			CompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
			Error:           &errStr,
		}
	}

	compressed := buf.Bytes()
	compressedSize := len(compressed)

	return CompressionResult{
		Success:         true,
		CompressedSize:  &compressedSize,
		CompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
	}
}

func compressWithZlib(data []byte) CompressionResult {
	start := time.Now()

	var buf bytes.Buffer
	writer := zlib.NewWriter(&buf)

	_, err := writer.Write(data)
	if err != nil {
		errStr := err.Error()
		return CompressionResult{
			Success:         false,
			CompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
			Error:           &errStr,
		}
	}

	err = writer.Close()
	if err != nil {
		errStr := err.Error()
		return CompressionResult{
			Success:         false,
			CompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
			Error:           &errStr,
		}
	}

	compressed := buf.Bytes()
	compressedSize := len(compressed)

	return CompressionResult{
		Success:         true,
		CompressedSize:  &compressedSize,
		CompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
	}
}

func decompressGzip(data []byte) DecompressionResult {
	start := time.Now()

	reader, err := gzip.NewReader(bytes.NewReader(data))
	if err != nil {
		errStr := err.Error()
		return DecompressionResult{
			Success:           false,
			DecompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
			Error:             &errStr,
		}
	}
	defer reader.Close()

	decompressed, err := io.ReadAll(reader)
	if err != nil {
		errStr := err.Error()
		return DecompressionResult{
			Success:           false,
			DecompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
			Error:             &errStr,
		}
	}

	decompressedSize := len(decompressed)

	return DecompressionResult{
		Success:           true,
		DecompressedSize:  &decompressedSize,
		DecompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
	}
}

func decompressZlib(data []byte) DecompressionResult {
	start := time.Now()

	reader, err := zlib.NewReader(bytes.NewReader(data))
	if err != nil {
		errStr := err.Error()
		return DecompressionResult{
			Success:           false,
			DecompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
			Error:             &errStr,
		}
	}
	defer reader.Close()

	decompressed, err := io.ReadAll(reader)
	if err != nil {
		errStr := err.Error()
		return DecompressionResult{
			Success:           false,
			DecompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
			Error:             &errStr,
		}
	}

	decompressedSize := len(decompressed)

	return DecompressionResult{
		Success:           true,
		DecompressedSize:  &decompressedSize,
		DecompressionTime: float64(time.Since(start).Nanoseconds()) / 1e6,
	}
}

func runTextCompressionBenchmark(config Parameters) (BenchmarkResults, error) {
	inputSizes := config.InputSizes
	if len(inputSizes) == 0 {
		inputSizes = []int{1024}
	}

	textTypes := config.TextTypes
	if len(textTypes) == 0 {
		textTypes = []string{"ascii"}
	}

	algorithms := config.CompressionAlgorithms
	if len(algorithms) == 0 {
		algorithms = []string{"gzip"}
	}

	iterations := config.Iterations
	if iterations == 0 {
		iterations = 3
	}

	results := BenchmarkResults{
		StartTime: float64(time.Now().Unix()),
		TestCases: []TestCase{},
		Summary: Summary{
			BestCompressionRatios: make(map[string]float64),
			AlgorithmPerformance:  make(map[string]AlgorithmPerformance),
		},
	}

	algorithmStats := make(map[string][]float64)

	for _, size := range inputSizes {
		for _, textType := range textTypes {
			for _, algorithm := range algorithms {
				fmt.Fprintf(os.Stderr, "Testing %s text, size: %d, algorithm: %s...\n", textType, size, algorithm)

				testCase := TestCase{
					InputSize:  size,
					TextType:   textType,
					Algorithm:  algorithm,
					Iterations: []IterationResult{},
				}

				var compressionRatios []float64
				var compressionTimes []float64
				var decompressionTimes []float64

				for i := 0; i < iterations; i++ {
					fmt.Fprintf(os.Stderr, "  Iteration %d/%d...\n", i+1, iterations)

					textData, err := generateTextData(size, textType)
					if err != nil {
						return results, err
					}

					dataBytes := []byte(textData)
					originalSize := len(dataBytes)

					var compressResult CompressionResult

					switch algorithm {
					case "gzip":
						compressResult = compressWithGzip(dataBytes)
					case "zlib":
						compressResult = compressWithZlib(dataBytes)
					default:
						fmt.Fprintf(os.Stderr, "Warning: Algorithm %s not implemented, skipping\n", algorithm)
						continue
					}

					iterationResult := IterationResult{
						Iteration:    i + 1,
						OriginalSize: originalSize,
						Compression:  compressResult,
					}

					results.Summary.TotalTests++

					if compressResult.Success && compressResult.CompressedSize != nil {
						results.Summary.SuccessfulCompressions++

						compressedSize := *compressResult.CompressedSize
						var compressionRatio float64
						if compressedSize > 0 {
							compressionRatio = float64(originalSize) / float64(compressedSize)
						}

						compressionRatios = append(compressionRatios, compressionRatio)
						compressionTimes = append(compressionTimes, compressResult.CompressionTime)

						algorithmStats[algorithm] = append(algorithmStats[algorithm], compressionRatio)
					} else {
						results.Summary.FailedCompressions++
					}

					testCase.Iterations = append(testCase.Iterations, iterationResult)
				}

				if len(compressionRatios) > 0 {
					sum := 0.0
					for _, ratio := range compressionRatios {
						sum += ratio
					}
					testCase.AvgCompressionRatio = sum / float64(len(compressionRatios))

					sum = 0.0
					for _, time := range compressionTimes {
						sum += time
					}
					testCase.AvgCompressionTime = sum / float64(len(compressionTimes))

					if len(decompressionTimes) > 0 {
						sum = 0.0
						for _, time := range decompressionTimes {
							sum += time
						}
						testCase.AvgDecompressionTime = sum / float64(len(decompressionTimes))
					}
				}

				results.TestCases = append(results.TestCases, testCase)
			}
		}
	}

	// Calculate summary statistics
	for algorithm, ratios := range algorithmStats {
		if len(ratios) > 0 {
			sum := 0.0
			min := ratios[0]
			max := ratios[0]

			for _, ratio := range ratios {
				sum += ratio
				if ratio < min {
					min = ratio
				}
				if ratio > max {
					max = ratio
				}
			}

			results.Summary.AlgorithmPerformance[algorithm] = AlgorithmPerformance{
				AvgCompressionRatio: sum / float64(len(ratios)),
				MaxCompressionRatio: max,
				MinCompressionRatio: min,
			}
		}
	}

	endTime := float64(time.Now().Unix())
	results.EndTime = &endTime
	totalTime := endTime - results.StartTime
	results.TotalExecutionTime = &totalTime

	return results, nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <config_file>\n", os.Args[0])
		os.Exit(1)
	}

	configFile := os.Args[1]

	configData, err := os.ReadFile(configFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Config file '%s' not found\n", configFile)
		os.Exit(1)
	}

	var config Config
	err = json.Unmarshal(configData, &config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Invalid JSON in config file: %v\n", err)
		os.Exit(1)
	}

	results, err := runTextCompressionBenchmark(config.Parameters)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(output))
}
