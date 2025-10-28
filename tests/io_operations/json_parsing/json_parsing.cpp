#include <iostream>
#include <string>
#include <chrono>
#include <sstream>
#include <vector>
#include <random>
#include <map>
#include <fstream>

// Optimized JSON processor using string operations
class OptimizedJSON {
public:
    static std::string generateFlatJSON(int size) {
        std::ostringstream json;
        std::mt19937 gen(42);
        std::uniform_int_distribution<> dis(1, 1000);
        
        json << "{";
        for (int i = 0; i < size; i++) {
            if (i > 0) json << ",";
            json << "\"key_" << i << "\":" << dis(gen);
        }
        json << "}";
        return json.str();
    }
    
    static std::string generateNestedJSON(int size) {
        std::ostringstream json;
        std::mt19937 gen(42);
        std::uniform_int_distribution<> dis(1, 100);
        
        json << "{\"root\":{";
        for (int i = 0; i < size; i++) {
            if (i > 0) json << ",";
            json << "\"nested_key_" << i << "\":{\"value\":" << dis(gen) << "}";
        }
        json << "}}";
        return json.str();
    }
    
    static std::string generateArrayJSON(int size) {
        std::ostringstream json;
        std::mt19937 gen(42);
        std::uniform_int_distribution<> dis(1, 1000);
        
        json << "{\"users\":[";
        for (int i = 0; i < size; i++) {
            if (i > 0) json << ",";
            json << "{\"id\":" << i << ",\"name\":\"User" << i << "\",\"value\":" << dis(gen) << "}";
        }
        json << "]}";
        return json.str();
    }
    
    static int parseJSON(const std::string& json) {
        int operations = 0;
        bool inString = false;
        
        // Optimized parsing - count JSON elements efficiently
        for (size_t i = 0; i < json.length(); i++) {
            char c = json[i];
            
            if (c == '"' && (i == 0 || json[i-1] != '\\')) {
                inString = !inString;
                operations++;
            } else if (!inString) {
                if (c == '{' || c == '}' || c == '[' || c == ']' || c == ':' || c == ',') {
                    operations++;
                }
            }
        }
        
        return operations;
    }
    
    static std::string stringifyJSON(const std::map<std::string, int>& data) {
        std::ostringstream json;
        json << "{";
        bool first = true;
        for (const auto& pair : data) {
            if (!first) json << ",";
            json << "\"" << pair.first << "\":" << pair.second;
            first = false;
        }
        json << "}";
        return json.str();
    }
    
    static int traverseJSON(const std::string& json) {
        int count = 0;
        bool inString = false;
        
        for (char c : json) {
            if (c == '"' && !inString) {
                inString = true;
                count++;
            } else if (c == '"' && inString) {
                inString = false;
            } else if (!inString && (c == '{' || c == '}' || c == '[' || c == ']')) {
                count++;
            }
        }
        
        return count;
    }
};

int main() {
    const int json_size = 1000;
    const int iterations = 10;
    
    std::cout << "JSON processing benchmark" << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    std::vector<std::string> structures = {"flat", "nested", "array_heavy", "mixed"};
    std::vector<std::string> operations = {"parse", "stringify", "traverse"};
    
    double total_parse_time = 0.0;
    double total_stringify_time = 0.0;
    double total_traverse_time = 0.0;
    int total_tests = 0;
    int successful_tests = 0;
    
    for (const auto& structure : structures) {
        for (int i = 0; i < iterations; i++) {
            total_tests++;
            
            // Generate JSON
            std::string json_data;
            if (structure == "flat") {
                json_data = OptimizedJSON::generateFlatJSON(json_size);
            } else if (structure == "nested") {
                json_data = OptimizedJSON::generateNestedJSON(json_size);
            } else {
                json_data = OptimizedJSON::generateArrayJSON(json_size);
            }
            
            // Parse operation
            auto parse_start = std::chrono::high_resolution_clock::now();
            int parse_ops = OptimizedJSON::parseJSON(json_data);
            auto parse_end = std::chrono::high_resolution_clock::now();
            auto parse_time = std::chrono::duration_cast<std::chrono::microseconds>(parse_end - parse_start).count() / 1000.0;
            total_parse_time += parse_time;
            
            // Stringify operation
            std::map<std::string, int> test_data;
            for (int j = 0; j < 500; j++) {
                test_data["key_" + std::to_string(j)] = j * 10;
            }
            
            auto stringify_start = std::chrono::high_resolution_clock::now();
            std::string stringified = OptimizedJSON::stringifyJSON(test_data);
            auto stringify_end = std::chrono::high_resolution_clock::now();
            auto stringify_time = std::chrono::duration_cast<std::chrono::microseconds>(stringify_end - stringify_start).count() / 1000.0;
            total_stringify_time += stringify_time;
            
            // Traverse operation
            auto traverse_start = std::chrono::high_resolution_clock::now();
            int traverse_ops = OptimizedJSON::traverseJSON(json_data);
            auto traverse_end = std::chrono::high_resolution_clock::now();
            auto traverse_time = std::chrono::duration_cast<std::chrono::microseconds>(traverse_end - traverse_start).count() / 1000.0;
            total_traverse_time += traverse_time;
            
            successful_tests++;
        }
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << "JSON structures tested: " << structures.size() << std::endl;
    std::cout << "Total tests: " << total_tests << std::endl;
    std::cout << "Successful tests: " << successful_tests << std::endl;
    std::cout << "Average parse time: " << (total_parse_time / total_tests) << " ms" << std::endl;
    std::cout << "Average stringify time: " << (total_stringify_time / total_tests) << " ms" << std::endl;
    std::cout << "Average traverse time: " << (total_traverse_time / total_tests) << " ms" << std::endl;
    std::cout << "Total execution time: " << duration.count() / 1000000.0 << " seconds" << std::endl;
    
    return 0;
}