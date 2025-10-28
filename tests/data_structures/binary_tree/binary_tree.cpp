#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <algorithm>

struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
};

class BinarySearchTree {
private:
    TreeNode* root;
    int size;
    
    void insertRecursive(TreeNode* node, int val) {
        if (val < node->val) {
            if (node->left == nullptr) {
                node->left = new TreeNode(val);
                size++;
            } else {
                insertRecursive(node->left, val);
            }
        } else if (val > node->val) {
            if (node->right == nullptr) {
                node->right = new TreeNode(val);
                size++;
            } else {
                insertRecursive(node->right, val);
            }
        }
    }
    
    bool searchRecursive(TreeNode* node, int val) {
        if (node == nullptr) return false;
        if (node->val == val) return true;
        if (val < node->val) return searchRecursive(node->left, val);
        return searchRecursive(node->right, val);
    }
    
    void inorderRecursive(TreeNode* node, std::vector<int>& result) {
        if (node != nullptr) {
            inorderRecursive(node->left, result);
            result.push_back(node->val);
            inorderRecursive(node->right, result);
        }
    }
    
    void destroyTree(TreeNode* node) {
        if (node != nullptr) {
            destroyTree(node->left);
            destroyTree(node->right);
            delete node;
        }
    }

public:
    BinarySearchTree() : root(nullptr), size(0) {}
    
    ~BinarySearchTree() {
        destroyTree(root);
    }
    
    void insert(int val) {
        if (root == nullptr) {
            root = new TreeNode(val);
            size++;
        } else {
            insertRecursive(root, val);
        }
    }
    
    bool search(int val) {
        return searchRecursive(root, val);
    }
    
    std::vector<int> inorderTraversal() {
        std::vector<int> result;
        inorderRecursive(root, result);
        return result;
    }
    
    int getSize() const {
        return size;
    }
};

int main() {
    std::cout << "Starting binary tree benchmark..." << std::endl;
    
    auto start = std::chrono::high_resolution_clock::now();
    
    BinarySearchTree bst;
    
    // Insert operations
    const int nodes_count = 1000;
    std::vector<int> values(nodes_count);
    for (int i = 0; i < nodes_count; i++) {
        values[i] = i;
    }
    
    std::random_device rd;
    std::mt19937 g(42); // Fixed seed for reproducible results
    std::shuffle(values.begin(), values.end(), g);
    
    for (int val : values) {
        bst.insert(val);
    }
    
    // Search operations
    int found_count = 0;
    int search_count = std::min(100, (int)values.size());
    
    for (int i = 0; i < search_count; i++) {
        if (bst.search(values[i])) {
            found_count++;
        }
    }
    
    // Traversal operation
    std::vector<int> traversal_result = bst.inorderTraversal();
    bool is_sorted = std::is_sorted(traversal_result.begin(), traversal_result.end());
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    double execution_time = duration.count() / 1000000.0;
    
    std::cout << "Tree operations completed: " << nodes_count << " inserts, " 
              << found_count << " searches" << std::endl;
    std::cout << "Final tree size: " << bst.getSize() << std::endl;
    std::cout << "Inorder traversal length: " << traversal_result.size() << std::endl;
    std::cout << "Traversal is sorted: " << (is_sorted ? "true" : "false") << std::endl;
    std::cout << "Execution time: " << std::fixed << execution_time << " seconds" << std::endl;
    
    return 0;
}