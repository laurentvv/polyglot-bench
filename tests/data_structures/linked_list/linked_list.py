"""
Linked List benchmark implementation in Python.
Tests basic linked list operations: insert, search, delete.
"""

import time


class ListNode:
    """Node for linked list."""
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class LinkedList:
    """Simple linked list implementation."""
    
    def __init__(self):
        self.head = None
        self.size = 0
    
    def insert(self, val):
        """Insert value at the beginning."""
        new_node = ListNode(val)
        new_node.next = self.head
        self.head = new_node
        self.size += 1
    
    def search(self, val):
        """Search for a value in the list."""
        current = self.head
        position = 0
        while current:
            if current.val == val:
                return position
            current = current.next
            position += 1
        return -1
    
    def delete(self, val):
        """Delete first occurrence of value."""
        if not self.head:
            return False
        
        if self.head.val == val:
            self.head = self.head.next
            self.size -= 1
            return True
        
        current = self.head
        while current.next:
            if current.next.val == val:
                current.next = current.next.next
                self.size -= 1
                return True
            current = current.next
        return False
    
    def get_size(self):
        """Get the size of the list."""
        return self.size


def main():
    """Run linked list benchmark."""
    print("Starting linked list benchmark...")
    start_time = time.perf_counter()
    
    # Create linked list and perform operations
    linked_list = LinkedList()
    operations_count = 10000
    
    # Insert operations
    for i in range(operations_count):
        linked_list.insert(i)
    
    # Search operations
    found_count = 0
    for i in range(0, operations_count, 100):  # Search every 100th element
        if linked_list.search(i) != -1:
            found_count += 1
    
    # Delete operations
    deleted_count = 0
    for i in range(0, operations_count, 200):  # Delete every 200th element
        if linked_list.delete(i):
            deleted_count += 1
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    print(f"Operations completed: {operations_count} inserts, {found_count} searches, {deleted_count} deletes")
    print(f"Final list size: {linked_list.get_size()}")
    print(f"Execution time: {execution_time:.6f} seconds")


if __name__ == "__main__":
    main()