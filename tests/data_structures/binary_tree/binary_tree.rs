/// Binary Tree benchmark implementation in Rust.
/// Tests basic binary search tree operations: insert, search, traverse.

use std::time::Instant;
use std::collections::BTreeSet;

fn main() {
    println!("Starting binary tree benchmark...");
    let start_time = Instant::now();
    
    // Using BTreeSet as an efficient binary tree implementation
    let mut bst = BTreeSet::new();
    let nodes_count = 1000;
    
    // Create shuffled values for insertion
    let mut values: Vec<i32> = (0..nodes_count).collect();
    
    // Simple pseudo-random shuffle using a linear congruential generator
    let mut seed = 42u32;
    for i in (1..values.len()).rev() {
        seed = seed.wrapping_mul(1103515245).wrapping_add(12345);
        let j = (seed as usize) % (i + 1);
        values.swap(i, j);
    }
    
    // Insert operations
    for &val in &values {
        bst.insert(val);
    }
    
    // Search operations
    let mut found_count = 0;
    let search_count = std::cmp::min(100, values.len());
    for i in 0..search_count {
        if bst.contains(&values[i]) {
            found_count += 1;
        }
    }
    
    // Traversal operation (BTreeSet keeps elements sorted)
    let traversal_result: Vec<i32> = bst.iter().cloned().collect();
    let is_sorted = traversal_result.windows(2).all(|w| w[0] <= w[1]);
    
    let execution_time = start_time.elapsed();
    
    println!("Tree operations completed: {} inserts, {} searches", 
             nodes_count, found_count);
    println!("Final tree size: {}", bst.len());
    println!("Inorder traversal length: {}", traversal_result.len());
    println!("Traversal is sorted: {}", is_sorted);
    println!("Execution time: {:.6} seconds", execution_time.as_secs_f64());
}