/// Fibonacci benchmark implementation in Rust.
/// Calculates the nth Fibonacci number using recursive algorithm.

use std::time::Instant;

fn fibonacci(n: u32) -> u64 {
    /// Calculate the nth Fibonacci number recursively.
    if n <= 1 {
        return n as u64;
    }
    fibonacci(n - 1) + fibonacci(n - 2)
}

fn main() {
    // Test parameter
    let n = 35; // Adjusted for reasonable execution time
    
    println!("Calculating fibonacci({})...", n);
    let start_time = Instant::now();
    
    let result = fibonacci(n);
    
    let execution_time = start_time.elapsed();
    
    println!("Result: {}", result);
    println!("Execution time: {:.6} seconds", execution_time.as_secs_f64());
}