#include <iostream>
#include <unordered_map>
#include <chrono>
#include <random>
#include <string>

std::string random_string(std::mt19937& gen, int length = 10) {
    const std::string chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    std::uniform_int_distribution<> dis(0, chars.size() - 1);
    
    std::string result;
    result.reserve(length);
    for (int i = 0; i < length; i++) {
        result += chars[dis(gen)];
    }
    return result;
}

int main() {
    const int num_operations = 100000;
    
    // Generate test data
    std::vector<std::string> keys(num_operations);
    std::vector<int> values(num_operations);
    
    std::mt19937 gen(42); // Fixed seed for reproducible results
    std::uniform_int_distribution<> value_dis(1, 1000000);
    
    for (int i = 0; i < num_operations; i++) {
        keys[i] = random_string(gen);
        values[i] = value_dis(gen);
    }
    
    std::cout << "Testing hash table with " << num_operations << " operations..." << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    std::unordered_map<std::string, int> hash_table;
    
    // Insert operations
    auto insert_start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < num_operations; i++) {
        hash_table[keys[i]] = values[i];
    }
    auto insert_end = std::chrono::high_resolution_clock::now();
    
    // Lookup operations
    auto lookup_start = std::chrono::high_resolution_clock::now();
    int found_count = 0;
    for (const auto& key : keys) {
        if (hash_table.find(key) != hash_table.end()) {
            found_count++;
        }
    }
    auto lookup_end = std::chrono::high_resolution_clock::now();
    
    // Delete operations
    auto delete_start = std::chrono::high_resolution_clock::now();
    int deleted_count = 0;
    for (int i = 0; i < num_operations; i += 2) {
        if (hash_table.erase(keys[i]) > 0) {
            deleted_count++;
        }
    }
    auto delete_end = std::chrono::high_resolution_clock::now();
    
    auto end = std::chrono::high_resolution_clock::now();
    
    auto insert_time = std::chrono::duration_cast<std::chrono::microseconds>(insert_end - insert_start).count() / 1000000.0;
    auto lookup_time = std::chrono::duration_cast<std::chrono::microseconds>(lookup_end - lookup_start).count() / 1000000.0;
    auto delete_time = std::chrono::duration_cast<std::chrono::microseconds>(delete_end - delete_start).count() / 1000000.0;
    auto total_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() / 1000000.0;
    
    std::cout << "Result:" << std::endl;
    std::cout << "  Inserted: " << num_operations << " items" << std::endl;
    std::cout << "  Found: " << found_count << "/" << num_operations << " items" << std::endl;
    std::cout << "  Deleted: " << deleted_count << " items" << std::endl;
    std::cout << "  Remaining: " << hash_table.size() << " items" << std::endl;
    std::cout << "Timing:" << std::endl;
    std::cout << "  Insert time: " << std::fixed << insert_time << " seconds" << std::endl;
    std::cout << "  Lookup time: " << std::fixed << lookup_time << " seconds" << std::endl;
    std::cout << "  Delete time: " << std::fixed << delete_time << " seconds" << std::endl;
    std::cout << "  Total time: " << std::fixed << total_time << " seconds" << std::endl;
    
    return 0;
}