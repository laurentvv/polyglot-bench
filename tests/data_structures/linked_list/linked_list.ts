/**
 * Linked List benchmark implementation in TypeScript.
 * Tests basic linked list operations: insert, search, delete.
 */

class ListNode {
    val: number;
    next: ListNode | null;
    
    constructor(val: number) {
        this.val = val;
        this.next = null;
    }
}

class LinkedList {
    private head: ListNode | null;
    private size: number;
    
    constructor() {
        this.head = null;
        this.size = 0;
    }
    
    insert(val: number): void {
        const newNode = new ListNode(val);
        newNode.next = this.head;
        this.head = newNode;
        this.size++;
    }
    
    search(val: number): number {
        let current = this.head;
        let position = 0;
        
        while (current !== null) {
            if (current.val === val) {
                return position;
            }
            current = current.next;
            position++;
        }
        return -1;
    }
    
    delete(val: number): boolean {
        if (this.head === null) {
            return false;
        }
        
        if (this.head.val === val) {
            this.head = this.head.next;
            this.size--;
            return true;
        }
        
        let current = this.head;
        while (current.next !== null) {
            if (current.next.val === val) {
                current.next = current.next.next;
                this.size--;
                return true;
            }
            current = current.next;
        }
        return false;
    }
    
    getSize(): number {
        return this.size;
    }
}

function main(): void {
    console.log("Starting linked list benchmark...");
    const startTime = process.hrtime.bigint();
    
    const linkedList = new LinkedList();
    const operationsCount = 10000;
    
    // Insert operations
    for (let i = 0; i < operationsCount; i++) {
        linkedList.insert(i);
    }
    
    // Search operations
    let foundCount = 0;
    for (let i = 0; i < operationsCount; i += 100) {
        if (linkedList.search(i) !== -1) {
            foundCount++;
        }
    }
    
    // Delete operations
    let deletedCount = 0;
    for (let i = 0; i < operationsCount; i += 200) {
        if (linkedList.delete(i)) {
            deletedCount++;
        }
    }
    
    const endTime = process.hrtime.bigint();
    const executionTime = Number(endTime - startTime) / 1e9; // Convert to seconds
    
    console.log(`Operations completed: ${operationsCount} inserts, ${foundCount} searches, ${deletedCount} deletes`);
    console.log(`Final list size: ${linkedList.getSize()}`);
    console.log(`Execution time: ${executionTime.toFixed(6)} seconds`);
}

main();