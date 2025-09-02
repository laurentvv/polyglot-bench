use std::time::Instant;
use rand::prelude::*;

fn quicksort(arr: &mut [i32]) {
    if arr.len() <= 1 {
        return;
    }
    
    let pivot_index = partition(arr);
    let (left, right) = arr.split_at_mut(pivot_index);
    
    if !left.is_empty() {
        quicksort(left);
    }
    if right.len() > 1 {
        quicksort(&mut right[1..]);
    }
}

fn partition(arr: &mut [i32]) -> usize {
    let pivot = arr[arr.len() - 1];
    let mut i = 0;
    
    for j in 0..arr.len() - 1 {
        if arr[j] <= pivot {
            arr.swap(i, j);
            i += 1;
        }
    }
    
    arr.swap(i, arr.len() - 1);
    i
}

fn main() {
    let size = 10000;
    let mut arr: Vec<i32> = (0..size).collect();
    arr.shuffle(&mut thread_rng());
    
    println!("Sorting array of size {}...", size);
    let start = Instant::now();
    
    quicksort(&mut arr);
    
    let duration = start.elapsed();
    
    // Verify correctness
    let is_sorted = arr.windows(2).all(|w| w[0] <= w[1]);
    
    println!("Result: {}", if is_sorted { "Sorted correctly" } else { "Sort failed" });
    println!("Execution time: {:.6} seconds", duration.as_secs_f64());
}