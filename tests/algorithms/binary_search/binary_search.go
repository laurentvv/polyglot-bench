package main

import (
	"fmt"
	"math/rand"
	"time"
)

func binarySearch(arr []int, target int) int {
	left, right := 0, len(arr)-1
	
	for left <= right {
		mid := left + (right-left)/2
		
		if arr[mid] == target {
			return mid
		} else if arr[mid] < target {
			left = mid + 1
		} else {
			right = mid - 1
		}
	}
	
	return -1
}

func main() {
	size := 1000000
	arr := make([]int, size)
	for i := range arr {
		arr[i] = i
	}
	
	numSearches := 1000
	targets := make([]int, numSearches)
	for i := range targets {
		targets[i] = rand.Intn(size)
	}
	
	fmt.Printf("Performing %d binary searches on array of size %d...\n", numSearches, size)
	start := time.Now()
	
	foundCount := 0
	for _, target := range targets {
		if result := binarySearch(arr, target); result != -1 {
			foundCount++
		}
	}
	
	duration := time.Since(start)
	
	fmt.Printf("Result: Found %d/%d targets\n", foundCount, numSearches)
	fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}