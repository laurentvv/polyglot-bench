use std::time::Instant;
use rand::prelude::*;

fn binary_search(arr: &[i32], target: i32) -> Option<usize> {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        
        match arr[mid].cmp(&target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid,
        }
    }
    
    None
}

fn main() {
    let size = 1_000_000;
    let arr: Vec<i32> = (0..size).collect();
    let num_searches = 1000;
    
    // Generate random targets
    let mut rng = thread_rng();
    let targets: Vec<i32> = (0..num_searches)
        .map(|_| rng.gen_range(0..size))
        .collect();
    
    println!("Performing {} binary searches on array of size {}...", num_searches, size);
    let start = Instant::now();
    
    let found_count = targets
        .iter()
        .filter(|&&target| binary_search(&arr, target).is_some())
        .count();
    
    let duration = start.elapsed();
    
    println!("Result: Found {}/{} targets", found_count, num_searches);
    println!("Execution time: {:.6} seconds", duration.as_secs_f64());
}