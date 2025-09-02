#!/usr/bin/env node

function randomString(length: number = 10): string {
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    return result;
}

function main(): void {
    const numOperations = 100000;
    
    // Generate test data
    const keys: string[] = [];
    const values: number[] = [];
    
    for (let i = 0; i < numOperations; i++) {
        keys.push(randomString(10));
        values.push(Math.floor(Math.random() * 1000000) + 1);
    }
    
    console.log(`Testing hash table with ${numOperations} operations...`);
    const totalStart = process.hrtime.bigint();
    
    // Create hash table (Map in TypeScript)
    const hashTable = new Map<string, number>();
    
    // Insert operations
    const insertStart = process.hrtime.bigint();
    for (let i = 0; i < numOperations; i++) {
        hashTable.set(keys[i], values[i]);
    }
    const insertTime = Number(process.hrtime.bigint() - insertStart) / 1e9;
    
    // Lookup operations
    const lookupStart = process.hrtime.bigint();
    let foundCount = 0;
    for (const key of keys) {
        if (hashTable.has(key)) {
            foundCount++;
        }
    }
    const lookupTime = Number(process.hrtime.bigint() - lookupStart) / 1e9;
    
    // Delete operations (every other key)
    const deleteStart = process.hrtime.bigint();
    let deletedCount = 0;
    for (let i = 0; i < numOperations; i += 2) {
        if (hashTable.has(keys[i])) {
            hashTable.delete(keys[i]);
            deletedCount++;
        }
    }
    const deleteTime = Number(process.hrtime.bigint() - deleteStart) / 1e9;
    
    const totalTime = Number(process.hrtime.bigint() - totalStart) / 1e9;
    
    console.log("Result:");
    console.log(`  Inserted: ${numOperations} items`);
    console.log(`  Found: ${foundCount}/${numOperations} items`);
    console.log(`  Deleted: ${deletedCount} items`);
    console.log(`  Remaining: ${hashTable.size} items`);
    console.log("Timing:");
    console.log(`  Insert time: ${insertTime.toFixed(6)} seconds`);
    console.log(`  Lookup time: ${lookupTime.toFixed(6)} seconds`);
    console.log(`  Delete time: ${deleteTime.toFixed(6)} seconds`);
    console.log(`  Total time: ${totalTime.toFixed(6)} seconds`);
}

main();

