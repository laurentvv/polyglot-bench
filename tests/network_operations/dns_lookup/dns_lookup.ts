#!/usr/bin/env node

import * as fs from 'fs';
import * as dns from 'dns';
import { promisify } from 'util';

interface DnsResult {
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
    domain_results: DnsResult[];
}

interface TestCase {
    resolution_mode: string;
    domains_count: number;
    iterations: IterationResult[];
    avg_resolution_time: number;
    fastest_resolution: number;
    slowest_resolution: number;
    success_rate: number;
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
    test_cases: TestCase[];
    summary: Summary;
    end_time: number;
    total_execution_time: number;
}

interface Config {
    parameters: {
        domains?: string[];
        resolution_modes?: string[];
        iterations?: number;
        timeout_seconds?: number;
        concurrent_workers?: number;
    };
}

const lookupAsync = promisify(dns.lookup);

// Simple DNS cache
const dnsCache = new Map<string, DnsResult>();

async function resolveDomainWithCache(domain: string, timeoutMs: number): Promise<DnsResult> {
    // Check cache first
    if (dnsCache.has(domain)) {
        return dnsCache.get(domain)!;
    }

    const start = process.hrtime.bigint();
    const result: DnsResult = {
        domain,
        success: false,
        response_time_ms: 0,
        ip_addresses: []
    };

    try {
        // Create timeout promise
        const timeoutPromise = new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error(`Timeout after ${timeoutMs}ms`)), timeoutMs);
        });

        // Race between DNS resolution and timeout
        const lookupPromise = lookupAsync(domain, { all: true }) as Promise<dns.LookupAddress[]>;
        const addresses = await Promise.race([lookupPromise, timeoutPromise]);
        
        const end = process.hrtime.bigint();
        result.response_time_ms = Number(end - start) / 1e6; // Convert nanoseconds to milliseconds
        
        if (addresses && Array.isArray(addresses)) {
            result.ip_addresses = addresses.map(addr => addr.address);
        }
        
        result.success = result.ip_addresses.length > 0;
        
    } catch (error) {
        const end = process.hrtime.bigint();
        result.response_time_ms = Number(end - start) / 1e6;
        result.error = `DNS resolution failed: ${error instanceof Error ? error.message : String(error)}`;
    }

    // Cache the result
    dnsCache.set(domain, result);
    
    return result;
}

async function resolveDomain(domain: string, timeoutMs: number): Promise<DnsResult> {
    return resolveDomainWithCache(domain, timeoutMs);
}

async function resolveDomainsSequential(domains: string[], timeoutMs: number): Promise<DnsResult[]> {
    const results: DnsResult[] = [];

    for (const domain of domains) {
        const result = await resolveDomain(domain, timeoutMs);
        const status = result.success ? '✓' : '✗';
        console.error(`  Resolved ${domain}: ${status} (${result.response_time_ms.toFixed(2)}ms)`);
        results.push(result);
    }

    return results;
}

async function resolveDomainsConcurrent(domains: string[], maxWorkers: number, timeoutMs: number): Promise<DnsResult[]> {
    // Use a more efficient semaphore implementation
    const semaphore = Array(maxWorkers).fill(null).map(() => Promise.resolve());
    let semaphoreIndex = 0;

    const promises = domains.map(async (domain) => {
        // Wait for an available slot
        await semaphore[semaphoreIndex];
        const currentIndex = semaphoreIndex;
        semaphoreIndex = (semaphoreIndex + 1) % maxWorkers;

        // Start resolution and update semaphore when done
        const resolutionPromise = resolveDomain(domain, timeoutMs);
        semaphore[currentIndex] = resolutionPromise.then(result => {
            const status = result.success ? '✓' : '✗';
            console.error(`  Resolved ${domain}: ${status} (${result.response_time_ms.toFixed(2)}ms)`);
            return result;
        }).then(() => {}); // Convert to Promise<void>

        return await resolutionPromise;
    });

    const results = await Promise.all(promises);
    
    // Sort results by domain name for consistent ordering
    results.sort((a, b) => a.domain.localeCompare(b.domain));
    
    return results;
}

async function runDnsBenchmark(config: Config): Promise<BenchmarkResult> {
    const params = config.parameters;
    
    // Set defaults
    const domains = params.domains || ['google.com', 'github.com', 'stackoverflow.com'];
    const resolutionModes = params.resolution_modes || ['sequential'];
    const iterations = params.iterations || 3;
    const timeoutSeconds = params.timeout_seconds || 5;
    const concurrentWorkers = params.concurrent_workers || 5;
    const timeoutMs = timeoutSeconds * 1000;
    
    const startTime = Date.now();
    const testCases: TestCase[] = [];
    const allResolutionTimes: number[] = [];
    let totalIterations = 0;
    
    for (const mode of resolutionModes) {
        console.error(`Testing DNS resolution mode: ${mode}...`);
        
        const modeResolutionTimes: number[] = [];
        let modeSuccessful = 0;
        let modeTotal = 0;
        const iterationsData: IterationResult[] = [];
        
        for (let i = 0; i < iterations; i++) {
            console.error(`  Iteration ${i + 1}/${iterations}...`);
            
            const iterationStart = process.hrtime.bigint();
            
            let domainResults: DnsResult[];
            switch (mode) {
                case 'sequential':
                    domainResults = await resolveDomainsSequential(domains, timeoutMs);
                    break;
                case 'concurrent':
                    domainResults = await resolveDomainsConcurrent(domains, concurrentWorkers, timeoutMs);
                    break;
                default:
                    console.error(`Warning: Unknown resolution mode '${mode}', using sequential`);
                    domainResults = await resolveDomainsSequential(domains, timeoutMs);
                    break;
            }
            
            const iterationEnd = process.hrtime.bigint();
            const iterationTotalTime = Number(iterationEnd - iterationStart) / 1e6; // Convert to milliseconds
            
            const iterationSuccessful = domainResults.filter(r => r.success).length;
            const iterationFailed = domainResults.length - iterationSuccessful;
            
            const successfulTimes = domainResults
                .filter(r => r.success)
                .map(r => r.response_time_ms);
            
            const iterationAvgTime = successfulTimes.length > 0 
                ? successfulTimes.reduce((sum, t) => sum + t, 0) / successfulTimes.length 
                : 0;
            
            // Collect timing data
            for (const result of domainResults) {
                if (result.success) {
                    modeResolutionTimes.push(result.response_time_ms);
                    allResolutionTimes.push(result.response_time_ms);
                }
            }
            
            modeSuccessful += iterationSuccessful;
            modeTotal += domainResults.length;
            totalIterations++;
            
            const iterationResult: IterationResult = {
                iteration: i + 1,
                total_time_ms: iterationTotalTime,
                domains_resolved: domainResults.length,
                successful_resolutions: iterationSuccessful,
                failed_resolutions: iterationFailed,
                avg_resolution_time_ms: iterationAvgTime,
                domain_results: domainResults
            };
            
            iterationsData.push(iterationResult);
        }
        
        // Calculate test case averages
        const avgResolutionTime = modeResolutionTimes.length > 0 
            ? modeResolutionTimes.reduce((sum, t) => sum + t, 0) / modeResolutionTimes.length 
            : 0;
        
        const fastestResolution = modeResolutionTimes.length > 0 ? Math.min(...modeResolutionTimes) : 0;
        const slowestResolution = modeResolutionTimes.length > 0 ? Math.max(...modeResolutionTimes) : 0;
        const successRate = modeTotal > 0 ? (modeSuccessful / modeTotal) * 100 : 0;
        
        const testCase: TestCase = {
            resolution_mode: mode,
            domains_count: domains.length,
            iterations: iterationsData,
            avg_resolution_time: avgResolutionTime,
            fastest_resolution: fastestResolution,
            slowest_resolution: slowestResolution,
            success_rate: successRate,
            total_successful: modeSuccessful,
            total_attempts: modeTotal
        };
        
        testCases.push(testCase);
    }
    
    // Calculate overall summary
    const successfulResolutions = allResolutionTimes.length;
    const failedResolutions = (totalIterations * domains.length) - successfulResolutions;
    
    const avgResolutionTime = allResolutionTimes.length > 0 
        ? allResolutionTimes.reduce((sum, t) => sum + t, 0) / allResolutionTimes.length 
        : 0;
    
    const fastestResolution = allResolutionTimes.length > 0 ? Math.min(...allResolutionTimes) : 0;
    const slowestResolution = allResolutionTimes.length > 0 ? Math.max(...allResolutionTimes) : 0;
    
    const endTime = Date.now();
    const executionTime = (endTime - startTime) / 1000; // Convert to seconds
    
    return {
        start_time: startTime,
        test_cases: testCases,
        summary: {
            total_domains: domains.length,
            total_iterations: totalIterations,
            successful_resolutions: successfulResolutions,
            failed_resolutions: failedResolutions,
            avg_resolution_time: avgResolutionTime,
            fastest_resolution: fastestResolution,
            slowest_resolution: slowestResolution
        },
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
        
        const results = await runDnsBenchmark(config);
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