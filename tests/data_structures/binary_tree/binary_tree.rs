/// Binary Tree benchmark implementation in Rust.
/// Tests basic binary search tree operations: insert, search, traverse.

use std::env;
use std::fs;
use serde::{Deserialize, Serialize};
use serde_json;

#[derive(Deserialize)]
struct Config {
    parameters: Parameters,
}

#[derive(Deserialize)]
struct Parameters {
    nodes_count: Option<usize>,
}

#[derive(Serialize)]
struct BenchmarkResult {
    start_time: f64,
    operations: Operations,
    tree_stats: TreeStats,
    end_time: f64,
    total_execution_time: f64,
}

#[derive(Serialize)]
struct Operations {
    inserts: usize,
    searches: usize,
    found_count: usize,
    traversal_length: usize,
}

#[derive(Serialize)]
struct TreeStats {
    final_size: usize,
    is_sorted: bool,
}

// Custom binary tree node for better performance
#[derive(Debug)]
struct TreeNode {
    value: i32,
    left: Option<Box<TreeNode>>,
    right: Option<Box<TreeNode>>,
}

impl TreeNode {
    fn new(value: i32) -> Self {
        TreeNode {
            value,
            left: None,
            right: None,
        }
    }
}

struct BinarySearchTree {
    root: Option<Box<TreeNode>>,
    size: usize,
}

impl BinarySearchTree {
    fn new() -> Self {
        BinarySearchTree {
            root: None,
            size: 0,
        }
    }

    fn insert(&mut self, value: i32) {
        self.root = Self::insert_recursive(self.root.take(), value);
        self.size += 1;
    }

    fn insert_recursive(node: Option<Box<TreeNode>>, value: i32) -> Option<Box<TreeNode>> {
        match node {
            None => Some(Box::new(TreeNode::new(value))),
            Some(mut boxed_node) => {
                if value < boxed_node.value {
                    boxed_node.left = Self::insert_recursive(boxed_node.left.take(), value);
                } else if value > boxed_node.value {
                    boxed_node.right = Self::insert_recursive(boxed_node.right.take(), value);
                }
                // If value == boxed_node.value, we don't insert (no duplicates)
                Some(boxed_node)
            }
        }
    }

    fn contains(&self, value: i32) -> bool {
        Self::contains_recursive(&self.root, value)
    }

    fn contains_recursive(node: &Option<Box<TreeNode>>, value: i32) -> bool {
        match node {
            None => false,
            Some(boxed_node) => {
                if value == boxed_node.value {
                    true
                } else if value < boxed_node.value {
                    Self::contains_recursive(&boxed_node.left, value)
                } else {
                    Self::contains_recursive(&boxed_node.right, value)
                }
            }
        }
    }

    fn inorder_traversal(&self) -> Vec<i32> {
        let mut result = Vec::with_capacity(self.size);
        Self::inorder_recursive(&self.root, &mut result);
        result
    }

    fn inorder_recursive(node: &Option<Box<TreeNode>>, result: &mut Vec<i32>) {
        if let Some(boxed_node) = node {
            Self::inorder_recursive(&boxed_node.left, result);
            result.push(boxed_node.value);
            Self::inorder_recursive(&boxed_node.right, result);
        }
    }

    fn size(&self) -> usize {
        self.size
    }
}

fn shuffle_values(values: &mut [i32]) {
    // Simple pseudo-random shuffle using a linear congruential generator
    let mut seed = 42u32;
    for i in (1..values.len()).rev() {
        seed = seed.wrapping_mul(1103515245).wrapping_add(12345);
        let j = (seed as usize) % (i + 1);
        values.swap(i, j);
    }
}

fn run_benchmark(nodes_count: usize) -> BenchmarkResult {
    let start_time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs_f64();

    let mut bst = BinarySearchTree::new();
    
    // Create shuffled values for insertion
    let mut values: Vec<i32> = (0..nodes_count as i32).collect();
    shuffle_values(&mut values);
    
    // Insert operations
    for &val in &values {
        bst.insert(val);
    }
    
    // Search operations
    let mut found_count = 0;
    let search_count = std::cmp::min(100, values.len());
    for i in 0..search_count {
        if bst.contains(values[i]) {
            found_count += 1;
        }
    }
    
    // Traversal operation
    let traversal_result = bst.inorder_traversal();
    let is_sorted = traversal_result.windows(2).all(|w| w[0] <= w[1]);
    
    let end_time = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs_f64();
    
    let execution_time = end_time - start_time;
    
    BenchmarkResult {
        start_time,
        operations: Operations {
            inserts: nodes_count,
            searches: search_count,
            found_count,
            traversal_length: traversal_result.len(),
        },
        tree_stats: TreeStats {
            final_size: bst.size(),
            is_sorted,
        },
        end_time,
        total_execution_time: execution_time,
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    
    let nodes_count = if args.len() > 1 {
        // Read from config file
        let config_file = &args[1];
        let config_content = fs::read_to_string(config_file)?;
        let config: Config = serde_json::from_str(&config_content)?;
        config.parameters.nodes_count.unwrap_or(1000)
    } else {
        // Default value
        1000
    };
    
    let result = run_benchmark(nodes_count);
    println!("{}", serde_json::to_string_pretty(&result)?);
    
    Ok(())
}