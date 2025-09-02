# Multi-Language Performance Benchmark Tool - Project Context

## Project Overview

This project is a comprehensive multi-language performance benchmarking tool designed to compare the execution performance of identical algorithms implemented in different programming languages. The tool currently supports Python, Rust, Go, and TypeScript.

The orchestrator coordinates the execution of benchmarks across these languages, collects performance metrics (execution time, memory usage, CPU usage), and generates detailed comparative reports in multiple formats (JSON, HTML, CSV).

### Core Technologies

- **Primary Language**: Python 3.x
- **Supported Benchmark Languages**: Python, Rust, Go, TypeScript
- **Dependencies**: 
  - Core: `psutil`, `pandas`, `numpy`
  - Reporting: `jinja2`, `matplotlib`, `plotly`
  - Utilities: `colorama`, `tqdm`, `tabulate`
- **Build Tools**: Cargo (Rust), Go toolchain, TypeScript compiler (tsc)

## Project Structure

```
benchmark/
├── bench_orchestrator.py          # Main orchestrator script
├── bench.config.json             # Configuration file
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
├── src/                          # Core source code
│   ├── __init__.py
│   ├── orchestrator/             # Orchestrator components
│   │   ├── __init__.py
│   │   ├── core.py              # Core orchestrator class
│   │   ├── runners.py           # Language runners
│   │   ├── metrics.py           # Performance metrics collector
│   │   ├── results.py           # Results compilation
│   │   └── reports.py           # Report generation
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── config.py            # Configuration management
│       ├── validation.py        # Environment validation
│       └── helpers.py           # Helper functions
├── tests/                        # Benchmark test implementations
│   ├── algorithms/               # Algorithm benchmarks
│   │   ├── fibonacci/
│   │   │   ├── fibonacci.py
│   │   │   ├── fibonacci.rs
│   │   │   ├── fibonacci.go
│   │   │   ├── fibonacci.ts
│   │   │   └── input.json
│   │   ├── quicksort/
│   │   ├── binary_search/
│   │   └── prime_sieve/
│   ├── data_structures/          # Data structure benchmarks
│   │   ├── hash_table/
│   │   ├── binary_tree/
│   │   └── linked_list/
│   ├── mathematical/             # Mathematical computation benchmarks
│   │   ├── pi_calculation/
│   │   └── matrix_multiply/
│   └── io_operations/            # I/O operation benchmarks
│       ├── file_read/
│       └── json_parse/
├── results/                      # Generated reports and results
├── binaries/                     # Compiled binaries (temporary)
└── scripts/                      # Utility scripts
    ├── setup.py                 # Environment setup
    └── cleanup.py               # Cleanup utilities
```

## Building and Running

### Prerequisites

- Python 3.7+
- Node.js and npm (for TypeScript)
- Rust toolchain (for Rust benchmarks)
- Go toolchain (for Go benchmarks)

### Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install TypeScript dependencies:
   ```bash
   npm install
   ```

3. For Rust benchmarks, ensure Rust is installed:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

4. For Go benchmarks, install Go from https://golang.org

### Quick Start

1. Validate environments:
   ```bash
   python bench_orchestrator.py validate
   ```

2. Run all benchmarks:
   ```bash
   python bench_orchestrator.py run
   ```

3. View results in `./results/` directory

### Usage Examples

- Run specific languages:
  ```bash
  python bench_orchestrator.py run --languages python,rust
  ```

- Run specific tests:
  ```bash
  python bench_orchestrator.py run --tests fibonacci,quicksort
  ```

- Generate HTML report:
  ```bash
  python bench_orchestrator.py run --output html
  ```

- Custom iterations:
  ```bash
  python bench_orchestrator.py run --iterations 20
  ```

## Development Guidelines

### Code Organization

- **Core Logic**: Located in `src/orchestrator/`
  - `core.py`: Main orchestrator class that coordinates benchmark execution
  - `runners.py`: Language-specific runners that handle compilation and execution
  - `metrics.py`: Performance metrics collection
  - `results.py`: Results compilation and analysis
  - `reports.py`: Report generation in various formats

- **Utilities**: Located in `src/utils/`
  - `config.py`: Configuration management
  - `validation.py`: Environment validation
  - `helpers.py`: General helper functions

### Adding New Languages

1. Update `bench.config.json` with language configuration
2. Add a new runner class in `src/orchestrator/runners.py`
3. Register the runner in the `create_language_runners` factory function

### Adding New Tests

1. Create a new directory in the appropriate category under `tests/`
2. Implement the test in each supported language
3. Add the test name to the appropriate test suite in `bench.config.json`

### Configuration

The main configuration file `bench.config.json` controls:
- Language execution settings
- Test suite definitions
- Performance measurement parameters
- Output and reporting options
- System monitoring settings

## Testing

The project includes:
- Sample benchmark implementations in `tests/` directory
- Unit tests in `tests/` (TODO: Implement actual unit tests)
- Validation scripts for environment checking

To run validation:
```bash
python bench_orchestrator.py validate
```

## Reports and Results

Generated reports are saved in the `results/` directory by default. The tool can generate:
- JSON reports for programmatic access
- HTML reports with visualizations
- CSV reports for spreadsheet analysis

Reports include:
- Performance metrics for each language and test
- Comparative rankings
- System information
- Execution metadata