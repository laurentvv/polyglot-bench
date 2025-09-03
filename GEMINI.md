# Project Overview

This project is a multi-language performance benchmark tool that compares the execution performance of Python, Rust, Go, and TypeScript across a variety of computational benchmarks.

**Key Technologies:**

*   **Python:** The core orchestration logic is written in Python.
*   **Rust, Go, TypeScript:** These are the languages being benchmarked, in addition to Python.
*   **JSON:** Used for configuration (`bench.config.json`) and data interchange.

**Architecture:**

The tool is designed with a modular architecture:

*   `bench_orchestrator.py`: The main entry point that handles command-line parsing and orchestrates the benchmark runs.
*   `src/orchestrator`: Contains the core logic for running benchmarks, collecting metrics, and generating reports.
*   `src/utils`: Provides utility functions for configuration, validation, and data generation.
*   `tests`: Contains the benchmark test implementations for each language, categorized by domain (e.g., algorithms, data structures).
*   `results`: The default directory for storing benchmark results.

# Building and Running

**Prerequisites:**

*   Python 3.7+
*   Node.js and npm
*   Rust toolchain
*   Go toolchain

**Installation:**

1.  **Clone the repository.**
2.  **Create a virtual environment:** `python -m venv .venv`
3.  **Activate the virtual environment:**
    *   Windows: `.venv\Scripts\activate`
    *   macOS/Linux: `source .venv/bin/activate`
4.  **Install Python dependencies:** `pip install -r requirements.txt`
5.  **Install TypeScript dependencies:** `npm install`

**Running Benchmarks:**

*   **Run all benchmarks:**
    ```bash
    python bench_orchestrator.py run
    ```
*   **Run benchmarks for specific languages:**
    ```bash
    python bench_orchestrator.py run --languages python,rust
    ```
*   **Run specific tests:**
    ```bash
    python bench_orchestrator.py run --tests fibonacci,quicksort
    ```

**Validating Environment:**

*   **Check that all language runtimes are correctly installed:**
    ```bash
    python bench_orchestrator.py validate
    ```

**Listing Tests and Languages:**

*   **List available tests:**
    ```bash
    python bench_orchestrator.py list --tests
    ```
*   **List available languages:**
    ```bash
    python bench_orchestrator.py list --languages
    ```

# Development Conventions

*   **Code Style:** The Python code follows the PEP 8 style guide.
*   **Testing:** The `tests` directory contains the benchmark implementations. The project also uses `pytest` for development testing.
*   **Contributions:** The `CONTRIBUTING.md` file provides guidelines for contributing to the project.
*   **Configuration:** The `bench.config.json` file is the central place for configuring benchmark runs, including languages, test suites, and output settings.
