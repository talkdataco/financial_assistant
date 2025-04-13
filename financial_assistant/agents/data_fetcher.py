# financial_assistant/agents/data_fetcher.py

from typing import Dict, List, Any, Optional
from financial_assistant.agents.query_analyzer import QueryAnalysis
from financial_assistant.connectors.base import DataConnector

class DataFetcher:
    """
    Agent responsible for fetching data from various sources based on query analysis.
    """
    
    def __init__(self, connectors: Dict[str, DataConnector]):
        """
        Initialize with available data connectors.
        
        Args:
            connectors: Dictionary mapping connector names to connector instances
        """
        self.connectors = connectors
    
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
                "filters": analysis.filters
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
                
                # Fetch current period data
                current_data = connector.fetch_data(
                    metrics=analysis.metrics,
                    dimensions=analysis.dimensions,
                    start_date=start_date,
                    end_date=end_date,
                    filters=filters
                )
                
                # Fetch comparison period data if needed
                if analysis.comparison_period:
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
        
        return result