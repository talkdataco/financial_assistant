# financial_assistant/agents/context_builder.py

from typing import Dict, Any, List
import json
from datetime import datetime

class ContextBuilder:
    """Transforms raw data from sources into a format suitable for RAG."""
    
    def __init__(self):
        """Initialize the context builder."""
        pass
        
    def build_context(self, query: str, query_analysis: Any, data: Dict[str, Any]) -> str:
        """
        Build a context string for RAG from the fetched data.
        
        Args:
            query: Original user query
            query_analysis: Structured analysis of the query
            data: Data fetched from various sources
            
        Returns:
            A formatted context string for the LLM
        """
        context_parts = []
        
        # Add query metadata
        context_parts.append(f"USER QUERY: {query}")
        context_parts.append("\nQUERY METADATA:")
        context_parts.append(f"- Time period: {query_analysis.time_period}")
        if query_analysis.comparison_period:
            context_parts.append(f"- Comparison period: {query_analysis.comparison_period}")
        
        # Format dates for display
        metadata = data.get("metadata", {})
        if "start_date" in metadata and "end_date" in metadata:
            start_date = datetime.strptime(metadata["start_date"], "%Y-%m-%d").strftime("%B %d, %Y")
            end_date = datetime.strptime(metadata["end_date"], "%Y-%m-%d").strftime("%B %d, %Y")
            context_parts.append(f"- Date range: {start_date} to {end_date}")
            
            if "comparison_start_date" in metadata and "comparison_end_date" in metadata:
                comp_start = datetime.strptime(metadata["comparison_start_date"], "%Y-%m-%d").strftime("%B %d, %Y")
                comp_end = datetime.strptime(metadata["comparison_end_date"], "%Y-%m-%d").strftime("%B %d, %Y")
                context_parts.append(f"- Comparison range: {comp_start} to {comp_end}")
                
        # Add data from each source
        context_parts.append("\nDATASOURCE RESULTS:")
        
        for source_name, source_data in data.get("data", {}).items():
            if "error" in source_data:
                context_parts.append(f"\n{source_name.upper()} ERROR: {source_data['error']}")
                continue
                
            context_parts.append(f"\n{source_name.upper()} DATA:")
            
            # Process metrics
            for metric_name, metric_data in source_data.get("data", {}).items():
                if "error" in metric_data:
                    context_parts.append(f"- {metric_name}: Error - {metric_data['error']}")
                    continue
                    
                context_parts.append(f"- {metric_name.replace('_', ' ').title()}:")
                
                # Current value
                if "current" in metric_data:
                    value = metric_data["current"]
                    # Format percentages
                    if 0 <= value <= 1 and (metric_name.endswith("rate") or metric_name.endswith("percentage")):
                        formatted_value = f"{value * 100:.2f}%"
                    # Format currency
                    elif metric_name in ["revenue", "average_order_value"]:
                        formatted_value = f"${value:,.2f}"
                    # Format numbers
                    else:
                        formatted_value = f"{value:,}"
                        
                    context_parts.append(f"  * Current value: {formatted_value}")
                
                # Previous value (if available)
                if "previous" in metric_data:
                    value = metric_data["previous"]
                    # Format based on metric type
                    if 0 <= value <= 1 and (metric_name.endswith("rate") or metric_name.endswith("percentage")):
                        formatted_value = f"{value * 100:.2f}%"
                    elif metric_name in ["revenue", "average_order_value"]:
                        formatted_value = f"${value:,.2f}"
                    else:
                        formatted_value = f"{value:,}"
                        
                    context_parts.append(f"  * Previous value: {formatted_value}")
                
                # Change percentage (if available)
                if "change" in metric_data:
                    change = metric_data["change"]
                    direction = "increase" if change >= 0 else "decrease"
                    formatted_change = f"{abs(change) * 100:.2f}%"
                    context_parts.append(f"  * Change: {formatted_change} {direction}")
                
                # Dimension data (if available)
                if "dimensions" in metric_data:
                    for dim_name, dim_data in metric_data["dimensions"].items():
                        context_parts.append(f"  * By {dim_name.replace('_', ' ')}:")
                        
                        if isinstance(dim_data, dict):
                            for category, value in dim_data.items():
                                # Format based on metric type
                                if metric_name in ["revenue", "average_order_value"]:
                                    formatted_value = f"${value:,.2f}"
                                else:
                                    formatted_value = f"{value:,}"
                                    
                                context_parts.append(f"    - {category.replace('_', ' ').title()}: {formatted_value}")
        
        return "\n".join(context_parts)
    
    def build_vector_store_documents(self, query: str, query_analysis: Any, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build documents for vector store indexing.
        
        Args:
            query: Original user query
            query_analysis: Structured analysis of the query
            data: Data fetched from various sources
            
        Returns:
            List of documents for vector store
        """
        documents = []
        
        # Create overall summary document
        summary = self.build_context(query, query_analysis, data)
        documents.append({
            "page_content": summary,
            "metadata": {
                "source": "summary",
                "query": query
            }
        })
        
        # Create individual documents for each metric
        for source_name, source_data in data.get("data", {}).items():
            if "error" in source_data:
                continue
                
            for metric_name, metric_data in source_data.get("data", {}).items():
                if "error" in metric_data:
                    continue
                
                # Create a document focused on this specific metric
                metric_content = []
                metric_content.append(f"{metric_name.replace('_', ' ').title()} from {source_name}:")
                
                # Current value
                if "current" in metric_data:
                    value = metric_data["current"]
                    # Format based on metric type
                    if 0 <= value <= 1 and (metric_name.endswith("rate") or metric_name.endswith("percentage")):
                        formatted_value = f"{value * 100:.2f}%"
                    elif metric_name in ["revenue", "average_order_value"]:
                        formatted_value = f"${value:,.2f}"
                    else:
                        formatted_value = f"{value:,}"
                        
                    metric_content.append(f"Current value: {formatted_value}")
                
                # Previous value and change
                if "previous" in metric_data and "change" in metric_data:
                    prev_value = metric_data["previous"]
                    change = metric_data["change"]
                    
                    # Format based on metric type
                    if 0 <= prev_value <= 1 and (metric_name.endswith("rate") or metric_name.endswith("percentage")):
                        formatted_prev = f"{prev_value * 100:.2f}%"
                    elif metric_name in ["revenue", "average_order_value"]:
                        formatted_prev = f"${prev_value:,.2f}"
                    else:
                        formatted_prev = f"{prev_value:,}"
                    
                    direction = "increased" if change >= 0 else "decreased"
                    formatted_change = f"{abs(change) * 100:.2f}%"
                    
                    metric_content.append(f"Previous value: {formatted_prev}")
                    metric_content.append(f"The {metric_name.replace('_', ' ')} has {direction} by {formatted_change} compared to the previous period.")
                
                # Dimension data
                if "dimensions" in metric_data:
                    for dim_name, dim_data in metric_data["dimensions"].items():
                        metric_content.append(f"Breakdown by {dim_name.replace('_', ' ')}:")
                        
                        if isinstance(dim_data, dict):
                            for category, value in dim_data.items():
                                if metric_name in ["revenue", "average_order_value"]:
                                    formatted_value = f"${value:,.2f}"
                                else:
                                    formatted_value = f"{value:,}"
                                    
                                metric_content.append(f"- {category.replace('_', ' ').title()}: {formatted_value}")
                
                # Add this metric as a document
                documents.append({
                    "page_content": "\n".join(metric_content),
                    "metadata": {
                        "source": source_name,
                        "metric": metric_name,
                        "query": query
                    }
                })
        
        return documents