# financial_assistant/run_test.py

import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Run the environment setup tests
from financial_assistant.tests.test_setup import TestEnvironmentSetup

if __name__ == '__main__':
    unittest.main(TestEnvironmentSetup())