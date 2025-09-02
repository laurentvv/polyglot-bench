// Binary Tree benchmark implementation in Go.
// Tests basic binary search tree operations: insert, search, traverse.

package main

import (
	"fmt"
	"math/rand"
	"time"
)

// TreeNode represents a node in the binary tree
type TreeNode struct {
	Val   int
	Left  *TreeNode
	Right *TreeNode
}

// BinarySearchTree represents a binary search tree
type BinarySearchTree struct {
	Root *TreeNode
	Size int
}

// NewBinarySearchTree creates a new binary search tree
func NewBinarySearchTree() *BinarySearchTree {
	return &BinarySearchTree{Root: nil, Size: 0}
}

// Insert adds a value to the tree
func (bst *BinarySearchTree) Insert(val int) {
	if bst.Root == nil {
		bst.Root = &TreeNode{Val: val}
		bst.Size++
	} else {
		bst.insertRecursive(bst.Root, val)
	}
}

func (bst *BinarySearchTree) insertRecursive(node *TreeNode, val int) {
	if val < node.Val {
		if node.Left == nil {
			node.Left = &TreeNode{Val: val}
			bst.Size++
		} else {
			bst.insertRecursive(node.Left, val)
		}
	} else if val > node.Val {
		if node.Right == nil {
			node.Right = &TreeNode{Val: val}
			bst.Size++
		} else {
			bst.insertRecursive(node.Right, val)
		}
	}
	// Equal values are ignored (no duplicates)
}

// Search finds a value in the tree
func (bst *BinarySearchTree) Search(val int) bool {
	return bst.searchRecursive(bst.Root, val)
}

func (bst *BinarySearchTree) searchRecursive(node *TreeNode, val int) bool {
	if node == nil {
		return false
	}
	if node.Val == val {
		return true
	} else if val < node.Val {
		return bst.searchRecursive(node.Left, val)
	} else {
		return bst.searchRecursive(node.Right, val)
	}
}

// InorderTraversal performs inorder traversal of the tree
func (bst *BinarySearchTree) InorderTraversal() []int {
	var result []int
	bst.inorderRecursive(bst.Root, &result)
	return result
}

func (bst *BinarySearchTree) inorderRecursive(node *TreeNode, result *[]int) {
	if node != nil {
		bst.inorderRecursive(node.Left, result)
		*result = append(*result, node.Val)
		bst.inorderRecursive(node.Right, result)
	}
}

// GetSize returns the size of the tree
func (bst *BinarySearchTree) GetSize() int {
	return bst.Size
}

// isSorted checks if a slice is sorted
func isSorted(arr []int) bool {
	for i := 1; i < len(arr); i++ {
		if arr[i-1] > arr[i] {
			return false
		}
	}
	return true
}

func main() {
	fmt.Println("Starting binary tree benchmark...")
	startTime := time.Now()
	
	bst := NewBinarySearchTree()
	nodesCount := 1000
	
	// Create shuffled values for insertion
	rand.Seed(42) // For reproducible results
	values := make([]int, nodesCount)
	for i := 0; i < nodesCount; i++ {
		values[i] = i
	}
	rand.Shuffle(len(values), func(i, j int) {
		values[i], values[j] = values[j], values[i]
	})
	
	// Insert operations
	for _, val := range values {
		bst.Insert(val)
	}
	
	// Search operations
	foundCount := 0
	searchCount := 100
	if searchCount > len(values) {
		searchCount = len(values)
	}
	
	for i := 0; i < searchCount; i++ {
		if bst.Search(values[i]) {
			foundCount++
		}
	}
	
	// Traversal operation
	traversalResult := bst.InorderTraversal()
	sorted := isSorted(traversalResult)
	
	executionTime := time.Since(startTime)
	
	fmt.Printf("Tree operations completed: %d inserts, %d searches\n", 
		nodesCount, foundCount)
	fmt.Printf("Final tree size: %d\n", bst.GetSize())
	fmt.Printf("Inorder traversal length: %d\n", len(traversalResult))
	fmt.Printf("Traversal is sorted: %t\n", sorted)
	fmt.Printf("Execution time: %.6f seconds\n", executionTime.Seconds())
}