#!/usr/bin/env node
/**
 * Pi calculation benchmark implementation in TypeScript.
 * Calculates pi using the Monte Carlo method.
 */

function calculatePiMonteCarlo(numSamples: number): number {
    let insideCircle = 0;
    
    for (let i = 0; i < numSamples; i++) {
        const x = Math.random();
        const y = Math.random();
        
        if (x*x + y*y <= 1) {
            insideCircle++;
        }
    }
    
    return 4.0 * insideCircle / numSamples;
}

function main(): void {
    const numSamples = 1000000;
    
    console.log(`Calculating pi with ${numSamples} samples...`);
    const start = performance.now();
    
    const piEstimate = calculatePiMonteCarlo(numSamples);
    
    const end = performance.now();
    const executionTime = (end - start) / 1000; // Convert to seconds
    
    const actualPi = Math.PI;
    const error = Math.abs(piEstimate - actualPi);
    
    console.log(`Result: ${piEstimate.toFixed(6)}`);
    console.log(`Actual pi: ${actualPi.toFixed(6)}`);
    console.log(`Error: ${error.toFixed(6)}`);
    console.log(`Execution time: ${executionTime.toFixed(6)} seconds`);
}

if (require.main === module) {
    main();
}