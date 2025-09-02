#!/usr/bin/env node
/**
 * HTTP request test implementation in TypeScript/Node.js.
 * Measures HTTP request/response performance to specified endpoints.
 */

import * as fs from 'fs';
import * as https from 'https';
import axios from 'axios';

interface Config {
    parameters: Parameters;
}

interface Parameters {
    urls: string[];
    request_count?: number;
    timeout?: number;
    methods?: string[];
    concurrent_requests?: number;
}

interface RequestResult {
    success: boolean;
    response_time: number;
    status_code: number;
    content_length: number;
    error?: string;
}

interface URLResults {
    requests: RequestResult[];
    avg_response_time: number;
    success_rate: number;
    total_requests: number;
    successful_requests: number;
}

interface Summary {
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    avg_response_time: number;
    min_response_time: number;
    max_response_time: number;
    success_rate: number;
}

interface Results {
    start_time: number;
    urls: { [key: string]: URLResults };
    summary: Summary;
    end_time: number;
    total_execution_time: number;
}

async function makeHTTPRequest(url: string, method: string = 'GET', timeoutMs: number = 10000): Promise<RequestResult> {
    const startTime = Date.now();

    try {
        // Create axios instance with configuration
        const axiosInstance = axios.create({
            timeout: timeoutMs,
            headers: {
                'User-Agent': 'BenchmarkTool/1.0'
            },
            httpsAgent: new https.Agent({
                rejectUnauthorized: false // Allow self-signed certificates
            }),
            validateStatus: () => true // Don't throw errors for HTTP error status codes
        });

        const response = await axiosInstance({
            method: method.toLowerCase(),
            url: url
        });

        const responseTime = Date.now() - startTime;
        const isSuccess = response.status >= 200 && response.status < 300;

        return {
            success: isSuccess,
            response_time: responseTime,
            status_code: response.status,
            content_length: JSON.stringify(response.data).length,
            error: isSuccess ? undefined : `HTTP Error ${response.status}`
        };

    } catch (error: any) {
        const responseTime = Date.now() - startTime;
        
        let statusCode = 0;
        let errorMessage = error.message;

        if (error.response) {
            statusCode = error.response.status;
            errorMessage = `HTTP Error ${statusCode}: ${error.response.statusText}`;
        } else if (error.request) {
            errorMessage = 'Network error: No response received';
        } else if (error.code === 'ECONNABORTED') {
            errorMessage = 'Request timeout';
        }

        return {
            success: false,
            response_time: responseTime,
            status_code: statusCode,
            content_length: 0,
            error: errorMessage
        };
    }
}

async function runHTTPBenchmark(params: Parameters): Promise<Results> {
    const startTime = Date.now() / 1000;

    const requestCount = params.request_count || 5;
    const timeout = params.timeout || 10000;
    const methods = params.methods || ['GET'];

    const urlsResults: { [key: string]: URLResults } = {};
    let totalRequests = 0;
    let successfulRequests = 0;
    let totalResponseTime = 0;
    let minResponseTime = Infinity;
    let maxResponseTime = 0;

    for (const url of params.urls) {
        console.error(`Testing ${url}...`);

        const urlResults: URLResults = {
            requests: [],
            avg_response_time: 0,
            success_rate: 0,
            total_requests: 0,
            successful_requests: 0
        };

        const urlResponseTimes: number[] = [];
        let urlSuccessful = 0;

        for (const method of methods) {
            for (let i = 0; i < requestCount; i++) {
                console.error(`  Request ${i + 1}/${requestCount} (${method})...`);

                const requestResult = await makeHTTPRequest(url, method, timeout);

                totalRequests++;
                urlResults.total_requests++;

                if (requestResult.success) {
                    successfulRequests++;
                    urlSuccessful++;

                    const responseTime = requestResult.response_time;
                    urlResponseTimes.push(responseTime);
                    totalResponseTime += responseTime;
                    minResponseTime = Math.min(minResponseTime, responseTime);
                    maxResponseTime = Math.max(maxResponseTime, responseTime);
                }

                urlResults.requests.push(requestResult);
            }
        }

        urlResults.successful_requests = urlSuccessful;
        urlResults.success_rate = urlResults.total_requests > 0 
            ? (urlSuccessful / urlResults.total_requests) * 100 
            : 0;

        if (urlResponseTimes.length > 0) {
            urlResults.avg_response_time = urlResponseTimes.reduce((a, b) => a + b, 0) / urlResponseTimes.length;
        }

        urlsResults[url] = urlResults;
    }

    const successRate = totalRequests > 0 ? (successfulRequests / totalRequests) * 100 : 0;
    const avgResponseTime = successfulRequests > 0 ? totalResponseTime / successfulRequests : 0;

    if (minResponseTime === Infinity) {
        minResponseTime = 0;
    }

    const endTime = Date.now() / 1000;

    return {
        start_time: startTime,
        urls: urlsResults,
        summary: {
            total_requests: totalRequests,
            successful_requests: successfulRequests,
            failed_requests: totalRequests - successfulRequests,
            avg_response_time: avgResponseTime,
            min_response_time: minResponseTime,
            max_response_time: maxResponseTime,
            success_rate: successRate
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

        const results = await runHTTPBenchmark(config.parameters);
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

if (require.main === module) {
    main().catch(error => {
        console.error('Unhandled error:', error);
        process.exit(1);
    });
}