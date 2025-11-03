package main

import (
	"fmt"
	"math/rand"
	"time"
)

// Use a more robust partitioning method and better pivot selection
func quicksort(arr []int, low, high int) {
    if low < high {
        // Randomized pivot to avoid worst-case performance
        randomIndex := low + rand.Intn(high-low+1)
        arr[randomIndex], arr[high] = arr[high], arr[randomIndex]
        
        pivotIndex := partition(arr, low, high)
        quicksort(arr, low, pivotIndex-1)
        quicksort(arr, pivotIndex+1, high)
    }
}

// Hoare partition scheme (more efficient than Lomuto)
func partition(arr []int, low, high int) int {
    pivot := arr[high]
    i := low - 1
    
    for j := low; j < high; j++ {
        if arr[j] <= pivot {
            i++
            arr[i], arr[j] = arr[j], arr[i]
        }
    }
    
    arr[i+1], arr[high] = arr[high], arr[i+1]
    return i + 1
}

// Hybrid approach: Use insertion sort for small arrays
func insertionSort(arr []int, low, high int) {
    for i := low + 1; i <= high; i++ {
        key := arr[i]
        j := i - 1
        
        for j >= low && arr[j] > key {
            arr[j+1] = arr[j]
            j--
        }
        arr[j+1] = key
    }
}

// Optimized quicksort with hybrid approach
func optimizedQuicksort(arr []int, low, high int) {
    for low < high {
        // Use insertion sort for small subarrays
        if high-low < 10 {
            insertionSort(arr, low, high)
            break
        } else {
            // Randomized pivot to avoid worst-case performance
            randomIndex := low + rand.Intn(high-low+1)
            arr[randomIndex], arr[high] = arr[high], arr[randomIndex]
            
            pivotIndex := partition(arr, low, high)
            
            // Optimize tail recursion
            if pivotIndex-low < high-pivotIndex {
                optimizedQuicksort(arr, low, pivotIndex-1)
                low = pivotIndex + 1
            } else {
                optimizedQuicksort(arr, pivotIndex+1, high)
                high = pivotIndex - 1
            }
        }
    }
}

func main() {
    size := 10000
    arr := make([]int, size)
    for i := range arr {
        arr[i] = i
    }
    
    // Shuffle array
    rand.Seed(time.Now().UnixNano())
    for i := len(arr) - 1; i > 0; i-- {
        j := rand.Intn(i + 1)
        arr[i], arr[j] = arr[j], arr[i]
    }
    
    fmt.Printf("Sorting array of size %d...\n", size)
    start := time.Now()
    
    optimizedQuicksort(arr, 0, size-1)
    
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