import unittest
import os
import sys
import shutil

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from utils.config import BenchmarkConfig

class TestBenchmarkConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config_path = "tests/unit/test_bench.config.json"
        cls.config = BenchmarkConfig(cls.config_path)

    @classmethod
    def tearDownClass(cls):
        # Clean up created output directory if it exists
        if hasattr(cls, 'config') and os.path.exists(cls.config.output.directory):
            shutil.rmtree(cls.config.output.directory)

    def test_get_enabled_languages(self):
        """Test that get_enabled_languages returns the correct list of languages."""
        enabled_languages = self.config.get_enabled_languages()
        self.assertIn("python", enabled_languages)
        self.assertIn("rust", enabled_languages)
        self.assertEqual(len(enabled_languages), 2)

    def test_get_enabled_test_suites(self):
        """Test that get_enabled_test_suites returns only enabled suites."""
        enabled_suites = self.config.get_enabled_test_suites()
        self.assertIn("algorithms", enabled_suites)
        self.assertNotIn("disabled_suite", enabled_suites)
        self.assertEqual(len(enabled_suites), 1)

    def test_get_language_config(self):
        """Test that get_language_config returns the correct configuration for a language."""
        python_config = self.config.get_language_config("python")
        self.assertIsNotNone(python_config)
        self.assertEqual(python_config.executable, "python")
        self.assertEqual(python_config.file_extension, ".py")

        non_existent_config = self.config.get_language_config("non_existent")
        self.assertIsNone(non_existent_config)

if __name__ == "__main__":
    unittest.main()
