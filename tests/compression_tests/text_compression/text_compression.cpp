#include <iostream>
#include <string>
#include <chrono>
#include <unordered_map>
#include <vector>

class TextCompressor {
public:
    // Simple run-length encoding
    static std::string compress(const std::string& text) {
        if (text.empty()) return "";
        
        std::string compressed;
        // In worst case, RLE can double the size (e.g. "abcdef" -> "a1b1c1d1e1f1")
        compressed.reserve(text.size() * 2);

        char current = text[0];
        int count = 1;
        
        for (size_t i = 1; i < text.size(); i++) {
            if (text[i] == current) {
                count++;
            } else {
                compressed += current;
                compressed += std::to_string(count);
                current = text[i];
                count = 1;
            }
        }
        compressed += current;
        compressed += std::to_string(count);
        
        return compressed;
    }
    
    // Simple dictionary compression
    static std::string dictionaryCompress(const std::string& text) {
        std::unordered_map<std::string, int> dictionary;
        std::string compressed;
        // Estimate compressed size to reduce reallocations
        compressed.reserve(text.size());

        int dictIndex = 0;
        
        for (size_t i = 0; i < text.length(); i += 3) {
            std::string chunk = text.substr(i, 3);
            if (dictionary.find(chunk) == dictionary.end()) {
                dictionary[chunk] = dictIndex++;
            }
            compressed += std::to_string(dictionary[chunk]);
            compressed += ' ';
        }
        
        return compressed;
    }
    
    static std::string generateTestText(int size) {
        std::string text;
        text.reserve(size);
        
        const std::string pattern = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        for (int i = 0; i < size; i++) {
            text += pattern[i % pattern.length()];
            if (i % 10 == 9) text += ' '; // Add spaces
        }
        
        return text;
    }
};

int main() {
    const int text_size = 10000;
    
    std::cout << "Text compression benchmark" << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    // Generate test text
    std::string original_text = TextCompressor::generateTestText(text_size);
    
    // Run-length encoding
    std::string rle_compressed = TextCompressor::compress(original_text);
    
    // Dictionary compression
    std::string dict_compressed = TextCompressor::dictionaryCompress(original_text);
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    double rle_ratio = (double)original_text.length() / rle_compressed.length();
    double dict_ratio = (double)original_text.length() / dict_compressed.length();
    
    std::cout << "Original size: " << original_text.length() << " bytes" << std::endl;
    std::cout << "RLE compressed: " << rle_compressed.length() << " bytes (ratio: " << rle_ratio << ")" << std::endl;
    std::cout << "Dict compressed: " << dict_compressed.length() << " bytes (ratio: " << dict_ratio << ")" << std::endl;
    std::cout << "Execution time: " << duration.count() / 1000000.0 << " seconds" << std::endl;
    
    return 0;
}