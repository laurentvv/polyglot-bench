#include <iostream>
#include <vector>
#include <chrono>
#include <cmath>

std::vector<int> sieve_of_eratosthenes(int n) {
    if (n < 2) return {};
    
    std::vector<bool> is_prime(n + 1, true);
    is_prime[0] = is_prime[1] = false;
    
    for (int i = 2; i <= std::sqrt(n); i++) {
        if (is_prime[i]) {
            for (int j = i * i; j <= n; j += i) {
                is_prime[j] = false;
            }
        }
    }
    
    std::vector<int> primes;
    for (int i = 2; i <= n; i++) {
        if (is_prime[i]) {
            primes.push_back(i);
        }
    }
    
    return primes;
}

int main() {
    const int n = 100000;
    
    std::cout << "Finding all primes up to " << n << "..." << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    std::vector<int> primes = sieve_of_eratosthenes(n);
    auto end = std::chrono::high_resolution_clock::now();
    
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    double execution_time = duration.count() / 1000000.0;
    
    std::cout << "Result: Found " << primes.size() << " primes" << std::endl;
    if (!primes.empty()) {
        std::cout << "Largest prime: " << primes.back() << std::endl;
    }
    std::cout << "Execution time: " << std::fixed << execution_time << " seconds" << std::endl;
    
    return 0;
}