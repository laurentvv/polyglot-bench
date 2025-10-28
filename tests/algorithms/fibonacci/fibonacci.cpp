#include <iostream>
#include <chrono>

long long fibonacci(int n) {
    if (n <= 1) return n;
    long long a = 0, b = 1;
    for (int i = 0; i < n - 1; ++i) {
        long long temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

int main() {
    int n = 35;
    
    std::cout << "Calculating fibonacci(" << n << ")..." << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    long long result = fibonacci(n);
    auto end = std::chrono::high_resolution_clock::now();
    
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    double execution_time = duration.count() / 1000000.0;
    
    std::cout << "Result: " << result << std::endl;
    std::cout << "Execution time: " << std::fixed << execution_time << " seconds" << std::endl;
    
    return 0;
}