package main

import (
	"fmt"
	"math/rand"
	"time"
)

func randomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	result := make([]byte, length)
	for i := range result {
		result[i] = charset[rand.Intn(len(charset))]
	}
	return string(result)
}

func main() {
	rand.Seed(time.Now().UnixNano())
	numOperations := 100000
	
	// Generate test data
	keys := make([]string, numOperations)
	values := make([]int, numOperations)
	
	for i := 0; i < numOperations; i++ {
		keys[i] = randomString(10)
		values[i] = rand.Intn(1000000) + 1
	}
	
	fmt.Printf("Testing hash table with %d operations...\n", numOperations)
	totalStart := time.Now()
	
	// Create hash table (map in Go)
	hashTable := make(map[string]int)
	
	// Insert operations
	insertStart := time.Now()
	for i := 0; i < numOperations; i++ {
		hashTable[keys[i]] = values[i]
	}
	insertTime := time.Since(insertStart)
	
	// Lookup operations
	lookupStart := time.Now()
	foundCount := 0
	for _, key := range keys {
		if _, exists := hashTable[key]; exists {
			foundCount++
		}
	}
	lookupTime := time.Since(lookupStart)
	
	// Delete operations (every other key)
	deleteStart := time.Now()
	deletedCount := 0
	for i := 0; i < numOperations; i += 2 {
		if _, exists := hashTable[keys[i]]; exists {
			delete(hashTable, keys[i])
			deletedCount++
		}
	}
	deleteTime := time.Since(deleteStart)
	
	totalTime := time.Since(totalStart)
	
	fmt.Println("Result:")
	fmt.Printf("  Inserted: %d items\n", numOperations)
	fmt.Printf("  Found: %d/%d items\n", foundCount, numOperations)
	fmt.Printf("  Deleted: %d items\n", deletedCount)
	fmt.Printf("  Remaining: %d items\n", len(hashTable))
	fmt.Println("Timing:")
	fmt.Printf("  Insert time: %.6f seconds\n", insertTime.Seconds())
	fmt.Printf("  Lookup time: %.6f seconds\n", lookupTime.Seconds())
	fmt.Printf("  Delete time: %.6f seconds\n", deleteTime.Seconds())
	fmt.Printf("  Total time: %.6f seconds\n", totalTime.Seconds())
}
