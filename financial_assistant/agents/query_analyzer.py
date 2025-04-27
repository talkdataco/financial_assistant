# financial_assistant/agents/query_analyzer.py

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import re
from financial_assistant.utils.calculator import FinancialCalculator

class CalculationStep(BaseModel):
    """Represents a calculation step in a complex query."""
    expression: str = Field(description="The mathematical expression to evaluate")
    description: str = Field(description="Description of what this calculation does")
    result_metric: str = Field(description="Name of the metric this calculation produces")

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
    requires_calculation: bool = Field(
        description="Whether this query requires calculations beyond simple data fetching",
        default=False)
    calculation_steps: List[CalculationStep] = Field(
        description="List of calculation steps needed for this query", 
        default=[])
    
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
        self.calculator = FinancialCalculator()
        
        self.calculation_keywords = [
            "calculate", "compute", "ratio", "average", "mean", "total", "sum",
            "difference", "increase", "decrease", "percentage", "growth",
            "compare", "divide", "multiply", "subtract", "add",
            "margin", "profit", "change", "conversion", "rate",
            "year-over-year", "month-over-month", "yoy", "mom"
        ]
        
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
            7. Whether calculations are needed (e.g., computing ratios, averages, or percentage changes)
            8. What calculation steps are required, if any
            
            Your response should be a valid JSON object with the following structure:
            {{
              "data_sources": ["source1", "source2"],
              "metrics": ["metric1", "metric2"],
              "dimensions": ["dimension1", "dimension2"],
              "time_period": "period",
              "comparison_period": "comparison_period",
              "filters": ["filter1", "filter2"],
              "requires_calculation": true/false,
              "calculation_steps": [
                {{
                  "expression": "mathematical expression",
                  "description": "what this calculates",
                  "result_metric": "name of resulting metric"
                }}
              ]
            }}
            
            For empty arrays, use []
            If there's no comparison period, use null
            For calculations, use metric references in the format SOURCE:METRIC:FIELD, 
            e.g., "GA:conversion_rate:current * 100" or "stripe:revenue:current / stripe:revenue:previous - 1"
            
            Examples of calculations:
            - Convert decimal to percentage: "GA:conversion_rate:current * 100"
            - Calculate revenue growth: "percentage_change(stripe:revenue:current, stripe:revenue:previous)"
            - Calculate revenue per session: "stripe:revenue:current / GA:sessions:current"
            
            User Query: {query}
            """,
            input_variables=["query"]
        )
        
    def analyze(self, query):
        """Analyze a user query and return structured understanding."""
        # Run the initial LLM-based analysis
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
                analysis = QueryAnalysis(**data)
            else:
                raise ValueError("No JSON found in response")
                
            # If LLM didn't identify calculation requirements, check with rule-based system
            if not analysis.requires_calculation:
                analysis.requires_calculation = self._check_calculation_requirements(query)
                
                # If we detect calculation requirements, add default calculation steps
                if analysis.requires_calculation and not analysis.calculation_steps:
                    analysis.calculation_steps = self._generate_default_calculations(query, analysis)
                    
            return analysis
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {result}")
            
            # Fallback: Use a simple rule-based approach
            return self._fallback_analysis(query)
    
    def _check_calculation_requirements(self, query):
        """Check if a query likely requires calculations using rules."""
        query_lower = query.lower()
        
        # Check for calculation keywords
        for keyword in self.calculation_keywords:
            if keyword in query_lower:
                return True
                
        # Check for mathematical operators
        if re.search(r'(ratio|percent|divided by|times|multiplied|plus|minus|average|mean)', query_lower):
            return True
            
        # Use calculator's decomposition logic
        calculation_steps = self.calculator.decompose_calculation_query(query)
        if len(calculation_steps) > 1 or (len(calculation_steps) == 1 and calculation_steps[0][1] is not None):
            return True
            
        return False
        
    def _generate_default_calculations(self, query, analysis):
        """Generate default calculation steps based on the query and initial analysis."""
        calculation_steps = []
        query_lower = query.lower()
        
        # Use the calculator's decomposition logic
        decomposed = self.calculator.decompose_calculation_query(query)
        for _, expression in decomposed:
            if expression:
                # Create a calculation step
                step = CalculationStep(
                    expression=expression,
                    description=f"Calculated based on query: {query}",
                    result_metric="calculated_result"
                )
                calculation_steps.append(step)
        
        # If no steps were generated but calculation is required, add some common calculations
        if not calculation_steps:
            # Check for percentage calculations
            if "percentage" in query_lower or "percent" in query_lower:
                for metric in analysis.metrics:
                    if "rate" in metric or "ratio" in metric:
                        # Metrics that are typically percentages
                        source = analysis.data_sources[0] if analysis.data_sources else "google_analytics"
                        step = CalculationStep(
                            expression=f"{source}:{metric}:current * 100",
                            description=f"Convert {metric} from decimal to percentage",
                            result_metric=f"{metric}_percent"
                        )
                        calculation_steps.append(step)
                        
            # Check for comparison calculations
            if "compare" in query_lower or "growth" in query_lower or "change" in query_lower:
                for metric in analysis.metrics:
                    source = analysis.data_sources[0] if analysis.data_sources else "google_analytics"
                    step = CalculationStep(
                        expression=f"percentage_change({source}:{metric}:current, {source}:{metric}:previous)",
                        description=f"Calculate percentage change in {metric}",
                        result_metric=f"{metric}_change_percent"
                    )
                    calculation_steps.append(step)
        
        return calculation_steps
    
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
        
        # Check for calculation requirements
        requires_calculation = self._check_calculation_requirements(query)
        calculation_steps = []
        
        if requires_calculation:
            # Simple calculation step for common metrics
            if "conversion_rate" in metrics:
                calculation_steps.append(
                    CalculationStep(
                        expression="google_analytics:conversion_rate:current * 100",
                        description="Convert conversion rate from decimal to percentage",
                        result_metric="conversion_rate_percent"
                    )
                )
            if "revenue" in metrics and comparison_period:
                calculation_steps.append(
                    CalculationStep(
                        expression="percentage_change(stripe:revenue:current, stripe:revenue:previous)",
                        description="Calculate percentage change in revenue",
                        result_metric="revenue_change_percent"
                    )
                )
                
        return QueryAnalysis(
            data_sources=data_sources,
            metrics=metrics,
            dimensions=[],
            time_period=time_period,
            comparison_period=comparison_period,
            filters=[],
            requires_calculation=requires_calculation,
            calculation_steps=calculation_steps
        )