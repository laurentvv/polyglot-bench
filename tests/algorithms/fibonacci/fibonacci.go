// Fibonacci benchmark implementation in Go.
// Calculates the nth Fibonacci number using recursive algorithm.

package main

import (
	"fmt"
	"time"
)

// fibonacci calculates the nth Fibonacci number recursively.
func fibonacci(n int) int {
	if n <= 1 {
		return n
	}
	return fibonacci(n-1) + fibonacci(n-2)
}

func main() {
	// Test parameter
	n := 35 // Adjusted for reasonable execution time

	fmt.Printf("Calculating fibonacci(%d)...\n", n)
	startTime := time.Now()

	result := fibonacci(n)

	executionTime := time.Since(startTime)

	fmt.Printf("Result: %d\n", result)
	fmt.Printf("Execution time: %.6f seconds\n", executionTime.Seconds())
}