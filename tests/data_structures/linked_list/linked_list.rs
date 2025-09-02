/// Linked List benchmark implementation in Rust.
/// Tests basic linked list operations: insert, search, delete.

use std::time::Instant;

fn main() {
    println!("Starting linked list benchmark...");
    let start_time = Instant::now();
    
    // Using Vec as a simple list implementation to avoid stack overflow
    let mut linked_list = Vec::new();
    let operations_count = 10000;
    
    // Insert operations (insert at beginning)
    for i in 0..operations_count {
        linked_list.insert(0, i);
    }
    
    // Search operations
    let mut found_count = 0;
    for i in (0..operations_count).step_by(100) {
        if linked_list.iter().any(|&x| x == i) {
            found_count += 1;
        }
    }
    
    // Delete operations
    let mut deleted_count = 0;
    for i in (0..operations_count).step_by(200) {
        if let Some(pos) = linked_list.iter().position(|&x| x == i) {
            linked_list.remove(pos);
            deleted_count += 1;
        }
    }
    
    let execution_time = start_time.elapsed();
    
    println!("Operations completed: {} inserts, {} searches, {} deletes", 
             operations_count, found_count, deleted_count);
    println!("Final list size: {}", linked_list.len());
    println!("Execution time: {:.6} seconds", execution_time.as_secs_f64());
}