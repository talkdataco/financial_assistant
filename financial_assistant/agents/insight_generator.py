# financial_assistant/agents/insight_generator.py

from typing import Dict, Any, List
from langchain_core.language_models import LLM
from financial_assistant.agents.query_analyzer import QueryAnalysis
from financial_assistant.agents.context_builder import ContextBuilder
from financial_assistant.models.prompt_templates import get_insight_generation_template

class InsightGenerator:
    """Generates additional insights from the data."""
    
    def __init__(self, llm: LLM):
        """
        Initialize the insight generator.
        
        Args:
            llm: Language model to use for insight generation
        """
        self.llm = llm
        self.context_builder = ContextBuilder()
        self.prompt_template = get_insight_generation_template()
    
    def generate_insights(self, query: str, query_analysis: QueryAnalysis, data: Dict[str, Any]) -> List[str]:
        """
        Generate insights from the data.
        
        Args:
            query: Original user query
            query_analysis: Structured analysis of the query
            data: Data fetched from various sources
            
        Returns:
            List of insights
        """
        # Build the context
        context = self.context_builder.build_context(query, query_analysis, data)
        
        # Generate insights
        prompt = self.prompt_template.format(context=context)
        response = self.llm.invoke(prompt)
        
        # Parse the response to extract insights
        insights = []
        
        for line in response.split('\n'):
            line = line.strip()
            # Look for lines that look like insights (numbered or with bullet points)
            if line and (line.startswith('-') or line.startswith('*') or 
                        (line[0].isdigit() and line[1:3] in ['. ', ') '])):
                # Clean up the line
                insight = line[2:] if line.startswith(('-', '*')) else line[3:] if line[1:3] in ['. ', ') '] else line
                insights.append(insight)
                
        # If we couldn't parse structured insights, try to find paragraphs
        if not insights:
            paragraphs = [p for p in response.split('\n\n') if p.strip()]
            insights = paragraphs[:3]  # Take up to 3 paragraphs
            
        return insights