use std::time::Instant;
use rand::{thread_rng, Rng};

fn create_matrix(rows: usize, cols: usize) -> Vec<Vec<f64>> {
    let mut rng = thread_rng();
    (0..rows)
        .map(|_| {
            (0..cols)
                .map(|_| rng.gen_range(0.0..100.0))
                .collect()
        })
        .collect()
}

fn multiply_matrices(a: &[Vec<f64>], b: &[Vec<f64>]) -> Vec<Vec<f64>> {
    let rows_a = a.len();
    let cols_a = a[0].len();
    let cols_b = b[0].len();
    
    let mut result = vec![vec![0.0; cols_b]; rows_a];
    
    for i in 0..rows_a {
        for j in 0..cols_b {
            for k in 0..cols_a {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    
    result
}

fn main() {
    let size = 200;  // Matrix size (200x200)
    
    println!("Multiplying two {}x{} matrices...", size, size);
    
    // Create matrices
    let create_start = Instant::now();
    let matrix_a = create_matrix(size, size);
    let matrix_b = create_matrix(size, size);
    let create_time = create_start.elapsed();
    
    // Multiply matrices
    let multiply_start = Instant::now();
    let result = multiply_matrices(&matrix_a, &matrix_b);
    let multiply_time = multiply_start.elapsed();
    
    let total_time = create_time + multiply_time;
    
    // Verify result dimensions
    let result_rows = result.len();
    let result_cols = result[0].len();
    
    println!("Result: {}x{} matrix", result_rows, result_cols);
    println!("Sample result[0][0]: {:.6}", result[0][0]);
    println!("Timing:");
    println!("  Matrix creation: {:.6} seconds", create_time.as_secs_f64());
    println!("  Matrix multiplication: {:.6} seconds", multiply_time.as_secs_f64());
    println!("  Total time: {:.6} seconds", total_time.as_secs_f64());
}