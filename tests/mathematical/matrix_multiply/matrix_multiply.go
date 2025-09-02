package main

import (
	"fmt"
	"math/rand"
	"time"
)

func createMatrix(rows, cols int) [][]float64 {
	matrix := make([][]float64, rows)
	for i := range matrix {
		matrix[i] = make([]float64, cols)
		for j := range matrix[i] {
			matrix[i][j] = rand.Float64() * 100
		}
	}
	return matrix
}

func multiplyMatrices(a, b [][]float64) [][]float64 {
	rowsA := len(a)
	colsA := len(a[0])
	colsB := len(b[0])
	
	result := make([][]float64, rowsA)
	for i := range result {
		result[i] = make([]float64, colsB)
	}
	
	for i := 0; i < rowsA; i++ {
		for j := 0; j < colsB; j++ {
			for k := 0; k < colsA; k++ {
				result[i][j] += a[i][k] * b[k][j]
			}
		}
	}
	
	return result
}

func main() {
	rand.Seed(time.Now().UnixNano())
	size := 200 // Matrix size (200x200)
	
	fmt.Printf("Multiplying two %dx%d matrices...\n", size, size)
	
	// Create matrices
	createStart := time.Now()
	matrixA := createMatrix(size, size)
	matrixB := createMatrix(size, size)
	createTime := time.Since(createStart)
	
	// Multiply matrices
	multiplyStart := time.Now()
	result := multiplyMatrices(matrixA, matrixB)
	multiplyTime := time.Since(multiplyStart)
	
	totalTime := createTime + multiplyTime
	
	// Verify result dimensions
	resultRows := len(result)
	resultCols := len(result[0])
	
	fmt.Printf("Result: %dx%d matrix\n", resultRows, resultCols)
	fmt.Printf("Sample result[0][0]: %.6f\n", result[0][0])
	fmt.Println("Timing:")
	fmt.Printf("  Matrix creation: %.6f seconds\n", createTime.Seconds())
	fmt.Printf("  Matrix multiplication: %.6f seconds\n", multiplyTime.Seconds())
	fmt.Printf("  Total time: %.6f seconds\n", totalTime.Seconds())
}