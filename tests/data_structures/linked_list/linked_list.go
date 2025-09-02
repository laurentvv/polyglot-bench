// Linked List benchmark implementation in Go.
// Tests basic linked list operations: insert, search, delete.

package main

import (
	"fmt"
	"time"
)

// ListNode represents a node in the linked list
type ListNode struct {
	Val  int
	Next *ListNode
}

// LinkedList represents a linked list
type LinkedList struct {
	Head *ListNode
	Size int
}

// NewLinkedList creates a new linked list
func NewLinkedList() *LinkedList {
	return &LinkedList{Head: nil, Size: 0}
}

// Insert adds a value at the beginning of the list
func (ll *LinkedList) Insert(val int) {
	newNode := &ListNode{Val: val, Next: ll.Head}
	ll.Head = newNode
	ll.Size++
}

// Search finds a value in the list and returns its position
func (ll *LinkedList) Search(val int) int {
	current := ll.Head
	position := 0
	
	for current != nil {
		if current.Val == val {
			return position
		}
		current = current.Next
		position++
	}
	return -1
}

// Delete removes the first occurrence of a value
func (ll *LinkedList) Delete(val int) bool {
	if ll.Head == nil {
		return false
	}
	
	if ll.Head.Val == val {
		ll.Head = ll.Head.Next
		ll.Size--
		return true
	}
	
	current := ll.Head
	for current.Next != nil {
		if current.Next.Val == val {
			current.Next = current.Next.Next
			ll.Size--
			return true
		}
		current = current.Next
	}
	return false
}

// GetSize returns the size of the list
func (ll *LinkedList) GetSize() int {
	return ll.Size
}

func main() {
	fmt.Println("Starting linked list benchmark...")
	startTime := time.Now()
	
	linkedList := NewLinkedList()
	operationsCount := 10000
	
	// Insert operations
	for i := 0; i < operationsCount; i++ {
		linkedList.Insert(i)
	}
	
	// Search operations
	foundCount := 0
	for i := 0; i < operationsCount; i += 100 {
		if linkedList.Search(i) != -1 {
			foundCount++
		}
	}
	
	// Delete operations
	deletedCount := 0
	for i := 0; i < operationsCount; i += 200 {
		if linkedList.Delete(i) {
			deletedCount++
		}
	}
	
	executionTime := time.Since(startTime)
	
	fmt.Printf("Operations completed: %d inserts, %d searches, %d deletes\n", 
		operationsCount, foundCount, deletedCount)
	fmt.Printf("Final list size: %d\n", linkedList.GetSize())
	fmt.Printf("Execution time: %.6f seconds\n", executionTime.Seconds())
}