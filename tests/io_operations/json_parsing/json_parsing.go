package main

import (
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"time"
)

type TestResult struct {
	StartTime          int64      `json:"start_time"`
	TestCases          []TestCase `json:"test_cases"`
	Summary            Summary    `json:"summary"`
	EndTime            int64      `json:"end_time"`
	TotalExecutionTime float64    `json:"total_execution_time"`
}

type TestCase struct {
	JsonSize         int               `json:"json_size"`
	StructureType    string            `json:"structure_type"`
	Operations       []string          `json:"operations"`
	Iterations       []IterationResult `json:"iterations"`
	AvgParseTime     float64           `json:"avg_parse_time"`
	AvgStringifyTime float64           `json:"avg_stringify_time"`
	AvgTraverseTime  float64           `json:"avg_traverse_time"`
}

type IterationResult struct {
	Iteration  int                        `json:"iteration"`
	DataSize   int                        `json:"data_size"`
	Operations map[string]OperationResult `json:"operations"`
}

type OperationResult struct {
	Success          bool     `json:"success"`
	TimeMs           *float64 `json:"time_ms,omitempty"`
	JsonStringLength *int     `json:"json_string_length,omitempty"`
	OutputLength     *int     `json:"output_length,omitempty"`
	OperationsCount  *int     `json:"operations_count,omitempty"`
	Error            *string  `json:"error,omitempty"`
}

type Summary struct {
	TotalTests       int     `json:"total_tests"`
	SuccessfulTests  int     `json:"successful_tests"`
	FailedTests      int     `json:"failed_tests"`
	AvgParseTime     float64 `json:"avg_parse_time"`
	AvgStringifyTime float64 `json:"avg_stringify_time"`
	AvgTraverseTime  float64 `json:"avg_traverse_time"`
}

type Config struct {
	Parameters struct {
		JsonSizes      []int    `json:"json_sizes"`
		JsonStructures []string `json:"json_structures"`
		Operations     []string `json:"operations"`
		Iterations     int      `json:"iterations"`
	} `json:"parameters"`
}

func generateFlatJson(size int) interface{} {
	data := make(map[string]interface{})

	for i := 0; i < size; i++ {
		key := fmt.Sprintf("key_%d", i)
		valueType := rand.Intn(3)

		switch valueType {
		case 0:
			data[key] = fmt.Sprintf("value_%d", rand.Intn(1000))
		case 1:
			data[key] = rand.Intn(1000) + 1
		default:
			data[key] = rand.Float32() < 0.5
		}
	}

	return data
}

func generateNestedJson(size int, maxDepth int) interface{} {
	var createNestedObject func(int, int) interface{}

	createNestedObject = func(remainingSize, currentDepth int) interface{} {
		if remainingSize <= 0 || currentDepth >= maxDepth {
			choice := rand.Intn(3)
			switch choice {
			case 0:
				return fmt.Sprintf("leaf_%d", rand.Intn(100))
			case 1:
				return rand.Intn(100) + 1
			default:
				return rand.Float32() < 0.5
			}
		}

		if rand.Float32() < 0.6 {
			// Create object
			obj := make(map[string]interface{})
			keysCount := min(rand.Intn(4)+2, remainingSize)
			remainingPerKey := remainingSize / keysCount

			for i := 0; i < keysCount; i++ {
				key := fmt.Sprintf("nested_key_%d", i)
				obj[key] = createNestedObject(remainingPerKey, currentDepth+1)
			}
			return obj
		} else {
			// Create array
			itemsCount := min(rand.Intn(3)+2, remainingSize)
			remainingPerItem := remainingSize / itemsCount

			arr := make([]interface{}, itemsCount)
			for i := 0; i < itemsCount; i++ {
				arr[i] = createNestedObject(remainingPerItem, currentDepth+1)
			}
			return arr
		}
	}

	return map[string]interface{}{
		"root": createNestedObject(size, 0),
	}
}

func generateArrayHeavyJson(size int) interface{} {
	itemsPerArray := size / 3
	categories := []string{"electronics", "clothing", "books", "home"}

	users := make([]interface{}, itemsPerArray)
	for i := 0; i < itemsPerArray; i++ {
		users[i] = map[string]interface{}{
			"id":     i,
			"name":   fmt.Sprintf("User_%d", i),
			"email":  fmt.Sprintf("user%d@example.com", i),
			"active": rand.Float32() < 0.5,
		}
	}

	products := make([]interface{}, itemsPerArray)
	for i := 0; i < itemsPerArray; i++ {
		price := float64(rand.Intn(4900)+100) / 100.0
		products[i] = map[string]interface{}{
			"id":       i,
			"name":     fmt.Sprintf("Product_%d", i),
			"price":    price,
			"category": categories[rand.Intn(len(categories))],
		}
	}

	orders := make([]interface{}, itemsPerArray)
	for i := 0; i < itemsPerArray; i++ {
		productCount := rand.Intn(5) + 1
		productIds := make([]int, productCount)
		for j := 0; j < productCount; j++ {
			productIds[j] = rand.Intn(itemsPerArray)
		}

		total := float64(rand.Intn(9800)+200) / 100.0
		orders[i] = map[string]interface{}{
			"id":          i,
			"user_id":     rand.Intn(itemsPerArray),
			"product_ids": productIds,
			"total":       total,
			"timestamp":   fmt.Sprintf("2024-%02d-%02d", rand.Intn(12)+1, rand.Intn(28)+1),
		}
	}

	return map[string]interface{}{
		"users":    users,
		"products": products,
		"orders":   orders,
	}
}

func generateMixedJson(size int) interface{} {
	types := []string{"A", "B", "C"}
	tags := []string{"urgent", "normal", "low", "critical"}

	data := make([]interface{}, size)

	for i := 0; i < size; i++ {
		recordType := types[rand.Intn(len(types))]

		// Select random tags
		tagCount := rand.Intn(2) + 1
		selectedTags := make([]string, tagCount)
		for j := 0; j < tagCount; j++ {
			selectedTags[j] = tags[rand.Intn(len(tags))]
		}

		// Create relationships
		relationshipCount := rand.Intn(4)
		relationships := make([]interface{}, relationshipCount)
		for j := 0; j < relationshipCount; j++ {
			relationships[j] = map[string]interface{}{
				"id":   rand.Intn(size),
				"type": "related",
			}
		}

		data[i] = map[string]interface{}{
			"id":   i,
			"type": recordType,
			"attributes": map[string]interface{}{
				"name":  fmt.Sprintf("Item_%d", i),
				"value": rand.Intn(1000) + 1,
				"tags":  selectedTags,
			},
			"relationships": relationships,
		}
	}

	return map[string]interface{}{
		"metadata": map[string]interface{}{
			"version":       "1.0",
			"timestamp":     "2024-01-01T00:00:00Z",
			"total_records": size,
		},
		"config": map[string]interface{}{
			"settings": map[string]interface{}{
				"debug":         true,
				"cache_enabled": false,
				"timeout":       30,
			},
		},
		"data": data,
	}
}

func traverseJson(data interface{}) int {
	count := 0

	switch v := data.(type) {
	case map[string]interface{}:
		for _, value := range v {
			count++
			count += traverseJson(value)
		}
	case []interface{}:
		for _, item := range v {
			count++
			count += traverseJson(item)
		}
	default:
		count++
	}

	return count
}

func runJsonParsingBenchmark(config Config) TestResult {
	params := config.Parameters

	// Set defaults
	if len(params.JsonSizes) == 0 {
		params.JsonSizes = []int{1000}
	}
	if len(params.JsonStructures) == 0 {
		params.JsonStructures = []string{"flat"}
	}
	if len(params.Operations) == 0 {
		params.Operations = []string{"parse"}
	}
	if params.Iterations == 0 {
		params.Iterations = 5
	}

	startTime := time.Now()
	var testCases []TestCase
	var allParseTimes []float64
	var allStringifyTimes []float64
	var allTraverseTimes []float64
	totalTests := 0
	successfulTests := 0
	failedTests := 0

	generators := map[string]func(int) interface{}{
		"flat":        generateFlatJson,
		"nested":      func(size int) interface{} { return generateNestedJson(size, 5) },
		"array_heavy": generateArrayHeavyJson,
		"mixed":       generateMixedJson,
	}

	for _, size := range params.JsonSizes {
		for _, structure := range params.JsonStructures {
			generator, exists := generators[structure]
			if !exists {
				fmt.Fprintf(os.Stderr, "Warning: Structure %s not implemented, skipping\n", structure)
				continue
			}

			fmt.Fprintf(os.Stderr, "Testing %s JSON, size: %d...\n", structure, size)

			var parseTimes []float64
			var stringifyTimes []float64
			var traverseTimes []float64
			var iterationsData []IterationResult

			for i := 0; i < params.Iterations; i++ {
				fmt.Fprintf(os.Stderr, "  Iteration %d/%d...\n", i+1, params.Iterations)

				// Generate test data
				jsonData := generator(size)

				jsonBytes, _ := json.Marshal(jsonData)
				dataSize := len(jsonBytes)

				iterationResult := IterationResult{
					Iteration:  i + 1,
					DataSize:   dataSize,
					Operations: make(map[string]OperationResult),
				}

				totalTests++
				success := true

				// Parse operation
				if contains(params.Operations, "parse") {
					jsonString, err := json.Marshal(jsonData)
					if err != nil {
						success = false
						iterationResult.Operations["parse"] = OperationResult{
							Success: false,
							Error:   stringPtr(fmt.Sprintf("Marshal failed: %v", err)),
						}
					} else {
						start := time.Now()
						var parsedData interface{}
						err := json.Unmarshal(jsonString, &parsedData)
						parseTime := float64(time.Since(start).Nanoseconds()) / 1e6

						if err != nil {
							success = false
							iterationResult.Operations["parse"] = OperationResult{
								Success: false,
								Error:   stringPtr(fmt.Sprintf("Parse failed: %v", err)),
							}
						} else {
							parseTimes = append(parseTimes, parseTime)
							allParseTimes = append(allParseTimes, parseTime)

							iterationResult.Operations["parse"] = OperationResult{
								Success:          true,
								TimeMs:           &parseTime,
								JsonStringLength: intPtr(len(jsonString)),
							}
						}
					}
				}

				// Stringify operation
				if contains(params.Operations, "stringify") {
					start := time.Now()
					jsonString, err := json.Marshal(jsonData)
					stringifyTime := float64(time.Since(start).Nanoseconds()) / 1e6

					if err != nil {
						success = false
						iterationResult.Operations["stringify"] = OperationResult{
							Success: false,
							Error:   stringPtr(fmt.Sprintf("Stringify failed: %v", err)),
						}
					} else {
						stringifyTimes = append(stringifyTimes, stringifyTime)
						allStringifyTimes = append(allStringifyTimes, stringifyTime)

						iterationResult.Operations["stringify"] = OperationResult{
							Success:      true,
							TimeMs:       &stringifyTime,
							OutputLength: intPtr(len(jsonString)),
						}
					}
				}

				// Traverse operation
				if contains(params.Operations, "traverse") {
					start := time.Now()
					operationCount := traverseJson(jsonData)
					traverseTime := float64(time.Since(start).Nanoseconds()) / 1e6

					traverseTimes = append(traverseTimes, traverseTime)
					allTraverseTimes = append(allTraverseTimes, traverseTime)

					iterationResult.Operations["traverse"] = OperationResult{
						Success:         true,
						TimeMs:          &traverseTime,
						OperationsCount: &operationCount,
					}
				}

				if success {
					successfulTests++
				} else {
					failedTests++
				}

				iterationsData = append(iterationsData, iterationResult)
			}

			// Calculate averages for this test case
			testCase := TestCase{
				JsonSize:      size,
				StructureType: structure,
				Operations:    params.Operations,
				Iterations:    iterationsData,
			}

			if len(parseTimes) > 0 {
				testCase.AvgParseTime = average(parseTimes)
			}
			if len(stringifyTimes) > 0 {
				testCase.AvgStringifyTime = average(stringifyTimes)
			}
			if len(traverseTimes) > 0 {
				testCase.AvgTraverseTime = average(traverseTimes)
			}

			testCases = append(testCases, testCase)
		}
	}

	// Calculate overall summary
	summary := Summary{
		TotalTests:      totalTests,
		SuccessfulTests: successfulTests,
		FailedTests:     failedTests,
	}

	if len(allParseTimes) > 0 {
		summary.AvgParseTime = average(allParseTimes)
	}
	if len(allStringifyTimes) > 0 {
		summary.AvgStringifyTime = average(allStringifyTimes)
	}
	if len(allTraverseTimes) > 0 {
		summary.AvgTraverseTime = average(allTraverseTimes)
	}

	endTime := time.Now()
	executionTime := endTime.Sub(startTime).Seconds()

	return TestResult{
		StartTime:          startTime.Unix(),
		TestCases:          testCases,
		Summary:            summary,
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
		fmt.Fprintf(os.Stderr, "Error: Config file '%s' not found: %v\n", configFile, err)
		os.Exit(1)
	}

	var config Config
	if err := json.Unmarshal(configData, &config); err != nil {
		fmt.Fprintf(os.Stderr, "Error: Invalid JSON in config file: %v\n", err)
		os.Exit(1)
	}

	results := runJsonParsingBenchmark(config)

	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Failed to marshal results: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(output))
}

// Helper functions
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func average(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

func stringPtr(s string) *string {
	return &s
}

func intPtr(i int) *int {
	return &i
}
