# Changelog

## [1.3.0] - 2025-09-02

### Added
- Optimized JSON parsing benchmark implementations across all languages
- Created performance comparison script for measuring improvements
- Added JSON_PARSING_OPTIMIZATIONS.md documentation

### Changed
- Improved performance of JSON parsing test in all languages by 6-24%
- Updated README with latest performance results for JSON parsing test
- Converted package.json to use ES modules for TypeScript compatibility

## [1.2.0] - 2025-09-02

### Added
- Optimized Python implementation of CSV processing benchmark for better performance
- Created performance comparison script for measuring improvements

### Changed
- Improved performance of CSV processing test in Python by ~26% (from ~28s to ~21s)
- Updated README with latest performance results for CSV processing test

## [1.1.0] - 2025-09-02

### Fixed
- Resolved Go compilation errors in memory_allocation test by properly handling unused variables
- Fixed Rust compilation errors in large_file_read test by enhancing tempfile dependency detection
- Addressed Unicode encoding issues in orchestrator script for better Windows compatibility
- Fixed Python runner environment issue by using sys.executable for proper dependency management

### Changed
- Updated README to include reference to fixes summary
- Enhanced troubleshooting documentation to reflect current status of issues
- Updated implementation documentation to reflect recent fixes

### Added
- Created FIXES_SUMMARY.md to document compilation fixes
- Added .gitignore file to exclude compiled binaries and temporary files