use std::time::Instant;

fn sieve_of_eratosthenes(n: usize) -> Vec<usize> {
    if n < 2 {
        return Vec::new();
    }
    
    let mut is_prime = vec![true; n + 1];
    is_prime[0] = false;
    is_prime[1] = false;
    
    let limit = (n as f64).sqrt() as usize;
    
    for i in 2..=limit {
        if is_prime[i] {
            let mut j = i * i;
            while j <= n {
                is_prime[j] = false;
                j += i;
            }
        }
    }
    
    (2..=n).filter(|&i| is_prime[i]).collect()
}

fn main() {
    let n = 100_000;
    
    println!("Finding all primes up to {}...", n);
    let start = Instant::now();
    
    let primes = sieve_of_eratosthenes(n);
    
    let duration = start.elapsed();
    
    println!("Result: Found {} primes", primes.len());
    if let Some(&largest) = primes.last() {
        println!("Largest prime: {}", largest);
    }
    println!("Execution time: {:.6} seconds", duration.as_secs_f64());
}