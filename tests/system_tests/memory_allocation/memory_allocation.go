package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"os"
	"runtime"
	"time"
)

type Config struct {
	Parameters Parameters `json:"parameters"`
}

type Parameters struct {
	AllocationSizes     []int    `json:"allocation_sizes"`
	AllocationPatterns  []string `json:"allocation_patterns"`
	AllocationCounts    []int    `json:"allocation_counts"`
	DataStructures      []string `json:"data_structures"`
	Iterations          int      `json:"iterations"`
}

type Results struct {
	StartTime           float64     `json:"start_time"`
	TestCases           []TestCase  `json:"test_cases"`
	Summary             Summary     `json:"summary"`
	EndTime             float64     `json:"end_time"`
	TotalExecutionTime  float64     `json:"total_execution_time"`
}

type TestCase struct {
	AllocationSize       int              `json:"allocation_size"`
	AllocationCount      int              `json:"allocation_count"`
	DataStructure        string           `json:"data_structure"`
	AllocationPattern    string           `json:"allocation_pattern"`
	Iterations           []IterationResult `json:"iterations"`
	AvgAllocationTime    float64          `json:"avg_allocation_time"`
	AvgDeallocationTime  float64          `json:"avg_deallocation_time"`
	AvgMemoryEfficiency  float64          `json:"avg_memory_efficiency"`
}

type IterationResult struct {
	Iteration    int              `json:"iteration"`
	InitialMemory int            `json:"initial_memory"`
	Allocation   AllocationResult `json:"allocation"`
	Deallocation DeallocationResult `json:"deallocation"`
}

type AllocationResult struct {
	Success          bool    `json:"success"`
	TimeMs           float64 `json:"time_ms"`
	MemoryUsed       int     `json:"memory_used"`
	PeakMemory       int     `json:"peak_memory"`
	MemoryEfficiency float64 `json:"memory_efficiency"`
	ItemsAllocated   int     `json:"items_allocated"`
	Error            *string `json:"error,omitempty"`
}

type DeallocationResult struct {
	Success      bool    `json:"success"`
	TimeMs       float64 `json:"time_ms"`
	FinalMemory  int     `json:"final_memory"`
	MemoryFreed  int     `json:"memory_freed"`
	Error        *string `json:"error,omitempty"`
}

type Summary struct {
	TotalTests             int     `json:"total_tests"`
	SuccessfulTests        int     `json:"successful_tests"`
	FailedTests            int     `json:"failed_tests"`
	AvgAllocationTime      float64 `json:"avg_allocation_time"`
	AvgDeallocationTime    float64 `json:"avg_deallocation_time"`
	AvgMemoryEfficiency    float64 `json:"avg_memory_efficiency"`
}

// Memory tracking
func getMemoryUsage() int {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return int(m.Sys)
}

func allocateArrays(size, count int) [][]int {
	arrays := make([][]int, 0, count)
	
	for i := 0; i < count; i++ {
		array := make([]int, size)
		for j := 0; j < size; j++ {
			array[j] = rand.Intn(1000)
		}
		arrays = append(arrays, array)
	}
	
	return arrays
}

func allocateHashMaps(size, count int) []map[int]int {
	maps := make([]map[int]int, 0, count)
	
	for i := 0; i < count; i++ {
		hashMap := make(map[int]int)
		for j := 0; j < size; j++ {
			key := rand.Intn(size * 2)
			value := rand.Intn(1000)
			hashMap[key] = value
		}
		maps = append(maps, hashMap)
	}
	
	return maps
}

type ListNode struct {
	Value int
	Next  *ListNode
}

func allocateLinkedLists(size, count int) []*ListNode {
	lists := make([]*ListNode, 0, count)
	
	for i := 0; i < count; i++ {
		var head *ListNode
		for j := 0; j < size; j++ {
			newNode := &ListNode{
				Value: rand.Intn(1000),
				Next:  head,
			}
			head = newNode
		}
		lists = append(lists, head)
	}
	
	return lists
}

func runMemoryAllocationBenchmark(params Parameters) Results {
	startTime := float64(time.Now().UnixNano()) / 1e9
	testCases := make([]TestCase, 0)
	summary := Summary{
		TotalTests:          0,
		SuccessfulTests:     0,
		FailedTests:         0,
		AvgAllocationTime:   0.0,
		AvgDeallocationTime: 0.0,
		AvgMemoryEfficiency: 0.0,
	}
	
	allAllocationTimes := make([]float64, 0)
	allDeallocationTimes := make([]float64, 0)
	allMemoryEfficiencies := make([]float64, 0)
	
	for _, size := range params.AllocationSizes {
		for _, count := range params.AllocationCounts {
			for _, structure := range params.DataStructures {
				for _, pattern := range params.AllocationPatterns {
					fmt.Fprintf(os.Stderr, "Testing %s allocation: size=%d, count=%d, pattern=%s...\n", 
						structure, size, count, pattern)
					
					testCase := TestCase{
						AllocationSize:      size,
						AllocationCount:     count,
						DataStructure:       structure,
						AllocationPattern:   pattern,
						Iterations:          make([]IterationResult, 0),
						AvgAllocationTime:   0.0,
						AvgDeallocationTime: 0.0,
						AvgMemoryEfficiency: 0.0,
					}
					
					allocationTimes := make([]float64, 0)
					deallocationTimes := make([]float64, 0)
					memoryEfficiencies := make([]float64, 0)
					
					for i := 0; i < params.Iterations; i++ {
						fmt.Fprintf(os.Stderr, "  Iteration %d/%d...\n", i+1, params.Iterations)
						
						initialMemory := getMemoryUsage()
						summary.TotalTests++
						
						iterationResult := IterationResult{
							Iteration:    i + 1,
							InitialMemory: initialMemory,
							Allocation: AllocationResult{
								Success:        false,
								TimeMs:         0.0,
								MemoryUsed:     0,
								PeakMemory:     0,
								MemoryEfficiency: 0.0,
								ItemsAllocated: count,
							},
							Deallocation: DeallocationResult{
								Success:      false,
								TimeMs:       0.0,
								FinalMemory:  0,
								MemoryFreed:  0,
							},
						}
						
						success := false
						switch structure {
						case "array":
							start := time.Now()
							_ = allocateArrays(size, count)
							allocationTime := float64(time.Since(start).Nanoseconds()) / 1e6
							
							peakMemory := getMemoryUsage()
							memoryUsed := peakMemory - initialMemory
							theoreticalSize := size * count * 8 // 8 bytes per int
							memoryEfficiency := 100.0
							if memoryUsed > 0 {
								memoryEfficiency = float64(theoreticalSize) / float64(memoryUsed) * 100.0
							}
							
							allocationTimes = append(allocationTimes, allocationTime)
							allAllocationTimes = append(allAllocationTimes, allocationTime)
							memoryEfficiencies = append(memoryEfficiencies, memoryEfficiency)
							allMemoryEfficiencies = append(allMemoryEfficiencies, memoryEfficiency)
							
							iterationResult.Allocation = AllocationResult{
								Success:          true,
								TimeMs:           allocationTime,
								MemoryUsed:       memoryUsed,
								PeakMemory:       peakMemory,
								MemoryEfficiency: memoryEfficiency,
								ItemsAllocated:   count,
							}
							
							// Deallocation
							start = time.Now()
							runtime.GC()    // Force garbage collection
							deallocationTime := float64(time.Since(start).Nanoseconds()) / 1e6
							finalMemory := getMemoryUsage()
							
							deallocationTimes = append(deallocationTimes, deallocationTime)
							allDeallocationTimes = append(allDeallocationTimes, deallocationTime)
							
							iterationResult.Deallocation = DeallocationResult{
								Success:     true,
								TimeMs:      deallocationTime,
								FinalMemory: finalMemory,
								MemoryFreed: peakMemory - finalMemory,
							}
							
							success = true
							
						case "hash_map":
							start := time.Now()
							_ = allocateHashMaps(size, count)
							allocationTime := float64(time.Since(start).Nanoseconds()) / 1e6
							
							peakMemory := getMemoryUsage()
							memoryUsed := peakMemory - initialMemory
							theoreticalSize := size * count * 16 // Key-value pairs
							memoryEfficiency := 100.0
							if memoryUsed > 0 {
								memoryEfficiency = float64(theoreticalSize) / float64(memoryUsed) * 100.0
							}
							
							allocationTimes = append(allocationTimes, allocationTime)
							allAllocationTimes = append(allAllocationTimes, allocationTime)
							memoryEfficiencies = append(memoryEfficiencies, memoryEfficiency)
							allMemoryEfficiencies = append(allMemoryEfficiencies, memoryEfficiency)
							
							iterationResult.Allocation = AllocationResult{
								Success:          true,
								TimeMs:           allocationTime,
								MemoryUsed:       memoryUsed,
								PeakMemory:       peakMemory,
								MemoryEfficiency: memoryEfficiency,
								ItemsAllocated:   count,
							}
							
							// Deallocation
							start = time.Now()
							runtime.GC()    // Force garbage collection
							deallocationTime := float64(time.Since(start).Nanoseconds()) / 1e6
							finalMemory := getMemoryUsage()
							
							deallocationTimes = append(deallocationTimes, deallocationTime)
							allDeallocationTimes = append(allDeallocationTimes, deallocationTime)
							
							iterationResult.Deallocation = DeallocationResult{
								Success:     true,
								TimeMs:      deallocationTime,
								FinalMemory: finalMemory,
								MemoryFreed: peakMemory - finalMemory,
							}
							
							success = true
							
						case "linked_list":
							start := time.Now()
							_ = allocateLinkedLists(size, count)
							allocationTime := float64(time.Since(start).Nanoseconds()) / 1e6
							
							peakMemory := getMemoryUsage()
							memoryUsed := peakMemory - initialMemory
							theoreticalSize := size * count * 24 // Node overhead
							memoryEfficiency := 100.0
							if memoryUsed > 0 {
								memoryEfficiency = float64(theoreticalSize) / float64(memoryUsed) * 100.0
							}
							
							allocationTimes = append(allocationTimes, allocationTime)
							allAllocationTimes = append(allAllocationTimes, allocationTime)
							memoryEfficiencies = append(memoryEfficiencies, memoryEfficiency)
							allMemoryEfficiencies = append(allMemoryEfficiencies, memoryEfficiency)
							
							iterationResult.Allocation = AllocationResult{
								Success:          true,
								TimeMs:           allocationTime,
								MemoryUsed:       memoryUsed,
								PeakMemory:       peakMemory,
								MemoryEfficiency: memoryEfficiency,
								ItemsAllocated:   count,
							}
							
							// Deallocation
							start = time.Now()
							runtime.GC()    // Force garbage collection
							deallocationTime := float64(time.Since(start).Nanoseconds()) / 1e6
							finalMemory := getMemoryUsage()
							
							deallocationTimes = append(deallocationTimes, deallocationTime)
							allDeallocationTimes = append(allDeallocationTimes, deallocationTime)
							
							iterationResult.Deallocation = DeallocationResult{
								Success:     true,
								TimeMs:      deallocationTime,
								FinalMemory: finalMemory,
								MemoryFreed: peakMemory - finalMemory,
							}
							
							success = true
							
						default:
							errMsg := fmt.Sprintf("Unknown data structure: %s", structure)
							iterationResult.Allocation.Error = &errMsg
						}
						
						if success {
							summary.SuccessfulTests++
						} else {
							summary.FailedTests++
						}
						
						testCase.Iterations = append(testCase.Iterations, iterationResult)
					}
					
					// Calculate averages
					if len(allocationTimes) > 0 {
						sum := 0.0
						for _, t := range allocationTimes {
							sum += t
						}
						testCase.AvgAllocationTime = sum / float64(len(allocationTimes))
					}
					
					if len(deallocationTimes) > 0 {
						sum := 0.0
						for _, t := range deallocationTimes {
							sum += t
						}
						testCase.AvgDeallocationTime = sum / float64(len(deallocationTimes))
					}
					
					if len(memoryEfficiencies) > 0 {
						sum := 0.0
						for _, e := range memoryEfficiencies {
							sum += e
						}
						testCase.AvgMemoryEfficiency = sum / float64(len(memoryEfficiencies))
					}
					
					testCases = append(testCases, testCase)
				}
			}
		}
	}
	
	// Calculate overall summary
	if len(allAllocationTimes) > 0 {
		sum := 0.0
		for _, t := range allAllocationTimes {
			sum += t
		}
		summary.AvgAllocationTime = sum / float64(len(allAllocationTimes))
	}
	
	if len(allDeallocationTimes) > 0 {
		sum := 0.0
		for _, t := range allDeallocationTimes {
			sum += t
		}
		summary.AvgDeallocationTime = sum / float64(len(allDeallocationTimes))
	}
	
	if len(allMemoryEfficiencies) > 0 {
		sum := 0.0
		for _, e := range allMemoryEfficiencies {
			sum += e
		}
		summary.AvgMemoryEfficiency = sum / float64(len(allMemoryEfficiencies))
	}
	
	endTime := float64(time.Now().UnixNano()) / 1e9
	
	return Results{
		StartTime:           startTime,
		TestCases:           testCases,
		Summary:             summary,
		EndTime:             endTime,
		TotalExecutionTime:  endTime - startTime,
	}
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "Usage: go run memory_allocation.go <config_file>")
		os.Exit(1)
	}
	
	configFile := os.Args[1]
	
	data, err := ioutil.ReadFile(configFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Config file '%s' not found\n", configFile)
		os.Exit(1)
	}
	
	var config Config
	err = json.Unmarshal(data, &config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Invalid JSON in config file: %v\n", err)
		os.Exit(1)
	}
	
	// Seed random number generator
	rand.Seed(time.Now().UnixNano())
	
	results := runMemoryAllocationBenchmark(config.Parameters)
	
	output, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: Failed to serialize results: %v\n", err)
		os.Exit(1)
	}
	
	fmt.Println(string(output))
}