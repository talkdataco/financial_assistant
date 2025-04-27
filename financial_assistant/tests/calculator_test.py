# financial_assistant/utils/calculator_test.py

import unittest
from financial_assistant.utils.calculator import FinancialCalculator

class TestFinancialCalculator(unittest.TestCase):
    """Test cases for the FinancialCalculator utility."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample data context
        self.test_data = {
            "data": {
                "google_analytics": {
                    "data": {
                        "conversion_rate": {
                            "current": 0.035,  # 3.5%
                            "previous": 0.032,  # 3.2%
                            "change": 0.094     # 9.4% increase
                        },
                        "sessions": {
                            "current": 85000,
                            "previous": 80000,
                            "change": 0.0625
                        }
                    }
                },
                "stripe": {
                    "data": {
                        "revenue": {
                            "current": 125000.00,
                            "previous": 115000.00,
                            "change": 0.087
                        },
                        "average_order_value": {
                            "current": 85.50,
                            "previous": 82.75,
                            "change": 0.033
                        }
                    }
                }
            }
        }
        
        self.calculator = FinancialCalculator(self.test_data)
        
    def test_extract_value(self):
        """Test extracting values from data context."""
        self.assertEqual(self.calculator.extract_value("google_analytics", "conversion_rate", "current"), 0.035)
        self.assertEqual(self.calculator.extract_value("stripe", "revenue", "previous"), 115000.00)
        
        # Test non-existent path
        self.assertEqual(self.calculator.extract_value("nonexistent", "metric", "field"), 0.0)
        
    def test_evaluate_simple(self):
        """Test evaluating simple expressions."""
        self.assertEqual(self.calculator.evaluate("2 + 3"), 5)
        self.assertEqual(self.calculator.evaluate("10 * 5"), 50)
        self.assertEqual(self.calculator.evaluate("100 / 4"), 25)
        
    def test_evaluate_with_references(self):
        """Test evaluating expressions with metric references."""
        # Test with shorthand references
        self.assertAlmostEqual(
            self.calculator.evaluate("GA:conversion_rate:current * 100"), 
            3.5,
            places=1
        )
        
        # Test with full source names
        self.assertAlmostEqual(
            self.calculator.evaluate("stripe:revenue:current / stripe:revenue:previous - 1"), 
            0.087,  # 8.7% growth
            places=3
        )
        
    def test_evaluate_with_functions(self):
        """Test evaluating expressions with functions."""
        # Test percentage change calculation
        self.assertAlmostEqual(
            self.calculator.evaluate("percentage_change(GA:sessions:current, GA:sessions:previous)"),
            6.25,  # 6.25% increase
            places=2
        )
        
        # Test average function
        self.assertAlmostEqual(
            self.calculator.evaluate("avg([GA:sessions:current, 90000])"),
            87500,
            places=1
        )
        
    def test_decompose_calculation_query(self):
        """Test query decomposition."""
        query = "What is the ratio of revenue to average order value from Stripe?"
        results = self.calculator.decompose_calculation_query(query)
        
        self.assertTrue(len(results) > 0)
        # This test is simplified - a real test would be more thorough

if __name__ == "__main__":
    unittest.main()