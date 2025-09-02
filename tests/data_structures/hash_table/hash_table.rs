use std::collections::HashMap;
use std::time::Instant;
use rand::{distributions::Alphanumeric, thread_rng, Rng};

fn random_string(length: usize) -> String {
    thread_rng()
        .sample_iter(&Alphanumeric)
        .take(length)
        .map(char::from)
        .collect()
}

fn main() {
    let num_operations = 100_000;
    
    // Generate test data
    let keys: Vec<String> = (0..num_operations)
        .map(|_| random_string(10))
        .collect();
    
    let values: Vec<i32> = (0..num_operations)
        .map(|_| thread_rng().gen_range(1..=1_000_000))
        .collect();
    
    println!("Testing hash table with {} operations...", num_operations);
    let total_start = Instant::now();
    
    // Create hash table
    let mut hash_table = HashMap::new();
    
    // Insert operations
    let insert_start = Instant::now();
    for i in 0..num_operations {
        hash_table.insert(keys[i].clone(), values[i]);
    }
    let insert_time = insert_start.elapsed();
    
    // Lookup operations
    let lookup_start = Instant::now();
    let found_count = keys.iter()
        .filter(|key| hash_table.contains_key(*key))
        .count();
    let lookup_time = lookup_start.elapsed();
    
    // Delete operations (every other key)
    let delete_start = Instant::now();
    let mut deleted_count = 0;
    for i in (0..num_operations).step_by(2) {
        if hash_table.remove(&keys[i]).is_some() {
            deleted_count += 1;
        }
    }
    let delete_time = delete_start.elapsed();
    
    let total_time = total_start.elapsed();
    
    println!("Result:");
    println!("  Inserted: {} items", num_operations);
    println!("  Found: {}/{} items", found_count, num_operations);
    println!("  Deleted: {} items", deleted_count);
    println!("  Remaining: {} items", hash_table.len());
    println!("Timing:");
    println!("  Insert time: {:.6} seconds", insert_time.as_secs_f64());
    println!("  Lookup time: {:.6} seconds", lookup_time.as_secs_f64());
    println!("  Delete time: {:.6} seconds", delete_time.as_secs_f64());
    println!("  Total time: {:.6} seconds", total_time.as_secs_f64());
}
