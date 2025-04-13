# financial_assistant/tests/test_query_analyzer.py

import unittest
import sys
import os
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from financial_assistant.models.ollama import get_ollama_model
from financial_assistant.agents.query_analyzer import QueryAnalyzer

class TestQueryAnalyzer(unittest.TestCase):
    """Test the query analyzer component."""

    @classmethod
    def setUpClass(cls):
        # Initialize LLM
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt+1}/{max_retries} to connect to Ollama...")
                cls.llm = get_ollama_model()
                print("✅ Successfully connected to Ollama")
                break
            except Exception as e:
                print(f"❌ Error connecting to Ollama: {e}")
                if attempt < max_retries - 1:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("\nFailed to connect to Ollama after multiple attempts.")
                    print("Please ensure Ollama is running with 'ollama serve' in a separate terminal.")
                    raise

        # Initialize the query analyzer
        cls.analyzer = QueryAnalyzer(cls.llm)

    def test_analyze_conversion_query(self):
        """Test analyzing a conversion rate query."""
        query = "What was my conversion rate last month compared to the previous month?"
        analysis = self.analyzer.analyze(query)
        
        print("\nQuery:", query)
        print("Analysis:")
        print(f"Data Sources: {analysis.data_sources}")
        print(f"Metrics: {analysis.metrics}")
        print(f"Dimensions: {analysis.dimensions}")
        print(f"Time Period: {analysis.time_period}")
        print(f"Comparison Period: {analysis.comparison_period}")
        print(f"Filters: {analysis.filters}")
        
        self.assertIn("google_analytics", analysis.data_sources)
        self.assertIn("conversion_rate", analysis.metrics)
        self.assertEqual("last_month", analysis.time_period)
        
    def test_analyze_revenue_query(self):
        """Test analyzing a revenue query."""
        query = "Show me revenue by product category from Stripe for Q1"
        analysis = self.analyzer.analyze(query)
        
        print("\nQuery:", query)
        print("Analysis:")
        print(f"Data Sources: {analysis.data_sources}")
        print(f"Metrics: {analysis.metrics}")
        print(f"Dimensions: {analysis.dimensions}")
        print(f"Time Period: {analysis.time_period}")
        print(f"Comparison Period: {analysis.comparison_period}")
        print(f"Filters: {analysis.filters}")
        
        self.assertIn("stripe", analysis.data_sources)
        self.assertIn("revenue", analysis.metrics)

if __name__ == "__main__":
    unittest.main()