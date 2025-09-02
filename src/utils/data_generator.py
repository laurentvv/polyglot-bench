"""
Test data generation utilities for benchmark tests.
Generates various file sizes, data types, and structured data for testing.
"""

import os
import json
import csv
import random
import string
import gzip
import tempfile
from typing import Dict, List, Any, Union
from pathlib import Path


class DataGenerator:
    """Utility class for generating test data files."""
    
    def __init__(self, base_dir: str = None):
        """Initialize with optional base directory for test data."""
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.gettempdir())
        self.base_dir.mkdir(exist_ok=True)
    
    def generate_text_file(self, size_mb: float, filename: str = None) -> str:
        """Generate a text file of specified size in MB."""
        if filename is None:
            filename = f"test_text_{size_mb}mb.txt"
        
        filepath = self.base_dir / filename
        target_size = int(size_mb * 1024 * 1024)  # Convert to bytes
        
        with open(filepath, 'w', encoding='utf-8') as f:
            written = 0
            while written < target_size:
                # Generate paragraphs of random text
                paragraph = self._generate_paragraph()
                f.write(paragraph + '\n\n')
                written += len(paragraph.encode('utf-8')) + 2
        
        return str(filepath)
    
    def generate_binary_file(self, size_mb: float, filename: str = None) -> str:
        """Generate a binary file of specified size in MB."""
        if filename is None:
            filename = f"test_binary_{size_mb}mb.bin"
        
        filepath = self.base_dir / filename
        target_size = int(size_mb * 1024 * 1024)
        
        with open(filepath, 'wb') as f:
            chunk_size = 8192
            written = 0
            while written < target_size:
                chunk = bytes(random.getrandbits(8) for _ in range(
                    min(chunk_size, target_size - written)
                ))
                f.write(chunk)
                written += len(chunk)
        
        return str(filepath)
    
    def generate_json_file(self, num_records: int, filename: str = None) -> str:
        """Generate a JSON file with specified number of records."""
        if filename is None:
            filename = f"test_data_{num_records}records.json"
        
        filepath = self.base_dir / filename
        
        data = []
        for i in range(num_records):
            record = {
                "id": i + 1,
                "name": self._generate_name(),
                "email": self._generate_email(),
                "age": random.randint(18, 80),
                "address": {
                    "street": self._generate_street(),
                    "city": self._generate_city(),
                    "zipcode": f"{random.randint(10000, 99999)}"
                },
                "scores": [random.randint(0, 100) for _ in range(5)],
                "metadata": {
                    "created_at": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                    "active": random.choice([True, False]),
                    "tags": random.sample(["python", "rust", "go", "typescript", "benchmark", "performance"], 
                                        k=random.randint(1, 3))
                }
            }
            data.append(record)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return str(filepath)
    
    def generate_csv_file(self, num_rows: int, num_cols: int = 10, filename: str = None) -> str:
        """Generate a CSV file with specified dimensions."""
        if filename is None:
            filename = f"test_data_{num_rows}x{num_cols}.csv"
        
        filepath = self.base_dir / filename
        
        headers = [f"col_{i+1}" for i in range(num_cols)]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for row in range(num_rows):
                data_row = []
                for col in range(num_cols):
                    if col % 4 == 0:  # String column
                        data_row.append(self._generate_word())
                    elif col % 4 == 1:  # Integer column
                        data_row.append(random.randint(1, 10000))
                    elif col % 4 == 2:  # Float column
                        data_row.append(round(random.uniform(0, 1000), 2))
                    else:  # Boolean column
                        data_row.append(random.choice(['true', 'false']))
                writer.writerow(data_row)
        
        return str(filepath)
    
    def generate_compressed_data(self, original_file: str, compression_level: int = 6) -> str:
        """Generate compressed version of a file using gzip."""
        compressed_path = original_file + '.gz'
        
        with open(original_file, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb', compresslevel=compression_level) as f_out:
                f_out.writelines(f_in)
        
        return compressed_path
    
    def generate_test_urls(self) -> List[str]:
        """Generate list of test URLs for network operations."""
        return [
            "https://httpbin.org/delay/1",
            "https://jsonplaceholder.typicode.com/posts/1",
            "https://api.github.com/zen",
            "https://httpstat.us/200",
            "https://www.google.com",
            "https://www.cloudflare.com"
        ]
    
    def generate_dns_targets(self) -> List[str]:
        """Generate list of DNS targets for lookup tests."""
        return [
            "google.com",
            "github.com",
            "cloudflare.com",
            "stackoverflow.com",
            "amazon.com",
            "microsoft.com"
        ]
    
    def generate_ping_targets(self) -> List[str]:
        """Generate list of ping targets."""
        return [
            "8.8.8.8",  # Google DNS
            "1.1.1.1",  # Cloudflare DNS
            "google.com",
            "github.com"
        ]
    
    def cleanup_test_files(self, pattern: str = "test_*"):
        """Clean up generated test files matching pattern."""
        for file_path in self.base_dir.glob(pattern):
            try:
                file_path.unlink()
            except OSError:
                pass  # File might be in use
    
    def _generate_paragraph(self, sentences: int = None) -> str:
        """Generate a paragraph of random text."""
        if sentences is None:
            sentences = random.randint(3, 8)
        
        paragraph_sentences = []
        for _ in range(sentences):
            words = [self._generate_word() for _ in range(random.randint(5, 15))]
            sentence = ' '.join(words).capitalize() + '.'
            paragraph_sentences.append(sentence)
        
        return ' '.join(paragraph_sentences)
    
    def _generate_word(self, length: int = None) -> str:
        """Generate a random word."""
        if length is None:
            length = random.randint(3, 12)
        return ''.join(random.choices(string.ascii_lowercase, k=length))
    
    def _generate_name(self) -> str:
        """Generate a random name."""
        first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def _generate_email(self) -> str:
        """Generate a random email address."""
        domains = ["example.com", "test.org", "demo.net", "sample.io"]
        username = self._generate_word(random.randint(5, 10))
        return f"{username}@{random.choice(domains)}"
    
    def _generate_street(self) -> str:
        """Generate a random street address."""
        streets = ["Main St", "Oak Ave", "Pine Rd", "Elm Dr", "Maple Ln", "Cedar Ct"]
        return f"{random.randint(100, 9999)} {random.choice(streets)}"
    
    def _generate_city(self) -> str:
        """Generate a random city name."""
        cities = ["Springfield", "Madison", "Franklin", "Georgetown", "Arlington", "Fairview"]
        return random.choice(cities)


def get_standard_test_sizes() -> Dict[str, float]:
    """Return standard test file sizes in MB."""
    return {
        "small": 1.0,      # 1MB
        "medium": 10.0,    # 10MB
        "large": 50.0,     # 50MB
        "xlarge": 100.0    # 100MB
    }


def get_standard_record_counts() -> Dict[str, int]:
    """Return standard record counts for structured data."""
    return {
        "small": 1000,     # 1K records
        "medium": 10000,   # 10K records
        "large": 100000,   # 100K records
        "xlarge": 1000000  # 1M records
    }


if __name__ == "__main__":
    """Example usage of the data generator."""
    generator = DataGenerator("./test_data")
    
    # Generate various test files
    sizes = get_standard_test_sizes()
    records = get_standard_record_counts()
    
    print("Generating test data files...")
    
    # Text files
    for name, size in sizes.items():
        if size <= 10:  # Only small/medium for example
            print(f"Creating {name} text file ({size}MB)...")
            generator.generate_text_file(size, f"{name}_text.txt")
    
    # JSON files
    for name, count in records.items():
        if count <= 10000:  # Only small/medium for example
            print(f"Creating {name} JSON file ({count} records)...")
            generator.generate_json_file(count, f"{name}_data.json")
    
    # CSV files
    print("Creating CSV files...")
    generator.generate_csv_file(1000, 8, "small_data.csv")
    generator.generate_csv_file(10000, 12, "medium_data.csv")
    
    print("Test data generation complete!")