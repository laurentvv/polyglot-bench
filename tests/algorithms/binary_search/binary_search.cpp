#include <iostream>
#include <vector>
#include <chrono>
#include <random>

int binary_search(const std::vector<int>& arr, int target) {
    int left = 0, right = arr.size() - 1;
    
    while (left <= right) {
        int mid = left + (right - left) / 2;
        
        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    return -1;
}

int main() {
    const int size = 1000000;
    const int num_searches = 1000;
    
    std::vector<int> arr(size);
    for (int i = 0; i < size; i++) {
        arr[i] = i;
    }
    
    // Generate random targets
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, size - 1);
    
    std::vector<int> targets(num_searches);
    for (int i = 0; i < num_searches; i++) {
        targets[i] = dis(gen);
    }
    
    std::cout << "Performing " << num_searches << " binary searches on array of size " << size << "..." << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    int found_count = 0;
    for (int target : targets) {
        int result = binary_search(arr, target);
        if (result != -1) {
            found_count++;
        }
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    double execution_time = duration.count() / 1000000.0;
    
    std::cout << "Result: Found " << found_count << "/" << num_searches << " targets" << std::endl;
    std::cout << "Execution time: " << std::fixed << execution_time << " seconds" << std::endl;
    
    return 0;
}