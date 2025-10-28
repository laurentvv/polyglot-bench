#include <iostream>
#include <fstream>
#include <chrono>
#include <string>
#include <random>

void generate_test_file(const std::string& filename, size_t size_bytes) {
    std::ofstream file(filename);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis('A', 'Z');
    
    const size_t chunk_size = 8192;
    std::string chunk;
    chunk.reserve(chunk_size);
    
    for (size_t i = 0; i < chunk_size; i++) {
        chunk += static_cast<char>(dis(gen));
    }
    
    size_t bytes_written = 0;
    while (bytes_written < size_bytes) {
        size_t remaining = size_bytes - bytes_written;
        if (remaining < chunk_size) {
            file.write(chunk.c_str(), remaining);
            bytes_written += remaining;
        } else {
            file.write(chunk.c_str(), chunk_size);
            bytes_written += chunk_size;
        }
    }
}

double read_file_sequential(const std::string& filename, size_t buffer_size) {
    std::ifstream file(filename, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Cannot open file");
    }
    
    auto start = std::chrono::high_resolution_clock::now();
    
    std::string buffer(buffer_size, '\0');
    size_t total_bytes = 0;
    
    while (file.read(&buffer[0], buffer_size) || file.gcount() > 0) {
        total_bytes += file.gcount();
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    return duration.count() / 1000000.0;
}

int main() {
    const size_t file_size = 10 * 1024 * 1024; // 10MB
    const size_t buffer_size = 4096;
    const std::string filename = "test_file.txt";
    
    std::cout << "Large file read benchmark" << std::endl;
    std::cout << "File size: " << file_size / (1024 * 1024) << " MB" << std::endl;
    std::cout << "Buffer size: " << buffer_size << " bytes" << std::endl;
    
    try {
        // Generate test file
        auto gen_start = std::chrono::high_resolution_clock::now();
        generate_test_file(filename, file_size);
        auto gen_end = std::chrono::high_resolution_clock::now();
        auto gen_time = std::chrono::duration_cast<std::chrono::microseconds>(gen_end - gen_start).count() / 1000000.0;
        
        std::cout << "File generation time: " << std::fixed << gen_time << " seconds" << std::endl;
        
        // Read file
        double read_time = read_file_sequential(filename, buffer_size);
        double throughput = (file_size / (1024.0 * 1024.0)) / read_time;
        
        std::cout << "File read time: " << std::fixed << read_time << " seconds" << std::endl;
        std::cout << "Throughput: " << std::fixed << throughput << " MB/s" << std::endl;
        
        // Clean up
        std::remove(filename.c_str());
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}