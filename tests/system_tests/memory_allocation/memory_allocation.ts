#!/usr/bin/env node

/**
 * Memory allocation test implementation in TypeScript.
 * Measures memory allocation, deallocation, and management performance.
 */

import * as fs from 'fs';
import * as path from 'path';

interface Config {
  parameters: Parameters;
}

interface Parameters {
  allocation_sizes: number[];
  allocation_patterns: string[];
  allocation_counts: number[];
  data_structures: string[];
  iterations: number;
}

interface Results {
  start_time: number;
  test_cases: TestCase[];
  summary: Summary;
  end_time: number;
  total_execution_time: number;
}

interface TestCase {
  allocation_size: number;
  allocation_count: number;
  data_structure: string;
  allocation_pattern: string;
  iterations: IterationResult[];
  avg_allocation_time: number;
  avg_deallocation_time: number;
  avg_memory_efficiency: number;
}

interface IterationResult {
  iteration: number;
  initial_memory: number;
  allocation: AllocationResult;
  deallocation: DeallocationResult;
}

interface AllocationResult {
  success: boolean;
  time_ms: number;
  memory_used: number;
  peak_memory: number;
  memory_efficiency: number;
  items_allocated: number;
  error?: string;
}

interface DeallocationResult {
  success: boolean;
  time_ms: number;
  final_memory: number;
  memory_freed: number;
  error?: string;
}

interface Summary {
  total_tests: number;
  successful_tests: number;
  failed_tests: number;
  avg_allocation_time: number;
  avg_deallocation_time: number;
  avg_memory_efficiency: number;
}

// Memory tracking
function getMemoryUsage(): number {
  const memUsage = process.memoryUsage();
  return memUsage.rss;
}

function allocateArrays(size: number, count: number): number[][] {
  const arrays: number[][] = [];
  
  for (let i = 0; i < count; i++) {
    const array: number[] = [];
    for (let j = 0; j < size; j++) {
      array.push(Math.floor(Math.random() * 1000));
    }
    arrays.push(array);
  }
  
  return arrays;
}

function allocateHashMaps(size: number, count: number): Map<number, number>[] {
  const maps: Map<number, number>[] = [];
  
  for (let i = 0; i < count; i++) {
    const hashMap = new Map<number, number>();
    for (let j = 0; j < size; j++) {
      const key = Math.floor(Math.random() * size * 2);
      const value = Math.floor(Math.random() * 1000);
      hashMap.set(key, value);
    }
    maps.push(hashMap);
  }
  
  return maps;
}

class ListNode {
  value: number;
  next: ListNode | null;
  
  constructor(value: number, next: ListNode | null = null) {
    this.value = value;
    this.next = next;
  }
}

function allocateLinkedLists(size: number, count: number): ListNode[] {
  const lists: ListNode[] = [];
  
  for (let i = 0; i < count; i++) {
    let head: ListNode | null = null;
    for (let j = 0; j < size; j++) {
      const newNode = new ListNode(Math.floor(Math.random() * 1000));
      newNode.next = head;
      head = newNode;
    }
    if (head) {
      lists.push(head);
    }
  }
  
  return lists;
}

function runMemoryAllocationBenchmark(params: Parameters): Results {
  const startTime = Date.now() / 1000;
  const testCases: TestCase[] = [];
  const summary: Summary = {
    total_tests: 0,
    successful_tests: 0,
    failed_tests: 0,
    avg_allocation_time: 0,
    avg_deallocation_time: 0,
    avg_memory_efficiency: 0
  };
  
  const allAllocationTimes: number[] = [];
  const allDeallocationTimes: number[] = [];
  const allMemoryEfficiencies: number[] = [];
  
  for (const size of params.allocation_sizes) {
    for (const count of params.allocation_counts) {
      for (const structure of params.data_structures) {
        for (const pattern of params.allocation_patterns) {
          console.error(`Testing ${structure} allocation: size=${size}, count=${count}, pattern=${pattern}...`);
          
          const testCase: TestCase = {
            allocation_size: size,
            allocation_count: count,
            data_structure: structure,
            allocation_pattern: pattern,
            iterations: [],
            avg_allocation_time: 0,
            avg_deallocation_time: 0,
            avg_memory_efficiency: 0
          };
          
          const allocationTimes: number[] = [];
          const deallocationTimes: number[] = [];
          const memoryEfficiencies: number[] = [];
          
          for (let i = 0; i < params.iterations; i++) {
            console.error(`  Iteration ${i+1}/${params.iterations}...`);
            
            const initialMemory = getMemoryUsage();
            summary.total_tests++;
            
            const iterationResult: IterationResult = {
              iteration: i + 1,
              initial_memory: initialMemory,
              allocation: {
                success: false,
                time_ms: 0,
                memory_used: 0,
                peak_memory: 0,
                memory_efficiency: 0,
                items_allocated: count
              },
              deallocation: {
                success: false,
                time_ms: 0,
                final_memory: 0,
                memory_freed: 0
              }
            };
            
            let success = false;
            
            try {
              // Allocation phase
              const allocatorStart = process.hrtime.bigint();
              let allocatedData: any = null;
              
              switch (structure) {
                case "array":
                  allocatedData = allocateArrays(size, count);
                  break;
                case "hash_map":
                  allocatedData = allocateHashMaps(size, count);
                  break;
                case "linked_list":
                  allocatedData = allocateLinkedLists(size, count);
                  break;
                default:
                  throw new Error(`Unknown data structure: ${structure}`);
              }
              
              const allocatorEnd = process.hrtime.bigint();
              const allocationTime = Number(allocatorEnd - allocatorStart) / 1000000; // ms
              
              // Measure memory after allocation
              const peakMemory = getMemoryUsage();
              const memoryUsed = peakMemory - initialMemory;
              
              // Calculate theoretical vs actual memory usage
              let theoreticalSize = 0;
              if (structure === "array") {
                theoreticalSize = size * count * 8; // Assuming 8 bytes per number
              } else if (structure === "hash_map") {
                theoreticalSize = size * count * 16; // Key-value pairs
              } else { // linked_list
                theoreticalSize = size * count * 24; // Node overhead
              }
              
              const memoryEfficiency = memoryUsed > 0 ? (theoreticalSize / memoryUsed) * 100 : 0;
              
              allocationTimes.push(allocationTime);
              allAllocationTimes.push(allocationTime);
              memoryEfficiencies.push(memoryEfficiency);
              allMemoryEfficiencies.push(memoryEfficiency);
              
              iterationResult.allocation = {
                success: true,
                time_ms: allocationTime,
                memory_used: memoryUsed,
                peak_memory: peakMemory,
                memory_efficiency: memoryEfficiency,
                items_allocated: count
              };
              
              // Deallocation phase
              const deallocatorStart = process.hrtime.bigint();
              
              // Clear references to trigger deallocation
              allocatedData = null;
              
              // Force garbage collection if available
              if (global.gc) {
                global.gc();
              }
              
              const deallocatorEnd = process.hrtime.bigint();
              const deallocationTime = Number(deallocatorEnd - deallocatorStart) / 1000000; // ms
              const finalMemory = getMemoryUsage();
              
              deallocationTimes.push(deallocationTime);
              allDeallocationTimes.push(deallocationTime);
              
              iterationResult.deallocation = {
                success: true,
                time_ms: deallocationTime,
                final_memory: finalMemory,
                memory_freed: peakMemory - finalMemory
              };
              
              success = true;
            } catch (error: any) {
              iterationResult.allocation.success = false;
              iterationResult.allocation.error = error.message;
            }
            
            if (success) {
              summary.successful_tests++;
            } else {
              summary.failed_tests++;
            }
            
            testCase.iterations.push(iterationResult);
          }
          
          // Calculate averages for this test case
          if (allocationTimes.length > 0) {
            testCase.avg_allocation_time = allocationTimes.reduce((a, b) => a + b, 0) / allocationTimes.length;
          }
          if (deallocationTimes.length > 0) {
            testCase.avg_deallocation_time = deallocationTimes.reduce((a, b) => a + b, 0) / deallocationTimes.length;
          }
          if (memoryEfficiencies.length > 0) {
            testCase.avg_memory_efficiency = memoryEfficiencies.reduce((a, b) => a + b, 0) / memoryEfficiencies.length;
          }
          
          testCases.push(testCase);
        }
      }
    }
  }
  
  // Calculate overall summary
  if (allAllocationTimes.length > 0) {
    summary.avg_allocation_time = allAllocationTimes.reduce((a, b) => a + b, 0) / allAllocationTimes.length;
  }
  if (allDeallocationTimes.length > 0) {
    summary.avg_deallocation_time = allDeallocationTimes.reduce((a, b) => a + b, 0) / allDeallocationTimes.length;
  }
  if (allMemoryEfficiencies.length > 0) {
    summary.avg_memory_efficiency = allMemoryEfficiencies.reduce((a, b) => a + b, 0) / allMemoryEfficiencies.length;
  }
  
  const endTime = Date.now() / 1000;
  
  return {
    start_time: startTime,
    test_cases: testCases,
    summary: summary,
    end_time: endTime,
    total_execution_time: endTime - startTime
  };
}

function main() {
  if (process.argv.length < 3) {
    console.error("Usage: node memory_allocation.js <config_file>");
    process.exit(1);
  }
  
  const configFile = process.argv[2];
  
  try {
    const configData = fs.readFileSync(configFile, 'utf8');
    const config: Config = JSON.parse(configData);
    
    const results = runMemoryAllocationBenchmark(config.parameters);
    
    console.log(JSON.stringify(results, null, 2));
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      console.error(`Error: Config file '${configFile}' not found`);
    } else if (error instanceof SyntaxError) {
      console.error(`Error: Invalid JSON in config file: ${error.message}`);
    } else {
      console.error(`Error: ${error.message}`);
    }
    process.exit(1);
  }
}

// Run the main function
main();