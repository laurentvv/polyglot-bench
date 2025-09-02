#!/usr/bin/env node
/**
 * Binary search benchmark implementation in TypeScript.
 * Performs binary search on a sorted array.
 */

function binarySearch(arr: number[], target: number): number {
    let left = 0;
    let right = arr.length - 1;
    
    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        
        if (arr[mid] === target) {
            return mid;
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    return -1;
}

function main(): void {
    const size = 1000000;
    const arr = Array.from({length: size}, (_, i) => i);
    const numSearches = 1000;
    
    // Generate random targets
    const targets = Array.from({length: numSearches}, () => 
        Math.floor(Math.random() * size)
    );
    
    console.log(`Performing ${numSearches} binary searches on array of size ${size}...`);
    const start = performance.now();
    
    let foundCount = 0;
    for (const target of targets) {
        const result = binarySearch(arr, target);
        if (result !== -1) {
            foundCount++;
        }
    }
    
    const end = performance.now();
    const executionTime = (end - start) / 1000; // Convert to seconds
    
    console.log(`Result: Found ${foundCount}/${numSearches} targets`);
    console.log(`Execution time: ${executionTime.toFixed(6)} seconds`);
}

// Always run main for benchmark purposes
main();