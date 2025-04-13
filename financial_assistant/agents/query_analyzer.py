# financial_assistant/agents/query_analyzer.py

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import re

class QueryAnalysis(BaseModel):
    """Analysis of a user query about financial data."""
    data_sources: List[str] = Field(
        description="List of data sources needed (e.g., 'google_analytics', 'stripe')")
    metrics: List[str] = Field(
        description="List of specific metrics needed from the data sources")
    dimensions: List[str] = Field(
        description="List of dimensions to segment the data by (e.g., 'device', 'country')", 
        default=[])
    time_period: str = Field(
        description="Time period for the query (e.g., 'last_month', 'last_30_days')")
    comparison_period: Optional[str] = Field(
        description="Period to compare against, if applicable", default=None)
    filters: List[str] = Field(
        description="Any filters to apply to the data", default=[])
    
    def get_required_connectors(self):
        """Return the connectors required for this analysis."""
        connectors = []
        if "google_analytics" in self.data_sources:
            connectors.append("google_analytics")
        if "stripe" in self.data_sources:
            connectors.append("stripe")
        return connectors

class QueryAnalyzer:
    """Analyzes user queries to determine required data sources and metrics."""
    
    def __init__(self, llm):
        """Initialize the query analyzer with an LLM."""
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=QueryAnalysis)
        
        self.prompt = PromptTemplate(
            template="""
            You are a financial analytics assistant that helps analyze business data.
            
            Analyze the following user query and determine:
            1. Which data sources are needed (google_analytics, stripe, or both)
            2. What specific metrics are required (e.g., conversion_rate, revenue, page_views)
            3. What dimensions to segment by, if any (e.g., device, country, product)
            4. The time period for the analysis (e.g., last_month, last_week, year_to_date)
            5. A comparison period, if applicable (e.g., previous_month, previous_year)
            6. Any filters that should be applied
            
            Your response should be a valid JSON object with the following structure:
            {{
              "data_sources": ["source1", "source2"],
              "metrics": ["metric1", "metric2"],
              "dimensions": ["dimension1", "dimension2"],
              "time_period": "period",
              "comparison_period": "comparison_period",
              "filters": ["filter1", "filter2"]
            }}
            
            For empty arrays, use []
            If there's no comparison period, use null
            
            User Query: {query}
            """,
            input_variables=["query"]
        )
        
    def analyze(self, query):
        """Analyze a user query and return structured understanding."""
        prompt_value = self.prompt.format(query=query)
        result = self.llm.invoke(prompt_value)
        
        # Try to extract JSON from the response
        try:
            # Find JSON pattern in the response
            json_match = re.search(r'({[\s\S]*})', result)
            if json_match:
                json_str = json_match.group(1)
                # Parse the JSON
                data = json.loads(json_str)
                # Create QueryAnalysis object
                return QueryAnalysis(**data)
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {result}")
            
            # Fallback: Use a simple rule-based approach
            return self._fallback_analysis(query)
    
    def _fallback_analysis(self, query):
        """Fallback method when LLM parsing fails."""
        query = query.lower()
        
        # Simple rule-based analysis
        data_sources = []
        if "conversion" in query or "traffic" in query or "page" in query:
            data_sources.append("google_analytics")
        if "revenue" in query or "payment" in query or "order" in query:
            data_sources.append("stripe")
            
        # Default to both if we can't determine
        if not data_sources:
            data_sources = ["google_analytics", "stripe"]
            
        # Simple metric detection
        metrics = []
        if "conversion" in query:
            metrics.append("conversion_rate")
        if "revenue" in query:
            metrics.append("revenue")
        if "order" in query or "purchase" in query:
            metrics.append("average_order_value")
        if "traffic" in query or "visit" in query:
            metrics.append("sessions")
            
        # Default metrics if none detected
        if not metrics:
            metrics = ["conversion_rate"] if "google_analytics" in data_sources else ["revenue"]
            
        # Time period detection
        time_period = "last_month"
        if "last week" in query or "past week" in query:
            time_period = "last_week"
        if "30 day" in query or "thirty day" in query or "month" in query:
            time_period = "last_month"
        if "quarter" in query or " q1" in query or " q2" in query:
            time_period = "q1"  # Default to Q1
            
        # Comparison period
        comparison_period = None
        if "compar" in query or "previous" in query or "vs" in query:
            if time_period == "last_month":
                comparison_period = "previous_month"
            elif time_period == "last_week":
                comparison_period = "previous_week"
                
        return QueryAnalysis(
            data_sources=data_sources,
            metrics=metrics,
            dimensions=[],
            time_period=time_period,
            comparison_period=comparison_period,
            filters=[]
        )