#!/usr/bin/env node
/**
 * GZIP compression test implementation in TypeScript.
 * Measures compression performance, ratio, and throughput.
 */

import * as fs from 'fs';
import * as zlib from 'zlib';
import { promisify } from 'util';

interface CompressionResult {
    success: boolean;
    original_size?: number;
    compressed_size?: number;
    compression_ratio?: number;
    compression_time: number;
    throughput_mb_s?: number;
    error?: string;
}

interface IterationResult {
    iteration: number;
    compression: CompressionResult;
}

interface TestCase {
    input_size: number;
    data_type: string;
    compression_level: number;
    iterations: IterationResult[];
    avg_compression_ratio: number;
    avg_compression_time: number;
    avg_decompression_time: number;
    avg_compression_throughput: number;
    avg_decompression_throughput: number;
}

interface Summary {
    total_tests: number;
    successful_tests: number;
    failed_tests: number;
    avg_compression_ratio: number;
    avg_compression_time: number;
    avg_decompression_time: number;
    avg_compression_throughput: number;
    avg_decompression_throughput: number;
}

interface BenchmarkResults {
    start_time: number;
    test_cases: TestCase[];
    summary: Summary;
    end_time?: number;
    total_execution_time?: number;
}

interface Config {
    parameters: {
        input_sizes?: number[];
        data_types?: string[];
        compression_levels?: number[];
        iterations?: number;
    };
}

const gzipAsync = promisify(zlib.gzip);

function generateTestData(size: number, dataType: string): Buffer {
    switch (dataType) {
        case 'text': {
            const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n';
            let result = '';
            for (let i = 0; i < size; i++) {
                result += chars[Math.floor(Math.random() * chars.length)];
            }
            return Buffer.from(result, 'utf-8');
        }
        
        case 'binary': {
            const result = Buffer.alloc(size);
            for (let i = 0; i < size; i++) {
                result[i] = Math.floor(Math.random() * 256);
            }
            return result;
        }
        
        case 'json': {
            const data: any[] = [];
            let currentSize = 0;
            
            while (currentSize < size) {
                const record = {
                    id: data.length,
                    name: generateRandomString(10),
                    value: Math.floor(Math.random() * 1000) + 1,
                    active: Math.random() < 0.5,
                    data: generateRandomString(50)
                };
                data.push(record);
                currentSize = Buffer.from(JSON.stringify(data), 'utf-8').length;
            }
            
            const jsonStr = JSON.stringify(data);
            const jsonBuffer = Buffer.from(jsonStr, 'utf-8');
            return jsonBuffer.slice(0, Math.min(size, jsonBuffer.length));
        }
        
        default:
            throw new Error(`Unknown data type: ${dataType}`);
    }
}

function generateRandomString(length: number): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
}

async function compressData(data: Buffer, compressionLevel: number): Promise<CompressionResult> {
    const startTime = Date.now();
    const originalSize = data.length;
    
    try {
        // Map compression levels to zlib constants
        let level: number;
        switch (compressionLevel) {
            case 1:
                level = zlib.constants.Z_BEST_SPEED;
                break;
            case 2:
            case 3:
            case 4:
            case 5:
                level = compressionLevel;
                break;
            case 6:
                level = zlib.constants.Z_DEFAULT_COMPRESSION;
                break;
            case 7:
            case 8:
            case 9:
                level = compressionLevel;
                break;
            default:
                level = zlib.constants.Z_DEFAULT_COMPRESSION;
        }
        
        const compressed = await gzipAsync(data, { level });
        const compressionTime = Date.now() - startTime;
        
        const compressedSize = compressed.length;
        const compressionRatio = compressedSize > 0 ? originalSize / compressedSize : 0;
        const throughput = originalSize / (compressionTime / 1000) / (1024 * 1024); // MB/s
        
        return {
            success: true,
            original_size: originalSize,
            compressed_size: compressedSize,
            compression_ratio: Math.round(compressionRatio * 1000) / 1000,
            compression_time: Math.round(compressionTime * 100) / 100,
            throughput_mb_s: Math.round(throughput * 100) / 100
        };
    } catch (error) {
        const compressionTime = Date.now() - startTime;
        return {
            success: false,
            original_size: originalSize,
            compression_time: Math.round(compressionTime * 100) / 100,
            error: error instanceof Error ? error.message : String(error)
        };
    }
}

async function runCompressionBenchmark(config: any): Promise<BenchmarkResults> {
    const inputSizes = config.input_sizes || [1024];
    const dataTypes = config.data_types || ['text'];
    const compressionLevels = config.compression_levels || [6];
    const iterations = config.iterations || 5;
    
    const results: BenchmarkResults = {
        start_time: Date.now() / 1000,
        test_cases: [],
        summary: {
            total_tests: 0,
            successful_tests: 0,
            failed_tests: 0,
            avg_compression_ratio: 0.0,
            avg_compression_time: 0.0,
            avg_decompression_time: 0.0,
            avg_compression_throughput: 0.0,
            avg_decompression_throughput: 0.0
        }
    };
    
    const totalCompressionRatios: number[] = [];
    const totalCompressionTimes: number[] = [];
    const totalCompressionThroughputs: number[] = [];
    
    for (const size of inputSizes) {
        for (const dataType of dataTypes) {
            for (const level of compressionLevels) {
                console.error(`Testing ${dataType} data, size: ${size} bytes, level: ${level}...`);
                
                const testCase: TestCase = {
                    input_size: size,
                    data_type: dataType,
                    compression_level: level,
                    iterations: [],
                    avg_compression_ratio: 0.0,
                    avg_compression_time: 0.0,
                    avg_decompression_time: 0.0,
                    avg_compression_throughput: 0.0,
                    avg_decompression_throughput: 0.0
                };
                
                const iterationCompressionRatios: number[] = [];
                const iterationCompressionTimes: number[] = [];
                const iterationCompressionThroughputs: number[] = [];
                
                for (let i = 0; i < iterations; i++) {
                    console.error(`  Iteration ${i + 1}/${iterations}...`);
                    
                    try {
                        const testData = generateTestData(size, dataType);
                        const compressionResult = await compressData(testData, level);
                        
                        const iterationResult: IterationResult = {
                            iteration: i + 1,
                            compression: compressionResult
                        };
                        
                        results.summary.total_tests++;
                        
                        if (compressionResult.success) {
                            results.summary.successful_tests++;
                            
                            if (compressionResult.compression_ratio !== undefined) {
                                iterationCompressionRatios.push(compressionResult.compression_ratio);
                            }
                            iterationCompressionTimes.push(compressionResult.compression_time);
                            if (compressionResult.throughput_mb_s !== undefined) {
                                iterationCompressionThroughputs.push(compressionResult.throughput_mb_s);
                            }
                        } else {
                            results.summary.failed_tests++;
                        }
                        
                        testCase.iterations.push(iterationResult);
                    } catch (error) {
                        console.error(`Error in iteration ${i + 1}: ${error}`);
                        results.summary.total_tests++;
                        results.summary.failed_tests++;
                    }
                }
                
                // Calculate averages for this test case
                if (iterationCompressionRatios.length > 0) {
                    testCase.avg_compression_ratio = iterationCompressionRatios.reduce((a, b) => a + b) / iterationCompressionRatios.length;
                    testCase.avg_compression_time = iterationCompressionTimes.reduce((a, b) => a + b) / iterationCompressionTimes.length;
                    testCase.avg_compression_throughput = iterationCompressionThroughputs.reduce((a, b) => a + b) / iterationCompressionThroughputs.length;
                    
                    totalCompressionRatios.push(...iterationCompressionRatios);
                    totalCompressionTimes.push(...iterationCompressionTimes);
                    totalCompressionThroughputs.push(...iterationCompressionThroughputs);
                }
                
                results.test_cases.push(testCase);
            }
        }
    }
    
    // Calculate overall summary
    if (totalCompressionRatios.length > 0) {
        results.summary.avg_compression_ratio = totalCompressionRatios.reduce((a, b) => a + b) / totalCompressionRatios.length;
        results.summary.avg_compression_time = totalCompressionTimes.reduce((a, b) => a + b) / totalCompressionTimes.length;
        results.summary.avg_compression_throughput = totalCompressionThroughputs.reduce((a, b) => a + b) / totalCompressionThroughputs.length;
    }
    
    results.end_time = Date.now() / 1000;
    results.total_execution_time = results.end_time - results.start_time;
    
    return results;
}

async function main(): Promise<void> {
    if (process.argv.length < 3) {
        console.error(`Usage: ${process.argv[0]} ${process.argv[1]} <config_file>`);
        process.exit(1);
    }
    
    const configFile = process.argv[2];
    
    try {
        const configContent = fs.readFileSync(configFile, 'utf-8');
        const config: Config = JSON.parse(configContent);
        
        const results = await runCompressionBenchmark(config.parameters);
        
        console.log(JSON.stringify(results, null, 2));
    } catch (error) {
        if (error instanceof Error) {
            if ((error as any).code === 'ENOENT') {
                console.error(`Error: Config file '${configFile}' not found`);
            } else if (error instanceof SyntaxError) {
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
        console.error('Unhandled error:', error);
        process.exit(1);
});