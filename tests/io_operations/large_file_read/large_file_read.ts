#!/usr/bin/env node

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { performance } from 'perf_hooks';

interface ReadResult {
    readTime: number;
    bytesRead: number;
    throughputMbps: number;
    chunkCount?: number;
    avgChunkSize?: number;
}

interface IterationResult {
    iteration: number;
    readTime: number;
    bytesRead: number;
    throughputMbps: number;
    memoryUsed: number;
    ioWaitTime: number;
    chunkCount?: number;
    avgChunkSize?: number;
    error?: string;
}

interface TestCase {
    fileSize: number;
    bufferSize: number;
    readPattern: string;
    iterations: IterationResult[];
    avgReadTime: number;
    avgThroughput: number;
    memoryEfficiency: number;
}

interface Summary {
    totalTests: number;
    successfulTests: number;
    failedTests: number;
    avgReadTime: number;
    avgThroughput: number;
    peakMemoryUsage: number;
}

interface BenchmarkResult {
    startTime: number;
    endTime: number;
    totalDuration: number;
    testCases: TestCase[];
    summary: Summary;
}

interface Config {
    parameters: {
        file_sizes?: number[];
        buffer_sizes?: number[];
        read_patterns?: string[];
        iterations?: number;
        generate_test_files?: boolean;
    };
}

function generateTestFile(filePath: string, sizeBytes: number): void {
    console.error(`Generating test file: ${sizeBytes} bytes...`);
    
    const chunkSize = 8192;
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n';
    
    const fd = fs.openSync(filePath, 'w');
    let bytesWritten = 0;
    
    try {
        while (bytesWritten < sizeBytes) {
            const remaining = sizeBytes - bytesWritten;
            const currentChunkSize = Math.min(remaining, chunkSize);
            
            // Generate random text data
            let data = '';
            for (let i = 0; i < currentChunkSize; i++) {
                data += chars[Math.floor(Math.random() * chars.length)];
            }
            
            const buffer = Buffer.from(data, 'utf8');
            fs.writeSync(fd, buffer);
            bytesWritten += buffer.length;
        }
        
        fs.fsyncSync(fd);
    } finally {
        fs.closeSync(fd);
    }
}

function readFileSequential(filePath: string, bufferSize: number): ReadResult {
    const startTime = performance.now();
    const fd = fs.openSync(filePath, 'r');
    const buffer = Buffer.alloc(bufferSize);
    let totalBytes = 0;
    
    try {
        while (true) {
            const bytesRead = fs.readSync(fd, buffer, 0, bufferSize, null);
            if (bytesRead === 0) {
                break;
            }
            totalBytes += bytesRead;
        }
    } finally {
        fs.closeSync(fd);
    }
    
    const readTime = performance.now() - startTime;
    const throughputMbps = readTime > 0 ? (totalBytes / (1024 * 1024)) / (readTime / 1000) : 0;
    
    return {
        readTime,
        bytesRead: totalBytes,
        throughputMbps
    };
}

function readFileChunked(filePath: string, bufferSize: number): ReadResult {
    const startTime = performance.now();
    const fd = fs.openSync(filePath, 'r');
    const buffer = Buffer.alloc(bufferSize);
    let totalBytes = 0;
    let chunkCount = 0;
    
    try {
        while (true) {
            const bytesRead = fs.readSync(fd, buffer, 0, bufferSize, null);
            if (bytesRead === 0) {
                break;
            }
            totalBytes += bytesRead;
            chunkCount++;
        }
    } finally {
        fs.closeSync(fd);
    }
    
    const readTime = performance.now() - startTime;
    const throughputMbps = readTime > 0 ? (totalBytes / (1024 * 1024)) / (readTime / 1000) : 0;
    const avgChunkSize = chunkCount > 0 ? totalBytes / chunkCount : 0;
    
    return {
        readTime,
        bytesRead: totalBytes,
        throughputMbps,
        chunkCount,
        avgChunkSize
    };
}

function getMemoryUsage(): number {
    const memUsage = process.memoryUsage();
    return memUsage.heapUsed / (1024 * 1024); // Convert to MB
}

function performReadTest(filePath: string, bufferSize: number, pattern: string): ReadResult {
    switch (pattern) {
        case 'sequential':
            return readFileSequential(filePath, bufferSize);
        case 'chunked':
            return readFileChunked(filePath, bufferSize);
        default:
            throw new Error(`Unknown read pattern: ${pattern}`);
    }
}

function runLargeFileReadBenchmark(parameters: Config['parameters']): BenchmarkResult {
    // Parse configuration with defaults
    const fileSizes = parameters.file_sizes || [1048576]; // Default 1MB
    const bufferSizes = parameters.buffer_sizes || [4096];
    const readPatterns = parameters.read_patterns || ['sequential'];
    const iterations = parameters.iterations || 3;
    const generateTestFiles = parameters.generate_test_files !== undefined ? parameters.generate_test_files : true;

    const startTime = performance.now();
    const testCases: TestCase[] = [];
    let totalTests = 0;
    let successfulTests = 0;
    let failedTests = 0;
    const allReadTimes: number[] = [];
    const allThroughputs: number[] = [];
    let peakMemory = 0;

    // Create temporary directory for test files
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'large_file_read_test_'));

    try {
        for (const fileSize of fileSizes) {
            for (const bufferSize of bufferSizes) {
                for (const pattern of readPatterns) {
                    console.error(`Testing file size: ${fileSize} bytes, buffer: ${bufferSize}, pattern: ${pattern}...`);

                    const testCase: TestCase = {
                        fileSize,
                        bufferSize,
                        readPattern: pattern,
                        iterations: [],
                        avgReadTime: 0,
                        avgThroughput: 0,
                        memoryEfficiency: 0
                    };

                    // Generate test file if needed
                    const testFilePath = path.join(tempDir, `test_file_${fileSize}_${bufferSize}.txt`);
                    if (generateTestFiles && !fs.existsSync(testFilePath)) {
                        generateTestFile(testFilePath, fileSize);
                    }

                    const readTimes: number[] = [];
                    const throughputs: number[] = [];

                    for (let i = 0; i < iterations; i++) {
                        console.error(`  Iteration ${i + 1}/${iterations}...`);
                        totalTests++;

                        try {
                            const memoryBefore = getMemoryUsage();

                            const readResult = performReadTest(testFilePath, bufferSize, pattern);

                            const memoryAfter = getMemoryUsage();
                            const memoryUsed = memoryAfter - memoryBefore;
                            peakMemory = Math.max(peakMemory, memoryAfter);

                            const iterationResult: IterationResult = {
                                iteration: i + 1,
                                readTime: readResult.readTime,
                                bytesRead: readResult.bytesRead,
                                throughputMbps: readResult.throughputMbps,
                                memoryUsed,
                                ioWaitTime: readResult.readTime, // Approximation
                                chunkCount: readResult.chunkCount,
                                avgChunkSize: readResult.avgChunkSize
                            };

                            testCase.iterations.push(iterationResult);
                            readTimes.push(readResult.readTime);
                            throughputs.push(readResult.throughputMbps);
                            successfulTests++;

                        } catch (error) {
                            console.error(`Error in iteration ${i + 1}: ${error}`);
                            failedTests++;
                            testCase.iterations.push({
                                iteration: i + 1,
                                readTime: 0,
                                bytesRead: 0,
                                throughputMbps: 0,
                                memoryUsed: 0,
                                ioWaitTime: 0,
                                error: error instanceof Error ? error.message : String(error)
                            });
                        }
                    }

                    // Calculate averages for this test case
                    if (readTimes.length > 0) {
                        testCase.avgReadTime = readTimes.reduce((a, b) => a + b, 0) / readTimes.length;
                        testCase.avgThroughput = throughputs.reduce((a, b) => a + b, 0) / throughputs.length;
                        testCase.memoryEfficiency = (fileSize / (1024 * 1024)) / Math.max(1, peakMemory);

                        allReadTimes.push(...readTimes);
                        allThroughputs.push(...throughputs);
                    }

                    testCases.push(testCase);
                }
            }
        }
    } finally {
        // Clean up temporary files
        try {
            fs.rmSync(tempDir, { recursive: true, force: true });
        } catch (error) {
            console.error(`Warning: Could not clean up temp directory: ${error}`);
        }
    }

    const endTime = performance.now();
    const totalDuration = (endTime - startTime) / 1000; // Convert to seconds

    // Calculate overall summary
    const avgReadTime = allReadTimes.length > 0 ? allReadTimes.reduce((a, b) => a + b, 0) / allReadTimes.length : 0;
    const avgThroughput = allThroughputs.length > 0 ? allThroughputs.reduce((a, b) => a + b, 0) / allThroughputs.length : 0;

    return {
        startTime: startTime / 1000, // Convert to seconds
        endTime: endTime / 1000,
        totalDuration,
        testCases,
        summary: {
            totalTests,
            successfulTests,
            failedTests,
            avgReadTime,
            avgThroughput,
            peakMemoryUsage: peakMemory
        }
    };
}

function main(): void {
    if (process.argv.length !== 3) {
        console.error(`Usage: ${process.argv[0]} ${process.argv[1]} <input_file>`);
        process.exit(1);
    }

    const inputFile = process.argv[2];

    try {
        // Read and parse input configuration
        const configContent = fs.readFileSync(inputFile, 'utf8');
        const config: Config = JSON.parse(configContent);

        const result = runLargeFileReadBenchmark(config.parameters);

        // Output results as JSON
        console.log(JSON.stringify(result, null, 2));

    } catch (error) {
        console.error(`Error: ${error}`);
        process.exit(1);
    }
}

main();