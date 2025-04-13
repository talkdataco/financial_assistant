# financial_assistant/agents/response_generator.py

from typing import Dict, Any, List
from financial_assistant.models.rag_engine import RAGEngine
from financial_assistant.agents.query_analyzer import QueryAnalysis

class ResponseGenerator:
    """Generates responses to user queries based on fetched data."""
    
    def __init__(self, rag_engine: RAGEngine):
        """
        Initialize the response generator.
        
        Args:
            rag_engine: RAG engine to use for response generation
        """
        self.rag_engine = rag_engine
    
    def generate_response(self, query: str, query_analysis: QueryAnalysis, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a response to a user query.
        
        Args:
            query: Original user query
            query_analysis: Structured analysis of the query
            data: Data fetched from various sources
            
        Returns:
            Dictionary containing the response and follow-up questions
        """
        # Generate the main response
        response = self.rag_engine.generate_response(query, query_analysis, data)
        
        # Generate follow-up questions
        follow_up_questions = self.rag_engine.generate_follow_up_questions(
            query, query_analysis, data, response
        )
        
        # Build response object
        result = {
            "response": response,
            "follow_up_questions": follow_up_questions,
            "metadata": {
                "data_sources": query_analysis.data_sources,
                "metrics": query_analysis.metrics,
                "time_period": query_analysis.time_period
            }
        }
        
        return result