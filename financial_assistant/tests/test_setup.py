# financial_assistant/tests/test_setup.py

import unittest
import importlib
import sys

class TestEnvironmentSetup(unittest.TestCase):
    """Test class to verify the environment setup."""

    def test_python_version(self):
        """Test that Python version is compatible."""
        major, minor = sys.version_info[:2]
        print(f"Python version: {major}.{minor}")
        self.assertGreaterEqual(minor, 9, "Python version should be at least 3.9")
        
    def test_core_dependencies(self):
        """Test that core dependencies are installed."""
        required_packages = [
            'langchain',
            'langchain_core',
            'langchain_community',
            'pydantic',
            'chromadb'
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package)
                print(f"✅ {package} is installed")
            except ImportError:
                self.fail(f"Required package {package} is not installed")
                
    def test_optional_dependencies(self):
        """Test for optional dependencies."""
        optional_packages = [
            'langgraph',
            'ollama'
        ]
        
        for package in optional_packages:
            try:
                importlib.import_module(package)
                print(f"✅ {package} is installed")
            except ImportError:
                print(f"ℹ️ Optional package {package} is not installed")

if __name__ == '__main__':
    unittest.main()