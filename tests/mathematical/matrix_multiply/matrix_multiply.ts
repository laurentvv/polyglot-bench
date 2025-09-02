#!/usr/bin/env node

function createMatrix(rows: number, cols: number): number[][] {
    const matrix: number[][] = [];
    for (let i = 0; i < rows; i++) {
        matrix[i] = [];
        for (let j = 0; j < cols; j++) {
            matrix[i][j] = Math.random() * 100;
        }
    }
    return matrix;
}

function multiplyMatrices(a: number[][], b: number[][]): number[][] {
    const rowsA = a.length;
    const colsA = a[0].length;
    const colsB = b[0].length;
    
    const result: number[][] = [];
    for (let i = 0; i < rowsA; i++) {
        result[i] = new Array(colsB).fill(0);
    }
    
    for (let i = 0; i < rowsA; i++) {
        for (let j = 0; j < colsB; j++) {
            for (let k = 0; k < colsA; k++) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    
    return result;
}

function main(): void {
    const size = 200; // Matrix size (200x200)
    
    console.log(`Multiplying two ${size}x${size} matrices...`);
    
    // Create matrices
    const createStart = process.hrtime.bigint();
    const matrixA = createMatrix(size, size);
    const matrixB = createMatrix(size, size);
    const createTime = Number(process.hrtime.bigint() - createStart) / 1e9;
    
    // Multiply matrices
    const multiplyStart = process.hrtime.bigint();
    const result = multiplyMatrices(matrixA, matrixB);
    const multiplyTime = Number(process.hrtime.bigint() - multiplyStart) / 1e9;
    
    const totalTime = createTime + multiplyTime;
    
    // Verify result dimensions
    const resultRows = result.length;
    const resultCols = result[0].length;
    
    console.log(`Result: ${resultRows}x${resultCols} matrix`);
    console.log(`Sample result[0][0]: ${result[0][0].toFixed(6)}`);
    console.log("Timing:");
    console.log(`  Matrix creation: ${createTime.toFixed(6)} seconds`);
    console.log(`  Matrix multiplication: ${multiplyTime.toFixed(6)} seconds`);
    console.log(`  Total time: ${totalTime.toFixed(6)} seconds`);
}

main();
