#!/usr/bin/env node
/**
 * Prime sieve benchmark implementation in TypeScript.
 * Finds all prime numbers up to n using the Sieve of Eratosthenes.
 */

function sieveOfEratosthenes(n: number): number[] {
    if (n < 2) {
        return [];
    }
    
    const isPrime = new Array(n + 1).fill(true);
    isPrime[0] = isPrime[1] = false;
    
    const limit = Math.floor(Math.sqrt(n));
    
    for (let i = 2; i <= limit; i++) {
        if (isPrime[i]) {
            for (let j = i * i; j <= n; j += i) {
                isPrime[j] = false;
            }
        }
    }
    
    const primes: number[] = [];
    for (let i = 2; i <= n; i++) {
        if (isPrime[i]) {
            primes.push(i);
        }
    }
    
    return primes;
}

function main(): void {
    const n = 100000;
    
    console.log(`Finding all primes up to ${n}...`);
    const start = performance.now();
    
    const primes = sieveOfEratosthenes(n);
    
    const end = performance.now();
    const executionTime = (end - start) / 1000; // Convert to seconds
    
    console.log(`Result: Found ${primes.length} primes`);
    if (primes.length > 0) {
        console.log(`Largest prime: ${primes[primes.length - 1]}`);
    }
    console.log(`Execution time: ${executionTime.toFixed(6)} seconds`);
}

if (require.main === module) {
    main();
}