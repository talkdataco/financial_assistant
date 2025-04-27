import unittest
from financial_assistant.utils.calculator import FinancialCalculator

class TestFinancialCalculator(unittest.TestCase):
    def setUp(self):
        """Set up test data context"""
        self.data_context = {
            'GA:sessions:current': 50000,
            'revenue': 100000.50
        }
        self.calculator = FinancialCalculator(self.data_context)
    
    def test_evaluate_with_constants(self):
        """Test evaluation of simple numeric expressions"""
        result = self.calculator.evaluate_expression('avg(10, 20, 30)')
        self.assertAlmostEqual(result, 20)
    
    def test_evaluate_with_metrics(self):
        """Test evaluation using metrics from data context"""
        result = self.calculator.evaluate_expression('GA:sessions:current')
        self.assertEqual(result, 50000)
    
    def test_evaluate_with_functions(self):
        """Test evaluation of functions with mixed arguments"""
        result = self.calculator.evaluate_expression('avg(GA:sessions:current, 90000)')
        self.assertAlmostEqual(result, 70000)
    
    def test_decompose_calculation_query(self):
        """Test query decomposition"""
        query = 'avg(GA:sessions:current, 90000)'
        results = self.calculator.decompose_calculation_query(query)
        
        self.assertEqual(results['function'], 'avg')
        self.assertEqual(results['arguments'], ['GA:sessions:current', '90000'])
    
    def test_unsupported_function(self):
        """Test handling of unsupported functions"""
        with self.assertRaises(ValueError):
            self.calculator.evaluate_expression('unsupported_func(10, 20)')
    
    def test_missing_metric(self):
        """Test handling of missing metrics"""
        with self.assertRaises(ValueError):
            self.calculator.evaluate_expression('nonexistent_metric')

if __name__ == '__main__':
    unittest.main()