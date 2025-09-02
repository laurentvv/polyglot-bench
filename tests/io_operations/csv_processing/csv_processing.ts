#!/usr/bin/env node

/**
 * CSV processing test implementation in TypeScript.
 * Measures CSV file read, write, filtering, and aggregation performance.
 */

import * as fs from 'fs';
import * as process from 'process';

interface Config {
    parameters: {
        row_counts?: number[];
        column_counts?: number[];
        operations?: string[];
        data_types?: string[];
        iterations?: number;
    };
}

interface OperationResult {
    success: boolean;
    time_ms?: number;
    error?: string;
    output_size?: number;
    rows_read?: number;
    original_rows?: number;
    filtered_rows?: number;
    aggregated_columns?: number;
}

interface IterationResult {
    iteration: number;
    data_size: number;
    operations: { [key: string]: OperationResult };
}

interface TestCase {
    row_count: number;
    column_count: number;
    data_type: string;
    operations: string[];
    iterations: IterationResult[];
    avg_read_time: number;
    avg_write_time: number;
    avg_filter_time: number;
    avg_aggregate_time: number;
}

interface Summary {
    total_tests: number;
    successful_tests: number;
    failed_tests: number;
    avg_read_time: number;
    avg_write_time: number;
    avg_filter_time: number;
    avg_aggregate_time: number;
}

interface Results {
    start_time: number;
    test_cases: TestCase[];
    summary: Summary;
    end_time: number;
    total_execution_time: number;
}

function generateCSVData(rows: number, cols: number, dataType: string): string[][] {
    const data: string[][] = [];
    
    // Generate headers
    const headers: string[] = [];
    for (let i = 0; i < cols; i++) {
        headers.push(`col_${i + 1}`);
    }
    data.push(headers);
    
    // Generate data rows
    for (let row = 0; row < rows; row++) {
        const rowData: string[] = [];
        for (let col = 0; col < cols; col++) {
            let value: string;
            
            if (dataType === "numeric") {
                value = (Math.random() * 1000).toFixed(2);
            } else if (dataType === "text") {
                const length = Math.floor(Math.random() * 11) + 5; // 5-15 characters
                value = Array.from({ length }, () => 
                    String.fromCharCode(97 + Math.floor(Math.random() * 26))
                ).join('');
            } else { // mixed
                switch (col % 3) {
                    case 0:
                        value = String(Math.floor(Math.random() * 10000) + 1);
                        break;
                    case 1:
                        value = Array.from({ length: 10 }, () => 
                            String.fromCharCode(97 + Math.floor(Math.random() * 26))
                        ).join('');
                        break;
                    default:
                        value = (Math.random() * 1000).toFixed(2);
                        break;
                }
            }
            
            rowData.push(value);
        }
        data.push(rowData);
    }
    
    return data;
}

function writeCSVToString(data: string[][]): string {
    return data.map(row => row.join(',')).join('\n') + '\n';
}

function readCSVFromString(csvString: string): string[][] {
    return csvString.trim().split('\n').map(line => line.split(','));
}

function filterCSVData(data: string[][], filterColumn: number = 0): string[][] {
    if (data.length < 2) {
        return data;
    }
    
    const filtered: string[][] = [data[0]]; // Keep headers
    
    for (let i = 1; i < data.length; i++) {
        const row = data[i];
        if (row.length > filterColumn) {
            const value = parseFloat(row[filterColumn]);
            if (!isNaN(value)) {
                if (value > 500) {
                    filtered.push(row);
                }
            } else if (row[filterColumn].length > 5) {
                filtered.push(row);
            }
        }
    }
    
    return filtered;
}

function aggregateCSVData(data: string[][]): { [key: string]: { [key: string]: number } } {
    if (data.length < 2) {
        return {};
    }
    
    const headers = data[0];
    const numericColumns: number[] = [];
    
    // Find numeric columns (check first 5 rows)
    for (let colIdx = 0; colIdx < headers.length; colIdx++) {
        let isNumeric = true;
        const checkRows = Math.min(5, data.length - 1);
        
        for (let rowIdx = 1; rowIdx <= checkRows; rowIdx++) {
            if (colIdx < data[rowIdx].length) {
                if (isNaN(parseFloat(data[rowIdx][colIdx]))) {
                    isNumeric = false;
                    break;
                }
            }
        }
        if (isNumeric) {
            numericColumns.push(colIdx);
        }
    }
    
    const aggregations: { [key: string]: { [key: string]: number } } = {};
    
    for (const colIdx of numericColumns) {
        const colName = headers[colIdx];
        const values: number[] = [];
        
        for (let i = 1; i < data.length; i++) {
            const row = data[i];
            if (colIdx < row.length) {
                const value = parseFloat(row[colIdx]);
                if (!isNaN(value)) {
                    values.push(value);
                }
            }
        }
        
        if (values.length > 0) {
            const sum = values.reduce((acc, val) => acc + val, 0);
            const stats = {
                sum: sum,
                avg: sum / values.length,
                min: Math.min(...values),
                max: Math.max(...values),
                count: values.length
            };
            
            aggregations[colName] = stats;
        }
    }
    
    return aggregations;
}

function runCSVProcessingBenchmark(config: Config): Results {
    const parameters = config.parameters;
    
    // Set defaults
    const rowCounts = parameters.row_counts || [1000];
    const columnCounts = parameters.column_counts || [5];
    const operations = parameters.operations || ["read", "write"];
    const dataTypes = parameters.data_types || ["mixed"];
    const iterations = parameters.iterations || 3;
    
    const startTime = Date.now();
    const testCases: TestCase[] = [];
    const allReadTimes: number[] = [];
    const allWriteTimes: number[] = [];
    const allFilterTimes: number[] = [];
    const allAggregateTimes: number[] = [];
    let totalTests = 0;
    let successfulTests = 0;
    let failedTests = 0;
    
    for (const rows of rowCounts) {
        for (const cols of columnCounts) {
            for (const dataType of dataTypes) {
                console.error(`Testing CSV: ${rows} rows x ${cols} cols, type: ${dataType}...`);
                
                const readTimes: number[] = [];
                const writeTimes: number[] = [];
                const filterTimes: number[] = [];
                const aggregateTimes: number[] = [];
                const iterationsData: IterationResult[] = [];
                
                for (let i = 0; i < iterations; i++) {
                    console.error(`  Iteration ${i + 1}/${iterations}...`);
                    
                    // Generate test data
                    const csvData = generateCSVData(rows, cols, dataType);
                    
                    const iterationResult: IterationResult = {
                        iteration: i + 1,
                        data_size: csvData.length,
                        operations: {}
                    };
                    
                    totalTests++;
                    let success = true;
                    
                    // Write operation
                    if (operations.includes("write")) {
                        try {
                            const start = process.hrtime.bigint();
                            const csvString = writeCSVToString(csvData);
                            const writeTime = Number(process.hrtime.bigint() - start) / 1000000; // Convert to ms
                            
                            writeTimes.push(writeTime);
                            allWriteTimes.push(writeTime);
                            
                            iterationResult.operations["write"] = {
                                success: true,
                                time_ms: writeTime,
                                output_size: csvString.length
                            };
                        } catch (e) {
                            success = false;
                            iterationResult.operations["write"] = {
                                success: false,
                                error: String(e)
                            };
                        }
                    }
                    
                    // Read operation
                    if (operations.includes("read")) {
                        try {
                            const csvString = writeCSVToString(csvData);
                            
                            const start = process.hrtime.bigint();
                            const readData = readCSVFromString(csvString);
                            const readTime = Number(process.hrtime.bigint() - start) / 1000000; // Convert to ms
                            
                            readTimes.push(readTime);
                            allReadTimes.push(readTime);
                            
                            iterationResult.operations["read"] = {
                                success: true,
                                time_ms: readTime,
                                rows_read: readData.length
                            };
                        } catch (e) {
                            success = false;
                            iterationResult.operations["read"] = {
                                success: false,
                                error: String(e)
                            };
                        }
                    }
                    
                    // Filter operation
                    if (operations.includes("filter")) {
                        try {
                            const start = process.hrtime.bigint();
                            const filteredData = filterCSVData(csvData);
                            const filterTime = Number(process.hrtime.bigint() - start) / 1000000; // Convert to ms
                            
                            filterTimes.push(filterTime);
                            allFilterTimes.push(filterTime);
                            
                            iterationResult.operations["filter"] = {
                                success: true,
                                time_ms: filterTime,
                                original_rows: csvData.length,
                                filtered_rows: filteredData.length
                            };
                        } catch (e) {
                            success = false;
                            iterationResult.operations["filter"] = {
                                success: false,
                                error: String(e)
                            };
                        }
                    }
                    
                    // Aggregate operation
                    if (operations.includes("aggregate")) {
                        try {
                            const start = process.hrtime.bigint();
                            const aggregations = aggregateCSVData(csvData);
                            const aggregateTime = Number(process.hrtime.bigint() - start) / 1000000; // Convert to ms
                            
                            aggregateTimes.push(aggregateTime);
                            allAggregateTimes.push(aggregateTime);
                            
                            iterationResult.operations["aggregate"] = {
                                success: true,
                                time_ms: aggregateTime,
                                aggregated_columns: Object.keys(aggregations).length
                            };
                        } catch (e) {
                            success = false;
                            iterationResult.operations["aggregate"] = {
                                success: false,
                                error: String(e)
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
                    row_count: rows,
                    column_count: cols,
                    data_type: dataType,
                    operations: operations,
                    iterations: iterationsData,
                    avg_read_time: readTimes.length > 0 ? readTimes.reduce((a, b) => a + b, 0) / readTimes.length : 0,
                    avg_write_time: writeTimes.length > 0 ? writeTimes.reduce((a, b) => a + b, 0) / writeTimes.length : 0,
                    avg_filter_time: filterTimes.length > 0 ? filterTimes.reduce((a, b) => a + b, 0) / filterTimes.length : 0,
                    avg_aggregate_time: aggregateTimes.length > 0 ? aggregateTimes.reduce((a, b) => a + b, 0) / aggregateTimes.length : 0
                };
                
                testCases.push(testCase);
            }
        }
    }
    
    // Calculate overall summary
    const summary: Summary = {
        total_tests: totalTests,
        successful_tests: successfulTests,
        failed_tests: failedTests,
        avg_read_time: allReadTimes.length > 0 ? allReadTimes.reduce((a, b) => a + b, 0) / allReadTimes.length : 0,
        avg_write_time: allWriteTimes.length > 0 ? allWriteTimes.reduce((a, b) => a + b, 0) / allWriteTimes.length : 0,
        avg_filter_time: allFilterTimes.length > 0 ? allFilterTimes.reduce((a, b) => a + b, 0) / allFilterTimes.length : 0,
        avg_aggregate_time: allAggregateTimes.length > 0 ? allAggregateTimes.reduce((a, b) => a + b, 0) / allAggregateTimes.length : 0
    };
    
    const endTime = Date.now();
    const totalExecutionTime = (endTime - startTime) / 1000;
    
    return {
        start_time: startTime / 1000,
        test_cases: testCases,
        summary: summary,
        end_time: endTime / 1000,
        total_execution_time: totalExecutionTime
    };
}

function main(): void {
    if (process.argv.length < 3) {
        console.error("Usage: node csv_processing.js <config_file>");
        process.exit(1);
    }
    
    const configFile = process.argv[2];
    
    try {
        const configContent = fs.readFileSync(configFile, 'utf8');
        const config: Config = JSON.parse(configContent);
        
        const results = runCSVProcessingBenchmark(config);
        
        console.log(JSON.stringify(results, null, 2));
    } catch (e) {
        if (e instanceof Error) {
            if ((e as any).code === 'ENOENT') {
                console.error(`Error: Config file '${configFile}' not found`);
            } else if (e instanceof SyntaxError) {
                console.error(`Error: Invalid JSON in config file: ${e.message}`);
            } else {
                console.error(`Error: ${e.message}`);
            }
        } else {
            console.error(`Error: ${String(e)}`);
        }
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}