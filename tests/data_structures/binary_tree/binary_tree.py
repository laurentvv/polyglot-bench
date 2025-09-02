"""
Binary Tree benchmark implementation in Python.
Tests basic binary search tree operations: insert, search, traverse.
"""

import time


class TreeNode:
    """Node for binary tree."""
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class BinarySearchTree:
    """Binary search tree implementation."""
    
    def __init__(self):
        self.root = None
        self.size = 0
    
    def insert(self, val):
        """Insert a value into the tree."""
        if self.root is None:
            self.root = TreeNode(val)
            self.size += 1
        else:
            self._insert_recursive(self.root, val)
    
    def _insert_recursive(self, node, val):
        """Recursively insert a value."""
        if val < node.val:
            if node.left is None:
                node.left = TreeNode(val)
                self.size += 1
            else:
                self._insert_recursive(node.left, val)
        elif val > node.val:
            if node.right is None:
                node.right = TreeNode(val)
                self.size += 1
            else:
                self._insert_recursive(node.right, val)
        # Equal values are ignored (no duplicates)
    
    def search(self, val):
        """Search for a value in the tree."""
        return self._search_recursive(self.root, val)
    
    def _search_recursive(self, node, val):
        """Recursively search for a value."""
        if node is None:
            return False
        if node.val == val:
            return True
        elif val < node.val:
            return self._search_recursive(node.left, val)
        else:
            return self._search_recursive(node.right, val)
    
    def inorder_traversal(self):
        """Perform inorder traversal."""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node, result):
        """Recursively perform inorder traversal."""
        if node is not None:
            self._inorder_recursive(node.left, result)
            result.append(node.val)
            self._inorder_recursive(node.right, result)
    
    def get_size(self):
        """Get the size of the tree."""
        return self.size


def main():
    """Run binary tree benchmark."""
    print("Starting binary tree benchmark...")
    start_time = time.perf_counter()
    
    # Create binary search tree
    bst = BinarySearchTree()
    
    # Insert operations with a larger dataset
    nodes_count = 1000
    import random
    random.seed(42)  # For reproducible results
    values = list(range(nodes_count))
    random.shuffle(values)
    
    for val in values:
        bst.insert(val)
    
    # Search operations
    found_count = 0
    search_values = random.sample(values, min(100, len(values)))
    for val in search_values:
        if bst.search(val):
            found_count += 1
    
    # Traversal operation
    traversal_result = bst.inorder_traversal()
    is_sorted = all(traversal_result[i] <= traversal_result[i + 1] 
                   for i in range(len(traversal_result) - 1))
    
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    
    print(f"Tree operations completed: {nodes_count} inserts, {found_count} searches")
    print(f"Final tree size: {bst.get_size()}")
    print(f"Inorder traversal length: {len(traversal_result)}")
    print(f"Traversal is sorted: {is_sorted}")
    print(f"Execution time: {execution_time:.6f} seconds")


if __name__ == "__main__":
    main()