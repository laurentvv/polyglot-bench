#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <memory>
#include <unordered_map>

struct ListNode {
    int value;
    std::unique_ptr<ListNode> next;
    
    ListNode(int val) : value(val), next(nullptr) {}
};

class MemoryBenchmark {
private:
    std::random_device rd;
    std::mt19937 gen;
    std::uniform_int_distribution<> dis;

public:
    MemoryBenchmark() : gen(rd()), dis(0, 1000) {}
    
    std::vector<std::vector<int>> allocate_arrays(int size, int count) {
        std::vector<std::vector<int>> arrays;
        arrays.reserve(count);
        
        for (int i = 0; i < count; i++) {
            std::vector<int> array;
            array.reserve(size);
            for (int j = 0; j < size; j++) {
                array.push_back(dis(gen));
            }
            arrays.push_back(std::move(array));
        }
        
        return arrays;
    }
    
    std::vector<std::unique_ptr<ListNode>> allocate_linked_lists(int size, int count) {
        std::vector<std::unique_ptr<ListNode>> lists;
        lists.reserve(count);
        
        for (int i = 0; i < count; i++) {
            std::unique_ptr<ListNode> head = nullptr;
            for (int j = 0; j < size; j++) {
                auto new_node = std::make_unique<ListNode>(dis(gen));
                new_node->next = std::move(head);
                head = std::move(new_node);
            }
            lists.push_back(std::move(head));
        }
        
        return lists;
    }
    
    std::vector<std::unordered_map<int, int>> allocate_hash_maps(int size, int count) {
        std::vector<std::unordered_map<int, int>> maps;
        maps.reserve(count);
        
        for (int i = 0; i < count; i++) {
            std::unordered_map<int, int> map;
            map.reserve(size);
            for (int j = 0; j < size; j++) {
                int key = dis(gen) % (size * 2);
                int value = dis(gen);
                map[key] = value;
            }
            maps.push_back(std::move(map));
        }
        
        return maps;
    }
};

int main() {
    const int size = 1000;
    const int count = 100;
    
    std::cout << "Memory allocation benchmark" << std::endl;
    std::cout << "Size per structure: " << size << " elements" << std::endl;
    std::cout << "Number of structures: " << count << std::endl;
    
    MemoryBenchmark benchmark;
    
    // Test array allocation
    {
        std::cout << "\nTesting array allocation..." << std::endl;
        auto start = std::chrono::high_resolution_clock::now();
        
        auto arrays = benchmark.allocate_arrays(size, count);
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        double allocation_time = duration.count() / 1000.0; // ms
        
        std::cout << "Array allocation time: " << std::fixed << allocation_time << " ms" << std::endl;
        std::cout << "Arrays allocated: " << arrays.size() << std::endl;
        
        // Deallocation (automatic with RAII)
        start = std::chrono::high_resolution_clock::now();
        arrays.clear();
        end = std::chrono::high_resolution_clock::now();
        duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        double deallocation_time = duration.count() / 1000.0; // ms
        
        std::cout << "Array deallocation time: " << std::fixed << deallocation_time << " ms" << std::endl;
    }
    
    // Test linked list allocation
    {
        std::cout << "\nTesting linked list allocation..." << std::endl;
        auto start = std::chrono::high_resolution_clock::now();
        
        auto lists = benchmark.allocate_linked_lists(size, count);
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        double allocation_time = duration.count() / 1000.0; // ms
        
        std::cout << "Linked list allocation time: " << std::fixed << allocation_time << " ms" << std::endl;
        std::cout << "Lists allocated: " << lists.size() << std::endl;
        
        // Deallocation
        start = std::chrono::high_resolution_clock::now();
        lists.clear();
        end = std::chrono::high_resolution_clock::now();
        duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        double deallocation_time = duration.count() / 1000.0; // ms
        
        std::cout << "Linked list deallocation time: " << std::fixed << deallocation_time << " ms" << std::endl;
    }
    
    // Test hash map allocation
    {
        std::cout << "\nTesting hash map allocation..." << std::endl;
        auto start = std::chrono::high_resolution_clock::now();
        
        auto maps = benchmark.allocate_hash_maps(size, count);
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        double allocation_time = duration.count() / 1000.0; // ms
        
        std::cout << "Hash map allocation time: " << std::fixed << allocation_time << " ms" << std::endl;
        std::cout << "Maps allocated: " << maps.size() << std::endl;
        
        // Deallocation
        start = std::chrono::high_resolution_clock::now();
        maps.clear();
        end = std::chrono::high_resolution_clock::now();
        duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        double deallocation_time = duration.count() / 1000.0; // ms
        
        std::cout << "Hash map deallocation time: " << std::fixed << deallocation_time << " ms" << std::endl;
    }
    
    return 0;
}