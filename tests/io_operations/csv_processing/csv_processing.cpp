#include <iostream>
#include <sstream>
#include <vector>
#include <chrono>
#include <random>
#include <string>
#include <algorithm>
#include <numeric>

class OptimizedCSVProcessor {
public:
    static std::vector<std::vector<std::string>> generateCSVData(int rows, int cols, const std::string& dataType) {
        std::vector<std::vector<std::string>> data;
        std::mt19937 gen(42);
        
        // Generate headers
        std::vector<std::string> headers;
        for (int i = 0; i < cols; i++) {
            headers.push_back("col_" + std::to_string(i + 1));
        }
        data.push_back(headers);
        
        // Generate data rows
        for (int row = 0; row < rows; row++) {
            std::vector<std::string> rowData;
            for (int col = 0; col < cols; col++) {
                std::string value;
                if (dataType == "numeric") {
                    std::uniform_real_distribution<> dis(0.0, 1000.0);
                    value = std::to_string(dis(gen));
                } else if (dataType == "text") {
                    std::uniform_int_distribution<> len_dis(5, 15);
                    int length = len_dis(gen);
                    value.reserve(length);
                    for (int i = 0; i < length; i++) {
                        value += char('a' + gen() % 26);
                    }
                } else { // mixed
                    switch (col % 3) {
                        case 0:
                            value = std::to_string(gen() % 10000 + 1);
                            break;
                        case 1:
                            value.reserve(10);
                            for (int i = 0; i < 10; i++) {
                                value += char('a' + gen() % 26);
                            }
                            break;
                        default:
                            std::uniform_real_distribution<> dis(0.0, 1000.0);
                            value = std::to_string(dis(gen));
                            break;
                    }
                }
                rowData.push_back(value);
            }
            data.push_back(rowData);
        }
        
        return data;
    }
    
    static std::string writeCSVToString(const std::vector<std::vector<std::string>>& data) {
        std::ostringstream csv;
        for (const auto& row : data) {
            for (size_t i = 0; i < row.size(); i++) {
                if (i > 0) csv << ",";
                csv << row[i];
            }
            csv << "\n";
        }
        return csv.str();
    }
    
    static std::vector<std::vector<std::string>> readCSVFromString(const std::string& csvString) {
        std::vector<std::vector<std::string>> data;
        std::istringstream stream(csvString);
        std::string line;
        
        while (std::getline(stream, line)) {
            if (line.empty()) continue;
            std::vector<std::string> row;
            std::istringstream lineStream(line);
            std::string cell;
            
            while (std::getline(lineStream, cell, ',')) {
                row.push_back(cell);
            }
            data.push_back(row);
        }
        
        return data;
    }
    
    static std::vector<std::vector<std::string>> filterCSVData(const std::vector<std::vector<std::string>>& data, int filterColumn = 0) {
        if (data.size() < 2) return data;
        
        std::vector<std::vector<std::string>> filtered;
        filtered.push_back(data[0]); // Headers
        
        for (size_t i = 1; i < data.size(); i++) {
            const auto& row = data[i];
            if (row.size() > static_cast<size_t>(filterColumn)) {
                try {
                    double value = std::stod(row[filterColumn]);
                    if (value > 500.0) {
                        filtered.push_back(row);
                    }
                } catch (...) {
                    if (row[filterColumn].length() > 5) {
                        filtered.push_back(row);
                    }
                }
            }
        }
        
        return filtered;
    }
    
    static int aggregateCSVData(const std::vector<std::vector<std::string>>& data) {
        if (data.size() < 2) return 0;
        
        const auto& headers = data[0];
        std::vector<int> numericColumns;
        
        // Find numeric columns
        for (size_t colIdx = 0; colIdx < headers.size(); colIdx++) {
            bool isNumeric = true;
            size_t checkRows = std::min(size_t(6), data.size());
            
            for (size_t rowIdx = 1; rowIdx < checkRows; rowIdx++) {
                if (colIdx < data[rowIdx].size()) {
                    try {
                        std::stod(data[rowIdx][colIdx]);
                    } catch (...) {
                        isNumeric = false;
                        break;
                    }
                }
            }
            if (isNumeric) {
                numericColumns.push_back(colIdx);
            }
        }
        
        int aggregatedColumns = 0;
        for (int colIdx : numericColumns) {
            std::vector<double> values;
            
            for (size_t i = 1; i < data.size(); i++) {
                if (colIdx < static_cast<int>(data[i].size())) {
                    try {
                        values.push_back(std::stod(data[i][colIdx]));
                    } catch (...) {
                        // Skip invalid values
                    }
                }
            }
            
            if (!values.empty()) {
                aggregatedColumns++;
                // Calculate sum, avg, min, max (but don't output to keep it fast)
                double sum = std::accumulate(values.begin(), values.end(), 0.0);
                double avg = sum / values.size();
                auto minmax = std::minmax_element(values.begin(), values.end());
            }
        }
        
        return aggregatedColumns;
    }
};

int main() {
    const int rows = 1000;
    const int cols = 5;
    const int iterations = 3;
    
    std::cout << "CSV processing benchmark" << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    std::vector<std::string> dataTypes = {"mixed"};
    std::vector<std::string> operations = {"read", "write", "filter", "aggregate"};
    
    double total_read_time = 0.0;
    double total_write_time = 0.0;
    double total_filter_time = 0.0;
    double total_aggregate_time = 0.0;
    int total_tests = 0;
    int successful_tests = 0;
    
    for (const auto& dataType : dataTypes) {
        for (int i = 0; i < iterations; i++) {
            total_tests++;
            
            // Generate CSV data
            auto csvData = OptimizedCSVProcessor::generateCSVData(rows, cols, dataType);
            
            // Write operation
            auto write_start = std::chrono::high_resolution_clock::now();
            std::string csvString = OptimizedCSVProcessor::writeCSVToString(csvData);
            auto write_end = std::chrono::high_resolution_clock::now();
            auto write_time = std::chrono::duration_cast<std::chrono::microseconds>(write_end - write_start).count() / 1000.0;
            total_write_time += write_time;
            
            // Read operation
            auto read_start = std::chrono::high_resolution_clock::now();
            auto readData = OptimizedCSVProcessor::readCSVFromString(csvString);
            auto read_end = std::chrono::high_resolution_clock::now();
            auto read_time = std::chrono::duration_cast<std::chrono::microseconds>(read_end - read_start).count() / 1000.0;
            total_read_time += read_time;
            
            // Filter operation
            auto filter_start = std::chrono::high_resolution_clock::now();
            auto filteredData = OptimizedCSVProcessor::filterCSVData(csvData);
            auto filter_end = std::chrono::high_resolution_clock::now();
            auto filter_time = std::chrono::duration_cast<std::chrono::microseconds>(filter_end - filter_start).count() / 1000.0;
            total_filter_time += filter_time;
            
            // Aggregate operation
            auto aggregate_start = std::chrono::high_resolution_clock::now();
            int aggregatedCols = OptimizedCSVProcessor::aggregateCSVData(csvData);
            auto aggregate_end = std::chrono::high_resolution_clock::now();
            auto aggregate_time = std::chrono::duration_cast<std::chrono::microseconds>(aggregate_end - aggregate_start).count() / 1000.0;
            total_aggregate_time += aggregate_time;
            
            successful_tests++;
        }
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << "Total tests: " << total_tests << std::endl;
    std::cout << "Successful tests: " << successful_tests << std::endl;
    std::cout << "Average read time: " << (total_read_time / total_tests) << " ms" << std::endl;
    std::cout << "Average write time: " << (total_write_time / total_tests) << " ms" << std::endl;
    std::cout << "Average filter time: " << (total_filter_time / total_tests) << " ms" << std::endl;
    std::cout << "Average aggregate time: " << (total_aggregate_time / total_tests) << " ms" << std::endl;
    std::cout << "Total execution time: " << duration.count() / 1000000.0 << " seconds" << std::endl;
    
    return 0;
}