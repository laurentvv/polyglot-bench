#include <iostream>
#include <chrono>
#include <random>
#include <cmath>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

double calculate_pi_monte_carlo(int num_samples) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<> dis(0.0, 1.0);
    
    int inside_circle = 0;
    
    for (int i = 0; i < num_samples; i++) {
        double x = dis(gen);
        double y = dis(gen);
        
        if (x * x + y * y <= 1.0) {
            inside_circle++;
        }
    }
    
    return 4.0 * inside_circle / num_samples;
}

int main() {
    const int num_samples = 1000000;
    const double actual_pi = M_PI;
    
    std::cout << "Calculating pi with " << num_samples << " samples..." << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    double pi_estimate = calculate_pi_monte_carlo(num_samples);
    auto end = std::chrono::high_resolution_clock::now();
    
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    double execution_time = duration.count() / 1000000.0;
    
    double error = std::abs(pi_estimate - actual_pi);
    
    std::cout << "Result: " << std::fixed << pi_estimate << std::endl;
    std::cout << "Actual pi: " << std::fixed << actual_pi << std::endl;
    std::cout << "Error: " << std::fixed << error << std::endl;
    std::cout << "Execution time: " << std::fixed << execution_time << " seconds" << std::endl;
    
    return 0;
}