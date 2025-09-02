#!/usr/bin/env python3
"""
Cleanup script to remove unnecessary files from the benchmark project.
"""

import os
import glob
import shutil

def cleanup_unnecessary_files():
    """Remove unnecessary files and directories."""
    
    # Files to remove
    files_to_remove = [
        "debug_python_test.py",
        "test_fixes.py", 
        "test_fixes.config.json"
    ]
    
    # Remove individual files
    for file_path in files_to_remove:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                print(f"Removed: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    # Remove old result files (keep only the most recent few)
    results_dir = os.path.join(os.getcwd(), "results")
    if os.path.exists(results_dir):
        # Get all result files
        json_files = glob.glob(os.path.join(results_dir, "*.json"))
        csv_files = glob.glob(os.path.join(results_dir, "*.csv"))
        html_files = glob.glob(os.path.join(results_dir, "*.html"))
        
        # Sort by modification time (newest first)
        all_files = json_files + csv_files + html_files
        all_files.sort(key=os.path.getmtime, reverse=True)
        
        # Keep only the most recent 10 files of each type
        files_to_keep = set(all_files[:10])
        
        # Remove older files
        for file_path in all_files[10:]:
            try:
                os.remove(file_path)
                print(f"Removed old result: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    # Remove all binaries (they can be regenerated)
    binaries_dir = os.path.join(os.getcwd(), "binaries")
    if os.path.exists(binaries_dir):
        try:
            shutil.rmtree(binaries_dir)
            os.makedirs(binaries_dir)  # Recreate empty directory
            print("Cleaned binaries directory")
        except Exception as e:
            print(f"Error cleaning binaries directory: {e}")
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                print(f"Removed: {pycache_path}")
            except Exception as e:
                print(f"Error removing {pycache_path}: {e}")
    
    print("Cleanup completed!")

if __name__ == "__main__":
    cleanup_unnecessary_files()