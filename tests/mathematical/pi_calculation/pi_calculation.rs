use std::time::Instant;
use rand::prelude::*;

fn calculate_pi_monte_carlo(num_samples: usize) -> f64 {
    let mut rng = thread_rng();
    let mut inside_circle = 0;
    
    for _ in 0..num_samples {
        let x: f64 = rng.gen();
        let y: f64 = rng.gen();
        
        if x*x + y*y <= 1.0 {
            inside_circle += 1;
        }
    }
    
    4.0 * inside_circle as f64 / num_samples as f64
}

fn main() {
    let num_samples = 1_000_000;
    
    println!("Calculating pi with {} samples...", num_samples);
    let start = Instant::now();
    
    let pi_estimate = calculate_pi_monte_carlo(num_samples);
    
    let duration = start.elapsed();
    
    let actual_pi = std::f64::consts::PI;
    let error = (pi_estimate - actual_pi).abs();
    
    println!("Result: {:.6}", pi_estimate);
    println!("Actual pi: {:.6}", actual_pi);
    println!("Error: {:.6}", error);
    println!("Execution time: {:.6} seconds", duration.as_secs_f64());
}