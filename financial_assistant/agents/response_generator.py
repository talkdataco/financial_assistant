# financial_assistant/agents/response_generator.py

from typing import Dict, List, Any
from financial_assistant.models.rag_engine import RAGEngine
from financial_assistant.agents.query_analyzer import QueryAnalysis
from financial_assistant.utils.calculator import FinancialCalculator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseGenerator:
    """Generates responses to user queries based on fetched data."""
    
    def __init__(self, rag_engine: RAGEngine):
        """
        Initialize the response generator.
        
        Args:
            rag_engine: RAG engine to use for response generation
        """
        self.rag_engine = rag_engine
        self.calculator = FinancialCalculator()
    
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
        # Update calculator context with fetched data
        self.calculator.update_context(data)
        
        # Check if calculations were performed
        has_calculations = query_analysis.requires_calculation and "calculations" in data
        
        # Generate the main response
        if has_calculations:
            # Enhance context with calculation results
            enhanced_data = self._enhance_data_with_calculations(data)
            
            # Pass calculation information to the RAG engine
            response = self.rag_engine.generate_response(
                query, 
                query_analysis, 
                enhanced_data,
                include_calculations=True
            )
        else:
            # Regular response generation without calculations
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
        
        # Add calculation results to the response metadata if available
        if has_calculations:
            result["metadata"]["calculations"] = data["calculations"]
            
            # Add calculation explanations
            calc_explanations = self._generate_calculation_explanations(data["calculations"])
            if calc_explanations:
                result["calculation_explanations"] = calc_explanations
        
        return result
    
    def _enhance_data_with_calculations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance the data context with calculation results.
        
        Args:
            data: Original data with calculations
            
        Returns:
            Enhanced data with calculations integrated
        """
        enhanced_data = data.copy()
        
        # Create a new section for calculated metrics if not already present
        if "calculated_metrics" not in enhanced_data:
            enhanced_data["calculated_metrics"] = {}
            
        # Extract calculation results and add them to the enhanced data
        for metric_name, calc_info in data.get("calculations", {}).items():
            if "error" not in calc_info:
                enhanced_data["calculated_metrics"][metric_name] = {
                    "value": calc_info["value"],
                    "description": calc_info["description"]
                }
        
        return enhanced_data
    
    def _generate_calculation_explanations(self, calculations: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate user-friendly explanations for calculations.
        
        Args:
            calculations: Dictionary of calculation results
            
        Returns:
            Dictionary mapping metric names to explanations
        """
        explanations = {}
        
        for metric_name, calc_info in calculations.items():
            if "error" in calc_info:
                explanations[metric_name] = f"Could not calculate {metric_name}: {calc_info['error']}"
            else:
                # Format the value nicely
                value = calc_info["value"]
                if isinstance(value, float):
                    # Format percentages and regular values differently
                    if metric_name.endswith("_percent") or metric_name.endswith("_rate") or "percentage" in metric_name:
                        formatted_value = f"{value:.2f}%"
                    elif value > 1000:
                        formatted_value = f"{value:,.2f}"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                
                # Create explanation
                explanations[metric_name] = (
                    f"{calc_info['description']}: {formatted_value}\n"
                    f"Method: {calc_info.get('explanation', 'Calculated using the provided expression')}"
                )
        
        return explanations
    
    def generate_detailed_explanation(self, query: str, query_analysis: QueryAnalysis, 
                                      data: Dict[str, Any]) -> str:
        """
        Generate a detailed explanation of all calculations performed.
        
        Args:
            query: Original user query
            query_analysis: Structured analysis of the query
            data: Data fetched from various sources
            
        Returns:
            Detailed explanation string
        """
        if not query_analysis.requires_calculation or "calculations" not in data:
            return "No calculations were performed for this query."
            
        explanation_parts = ["Here's a detailed breakdown of the calculations:"]
        
        for metric_name, calc_info in data["calculations"].items():
            if "error" in calc_info:
                explanation_parts.append(
                    f"\n## {metric_name} (FAILED)\n"
                    f"- Attempted calculation: {calc_info['expression']}\n"
                    f"- Error: {calc_info['error']}\n"
                )
            else:
                # Format the value
                value = calc_info["value"]
                if isinstance(value, float):
                    if abs(value) < 0.01:
                        formatted_value = f"{value:.6f}"
                    elif abs(value) > 1000:
                        formatted_value = f"{value:,.2f}"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                
                explanation_parts.append(
                    f"\n## {metric_name}\n"
                    f"- Result: {formatted_value}\n"
                    f"- Expression: {calc_info['expression']}\n"
                    f"- Description: {calc_info['description']}\n"
                    f"- Explanation: {calc_info.get('explanation', 'Calculated using the provided expression')}\n"
                )
        
        return "\n".join(explanation_parts)