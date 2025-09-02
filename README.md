# Multi-Language Performance Benchmark Tool

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A comprehensive performance benchmarking tool that compares execution performance across Python, Rust, Go, and TypeScript implementations.

## 🚀 Overview

The Multi-Language Performance Benchmark Tool is designed to provide accurate and meaningful performance comparisons across different programming languages. It implements standardized computational benchmarks that measure execution time, memory usage, and CPU efficiency for equivalent algorithms across four major programming languages.

### Key Features

- **Cross-Language Comparison**: Benchmark the same algorithms across Python, Rust, Go, and TypeScript
- **Comprehensive Metrics**: Detailed performance analysis including execution time, memory usage, and CPU efficiency
- **Statistical Analysis**: Reliable results through statistical significance testing and confidence intervals
- **Multiple Test Categories**: Algorithmic, data structure, mathematical, and I/O operation benchmarks
- **Extensible Architecture**: Easy to add new languages and test implementations
- **Professional Reporting**: Generate JSON, HTML, and CSV reports with visualizations

## 📊 Benchmark Categories

### Algorithms
- Fibonacci sequence calculation
- Quicksort implementation
- Binary search algorithms
- Prime number sieving

### Data Structures
- Hash table operations
- Binary tree traversal
- Linked list manipulation

### Mathematical Computations
- Pi calculation using Monte Carlo method
- Matrix multiplication operations

### I/O Operations
- Large file reading performance
- JSON parsing efficiency
- CSV processing benchmarks

### System Tests
- Memory allocation and deallocation performance
- Garbage collection efficiency

## 🛠️ Installation

### Prerequisites

- Python 3.7+
- Node.js and npm (for TypeScript)
- Rust toolchain (for Rust benchmarks)
- Go toolchain (for Go benchmarks)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/multi-language-benchmark.git
cd multi-language-benchmark

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install TypeScript dependencies
npm install

# Validate language environments
python bench_orchestrator.py validate
```

### Language-Specific Setup

**Rust Setup:**
```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**Go Setup:**
Download and install Go from [golang.org](https://golang.org/dl/)

## 🏃 Usage

### Run All Benchmarks

```bash
python bench_orchestrator.py run
```

### Run Specific Languages

```bash
python bench_orchestrator.py run --languages python,rust,go
```

### Run Specific Tests

```bash
python bench_orchestrator.py run --tests fibonacci,quicksort --iterations 20
```

### Generate Reports

```bash
# Generate HTML report with visualizations
python bench_orchestrator.py run --output html

# Generate all report formats
python bench_orchestrator.py run --output all
```

### Custom Configuration

```bash
# List available tests and languages
python bench_orchestrator.py list --tests
python bench_orchestrator.py list --languages
```

## 📈 Sample Results

The tool generates comprehensive performance reports showing relative performance across languages:

| Test | Python | Rust | Go | TypeScript |
|------|--------|------|----|------------|
| Fibonacci (n=35) | 1.24s | 0.075s | 0.164s | 0.088s |
| Quicksort (1M elements) | 0.842s | 0.126s | 0.285s | 0.192s |
| Pi Calculation | 0.153s | 0.062s | 0.142s | 0.492s |
| CSV Processing (50K rows) | 20.68s | 6.15s | 5.59s | 12.99s |
| JSON Parsing (100K objects) | 9.51s | 7.50s | 6.80s | 9.10s |
| Ping Test (3 targets) | 8.25s | 6.75s | 5.80s | 7.90s |
| DNS Lookup (6 domains) | 4.85s | 3.75s | 2.90s | 4.20s |

## 📁 Project Structure

```
benchmark/
├── bench_orchestrator.py          # Main orchestrator script
├── bench.config.json             # Configuration file
├── requirements.txt               # Python dependencies
├── README.md                     # Project documentation
├── src/                          # Core source code
│   ├── orchestrator/             # Orchestrator components
│   │   ├── core.py              # Core orchestrator class
│   │   ├── runners.py           # Language runners
│   │   ├── metrics.py           # Performance metrics collector
│   │   ├── results.py           # Results compilation
│   │   └── reports.py           # Report generation
│   └── utils/                    # Utility functions
│       ├── config.py            # Configuration management
│       ├── validation.py        # Environment validation
│       └── helpers.py           # Helper functions
├── tests/                        # Benchmark test implementations
│   ├── algorithms/               # Algorithm benchmarks
│   ├── data_structures/          # Data structure benchmarks
│   ├── mathematical/             # Mathematical computation benchmarks
│   ├── io_operations/            # I/O operation benchmarks
│   ├── system_tests/            # System performance benchmarks
│   └── network_operations/      # Network operation benchmarks
├── results/                      # Generated reports and results
└── scripts/                     # Utility scripts
    ├── setup.py                 # Environment setup
    └── cleanup.py               # Cleanup utilities
```

## 🎯 Recent Improvements

Recent fixes have resolved critical compilation and execution issues:

### Compilation Fixes
- **Go**: Resolved "declared and not used" compilation errors in memory allocation tests
- **Rust**: Fixed tempfile dependency detection for I/O operation tests
- **Python**: Enhanced runner environment isolation for proper dependency management

### Performance Enhancements
- Improved subprocess handling for more reliable test execution
- Enhanced error handling and reporting
- Better cross-platform compatibility
- **Python CSV Processing**: Optimized implementation for ~26% performance improvement

See [FIXES_SUMMARY.md](FIXES_SUMMARY.md) for detailed information on recent improvements and [PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md) for details on performance optimization strategies.

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

### Ways to Contribute

1. **Add New Benchmarks**: Implement additional test cases in any of the supported languages
2. **Support New Languages**: Extend the tool to support additional programming languages
3. **Improve Existing Tests**: Optimize current benchmark implementations
4. **Enhance Reporting**: Add new visualization types or report formats
5. **Bug Fixes**: Report and fix any issues you encounter

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by various language performance comparison studies
- Built with performance analysis libraries including pandas, numpy, and matplotlib
- Thanks to the open-source community for language-specific optimization techniques

## 📞 Support

If you encounter any issues or have questions about the benchmark tool, please [open an issue](https://github.com/yourusername/multi-language-benchmark/issues) on GitHub.