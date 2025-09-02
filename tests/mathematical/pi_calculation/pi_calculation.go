package main

import (
	"fmt"
	"math"
	"math/rand"
	"time"
)

func calculatePiMonteCarlo(numSamples int) float64 {
	insideCircle := 0
	
	for i := 0; i < numSamples; i++ {
		x := rand.Float64()
		y := rand.Float64()
		
		if x*x+y*y <= 1 {
			insideCircle++
		}
	}
	
	return 4.0 * float64(insideCircle) / float64(numSamples)
}

func main() {
	numSamples := 1000000
	
	fmt.Printf("Calculating pi with %d samples...\n", numSamples)
	start := time.Now()
	
	piEstimate := calculatePiMonteCarlo(numSamples)
	
	duration := time.Since(start)
	
	actualPi := math.Pi
	error := math.Abs(piEstimate - actualPi)
	
	fmt.Printf("Result: %.6f\n", piEstimate)
	fmt.Printf("Actual pi: %.6f\n", actualPi)
	fmt.Printf("Error: %.6f\n", error)
	fmt.Printf("Execution time: %.6f seconds\n", duration.Seconds())
}