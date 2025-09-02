/**
 * Binary Tree benchmark implementation in TypeScript.
 * Tests basic binary search tree operations: insert, search, traverse.
 */

class TreeNode {
    val: number;
    left: TreeNode | null;
    right: TreeNode | null;
    
    constructor(val: number) {
        this.val = val;
        this.left = null;
        this.right = null;
    }
}

class BinarySearchTree {
    private root: TreeNode | null;
    private size: number;
    
    constructor() {
        this.root = null;
        this.size = 0;
    }
    
    insert(val: number): void {
        if (this.root === null) {
            this.root = new TreeNode(val);
            this.size++;
        } else {
            this.insertRecursive(this.root, val);
        }
    }
    
    private insertRecursive(node: TreeNode, val: number): void {
        if (val < node.val) {
            if (node.left === null) {
                node.left = new TreeNode(val);
                this.size++;
            } else {
                this.insertRecursive(node.left, val);
            }
        } else if (val > node.val) {
            if (node.right === null) {
                node.right = new TreeNode(val);
                this.size++;
            } else {
                this.insertRecursive(node.right, val);
            }
        }
        // Equal values are ignored (no duplicates)
    }
    
    search(val: number): boolean {
        return this.searchRecursive(this.root, val);
    }
    
    private searchRecursive(node: TreeNode | null, val: number): boolean {
        if (node === null) {
            return false;
        }
        if (node.val === val) {
            return true;
        } else if (val < node.val) {
            return this.searchRecursive(node.left, val);
        } else {
            return this.searchRecursive(node.right, val);
        }
    }
    
    inorderTraversal(): number[] {
        const result: number[] = [];
        this.inorderRecursive(this.root, result);
        return result;
    }
    
    private inorderRecursive(node: TreeNode | null, result: number[]): void {
        if (node !== null) {
            this.inorderRecursive(node.left, result);
            result.push(node.val);
            this.inorderRecursive(node.right, result);
        }
    }
    
    getSize(): number {
        return this.size;
    }
}

// Simple pseudo-random number generator for reproducible results
class SimpleRandom {
    private seed: number;
    
    constructor(seed: number) {
        this.seed = seed;
    }
    
    next(): number {
        this.seed = (this.seed * 1103515245 + 12345) & 0x7fffffff;
        return this.seed / 0x7fffffff;
    }
    
    shuffle<T>(array: T[]): void {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(this.next() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }
}

function isSorted(arr: number[]): boolean {
    for (let i = 1; i < arr.length; i++) {
        if (arr[i - 1] > arr[i]) {
            return false;
        }
    }
    return true;
}

function main(): void {
    console.log("Starting binary tree benchmark...");
    const startTime = process.hrtime.bigint();
    
    const bst = new BinarySearchTree();
    const nodesCount = 1000;
    
    // Create shuffled values for insertion
    const rng = new SimpleRandom(42);
    const values: number[] = [];
    for (let i = 0; i < nodesCount; i++) {
        values.push(i);
    }
    rng.shuffle(values);
    
    // Insert operations
    for (const val of values) {
        bst.insert(val);
    }
    
    // Search operations
    let foundCount = 0;
    const searchCount = Math.min(100, values.length);
    for (let i = 0; i < searchCount; i++) {
        if (bst.search(values[i])) {
            foundCount++;
        }
    }
    
    // Traversal operation
    const traversalResult = bst.inorderTraversal();
    const sorted = isSorted(traversalResult);
    
    const endTime = process.hrtime.bigint();
    const executionTime = Number(endTime - startTime) / 1e9; // Convert to seconds
    
    console.log(`Tree operations completed: ${nodesCount} inserts, ${foundCount} searches`);
    console.log(`Final tree size: ${bst.getSize()}`);
    console.log(`Inorder traversal length: ${traversalResult.length}`);
    console.log(`Traversal is sorted: ${sorted}`);
    console.log(`Execution time: ${executionTime.toFixed(6)} seconds`);
}

main();