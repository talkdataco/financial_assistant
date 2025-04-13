# financial_assistant/main.py

import os
from financial_assistant.models.ollama import get_ollama_model
from financial_assistant.agents.query_analyzer import QueryAnalyzer

def main():
    """Main entry point for the financial analytics assistant."""
    
    # Initialize the LLM
    try:
        llm = get_ollama_model()
        print("✅ Successfully connected to Ollama")
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return
    
    # Initialize the query analyzer
    analyzer = QueryAnalyzer(llm)
    
    # Test with a sample query
    query = "What was my conversion rate last month compared to the previous month?"
    
    print("\nAnalyzing query:", query)
    try:
        analysis = analyzer.analyze(query)
        print("\nQuery Analysis:")
        print(f"Data Sources: {analysis.data_sources}")
        print(f"Metrics: {analysis.metrics}")
        print(f"Time Period: {analysis.time_period}")
    except Exception as e:
        print(f"❌ Error analyzing query: {e}")

if __name__ == "__main__":
    main()