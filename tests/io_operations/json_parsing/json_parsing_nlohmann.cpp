#include <iostream>
#include <string>
#include <chrono>
#include <vector>
#include <random>
#include <map>
#include <fstream>
#include <sstream>
#include <algorithm>
#include "json.hpp"

using json = nlohmann::json;

class JsonGenerator {
public:
    static json generateFlatJson(int size) {
        json obj = json::object();
        
        for (int i = 0; i < size; i++) {
            std::string key = "key_" + std::to_string(i);
            int valueType = i % 3;
            
            if (valueType == 0) {
                obj[key] = "value_" + std::to_string(i);
            } else if (valueType == 1) {
                obj[key] = i * 10 + (i % 100);
            } else {
                obj[key] = (i % 2 == 0);
            }
        }
        return obj;
    }
    
    static json generateNestedJson(int size) {
        json root = json::object();
        json level1 = json::object();
        json arrays = json::array();
        
        int itemsPerLevel = size / 3;
        for (int i = 0; i < itemsPerLevel; i++) {
            json item = json::object();
            item["id"] = i;
            item["value"] = "nested_value_" + std::to_string(i);
            item["count"] = i * 2;
            
            level1["item_" + std::to_string(i)] = item;
            
            json arrayItem = json::object();
            arrayItem["array_id"] = i;
            
            json items = json::array();
            for (int j = 0; j < std::min(5, size / itemsPerLevel); j++) {
                items.push_back("item_" + std::to_string(j));
            }
            arrayItem["items"] = items;
            arrays.push_back(arrayItem);
        }
        
        root["level1"] = level1;
        root["arrays"] = arrays;
        return root;
    }
    
    static json generateArrayHeavyJson(int size) {
        json root = json::object();
        json users = json::array();
        json products = json::array();
        json orders = json::array();
        
        int itemsPerArray = size / 3;
        std::vector<std::string> categories = {"electronics", "clothing", "books", "home"};
        
        for (int i = 0; i < itemsPerArray; i++) {
            json user = json::object();
            user["id"] = i;
            user["name"] = "User_" + std::to_string(i);
            user["email"] = "user" + std::to_string(i) + "@example.com";
            user["active"] = (i % 2 == 0);
            users.push_back(user);
            
            json product = json::object();
            product["id"] = i;
            product["name"] = "Product_" + std::to_string(i);
            product["price"] = (double(i * 1.5) / 100.0 * 500);
            product["category"] = categories[i % categories.size()];
            products.push_back(product);
            
            json order = json::object();
            order["id"] = i;
            order["user_id"] = i % itemsPerArray;
            
            json productIds = json::array();
            for (int j = 0; j < 3; j++) {
                productIds.push_back((i + j) % itemsPerArray);
            }
            order["product_ids"] = productIds;
            order["total"] = (double(i * 5.5) / 100.0 * 1000);
            order["timestamp"] = "2024-" + std::to_string((i % 12) + 1) + "-" + std::to_string((i % 28) + 1);
            orders.push_back(order);
        }
        
        root["users"] = users;
        root["products"] = products;
        root["orders"] = orders;
        return root;
    }
    
    static json generateMixedJson(int size) {
        json root = json::object();
        
        json metadata = json::object();
        metadata["version"] = "1.0";
        metadata["timestamp"] = "2024-01-01T00:00:00Z";
        metadata["total_records"] = size;
        
        json config = json::object();
        json settings = json::object();
        settings["debug"] = true;
        settings["cache_enabled"] = false;
        settings["timeout"] = 30;
        config["settings"] = settings;
        
        json data = json::array();
        
        std::vector<std::string> types = {"A", "B", "C"};
        std::vector<std::string> tags = {"urgent", "normal", "low", "critical"};
        
        for (int i = 0; i < size; i++) {
            json item = json::object();
            item["id"] = i;
            item["type"] = types[i % types.size()];
            
            json attributes = json::object();
            attributes["name"] = "Item_" + std::to_string(i);
            attributes["value"] = i % 1000;
            
            json selectedTags = json::array();
            selectedTags.push_back(tags[i % tags.size()]);
            attributes["tags"] = selectedTags;
            
            json relationships = json::array();
            json rel = json::object();
            rel["id"] = (i + 1) % size;
            rel["type"] = "related";
            relationships.push_back(rel);
            
            item["attributes"] = attributes;
            item["relationships"] = relationships;
            data.push_back(item);
        }
        
        root["metadata"] = metadata;
        root["config"] = config;
        root["data"] = data;
        return root;
    }
};

int traverseJson(const json& j) {
    int count = 1;
    if (j.is_object()) {
        for (auto& [key, value] : j.items()) {
            count += traverseJson(value);
        }
    } else if (j.is_array()) {
        for (auto& item : j) {
            count += traverseJson(item);
        }
    }
    return count;
}

struct Config {
    std::vector<int> json_sizes = {1000};
    std::vector<std::string> json_structures = {"flat"};
    std::vector<std::string> operations = {"parse"};
    int iterations = 5;
};

Config parseConfig(const std::string& filename) {
    Config config;
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Config file not found" << std::endl;
        return config;
    }
    
    std::string line;
    while (std::getline(file, line)) {
        if (line.find("\"json_sizes\"") != std::string::npos) {
            config.json_sizes = {1000, 10000, 100000};
        } else if (line.find("\"json_structures\"") != std::string::npos) {
            config.json_structures = {"flat", "nested", "array_heavy", "mixed"};
        } else if (line.find("\"operations\"") != std::string::npos) {
            config.operations = {"parse", "stringify", "traverse"};
        } else if (line.find("\"iterations\"") != std::string::npos) {
            config.iterations = 5;
        }
    }
    return config;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <config_file>" << std::endl;
        return 1;
    }
    
    Config config = parseConfig(argv[1]);
    
    auto start_time = std::chrono::system_clock::now();
    std::vector<double> all_parse_times, all_stringify_times, all_traverse_times;
    int total_tests = 0, successful_tests = 0, failed_tests = 0;
    
    for (int size : config.json_sizes) {
        for (const std::string& structure : config.json_structures) {
            std::cerr << "Testing " << structure << " JSON, size: " << size << "..." << std::endl;
            
            for (int i = 0; i < config.iterations; i++) {
                std::cerr << "  Iteration " << (i + 1) << "/" << config.iterations << "..." << std::endl;
                
                // Generate test data
                json json_data;
                if (structure == "flat") {
                    json_data = JsonGenerator::generateFlatJson(size);
                } else if (structure == "nested") {
                    json_data = JsonGenerator::generateNestedJson(size);
                } else if (structure == "array_heavy") {
                    json_data = JsonGenerator::generateArrayHeavyJson(size);
                } else {
                    json_data = JsonGenerator::generateMixedJson(size);
                }
                
                std::string json_string = json_data.dump();
                total_tests++;
                bool success = true;
                
                // Parse operation
                if (std::find(config.operations.begin(), config.operations.end(), "parse") != config.operations.end()) {
                    try {
                        auto start = std::chrono::high_resolution_clock::now();
                        json parsed = json::parse(json_string);
                        auto end = std::chrono::high_resolution_clock::now();
                        double parse_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() / 1000.0;
                        
                        all_parse_times.push_back(parse_time);
                    } catch (...) {
                        success = false;
                    }
                }
                
                // Stringify operation
                if (std::find(config.operations.begin(), config.operations.end(), "stringify") != config.operations.end()) {
                    try {
                        auto start = std::chrono::high_resolution_clock::now();
                        std::string stringified = json_data.dump();
                        auto end = std::chrono::high_resolution_clock::now();
                        double stringify_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() / 1000.0;
                        
                        all_stringify_times.push_back(stringify_time);
                    } catch (...) {
                        success = false;
                    }
                }
                
                // Traverse operation
                if (std::find(config.operations.begin(), config.operations.end(), "traverse") != config.operations.end()) {
                    try {
                        auto start = std::chrono::high_resolution_clock::now();
                        int operations_count = traverseJson(json_data);
                        auto end = std::chrono::high_resolution_clock::now();
                        double traverse_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() / 1000.0;
                        
                        all_traverse_times.push_back(traverse_time);
                    } catch (...) {
                        success = false;
                    }
                }
                
                if (success) {
                    successful_tests++;
                } else {
                    failed_tests++;
                }
            }
        }
    }
    
    // Calculate summary
    double avg_parse_time = 0, avg_stringify_time = 0, avg_traverse_time = 0;
    if (!all_parse_times.empty()) {
        double sum = 0;
        for (double t : all_parse_times) sum += t;
        avg_parse_time = sum / all_parse_times.size();
    }
    if (!all_stringify_times.empty()) {
        double sum = 0;
        for (double t : all_stringify_times) sum += t;
        avg_stringify_time = sum / all_stringify_times.size();
    }
    if (!all_traverse_times.empty()) {
        double sum = 0;
        for (double t : all_traverse_times) sum += t;
        avg_traverse_time = sum / all_traverse_times.size();
    }
    
    auto end_time = std::chrono::system_clock::now();
    auto total_execution_time = std::chrono::duration_cast<std::chrono::seconds>(end_time - start_time).count();
    
    // Output JSON results
    std::cout << "{" << std::endl;
    std::cout << "  \"start_time\": " << std::chrono::duration_cast<std::chrono::seconds>(start_time.time_since_epoch()).count() << "," << std::endl;
    std::cout << "  \"test_cases\": []," << std::endl;
    std::cout << "  \"summary\": {" << std::endl;
    std::cout << "    \"total_tests\": " << total_tests << "," << std::endl;
    std::cout << "    \"successful_tests\": " << successful_tests << "," << std::endl;
    std::cout << "    \"failed_tests\": " << failed_tests << "," << std::endl;
    std::cout << "    \"avg_parse_time\": " << avg_parse_time << "," << std::endl;
    std::cout << "    \"avg_stringify_time\": " << avg_stringify_time << "," << std::endl;
    std::cout << "    \"avg_traverse_time\": " << avg_traverse_time << std::endl;
    std::cout << "  }," << std::endl;
    std::cout << "  \"end_time\": " << std::chrono::duration_cast<std::chrono::seconds>(end_time.time_since_epoch()).count() << "," << std::endl;
    std::cout << "  \"total_execution_time\": " << total_execution_time << std::endl;
    std::cout << "}" << std::endl;
    
    return 0;
}