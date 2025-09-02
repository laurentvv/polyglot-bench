package main

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	Parameters Parameters `json:"parameters"`
}

type Parameters struct {
	RowCounts    []int    `json:"row_counts"`
	ColumnCounts []int    `json:"column_counts"`
	Operations   []string `json:"operations"`
	DataTypes    []string `json:"data_types"`
	Iterations   int      `json:"iterations"`
}

type OperationResult struct {
	Success        bool    `json:"success"`
	TimeMs         float64 `json:"time_ms,omitempty"`
	Error          string  `json:"error,omitempty"`
	OutputSize     int     `json:"output_size,omitempty"`
	RowsRead       int     `json:"rows_read,omitempty"`
	OriginalRows   int     `json:"original_rows,omitempty"`
	FilteredRows   int     `json:"filtered_rows,omitempty"`
	AggregatedCols int     `json:"aggregated_columns,omitempty"`
}

type IterationResult struct {
	Iteration  int                        `json:"iteration"`
	DataSize   int                        `json:"data_size"`
	Operations map[string]OperationResult `json:"operations"`
}

type TestCase struct {
	RowCount         int               `json:"row_count"`
	ColumnCount      int               `json:"column_count"`
	DataType         string            `json:"data_type"`
	Operations       []string          `json:"operations"`
	Iterations       []IterationResult `json:"iterations"`
	AvgReadTime      float64           `json:"avg_read_time"`
	AvgWriteTime     float64           `json:"avg_write_time"`
	AvgFilterTime    float64           `json:"avg_filter_time"`
	AvgAggregateTime float64           `json:"avg_aggregate_time"`
}

type Summary struct {
	TotalTests       int     `json:"total_tests"`
	SuccessfulTests  int     `json:"successful_tests"`
	FailedTests      int     `json:"failed_tests"`
	AvgReadTime      float64 `json:"avg_read_time"`
	AvgWriteTime     float64 `json:"avg_write_time"`
	AvgFilterTime    float64 `json:"avg_filter_time"`
	AvgAggregateTime float64 `json:"avg_aggregate_time"`
}

type Results struct {
	StartTime          float64    `json:"start_time"`
	TestCases          []TestCase `json:"test_cases"`
	Summary            Summary    `json:"summary"`
	EndTime            float64    `json:"end_time"`
	TotalExecutionTime float64    `json:"total_execution_time"`
}

func generateCSVData(rows, cols int, dataType string) [][]string {
	rand.Seed(time.Now().UnixNano())
	data := make([][]string, 0, rows+1)

	// Generate headers
	headers := make([]string, cols)
	for i := 0; i < cols; i++ {
		headers[i] = fmt.Sprintf("col_%d", i+1)
	}
	data = append(data, headers)

	// Generate data rows
	for row := 0; row < rows; row++ {
		rowData := make([]string, cols)
		for col := 0; col < cols; col++ {
			var value string
			switch dataType {
			case "numeric":
				value = fmt.Sprintf("%.2f", rand.Float64()*1000)
			case "text":
				length := rand.Intn(11) + 5 // 5-15 characters
				runes := make([]rune, length)
				for i := range runes {
					runes[i] = rune('a' + rand.Intn(26))
				}
				value = string(runes)
			default: // mixed
				switch col % 3 {
				case 0:
					value = strconv.Itoa(rand.Intn(10000) + 1)
				case 1:
					runes := make([]rune, 10)
					for i := range runes {
						runes[i] = rune('a' + rand.Intn(26))
					}
					value = string(runes)
				default:
					value = fmt.Sprintf("%.2f", rand.Float64()*1000)
				}
			}
			rowData[col] = value
		}
		data = append(data, rowData)
	}

	return data
}

func writeCSVToString(data [][]string) string {
	var result strings.Builder
	for _, row := range data {
		result.WriteString(strings.Join(row, ","))
		result.WriteByte('\n')
	}
	return result.String()
}

func readCSVFromString(csvString string) [][]string {
	reader := csv.NewReader(strings.NewReader(csvString))
	records, err := reader.ReadAll()
	if err != nil {
		return nil
	}
	return records
}

func filterCSVData(data [][]string, filterColumn int) [][]string {
	if len(data) < 2 {
		return data
	}

	filtered := [][]string{data[0]} // Keep headers

	for _, row := range data[1:] {
		if len(row) > filterColumn {
			if value, err := strconv.ParseFloat(row[filterColumn], 64); err == nil {
				if value > 500 {
					filtered = append(filtered, row)
				}
			} else if len(row[filterColumn]) > 5 {
				filtered = append(filtered, row)
			}
		}
	}

	return filtered
}

func aggregateCSVData(data [][]string) map[string]map[string]float64 {
	if len(data) < 2 {
		return make(map[string]map[string]float64)
	}

	headers := data[0]
	var numericColumns []int

	// Find numeric columns (check first 5 rows)
	for colIdx := 0; colIdx < len(headers); colIdx++ {
		isNumeric := true
		checkRows := len(data) - 1
		if checkRows > 5 {
			checkRows = 5
		}

		for rowIdx := 1; rowIdx <= checkRows; rowIdx++ {
			if colIdx < len(data[rowIdx]) {
				if _, err := strconv.ParseFloat(data[rowIdx][colIdx], 64); err != nil {
					isNumeric = false
					break
				}
			}
		}
		if isNumeric {
			numericColumns = append(numericColumns, colIdx)
		}
	}

	aggregations := make(map[string]map[string]float64)

	for _, colIdx := range numericColumns {
		colName := headers[colIdx]
		var values []float64

		for _, row := range data[1:] {
			if colIdx < len(row) {
				if value, err := strconv.ParseFloat(row[colIdx], 64); err == nil {
					values = append(values, value)
				}
			}
		}

		if len(values) > 0 {
			sum := 0.0
			min := values[0]
			max := values[0]

			for _, value := range values {
				sum += value
				if value < min {
					min = value
				}
				if value > max {
					max = value
				}
			}

			stats := map[string]float64{
				"sum":   sum,
				"avg":   sum / float64(len(values)),
				"min":   min,
				"max":   max,
				"count": float64(len(values)),
			}

			aggregations[colName] = stats
		}
	}

	return aggregations
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

func runCSVProcessingBenchmark(config Config) Results {
	parameters := config.Parameters

	// Set defaults
	rowCounts := parameters.RowCounts
	if len(rowCounts) == 0 {
		rowCounts = []int{1000}
	}

	columnCounts := parameters.ColumnCounts
	if len(columnCounts) == 0 {
		columnCounts = []int{5}
	}

	operations := parameters.Operations
	if len(operations) == 0 {
		operations = []string{"read", "write"}
	}

	dataTypes := parameters.DataTypes
	if len(dataTypes) == 0 {
		dataTypes = []string{"mixed"}
	}

	iterations := parameters.Iterations
	if iterations == 0 {
		iterations = 3
	}

	startTime := time.Now()
	var testCases []TestCase
	var allReadTimes, allWriteTimes, allFilterTimes, allAggregateTimes []float64
	totalTests := 0
	successfulTests := 0
	failedTests := 0

	for _, rows := range rowCounts {
		for _, cols := range columnCounts {
			for _, dataType := range dataTypes {
				fmt.Fprintf(os.Stderr, "Testing CSV: %d rows x %d cols, type: %s...\n", rows, cols, dataType)

				var readTimes, writeTimes, filterTimes, aggregateTimes []float64
				var iterationsData []IterationResult

				for i := 0; i < iterations; i++ {
					fmt.Fprintf(os.Stderr, "  Iteration %d/%d...\n", i+1, iterations)

					// Generate test data
					csvData := generateCSVData(rows, cols, dataType)

					iterationResult := IterationResult{
						Iteration:  i + 1,
						DataSize:   len(csvData),
						Operations: make(map[string]OperationResult),
					}

					totalTests++
					success := true

					// Write operation
					if contains(operations, "write") {
						start := time.Now()
						csvString := writeCSVToString(csvData)
						writeTime := float64(time.Since(start).Nanoseconds()) / 1000000.0

						writeTimes = append(writeTimes, writeTime)
						allWriteTimes = append(allWriteTimes, writeTime)

						iterationResult.Operations["write"] = OperationResult{
							Success:    true,
							TimeMs:     writeTime,
							OutputSize: len(csvString),
						}
					}

					// Read operation
					if contains(operations, "read") {
						csvString := writeCSVToString(csvData)

						start := time.Now()
						readData := readCSVFromString(csvString)
						readTime := float64(time.Since(start).Nanoseconds()) / 1000000.0

						readTimes = append(readTimes, readTime)
						allReadTimes = append(allReadTimes, readTime)

						iterationResult.Operations["read"] = OperationResult{
							Success:  true,
							TimeMs:   readTime,
							RowsRead: len(readData),
						}
					}

					// Filter operation
					if contains(operations, "filter") {
						start := time.Now()
						filteredData := filterCSVData(csvData, 0)
						filterTime := float64(time.Since(start).Nanoseconds()) / 1000000.0

						filterTimes = append(filterTimes, filterTime)
						allFilterTimes = append(allFilterTimes, filterTime)

						iterationResult.Operations["filter"] = OperationResult{
							Success:      true,
							TimeMs:       filterTime,
							OriginalRows: len(csvData),
							FilteredRows: len(filteredData),
						}
					}

					// Aggregate operation
					if contains(operations, "aggregate") {
						start := time.Now()
						aggregations := aggregateCSVData(csvData)
						aggregateTime := float64(time.Since(start).Nanoseconds()) / 1000000.0

						aggregateTimes = append(aggregateTimes, aggregateTime)
						allAggregateTimes = append(allAggregateTimes, aggregateTime)

						iterationResult.Operations["aggregate"] = OperationResult{
							Success:        true,
							TimeMs:         aggregateTime,
							AggregatedCols: len(aggregations),
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
					RowCount:    rows,
					ColumnCount: cols,
					DataType:    dataType,
					Operations:  operations,
					Iterations:  iterationsData,
				}

				if len(readTimes) > 0 {
					sum := 0.0
					for _, t := range readTimes {
						sum += t
					}
					testCase.AvgReadTime = sum / float64(len(readTimes))
				}

				if len(writeTimes) > 0 {
					sum := 0.0
					for _, t := range writeTimes {
						sum += t
					}
					testCase.AvgWriteTime = sum / float64(len(writeTimes))
				}

				if len(filterTimes) > 0 {
					sum := 0.0
					for _, t := range filterTimes {
						sum += t
					}
					testCase.AvgFilterTime = sum / float64(len(filterTimes))
				}

				if len(aggregateTimes) > 0 {
					sum := 0.0
					for _, t := range aggregateTimes {
						sum += t
					}
					testCase.AvgAggregateTime = sum / float64(len(aggregateTimes))
				}

				testCases = append(testCases, testCase)
			}
		}
	}

	// Calculate overall summary
	summary := Summary{
		TotalTests:      totalTests,
		SuccessfulTests: successfulTests,
		FailedTests:     failedTests,
	}

	if len(allReadTimes) > 0 {
		sum := 0.0
		for _, t := range allReadTimes {
			sum += t
		}
		summary.AvgReadTime = sum / float64(len(allReadTimes))
	}

	if len(allWriteTimes) > 0 {
		sum := 0.0
		for _, t := range allWriteTimes {
			sum += t
		}
		summary.AvgWriteTime = sum / float64(len(allWriteTimes))
	}

	if len(allFilterTimes) > 0 {
		sum := 0.0
		for _, t := range allFilterTimes {
			sum += t
		}
		summary.AvgFilterTime = sum / float64(len(allFilterTimes))
	}

	if len(allAggregateTimes) > 0 {
		sum := 0.0
		for _, t := range allAggregateTimes {
			sum += t
		}
		summary.AvgAggregateTime = sum / float64(len(allAggregateTimes))
	}

	endTime := time.Now()
	totalExecutionTime := endTime.Sub(startTime).Seconds()

	return Results{
		StartTime:          float64(startTime.Unix()),
		TestCases:          testCases,
		Summary:            summary,
		EndTime:            float64(endTime.Unix()),
		TotalExecutionTime: totalExecutionTime,
	}
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "Usage: csv_processing <config_file>")
		os.Exit(1)
	}

	configFile := os.Args[1]

	configContent, err := os.ReadFile(configFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Config file '%s' not found: %v\n", configFile, err)
		os.Exit(1)
	}

	var config Config
	if err := json.Unmarshal(configContent, &config); err != nil {
		fmt.Fprintf(os.Stderr, "Error: Invalid JSON in config file: %v\n", err)
		os.Exit(1)
	}

	results := runCSVProcessingBenchmark(config)

	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling results: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(output))
}
