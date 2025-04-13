# financial_assistant/main.py

import os
import time
from financial_assistant.models.ollama import get_ollama_model
from financial_assistant.agents.query_analyzer import QueryAnalyzer
from financial_assistant.agents.data_fetcher import DataFetcher
from financial_assistant.connectors.google_analytics import GoogleAnalyticsConnector
from financial_assistant.connectors.stripe import StripeConnector

def main():
    """Main entry point for the financial analytics assistant."""
    
    # Initialize the LLM with retry logic
    llm = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt+1}/{max_retries} to connect to Ollama...")
            llm = get_ollama_model()
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
                return
    
    # Initialize connectors with mock credentials
    ga_connector = GoogleAnalyticsConnector({
        'key_file': './config/ga_credentials.json',  # This file doesn't need to exist for the mock
        'property_id': '123456789'
    })
    
    stripe_connector = StripeConnector({
        'api_key': 'mock_stripe_key'  # Mock API key
    })
    
    # Create connectors dictionary
    connectors = {
        'google_analytics': ga_connector,
        'stripe': stripe_connector
    }
    
    # Initialize the query analyzer and data fetcher
    analyzer = QueryAnalyzer(llm)
    fetcher = DataFetcher(connectors)
    
    # Test queries
    test_queries = [
        "What was my conversion rate last month compared to the previous month?",
        "Show me revenue by product category from Stripe for Q1",
        "What's the average order value from Stripe and how has it changed over the last 30 days?"
    ]
    
    for query in test_queries:
        print("\n" + "="*80)
        print(f"QUERY: {query}")
        print("="*80)
        
        try:
            # Analyze the query
            print("\nAnalyzing query...")
            analysis = analyzer.analyze(query)
            print("\nQuery Analysis:")
            print(f"Data Sources: {analysis.data_sources}")
            print(f"Metrics: {analysis.metrics}")
            print(f"Dimensions: {analysis.dimensions}")
            print(f"Time Period: {analysis.time_period}")
            print(f"Comparison Period: {analysis.comparison_period}")
            print(f"Filters: {analysis.filters}")
            
            # Fetch the data
            print("\nFetching data...")
            result = fetcher.fetch(analysis)
            
            # Display results
            print("\nResults:")
            for source, data in result["data"].items():
                print(f"\nFrom {source.upper()}:")
                if "error" in data:
                    print(f"  Error: {data['error']}")
                else:
                    for metric_name, metric_data in data.get("data", {}).items():
                        print(f"  {metric_name.upper()}:")
                        for key, value in metric_data.items():
                            if key == "dimensions":
                                print(f"    {key}:")
                                for dim_name, dim_data in value.items():
                                    print(f"      {dim_name}: {dim_data}")
                            else:
                                print(f"    {key}: {value}")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")

if __name__ == "__main__":
    main()