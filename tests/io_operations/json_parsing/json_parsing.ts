#!/usr/bin/env node

import * as fs from 'fs';

interface OperationResult {
    success: boolean;
    time_ms?: number;
    json_string_length?: number;
    output_length?: number;
    operations_count?: number;
    error?: string;
}

interface IterationResult {
    iteration: number;
    data_size: number;
    operations: Record<string, OperationResult>;
}

interface TestCase {
    json_size: number;
    structure_type: string;
    operations: string[];
    iterations: IterationResult[];
    avg_parse_time: number;
    avg_stringify_time: number;
    avg_traverse_time: number;
}

interface Summary {
    total_tests: number;
    successful_tests: number;
    failed_tests: number;
    avg_parse_time: number;
    avg_stringify_time: number;
    avg_traverse_time: number;
}

interface BenchmarkResult {
    start_time: number;
    test_cases: TestCase[];
    summary: Summary;
    end_time: number;
    total_execution_time: number;
}

interface Config {
    parameters: {
        json_sizes?: number[];
        json_structures?: string[];
        operations?: string[];
        iterations?: number;
    };
}

function generateFlatJson(size: number): Record<string, any> {
    const data: Record<string, any> = {};
    
    for (let i = 0; i < size; i++) {
        const key = `key_${i}`;
        const valueType = Math.floor(Math.random() * 3);
        
        switch (valueType) {
            case 0:
                data[key] = `value_${Math.floor(Math.random() * 1000)}`;
                break;
            case 1:
                data[key] = Math.floor(Math.random() * 1000) + 1;
                break;
            default:
                data[key] = Math.random() < 0.5;
                break;
        }
    }
    
    return data;
}

function generateNestedJson(size: number, maxDepth: number = 5): Record<string, any> {
    function createNestedObject(remainingSize: number, currentDepth: number): any {
        if (remainingSize <= 0 || currentDepth >= maxDepth) {
            const choice = Math.floor(Math.random() * 3);
            switch (choice) {
                case 0:
                    return `leaf_${Math.floor(Math.random() * 100)}`;
                case 1:
                    return Math.floor(Math.random() * 100) + 1;
                default:
                    return Math.random() < 0.5;
            }
        }
        
        if (Math.random() < 0.6) {
            // Create object
            const obj: Record<string, any> = {};
            const keysCount = Math.min(Math.floor(Math.random() * 4) + 2, remainingSize);
            const remainingPerKey = Math.floor(remainingSize / keysCount);
            
            for (let i = 0; i < keysCount; i++) {
                const key = `nested_key_${i}`;
                obj[key] = createNestedObject(remainingPerKey, currentDepth + 1);
            }
            return obj;
        } else {
            // Create array
            const itemsCount = Math.min(Math.floor(Math.random() * 3) + 2, remainingSize);
            const remainingPerItem = Math.floor(remainingSize / itemsCount);
            
            const arr: any[] = [];
            for (let i = 0; i < itemsCount; i++) {
                arr.push(createNestedObject(remainingPerItem, currentDepth + 1));
            }
            return arr;
        }
    }
    
    return {
        root: createNestedObject(size, 0)
    };
}

function generateArrayHeavyJson(size: number): Record<string, any> {
    const itemsPerArray = Math.floor(size / 3);
    const categories = ['electronics', 'clothing', 'books', 'home'];
    
    const users: any[] = [];
    for (let i = 0; i < itemsPerArray; i++) {
        users.push({
            id: i,
            name: `User_${i}`,
            email: `user${i}@example.com`,
            active: Math.random() < 0.5
        });
    }
    
    const products: any[] = [];
    for (let i = 0; i < itemsPerArray; i++) {
        const price = Math.round((Math.random() * 490 + 10) * 100) / 100;
        products.push({
            id: i,
            name: `Product_${i}`,
            price: price,
            category: categories[Math.floor(Math.random() * categories.length)]
        });
    }
    
    const orders: any[] = [];
    for (let i = 0; i < itemsPerArray; i++) {
        const productCount = Math.floor(Math.random() * 5) + 1;
        const productIds: number[] = [];
        for (let j = 0; j < productCount; j++) {
            productIds.push(Math.floor(Math.random() * itemsPerArray));
        }
        
        const total = Math.round((Math.random() * 980 + 20) * 100) / 100;
        orders.push({
            id: i,
            user_id: Math.floor(Math.random() * itemsPerArray),
            product_ids: productIds,
            total: total,
            timestamp: `2024-${String(Math.floor(Math.random() * 12) + 1).padStart(2, '0')}-${String(Math.floor(Math.random() * 28) + 1).padStart(2, '0')}`
        });
    }
    
    return {
        users: users,
        products: products,
        orders: orders
    };
}

function generateMixedJson(size: number): Record<string, any> {
    const types = ['A', 'B', 'C'];
    const tags = ['urgent', 'normal', 'low', 'critical'];
    
    const data: any[] = [];
    
    for (let i = 0; i < size; i++) {
        const recordType = types[Math.floor(Math.random() * types.length)];
        
        // Select random tags
        const tagCount = Math.floor(Math.random() * 2) + 1;
        const selectedTags: string[] = [];
        for (let j = 0; j < tagCount; j++) {
            selectedTags.push(tags[Math.floor(Math.random() * tags.length)]);
        }
        
        // Create relationships
        const relationshipCount = Math.floor(Math.random() * 4);
        const relationships: any[] = [];
        for (let j = 0; j < relationshipCount; j++) {
            relationships.push({
                id: Math.floor(Math.random() * size),
                type: 'related'
            });
        }
        
        data.push({
            id: i,
            type: recordType,
            attributes: {
                name: `Item_${i}`,
                value: Math.floor(Math.random() * 1000) + 1,
                tags: selectedTags
            },
            relationships: relationships
        });
    }
    
    return {
        metadata: {
            version: '1.0',
            timestamp: '2024-01-01T00:00:00Z',
            total_records: size
        },
        config: {
            settings: {
                debug: true,
                cache_enabled: false,
                timeout: 30
            }
        },
        data: data
    };
}

// Optimized traversal function using iterative approach to avoid call stack limit
function traverseJson(data: any): number {
    let count = 0;
    const stack: any[] = [data];
    
    while (stack.length > 0) {
        const current = stack.pop();
        count++;
        
        if (typeof current === 'object' && current !== null) {
            if (Array.isArray(current)) {
                for (const item of current) {
                    stack.push(item);
                }
            } else {
                for (const [key, value] of Object.entries(current)) {
                    stack.push(value);
                }
            }
        }
    }
    
    return count;
}

function runJsonParsingBenchmark(config: Config): BenchmarkResult {
    const params = config.parameters;
    
    // Set defaults
    const jsonSizes = params.json_sizes || [1000];
    const structures = params.json_structures || ['flat'];
    const operations = params.operations || ['parse'];
    const iterations = params.iterations || 5;
    
    const startTime = Date.now();
    const testCases: TestCase[] = [];
    const allParseTimes: number[] = [];
    const allStringifyTimes: number[] = [];
    const allTraverseTimes: number[] = [];
    let totalTests = 0;
    let successfulTests = 0;
    let failedTests = 0;
    
    // Pre-allocate arrays for better performance
    const totalExpectedTests = jsonSizes.length * structures.length * iterations;
    allParseTimes.length = totalExpectedTests;
    allStringifyTimes.length = totalExpectedTests;
    allTraverseTimes.length = totalExpectedTests;
    
    let parseIdx = 0;
    let stringifyIdx = 0;
    let traverseIdx = 0;
    
    const generators: Record<string, (size: number) => any> = {
        flat: generateFlatJson,
        nested: (size) => generateNestedJson(size, 5),
        array_heavy: generateArrayHeavyJson,
        mixed: generateMixedJson
    };
    
    for (const size of jsonSizes) {
        for (const structure of structures) {
            const generator = generators[structure];
            if (!generator) {
                console.error(`Warning: Structure ${structure} not implemented, skipping`);
                continue;
            }
            
            console.error(`Testing ${structure} JSON, size: ${size}...`);
            
            const parseTimes: number[] = [];
            const stringifyTimes: number[] = [];
            const traverseTimes: number[] = [];
            const iterationsData: IterationResult[] = [];
            
            for (let i = 0; i < iterations; i++) {
                console.error(`  Iteration ${i + 1}/${iterations}...`);
                
                // Generate test data
                const jsonData = generator(size);
                const dataSize = JSON.stringify(jsonData).length;
                
                const iterationResult: IterationResult = {
                    iteration: i + 1,
                    data_size: dataSize,
                    operations: {}
                };
                
                totalTests++;
                let success = true;
                
                // Parse operation
                if (operations.includes('parse')) {
                    try {
                        const jsonString = JSON.stringify(jsonData);
                        
                        const start = process.hrtime.bigint();
                        const parsedData = JSON.parse(jsonString);
                        const end = process.hrtime.bigint();
                        const parseTime = Number(end - start) / 1e6; // Convert nanoseconds to milliseconds
                        
                        parseTimes.push(parseTime);
                        allParseTimes[parseIdx++] = parseTime;
                        
                        iterationResult.operations.parse = {
                            success: true,
                            time_ms: parseTime,
                            json_string_length: jsonString.length
                        };
                    } catch (error) {
                        success = false;
                        iterationResult.operations.parse = {
                            success: false,
                            error: `Parse failed: ${error instanceof Error ? error.message : String(error)}`
                        };
                    }
                }
                
                // Stringify operation
                if (operations.includes('stringify')) {
                    try {
                        const start = process.hrtime.bigint();
                        const jsonString = JSON.stringify(jsonData);
                        const end = process.hrtime.bigint();
                        const stringifyTime = Number(end - start) / 1e6; // Convert nanoseconds to milliseconds
                        
                        stringifyTimes.push(stringifyTime);
                        allStringifyTimes[stringifyIdx++] = stringifyTime;
                        
                        iterationResult.operations.stringify = {
                            success: true,
                            time_ms: stringifyTime,
                            output_length: jsonString.length
                        };
                    } catch (error) {
                        success = false;
                        iterationResult.operations.stringify = {
                            success: false,
                            error: `Stringify failed: ${error instanceof Error ? error.message : String(error)}`
                        };
                    }
                }
                
                // Traverse operation
                if (operations.includes('traverse')) {
                    try {
                        const start = process.hrtime.bigint();
                        const operationCount = traverseJson(jsonData);
                        const end = process.hrtime.bigint();
                        const traverseTime = Number(end - start) / 1e6; // Convert nanoseconds to milliseconds
                        
                        traverseTimes.push(traverseTime);
                        allTraverseTimes[traverseIdx++] = traverseTime;
                        
                        iterationResult.operations.traverse = {
                            success: true,
                            time_ms: traverseTime,
                            operations_count: operationCount
                        };
                    } catch (error) {
                        success = false;
                        iterationResult.operations.traverse = {
                            success: false,
                            error: `Traverse failed: ${error instanceof Error ? error.message : String(error)}`
                        };
                    }
                }
                
                if (success) {
                    successfulTests++;
                } else {
                    failedTests++;
                }
                
                iterationsData.push(iterationResult);
            }
            
            // Calculate averages for this test case
            const testCase: TestCase = {
                json_size: size,
                structure_type: structure,
                operations: operations,
                iterations: iterationsData,
                avg_parse_time: parseTimes.length > 0 ? parseTimes.reduce((sum, t) => sum + t, 0) / parseTimes.length : 0,
                avg_stringify_time: stringifyTimes.length > 0 ? stringifyTimes.reduce((sum, t) => sum + t, 0) / stringifyTimes.length : 0,
                avg_traverse_time: traverseTimes.length > 0 ? traverseTimes.reduce((sum, t) => sum + t, 0) / traverseTimes.length : 0
            };
            
            testCases.push(testCase);
        }
    }
    
    // Filter out unused slots and calculate overall summary
    const validParseTimes = allParseTimes.slice(0, parseIdx);
    const validStringifyTimes = allStringifyTimes.slice(0, stringifyIdx);
    const validTraverseTimes = allTraverseTimes.slice(0, traverseIdx);
    
    const summary: Summary = {
        total_tests: totalTests,
        successful_tests: successfulTests,
        failed_tests: failedTests,
        avg_parse_time: validParseTimes.length > 0 ? validParseTimes.reduce((sum, t) => sum + t, 0) / validParseTimes.length : 0,
        avg_stringify_time: validStringifyTimes.length > 0 ? validStringifyTimes.reduce((sum, t) => sum + t, 0) / validStringifyTimes.length : 0,
        avg_traverse_time: validTraverseTimes.length > 0 ? validTraverseTimes.reduce((sum, t) => sum + t, 0) / validTraverseTimes.length : 0
    };
    
    const endTime = Date.now();
    const executionTime = (endTime - startTime) / 1000; // Convert to seconds
    
    return {
        start_time: startTime,
        test_cases: testCases,
        summary: summary,
        end_time: endTime,
        total_execution_time: executionTime
    };
}

async function main() {
    const args = process.argv.slice(2);
    if (args.length < 1) {
        console.error(`Usage: ${process.argv[1]} <config_file>`);
        process.exit(1);
    }
    
    const configFile = args[0];
    
    try {
        const configData = fs.readFileSync(configFile, 'utf8');
        const config: Config = JSON.parse(configData);
        
        const results = runJsonParsingBenchmark(config);
        console.log(JSON.stringify(results, null, 2));
        
    } catch (error) {
        if (error instanceof Error) {
            if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
                console.error(`Error: Config file '${configFile}' not found`);
            } else if (error.name === 'SyntaxError') {
                console.error(`Error: Invalid JSON in config file: ${error.message}`);
            } else {
                console.error(`Error: ${error.message}`);
            }
        } else {
            console.error(`Error: ${String(error)}`);
        }
        process.exit(1);
    }
}

main().catch(error => {
        console.error(`Unhandled error: ${error}`);
        process.exit(1);
    });