#!/usr/bin/env ts-node

import * as dns from 'dns';
import * as fs from 'fs';
import { promisify } from 'util';

const lookupAsync = promisify(dns.lookup);

interface DomainResult {
    domain: string;
    success: boolean;
    response_time_ms: number;
    ip_addresses: string[];
    error?: string;
}

interface IterationResult {
    iteration: number;
    total_time_ms: number;
    domains_resolved: number;
    successful_resolutions: number;
    failed_resolutions: number;
    avg_resolution_time_ms: number;
    domain_results: DomainResult[];
}

interface TestCase {
    resolution_mode: string;
    domains_count: number;
    iterations: IterationResult[];
    avg_resolution_time: number;
    success_rate: number;
    total_time: number;
    fastest_resolution?: number;
    slowest_resolution?: number;
    total_successful: number;
    total_attempts: number;
}

interface Summary {
    total_domains: number;
    total_iterations: number;
    successful_resolutions: number;
    failed_resolutions: number;
    avg_resolution_time: number;
    fastest_resolution: number;
    slowest_resolution: number;
}

interface BenchmarkResult {
    start_time: number;
    end_time: number;
    total_execution_time: number;
    test_cases: TestCase[];
    summary: Summary;
}

function resolveDomain(domain: string, timeout: number = 5000): Promise<DomainResult> {
    return new Promise((resolve) => {
        // For now, we're not implementing a cache since requiring external packages may not be supported
        const start = Date.now();
        const result: DomainResult = {
            domain,
            success: false,
            response_time_ms: 0,
            ip_addresses: []
        };

        // Set up timeout
        const timeoutId = setTimeout(() => {
            const end = Date.now();
            result.response_time_ms = end - start;
            result.error = 'Timeout';
            resolve(result);
        }, timeout);

        // Perform DNS lookup
        lookupAsync(domain, { family: 4 }, (err, address) => {
            // Clear timeout since we got a response
            clearTimeout(timeoutId);
            
            const end = Date.now();
            result.response_time_ms = end - start;
            
            if (err) {
                result.error = (err as Error).message;
                resolve(result);
            } else {
                result.success = true;
                result.ip_addresses = [address];
                resolve(result);
            }
        });
    });
}

async function resolveDomainsSequential(domains: string[], timeout: number = 5000): Promise<DomainResult[]> {
    const results: DomainResult[] = [];
    
    for (const domain of domains) {
        const result = await resolveDomain(domain, timeout);
        results.push(result);
        console.error(`  Resolved ${domain}: ${result.success ? '✓' : '✗'} (${result.response_time_ms.toFixed(2)}ms)`);
    }
    
    return results;
}

async function resolveDomainsConcurrent(domains: string[], timeout: number = 5000): Promise<DomainResult[]> {
    const promises = domains.map(domain => resolveDomain(domain, timeout));
    const results = await Promise.all(promises);
    
    for (const result of results) {
        console.error(`  Resolved ${result.domain}: ${result.success ? '✓' : '✗'} (${result.response_time_ms.toFixed(2)}ms)`);
    }
    
    // Sort results by domain name to maintain consistent order
    results.sort((a, b) => a.domain.localeCompare(b.domain));
    return results;
}

async function runDnsBenchmark(config: any): Promise<BenchmarkResult> {
    const domains = config.domains || ['google.com', 'github.com', 'stackoverflow.com'];
    const resolutionModes = config.resolution_modes || ['sequential'];
    const iterations = config.iterations || 3;
    const timeout = (config.timeout_seconds || 5) * 1000; // Convert to ms

    const startTime = Date.now();
    const testCases: TestCase[] = [];
    const allResolutionTimes: number[] = [];
    let totalIterations = 0;

    for (const mode of resolutionModes) {
        console.error(`Testing DNS resolution mode: ${mode}...`);

        const testCase: TestCase = {
            resolution_mode: mode,
            domains_count: domains.length,
            iterations: [],
            avg_resolution_time: 0,
            success_rate: 0,
            total_time: 0,
            total_successful: 0,
            total_attempts: 0
        };

        const modeResolutionTimes: number[] = [];
        let modeSuccessful = 0;
        let modeTotal = 0;

        for (let i = 0; i < iterations; i++) {
            console.error(`  Iteration ${i + 1}/${iterations}...`);
            totalIterations++;

            const iterationStart = Date.now();

            let domainResults: DomainResult[];
            if (mode === 'sequential') {
                domainResults = await resolveDomainsSequential(domains, timeout);
            } else if (mode === 'concurrent') {
                domainResults = await resolveDomainsConcurrent(domains, timeout);
            } else {
                console.error(`Warning: Unknown resolution mode '${mode}', using sequential`);
                domainResults = await resolveDomainsSequential(domains, timeout);
            }

            const iterationEnd = Date.now();
            const iterationTotalTime = iterationEnd - iterationStart;

            // Calculate iteration statistics
            const iterationSuccessful = domainResults.filter(r => r.success).length;
            const iterationFailed = domainResults.length - iterationSuccessful;
            const successfulTimes = domainResults.filter(r => r.success).map(r => r.response_time_ms);
            const iterationAvgTime = successfulTimes.length > 0 
                ? successfulTimes.reduce((a, b) => a + b, 0) / successfulTimes.length 
                : 0;

            // Collect timing data
            modeResolutionTimes.push(...successfulTimes);
            allResolutionTimes.push(...successfulTimes);

            modeSuccessful += iterationSuccessful;
            modeTotal += domainResults.length;

            const iterationResult: IterationResult = {
                iteration: i + 1,
                total_time_ms: iterationTotalTime,
                domains_resolved: domainResults.length,
                successful_resolutions: iterationSuccessful,
                failed_resolutions: iterationFailed,
                avg_resolution_time_ms: iterationAvgTime,
                domain_results: domainResults
            };

            testCase.iterations.push(iterationResult);
        }

        // Calculate test case averages
        if (modeResolutionTimes.length > 0) {
            testCase.avg_resolution_time = modeResolutionTimes.reduce((a, b) => a + b, 0) / modeResolutionTimes.length;
            testCase.fastest_resolution = Math.min(...modeResolutionTimes);
            testCase.slowest_resolution = Math.max(...modeResolutionTimes);
        }

        testCase.success_rate = modeTotal > 0 ? (modeSuccessful / modeTotal) * 100 : 0;
        testCase.total_successful = modeSuccessful;
        testCase.total_attempts = modeTotal;

        testCases.push(testCase);
    }

    const endTime = Date.now();
    const totalExecutionTime = (endTime - startTime) / 1000; // Convert to seconds

    // Calculate overall summary
    const successfulResolutions = allResolutionTimes.length;
    const failedResolutions = (totalIterations * domains.length) - successfulResolutions;
    const avgResolutionTime = allResolutionTimes.length > 0 
        ? allResolutionTimes.reduce((a, b) => a + b, 0) / allResolutionTimes.length 
        : 0;
    const fastestResolution = allResolutionTimes.length > 0 ? Math.min(...allResolutionTimes) : 0;
    const slowestResolution = allResolutionTimes.length > 0 ? Math.max(...allResolutionTimes) : 0;

    return {
        start_time: startTime / 1000, // Convert to seconds
        end_time: endTime / 1000,
        total_execution_time: totalExecutionTime,
        test_cases: testCases,
        summary: {
            total_domains: domains.length,
            total_iterations: totalIterations,
            successful_resolutions: successfulResolutions,
            failed_resolutions: failedResolutions,
            avg_resolution_time: avgResolutionTime,
            fastest_resolution: fastestResolution,
            slowest_resolution: slowestResolution
        }
    };
}

async function main() {
    if (process.argv.length < 3) {
        console.error('Usage: ts-node dns_lookup.ts <config_file>');
        process.exit(1);
    }

    const configFile = process.argv[2];

    try {
        const configData = fs.readFileSync(configFile, 'utf8');
        const config = JSON.parse(configData);
        const parameters = config.parameters || {};
        
        const results = await runDnsBenchmark(parameters);
        console.log(JSON.stringify(results, null, 2));

    } catch (error) {
        if (error instanceof Error) {
            if (error.message.includes('ENOENT')) {
                console.error(`Error: Config file '${configFile}' not found`);
            } else if (error.message.includes('JSON')) {
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

main();