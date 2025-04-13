# financial_assistant/agents/query_analyzer.py

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

class QueryAnalysis(BaseModel):
    """Analysis of a user query."""
    data_sources: List[str] = Field(description="List of data sources needed to answer the query")
    metrics: List[str] = Field(description="List of metrics needed from the data sources")
    time_period: str = Field(description="Time period for the query (e.g., 'last month', 'last week')")

class QueryAnalyzer:
    """Analyzes user queries to determine required data sources and metrics."""
    
    def __init__(self, llm):
        """
        Initialize the query analyzer.
        
        Args:
            llm: Language model to use for analysis
        """
        self.llm = llm
        self.parser = PydanticOutputParser(pydantic_object=QueryAnalysis)
        
        self.prompt = PromptTemplate(
            template="""
            You are a financial analytics assistant that helps analyze business data.
            
            Analyze the following user query and determine:
            1. Which data sources are needed (Google Analytics, Stripe, or both)
            2. What specific metrics are required
            3. The time period for the analysis
            
            User Query: {query}
            
            {format_instructions}
            """,
            input_variables=["query"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
    def analyze(self, query):
        """
        Analyze a user query.
        
        Args:
            query (str): User query to analyze
            
        Returns:
            QueryAnalysis: Analysis of the query
        """
        prompt_value = self.prompt.format(query=query)
        result = self.llm.invoke(prompt_value)
        return self.parser.parse(result)