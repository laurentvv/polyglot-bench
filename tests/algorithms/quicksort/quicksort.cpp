#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <algorithm>

int partition_array(std::vector<int>& arr, int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    
    for (int j = low; j < high; j++) {
        if (arr[j] < pivot) {
            i++;
            std::swap(arr[i], arr[j]);
        }
    }
    std::swap(arr[i + 1], arr[high]);
    return i + 1;
}

void quicksort(std::vector<int>& arr, int low, int high) {
    if (low < high) {
        int pivot = partition_array(arr, low, high);
        quicksort(arr, low, pivot - 1);
        quicksort(arr, pivot + 1, high);
    }
}

int main() {
    const int size = 10000;
    std::vector<int> arr(size);
    
    // Generate test data
    for (int i = 0; i < size; i++) {
        arr[i] = i;
    }
    
    std::random_device rd;
    std::mt19937 g(rd());
    std::shuffle(arr.begin(), arr.end(), g);
    
    std::cout << "Sorting array of size " << size << "..." << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    quicksort(arr, 0, size - 1);
    auto end = std::chrono::high_resolution_clock::now();
    
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    double execution_time = duration.count() / 1000000.0;
    
    // Verify correctness
    bool is_sorted = std::is_sorted(arr.begin(), arr.end());
    
    std::cout << "Result: " << (is_sorted ? "Sorted correctly" : "Sort failed") << std::endl;
    std::cout << "Execution time: " << std::fixed << execution_time << " seconds" << std::endl;
    
    return 0;
}