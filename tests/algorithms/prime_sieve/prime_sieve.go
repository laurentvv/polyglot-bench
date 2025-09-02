package main

import (
	"fmt"
	"math"
	"time"
)

func sieveOfEratosthenes(n int) []int {
	if n < 2 {
		return []int{}
	}
	
	isPrime := make([]bool, n+1)
	for i := range isPrime {
		isPrime[i] = true
	}
	isPrime[0], isPrime[1] = false, false
	
	limit := int(math.Sqrt(float64(n)))
	
	for i := 2; i <= limit; i++ {
		if isPrime[i] {
			for j := i * i; j <= n; j += i {
				isPrime[j] = false
			}
		}
	}
	
	var primes []int
	for i := 2; i <= n; i++ {
		if isPrime[i] {
			primes = append(primes, i)
		}
	}
	
	return primes
}

func main() {
	n := 100000
	
	fmt.Printf("Finding all primes up to %d...\n", n)
	start := time.Now()
	
	primes := sieveOfEratosthenes(n)
	
	duration := time.Since(start)
	
	fmt.Printf("Result: Found %d primes\n", len(primes))
	if len(primes) > 0 {
		fmt.Printf("Largest prime: %d\n", primes[len(primes)-1])
	}
	fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}