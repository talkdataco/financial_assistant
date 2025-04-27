# financial_assistant/agents/data_fetcher.py

from typing import Dict, List, Any, Optional
from financial_assistant.agents.query_analyzer import QueryAnalysis
from financial_assistant.connectors.base import DataConnector
from financial_assistant.utils.calculator import FinancialCalculator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    """
    Agent responsible for fetching data from various sources based on query analysis.
    Now with support for calculations on the fetched data.
    """
    
    def __init__(self, connectors: Dict[str, DataConnector]):
        """
        Initialize with available data connectors.
        
        Args:
            connectors: Dictionary mapping connector names to connector instances
        """
        self.connectors = connectors
        self.calculator = FinancialCalculator()
    
    def fetch(self, analysis: QueryAnalysis) -> Dict[str, Any]:
        """
        Fetch data based on query analysis.
        
        Args:
            analysis: QueryAnalysis object containing query understanding
            
        Returns:
            Dictionary with data from all required sources
        """
        result = {
            "metadata": {
                "metrics": analysis.metrics,
                "dimensions": analysis.dimensions,
                "time_period": analysis.time_period,
                "comparison_period": analysis.comparison_period,
                "filters": analysis.filters,
                "requires_calculation": analysis.requires_calculation
            },
            "data": {}
        }
        
        # Get time period dates
        start_date, end_date = None, None
        if analysis.time_period:
            # Use the first connector to parse time period (implementation is the same for all)
            first_connector = next(iter(self.connectors.values()))
            start_date, end_date = first_connector.parse_time_period(analysis.time_period)
            result["metadata"]["start_date"] = start_date
            result["metadata"]["end_date"] = end_date
            
        # Get comparison period dates
        comparison_start, comparison_end = None, None
        if analysis.comparison_period:
            first_connector = next(iter(self.connectors.values()))
            comparison_start, comparison_end = first_connector.parse_time_period(analysis.comparison_period)
            result["metadata"]["comparison_start_date"] = comparison_start
            result["metadata"]["comparison_end_date"] = comparison_end
        
        # Fetch data from each required source
        required_connectors = analysis.get_required_connectors()
        
        for source in required_connectors:
            if source in self.connectors:
                connector = self.connectors[source]
                
                # Build filters dict from filter strings
                filters = {}
                if analysis.filters:
                    for filter_str in analysis.filters:
                        if ":" in filter_str:
                            key, value = filter_str.split(":", 1)
                            filters[key.strip()] = value.strip()
                
                # Add comparison period to filters if present
                if analysis.comparison_period:
                    filters["comparison_period"] = analysis.comparison_period
                
                # Fetch current period data
                current_data = connector.fetch_data(
                    metrics=analysis.metrics,
                    dimensions=analysis.dimensions,
                    start_date=start_date,
                    end_date=end_date,
                    filters=filters
                )
                
                # Fetch comparison period data if needed but not already included
                if analysis.comparison_period and "comparison_data" not in current_data:
                    comparison_data = connector.fetch_data(
                        metrics=analysis.metrics,
                        dimensions=analysis.dimensions,
                        start_date=comparison_start,
                        end_date=comparison_end,
                        filters=filters
                    )
                    
                    # Add comparison data to result
                    if "data" in comparison_data:
                        current_data["comparison_data"] = comparison_data["data"]
                
                result["data"][source] = current_data
            else:
                result["data"][source] = {
                    "error": f"Connector for {source} not available"
                }
        
        # If calculations are required, perform them
        if analysis.requires_calculation and analysis.calculation_steps:
            result = self.perform_calculations(analysis, result)
            
        return result
    
    def perform_calculations(self, analysis: QueryAnalysis, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform calculations on the fetched data.
        
        Args:
            analysis: QueryAnalysis object with calculation steps
            data: Fetched data
            
        Returns:
            Data dictionary with calculation results added
        """
        # Initialize the calculator with the fetched data
        self.calculator.update_context(data)
        
        # Create a calculations section in the result
        if "calculations" not in data:
            data["calculations"] = {}
            
        # Process each calculation step
        for step in analysis.calculation_steps:
            try:
                # Evaluate the expression
                result = self.calculator.evaluate(step.expression)
                
                # Store the result
                data["calculations"][step.result_metric] = {
                    "value": result,
                    "expression": step.expression,
                    "description": step.description,
                    "explanation": self.calculator.explain_calculation(step.expression, result)
                }
                
                logger.info(f"Calculated {step.result_metric}: {result} using {step.expression}")
                
            except Exception as e:
                logger.error(f"Error calculating {step.result_metric}: {e}")
                data["calculations"][step.result_metric] = {
                    "error": str(e),
                    "expression": step.expression,
                    "description": step.description
                }
        
        return data
    
    def fetch_for_complex_query(self, analysis: QueryAnalysis) -> Dict[str, Any]:
        """
        Handle a complex query that requires multiple data fetches.
        
        Args:
            analysis: QueryAnalysis object with potential sub-queries
            
        Returns:
            Combined data from all sub-queries with calculations
        """
        # This is a placeholder for more sophisticated handling of complex queries
        # In a full implementation, we would:
        # 1. Decompose the query into sub-queries
        # 2. Modify analysis for each sub-query
        # 3. Fetch data for each sub-query
        # 4. Combine the results
        # 5. Perform calculations on the combined data
        
        # For now, we'll just use the regular fetch method
        return self.fetch(analysis)