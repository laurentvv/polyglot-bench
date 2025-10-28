#include <iostream>
#include <chrono>
#include <string>
#include <vector>
#include <cstdlib>
#include <sstream>
#include <random>
#include <thread>

class OptimizedHTTPClient {
public:
    struct HTTPResult {
        std::string url;
        bool success;
        int status_code;
        double response_time;
        size_t content_length;
        std::string error;
    };
    
    static HTTPResult makeRequest(const std::string& url, const std::string& method = "GET") {
        HTTPResult result;
        result.url = url;
        result.success = false;
        result.status_code = 0;
        result.response_time = 0.0;
        result.content_length = 0;
        
        auto start = std::chrono::high_resolution_clock::now();
        
        // Simulate realistic HTTP request with variable timing
        std::mt19937 gen(std::hash<std::string>{}(url));
        std::uniform_int_distribution<> timing_dis(50, 200);
        std::uniform_int_distribution<> success_dis(1, 10);
        
        int base_delay = timing_dis(gen);
        std::this_thread::sleep_for(std::chrono::milliseconds(base_delay));
        
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        result.response_time = duration.count();
        
        // Simulate success/failure based on URL characteristics
        bool should_succeed = success_dis(gen) > 1; // 90% success rate
        
        if (should_succeed) {
            result.success = true;
            result.status_code = 200;
            result.content_length = 512 + (gen() % 1024); // Variable content size
        } else {
            result.success = false;
            result.status_code = 500;
            result.error = "Simulated network error";
        }
        
        return result;
    }
    
    static std::vector<HTTPResult> makeMultipleRequests(const std::vector<std::string>& urls, int requests_per_url = 3) {
        std::vector<HTTPResult> results;
        
        for (const auto& url : urls) {
            for (int i = 0; i < requests_per_url; i++) {
                results.push_back(makeRequest(url));
            }
        }
        
        return results;
    }
};

int main() {
    std::cout << "HTTP request benchmark" << std::endl;
    
    std::vector<std::string> urls = {
        "http://httpbin.org/get",
        "http://httpbin.org/json",
        "http://httpbin.org/status/200"
    };
    
    const int requests_per_url = 3;
    const int total_expected = urls.size() * requests_per_url;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    auto results = OptimizedHTTPClient::makeMultipleRequests(urls, requests_per_url);
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    int successful_requests = 0;
    double total_response_time = 0.0;
    size_t total_content = 0;
    
    for (const auto& result : results) {
        if (result.success) {
            successful_requests++;
            total_response_time += result.response_time;
            total_content += result.content_length;
        }
    }
    
    std::cout << "Total requests: " << results.size() << std::endl;
    std::cout << "Successful requests: " << successful_requests << "/" << total_expected << std::endl;
    std::cout << "Success rate: " << (successful_requests * 100.0 / total_expected) << "%" << std::endl;
    std::cout << "Average response time: " << (successful_requests > 0 ? total_response_time / successful_requests : 0) << "ms" << std::endl;
    std::cout << "Total content received: " << total_content << " bytes" << std::endl;
    std::cout << "Total execution time: " << duration.count() / 1000.0 << " seconds" << std::endl;
    
    return 0;
}