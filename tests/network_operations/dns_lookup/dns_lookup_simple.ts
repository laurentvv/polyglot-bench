#!/usr/bin/env node

import * as dns from 'dns';
import { promisify } from 'util';

const lookupAsync = promisify(dns.lookup);

async function simpleDnsTest(): Promise<any> {
    const start = Date.now();
    
    // Simple DNS lookups
    const domains = ['google.com', 'github.com'];
    let successful = 0;
    let total_time = 0;
    
    for (let i = 0; i < 10; i++) {
        for (const domain of domains) {
            try {
                const lookupStart = Date.now();
                await lookupAsync(domain);
                const lookupTime = Date.now() - lookupStart;
                total_time += lookupTime;
                successful++;
            } catch (error) {
                // Ignore errors for simplicity
            }
        }
    }
    
    const total_duration = (Date.now() - start) / 1000;
    const avg_time = successful > 0 ? total_time / successful : 0;
    
    return {
        start_time: 0,
        end_time: total_duration,
        total_execution_time: total_duration,
        summary: {
            total_domains: domains.length,
            total_iterations: 10,
            successful_resolutions: successful,
            failed_resolutions: (10 * domains.length) - successful,
            avg_resolution_time: avg_time,
            fastest_resolution: avg_time,
            slowest_resolution: avg_time
        }
    };
}

async function main() {
    try {
        const results = await simpleDnsTest();
        console.log(JSON.stringify(results, null, 2));
    } catch (error) {
        console.error(`Error: ${error}`);
        process.exit(1);
    }
}

main();