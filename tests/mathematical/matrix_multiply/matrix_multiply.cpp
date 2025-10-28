#include <iostream>
#include <vector>
#include <chrono>
#include <random>

std::vector<std::vector<double>> create_matrix(int rows, int cols) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(0.0, 100.0);
    
    std::vector<std::vector<double>> matrix(rows, std::vector<double>(cols));
    
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            matrix[i][j] = dis(gen);
        }
    }
    
    return matrix;
}

std::vector<std::vector<double>> multiply_matrices(
    const std::vector<std::vector<double>>& a,
    const std::vector<std::vector<double>>& b) {
    
    int rows_a = a.size();
    int cols_a = a[0].size();
    int cols_b = b[0].size();
    
    std::vector<std::vector<double>> result(rows_a, std::vector<double>(cols_b, 0.0));
    
    for (int i = 0; i < rows_a; i++) {
        for (int j = 0; j < cols_b; j++) {
            for (int k = 0; k < cols_a; k++) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    
    return result;
}

int main() {
    const int size = 200;
    
    std::cout << "Multiplying two " << size << "x" << size << " matrices..." << std::endl;
    
    // Create matrices
    auto create_start = std::chrono::high_resolution_clock::now();
    auto matrix_a = create_matrix(size, size);
    auto matrix_b = create_matrix(size, size);
    auto create_end = std::chrono::high_resolution_clock::now();
    
    // Multiply matrices
    auto multiply_start = std::chrono::high_resolution_clock::now();
    auto result = multiply_matrices(matrix_a, matrix_b);
    auto multiply_end = std::chrono::high_resolution_clock::now();
    
    auto create_time = std::chrono::duration_cast<std::chrono::microseconds>(create_end - create_start).count() / 1000000.0;
    auto multiply_time = std::chrono::duration_cast<std::chrono::microseconds>(multiply_end - multiply_start).count() / 1000000.0;
    auto total_time = create_time + multiply_time;
    
    std::cout << "Result: " << result.size() << "x" << result[0].size() << " matrix" << std::endl;
    std::cout << "Sample result[0][0]: " << std::fixed << result[0][0] << std::endl;
    std::cout << "Timing:" << std::endl;
    std::cout << "  Matrix creation: " << std::fixed << create_time << " seconds" << std::endl;
    std::cout << "  Matrix multiplication: " << std::fixed << multiply_time << " seconds" << std::endl;
    std::cout << "  Total time: " << std::fixed << total_time << " seconds" << std::endl;
    
    return 0;
}