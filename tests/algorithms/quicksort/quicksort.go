package main

import (
	"fmt"
	"math/rand"
	"time"
)

func quicksort(arr []int) {
	if len(arr) <= 1 {
		return
	}
	
	pivotIndex := partition(arr)
	quicksort(arr[:pivotIndex])
	quicksort(arr[pivotIndex+1:])
}

func partition(arr []int) int {
	pivot := arr[len(arr)-1]
	i := 0
	
	for j := 0; j < len(arr)-1; j++ {
		if arr[j] <= pivot {
			arr[i], arr[j] = arr[j], arr[i]
			i++
		}
	}
	
	arr[i], arr[len(arr)-1] = arr[len(arr)-1], arr[i]
	return i
}

func main() {
	size := 10000
	arr := make([]int, size)
	for i := range arr {
		arr[i] = i
	}
	
	// Shuffle array
	rand.Shuffle(len(arr), func(i, j int) {
		arr[i], arr[j] = arr[j], arr[i]
	})
	
	fmt.Printf("Sorting array of size %d...\n", size)
	start := time.Now()
	
	quicksort(arr)
	
	duration := time.Since(start)
	
	// Verify correctness
	isSorted := true
	for i := 1; i < len(arr); i++ {
		if arr[i] < arr[i-1] {
			isSorted = false
			break
		}
	}
	
	if isSorted {
		fmt.Println("Result: Sorted correctly")
	} else {
		fmt.Println("Result: Sort failed")
	}
	fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}