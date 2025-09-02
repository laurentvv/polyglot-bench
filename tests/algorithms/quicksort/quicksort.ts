#!/usr/bin/env node
/**
 * Quicksort benchmark implementation in TypeScript.
 * Sorts an array using the quicksort algorithm.
 */

function quicksort(arr: number[]): number[] {
    if (arr.length <= 1) {
        return arr;
    }
    
    const pivot = arr[Math.floor(arr.length / 2)];
    const left = arr.filter(x => x < pivot);
    const middle = arr.filter(x => x === pivot);
    const right = arr.filter(x => x > pivot);
    
    return [...quicksort(left), ...middle, ...quicksort(right)];
}

function shuffle(arr: number[]): void {
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
}

function main(): void {
    const size = 10000;
    const arr = Array.from({length: size}, (_, i) => i);
    shuffle(arr);
    
    console.log(`Sorting array of size ${size}...`);
    const start = performance.now();
    
    const sortedArr = quicksort([...arr]);
    
    const end = performance.now();
    const executionTime = (end - start) / 1000; // Convert to seconds
    
    // Verify correctness
    const expected = [...arr].sort((a, b) => a - b);
    const isSorted = JSON.stringify(sortedArr) === JSON.stringify(expected);
    
    console.log(`Result: ${isSorted ? 'Sorted correctly' : 'Sort failed'}`);
    console.log(`Execution time: ${executionTime.toFixed(6)} seconds`);
}

// Always run main for benchmark purposes
main();