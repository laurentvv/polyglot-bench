#!/usr/bin/env node
/**
 * Ping test implementation in TypeScript/Node.js.
 * Measures network latency and packet loss to specified targets.
 * Optimized version for better performance using concurrent execution.
 */

import * as fs from 'fs';
import { spawn } from 'child_process';
import * as os from 'os';

interface Config {
    parameters: Parameters;
}

interface Parameters {
    targets: string[];
    packet_count?: number;
    timeout?: number;
}

interface PingResult {
    avg_latency: number;
    min_latency: number;
    max_latency: number;
    packet_loss: number;
    execution_time: number;
    error?: string;
}

interface Summary {
    total_targets: number;
    successful_targets: number;
    failed_targets: number;
    overall_avg_latency: number;
}

interface Results {
    start_time: number;
    targets: { [key: string]: PingResult };
    summary: Summary;
    end_time: number;
    total_execution_time: number;
}

function pingHost(host: string, count: number = 3, timeout: number = 3000): Promise<PingResult> {
    return new Promise((resolve) => {
        const startTime = Date.now();
        
        const isWindows = os.platform() === 'win32';
        const cmd = 'ping';
        const args = isWindows 
            ? ['-n', count.toString(), '-w', timeout.toString(), host]
            : ['-c', count.toString(), '-W', Math.ceil(timeout / 1000).toString(), host];

        const pingProcess = spawn(cmd, args);
        let stdout = '';
        let stderr = '';

        pingProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        pingProcess.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        pingProcess.on('close', (code) => {
            const executionTime = (Date.now() - startTime) / 1000;
            
            if (code !== 0) {
                resolve({
                    avg_latency: Infinity,
                    min_latency: Infinity,
                    max_latency: Infinity,
                    packet_loss: 100.0,
                    execution_time: executionTime,
                    error: stderr || 'Ping failed'
                });
                return;
            }

            const result = parsePingOutput(stdout, isWindows);
            result.execution_time = executionTime;
            resolve(result);
        });

        pingProcess.on('error', (error) => {
            const executionTime = (Date.now() - startTime) / 1000;
            resolve({
                avg_latency: Infinity,
                min_latency: Infinity,
                max_latency: Infinity,
                packet_loss: 100.0,
                execution_time: executionTime,
                error: error.message
            });
        });
    });
}

function parsePingOutput(output: string, isWindows: boolean): PingResult {
    const result: PingResult = {
        avg_latency: 0.0,
        min_latency: 0.0,
        max_latency: 0.0,
        packet_loss: 0.0,
        execution_time: 0.0
    };

    try {
        if (isWindows) {
            // Parse Windows ping output
            const lossMatch = output.match(/(\d+)% loss/);
            if (lossMatch) {
                result.packet_loss = parseFloat(lossMatch[1]);
            }

            // Extract individual ping times
            const timeMatches = output.match(/time[<>=]\s*(\d+)ms/g);
            if (timeMatches) {
                const times = timeMatches.map(match => {
                    const timeMatch = match.match(/(\d+)ms/);
                    return timeMatch ? parseFloat(timeMatch[1]) : 0;
                }).filter(time => time > 0);

                if (times.length > 0) {
                    result.min_latency = Math.min(...times);
                    result.max_latency = Math.max(...times);
                    result.avg_latency = times.reduce((a, b) => a + b, 0) / times.length;
                }
            }

            // Try to get average from summary line
            const avgMatch = output.match(/Average = (\d+)ms/);
            if (avgMatch) {
                result.avg_latency = parseFloat(avgMatch[1]);
            }
        } else {
            // Parse Unix/Linux ping output
            const lossMatch = output.match(/(\d+(?:\.\d+)?)% packet loss/);
            if (lossMatch) {
                result.packet_loss = parseFloat(lossMatch[1]);
            }

            // Parse rtt statistics
            const rttMatch = output.match(/rtt min\/avg\/max\/mdev = ([\d.]+)\/([\d.]+)\/([\d.]+)\/([\d.]+) ms/);
            if (rttMatch) {
                result.min_latency = parseFloat(rttMatch[1]);
                result.avg_latency = parseFloat(rttMatch[2]);
                result.max_latency = parseFloat(rttMatch[3]);
            }
        }
    } catch (error) {
        result.error = 'Failed to parse ping output';
    }

    // If no valid latency was parsed, mark as error
    if (result.avg_latency === 0.0 && result.packet_loss === 100.0) {
        result.error = 'Failed to parse ping output';
    }

    return result;
}

async function runPingBenchmark(params: Parameters): Promise<Results> {
    const startTime = Date.now() / 1000;
    
    const packetCount = params.packet_count || 3; // Reduced for better performance
    const timeout = params.timeout || 3000; // Reduced for better performance
    
    const targets: { [key: string]: PingResult } = {};
    let successfulTargets = 0;
    let failedTargets = 0;
    let totalLatency = 0.0;
    let successfulCount = 0;

    // Execute pings concurrently for better performance
    const pingPromises = params.targets.map(async (target) => {
        console.error(`Pinging ${target}...`);
        const pingResult = await pingHost(target, packetCount, timeout);
        return { target, pingResult };
    });

    // Wait for all pings to complete
    const results = await Promise.all(pingPromises);
    
    // Process results
    for (const { target, pingResult } of results) {
        targets[target] = pingResult;
        
        if (!pingResult.error && pingResult.packet_loss < 100.0) {
            successfulTargets++;
            if (isFinite(pingResult.avg_latency)) {
                totalLatency += pingResult.avg_latency;
                successfulCount++;
            }
        } else {
            failedTargets++;
        }
    }

    const overallAvgLatency = successfulCount > 0 ? totalLatency / successfulCount : 0.0;
    const endTime = Date.now() / 1000;

    return {
        start_time: startTime,
        targets,
        summary: {
            total_targets: params.targets.length,
            successful_targets: successfulTargets,
            failed_targets: failedTargets,
            overall_avg_latency: overallAvgLatency
        },
        end_time: endTime,
        total_execution_time: endTime - startTime
    };
}

async function main() {
    if (process.argv.length < 3) {
        console.error(`Usage: ${process.argv[1]} <config_file>`);
        process.exit(1);
    }

    const configFile = process.argv[2];

    try {
        const configContent = fs.readFileSync(configFile, 'utf8');
        const config: Config = JSON.parse(configContent);

        const results = await runPingBenchmark(config.parameters);
        console.log(JSON.stringify(results, null, 2));
    } catch (error) {
        if (error instanceof Error) {
            console.error(`Error: ${error.message}`);
        } else {
            console.error(`Error: ${error}`);
        }
        process.exit(1);
    }
}

// Always run main for benchmark purposes
main().catch(error => {
    console.error('Unhandled error:', error);
    process.exit(1);
});