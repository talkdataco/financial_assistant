# financial_assistant/main.py

import os
import time
import json
from financial_assistant.models.ollama import get_ollama_model
from financial_assistant.agents.query_analyzer import QueryAnalyzer
from financial_assistant.agents.data_fetcher import DataFetcher
from financial_assistant.agents.response_generator import ResponseGenerator
from financial_assistant.models.rag_engine import RAGEngine, MockEmbeddings
from financial_assistant.connectors.google_analytics import GoogleAnalyticsConnector
from financial_assistant.connectors.stripe import StripeConnector
from financial_assistant.agents.insight_generator import InsightGenerator


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
        'key_file': 'financial_assistant/config/ecclesia.json',  # This file doesn't need to exist for the mock
        'property_id': 'properties/386584150'
        # 'key_file': 'mock',
    })
    
    stripe_connector = StripeConnector({
        'api_key': 'mock_stripe_key'  # Mock API key
    })
    
    # Create connectors dictionary
    connectors = {
        'google_analytics': ga_connector,
        'stripe': stripe_connector
    }
    
    # Initialize components
    analyzer = QueryAnalyzer(llm)
    fetcher = DataFetcher(connectors)
    
    # Initialize RAG components
    rag_engine = RAGEngine(llm, MockEmbeddings())
    response_generator = ResponseGenerator(rag_engine)
    
    # Test queries
    test_queries = [
        # "What was my conversion rate last month compared to the previous month?",
        # "Show me revenue by product category from Stripe for Q1",
        # "What's the average order value from Stripe and how has it changed over the last 30 days?"
        "What are the number of active users for March 2025?",
        # "What are the number of total visits in March 2025?",
        # "What are the number of average daily users on 22nd April, 2025?"
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
        
            # Log calculation requirements if any
            if analysis.requires_calculation:
                print("\nQuery requires calculations:")
                for i, step in enumerate(analysis.calculation_steps, 1):
                    print(f"  {i}. {step.description}: {step.expression}")
            
            # Fetch the data
            print("\nFetching data...")
            data = fetcher.fetch(analysis)
            
            # Generate response
            print("\nGenerating response...")
            result = response_generator.generate_response(query, analysis, data)
            
            # Display the response
            print("\nRESPONSE:")
            print(result["response"])

            # Display calculation explanations if any
            if "calculation_explanations" in result:
                print("\nCALCULATION DETAILS:")
                for metric, explanation in result["calculation_explanations"].items():
                    print(f"\n{metric}:")
                    print(explanation)
            

            # # Display follow-up questions
            # print("\nFOLLOW-UP QUESTIONS:")
            # for i, question in enumerate(result["follow_up_questions"], 1):
            #     print(f"{i}. {question}")
            

            # # Generate Insights
            # insight_generator = InsightGenerator(llm)
            # print("\nGenerating additional insights...")
            # insights = insight_generator.generate_insights(query, analysis, data)

            # print("\nADDITIONAL INSIGHTS:")
            # for i, insight in enumerate(insights, 1):
            #     print(f"{i}. {insight}")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()