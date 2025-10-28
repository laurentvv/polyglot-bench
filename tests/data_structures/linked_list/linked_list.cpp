#include <iostream>
#include <chrono>
#include <random>

struct ListNode {
    int data;
    ListNode* next;
    ListNode(int val) : data(val), next(nullptr) {}
};

class LinkedList {
private:
    ListNode* head;
    int size;

public:
    LinkedList() : head(nullptr), size(0) {}
    
    ~LinkedList() {
        while (head) {
            ListNode* temp = head;
            head = head->next;
            delete temp;
        }
    }
    
    void insert(int val) {
        ListNode* newNode = new ListNode(val);
        newNode->next = head;
        head = newNode;
        size++;
    }
    
    bool search(int val) {
        ListNode* current = head;
        while (current) {
            if (current->data == val) return true;
            current = current->next;
        }
        return false;
    }
    
    bool remove(int val) {
        if (!head) return false;
        
        if (head->data == val) {
            ListNode* temp = head;
            head = head->next;
            delete temp;
            size--;
            return true;
        }
        
        ListNode* current = head;
        while (current->next && current->next->data != val) {
            current = current->next;
        }
        
        if (current->next) {
            ListNode* temp = current->next;
            current->next = current->next->next;
            delete temp;
            size--;
            return true;
        }
        return false;
    }
    
    int getSize() const { return size; }
};

int main() {
    const int operations = 10000;
    LinkedList list;
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, operations);
    
    auto start = std::chrono::high_resolution_clock::now();
    
    // Insert operations
    for (int i = 0; i < operations; i++) {
        list.insert(dis(gen));
    }
    
    // Search operations
    int found = 0;
    for (int i = 0; i < 1000; i++) {
        if (list.search(dis(gen))) found++;
    }
    
    // Delete operations
    int deleted = 0;
    for (int i = 0; i < 500; i++) {
        if (list.remove(dis(gen))) deleted++;
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << "Linked list operations completed" << std::endl;
    std::cout << "Final size: " << list.getSize() << std::endl;
    std::cout << "Found: " << found << ", Deleted: " << deleted << std::endl;
    std::cout << "Execution time: " << duration.count() / 1000000.0 << " seconds" << std::endl;
    
    return 0;
}