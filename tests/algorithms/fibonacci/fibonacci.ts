/**
 * Fibonacci benchmark implementation in TypeScript.
 * Calculates the nth Fibonacci number using recursive algorithm.
 */

/**
 * Calculate the nth Fibonacci number recursively.
 */
function fibonacci(n: number): number {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

function main(): void {
    // Test parameter
    const n = 35; // Adjusted for reasonable execution time

    console.log(`Calculating fibonacci(${n})...`);
    const startTime = process.hrtime.bigint();

    const result = fibonacci(n);

    const endTime = process.hrtime.bigint();
    const executionTime = Number(endTime - startTime) / 1e9; // Convert to seconds

    console.log(`Result: ${result}`);
    console.log(`Execution time: ${executionTime.toFixed(6)} seconds`);
}

main();