import unittest
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.data_generator import get_standard_test_sizes, get_standard_record_counts

class TestDataGeneratorUtils(unittest.TestCase):
    def test_get_standard_test_sizes(self):
        """Test that get_standard_test_sizes returns correct MB values."""
        sizes = get_standard_test_sizes()
        expected = {
            "small": 1.0,
            "medium": 10.0,
            "large": 50.0,
            "xlarge": 100.0
        }
        self.assertEqual(sizes, expected)
        for key, value in sizes.items():
            self.assertIsInstance(value, float)

    def test_get_standard_record_counts(self):
        """Test that get_standard_record_counts returns correct record counts."""
        counts = get_standard_record_counts()
        expected = {
            "small": 1000,
            "medium": 10000,
            "large": 100000,
            "xlarge": 1000000
        }
        self.assertEqual(counts, expected)
        for key, value in counts.items():
            self.assertIsInstance(value, int)

if __name__ == "__main__":
    unittest.main()
