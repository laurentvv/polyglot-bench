#!/usr/bin/env node
/**
 * Text compression test implementation in TypeScript.
 * Measures compression performance for different text types and algorithms.
 */

import * as fs from 'fs';
import * as zlib from 'zlib';
import { promisify } from 'util';

interface CompressionResult {
    success: boolean;
    compressed_size?: number;
    compression_time: number;
    error?: string;
}

interface DecompressionResult {
    success: boolean;
    decompressed_size?: number;
    decompression_time: number;
    error?: string;
}

interface IterationResult {
    iteration: number;
    original_size: number;
    compression: CompressionResult;
    decompression?: DecompressionResult;
}

interface TestCase {
    input_size: number;
    text_type: string;
    algorithm: string;
    iterations: IterationResult[];
    avg_compression_ratio: number;
    avg_compression_time: number;
    avg_decompression_time: number;
}

interface BenchmarkResults {
    start_time: number;
    test_cases: TestCase[];
    summary: {
        total_tests: number;
        successful_compressions: number;
        failed_compressions: number;
        best_compression_ratios: Record<string, number>;
        algorithm_performance: Record<string, {
            avg_compression_ratio: number;
            max_compression_ratio: number;
            min_compression_ratio: number;
        }>;
    };
    end_time?: number;
    total_execution_time?: number;
}

const gzipAsync = promisify(zlib.gzip);
const deflateAsync = promisify(zlib.deflate);
const gunzipAsync = promisify(zlib.gunzip);
const inflateAsync = promisify(zlib.inflate);

function generateTextData(size: number, textType: string): string {
    const chars: Record<string, string> = {
        ascii: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 \n',
        unicode: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789àáâãäåæçèéêëìíîïñòóôõöøùúûüý你好世界🌟🚀📊 \n',
        code: '',
        natural_language: ''
    };

    if (textType === 'code') {
        const keywords = ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return', 'try', 'catch'];
        const operators = ['=', '+', '-', '*', '/', '(', ')', '{', '}', '[', ']', ';', ':'];
        let text = '';
        
        while (text.length < size) {
            if (Math.random() < 0.3) {
                text += keywords[Math.floor(Math.random() * keywords.length)];
            } else {
                const wordLength = Math.floor(Math.random() * 8) + 3;
                for (let i = 0; i < wordLength; i++) {
                    text += String.fromCharCode(97 + Math.floor(Math.random() * 26)); // a-z
                }
            }
            
            if (Math.random() < 0.2) {
                text += operators[Math.floor(Math.random() * operators.length)];
            }
            
            if (Math.random() < 0.1) {
                text += '\n';
            } else {
                text += ' ';
            }
        }
        
        return text.substring(0, size);
    } else if (textType === 'natural_language') {
        const words = ['the', 'quick', 'brown', 'fox', 'jumps', 'over', 'lazy', 'dog', 'and', 'runs', 'through',
                      'forest', 'meadow', 'river', 'mountain', 'valley', 'beautiful', 'magnificent', 'wonderful'];
        let text = '';
        
        while (text.length < size) {
            text += words[Math.floor(Math.random() * words.length)];
            
            if (Math.random() < 0.1) {
                text += '. ';
            } else if (Math.random() < 0.05) {
                text += ', ';
            } else {
                text += ' ';
            }
            
            if (Math.random() < 0.05) {
                text += '\n';
            }
        }
        
        return text.substring(0, size);
    } else {
        const charset = chars[textType];
        if (!charset) {
            throw new Error(`Unknown text type: ${textType}`);
        }
        
        let result = '';
        for (let i = 0; i < size; i++) {
            result += charset[Math.floor(Math.random() * charset.length)];
        }
        return result;
    }
}

async function compressWithGzip(data: Buffer): Promise<CompressionResult> {
    const startTime = Date.now();
    try {
        const compressed = await gzipAsync(data);
        const compressionTime = Date.now() - startTime;
        
        return {
            success: true,
            compressed_size: compressed.length,
            compression_time: compressionTime
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : String(error),
            compression_time: Date.now() - startTime
        };
    }
}

async function compressWithZlib(data: Buffer): Promise<CompressionResult> {
    const startTime = Date.now();
    try {
        const compressed = await deflateAsync(data);
        const compressionTime = Date.now() - startTime;
        
        return {
            success: true,
            compressed_size: compressed.length,
            compression_time: compressionTime
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : String(error),
            compression_time: Date.now() - startTime
        };
    }
}

async function decompressGzip(data: Buffer): Promise<DecompressionResult> {
    const startTime = Date.now();
    try {
        const decompressed = await gunzipAsync(data);
        const decompressionTime = Date.now() - startTime;
        
        return {
            success: true,
            decompressed_size: decompressed.length,
            decompression_time: decompressionTime
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : String(error),
            decompression_time: Date.now() - startTime
        };
    }
}

async function decompressZlib(data: Buffer): Promise<DecompressionResult> {
    const startTime = Date.now();
    try {
        const decompressed = await inflateAsync(data);
        const decompressionTime = Date.now() - startTime;
        
        return {
            success: true,
            decompressed_size: decompressed.length,
            decompression_time: decompressionTime
        };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : String(error),
            decompression_time: Date.now() - startTime
        };
    }
}

async function runTextCompressionBenchmark(config: any): Promise<BenchmarkResults> {
    const inputSizes = config.input_sizes || [1024];
    const textTypes = config.text_types || ['ascii'];
    const algorithms = config.compression_algorithms || ['gzip'];
    const iterations = config.iterations || 3;
    
    const compressFuncs: Record<string, (data: Buffer) => Promise<CompressionResult>> = {
        gzip: compressWithGzip,
        zlib: compressWithZlib
    };
    
    const decompressFuncs: Record<string, (data: Buffer) => Promise<DecompressionResult>> = {
        gzip: decompressGzip,
        zlib: decompressZlib
    };
    
    const results: BenchmarkResults = {
        start_time: Date.now() / 1000,
        test_cases: [],
        summary: {
            total_tests: 0,
            successful_compressions: 0,
            failed_compressions: 0,
            best_compression_ratios: {},
            algorithm_performance: {}
        }
    };
    
    const algorithmStats: Record<string, number[]> = {};
    
    for (const size of inputSizes) {
        for (const textType of textTypes) {
            for (const algorithm of algorithms) {
                if (!(algorithm in compressFuncs)) {
                    console.error(`Warning: Algorithm ${algorithm} not implemented, skipping`);
                    continue;
                }
                
                console.error(`Testing ${textType} text, size: ${size}, algorithm: ${algorithm}...`);
                
                const testCase: TestCase = {
                    input_size: size,
                    text_type: textType,
                    algorithm: algorithm,
                    iterations: [],
                    avg_compression_ratio: 0.0,
                    avg_compression_time: 0.0,
                    avg_decompression_time: 0.0
                };
                
                const compressionRatios: number[] = [];
                const compressionTimes: number[] = [];
                const decompressionTimes: number[] = [];
                
                for (let i = 0; i < iterations; i++) {
                    console.error(`  Iteration ${i + 1}/${iterations}...`);
                    
                    const textData = generateTextData(size, textType);
                    const dataBytes = Buffer.from(textData, 'utf-8');
                    const originalSize = dataBytes.length;
                    
                    const compressResult = await compressFuncs[algorithm](dataBytes);
                    
                    const iterationResult: IterationResult = {
                        iteration: i + 1,
                        original_size: originalSize,
                        compression: compressResult
                    };
                    
                    results.summary.total_tests++;
                    
                    if (compressResult.success && compressResult.compressed_size !== undefined) {
                        results.summary.successful_compressions++;
                        
                        const compressedSize = compressResult.compressed_size;
                        const compressionRatio = compressedSize > 0 ? originalSize / compressedSize : 0;
                        
                        compressionRatios.push(compressionRatio);
                        compressionTimes.push(compressResult.compression_time);
                        
                        if (!(algorithm in algorithmStats)) {
                            algorithmStats[algorithm] = [];
                        }
                        algorithmStats[algorithm].push(compressionRatio);
                    } else {
                        results.summary.failed_compressions++;
                    }
                    
                    testCase.iterations.push(iterationResult);
                }
                
                if (compressionRatios.length > 0) {
                    testCase.avg_compression_ratio = compressionRatios.reduce((a, b) => a + b, 0) / compressionRatios.length;
                    testCase.avg_compression_time = compressionTimes.reduce((a, b) => a + b, 0) / compressionTimes.length;
                    
                    if (decompressionTimes.length > 0) {
                        testCase.avg_decompression_time = decompressionTimes.reduce((a, b) => a + b, 0) / decompressionTimes.length;
                    }
                }
                
                results.test_cases.push(testCase);
            }
        }
    }
    
    // Calculate summary statistics
    for (const [algorithm, ratios] of Object.entries(algorithmStats)) {
        if (ratios.length > 0) {
            results.summary.algorithm_performance[algorithm] = {
                avg_compression_ratio: ratios.reduce((a, b) => a + b, 0) / ratios.length,
                max_compression_ratio: Math.max(...ratios),
                min_compression_ratio: Math.min(...ratios)
            };
        }
    }
    
    results.end_time = Date.now() / 1000;
    results.total_execution_time = results.end_time - results.start_time;
    
    return results;
}

async function main() {
    if (process.argv.length < 3) {
        console.error('Usage: node text_compression.js <config_file>');
        process.exit(1);
    }
    
    const configFile = process.argv[2];
    
    try {
        const configData = fs.readFileSync(configFile, 'utf-8');
        const config = JSON.parse(configData);
        
        const parameters = config.parameters || {};
        const results = await runTextCompressionBenchmark(parameters);
        
        console.log(JSON.stringify(results, null, 2));
    } catch (error) {
        if (error instanceof Error) {
            if (error.message.includes('ENOENT')) {
                console.error(`Error: Config file '${configFile}' not found`);
            } else {
                console.error(`Error: ${error.message}`);
            }
        } else {
            console.error(`Error: ${String(error)}`);
        }
        process.exit(1);
    }
}

main().catch(console.error);
