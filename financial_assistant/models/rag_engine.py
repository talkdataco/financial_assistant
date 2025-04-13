# financial_assistant/models/rag_engine.py

from typing import Dict, Any, List, Optional
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import LLM
from langchain_core.prompts import PromptTemplate
from financial_assistant.agents.context_builder import ContextBuilder

class MockEmbeddings(Embeddings):
    """Simple mock embeddings for testing without an actual embedding model."""
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return mock embeddings for documents."""
        # Generate a simple deterministic vector for each text
        return [[hash(text) % 100 / 100.0 for _ in range(10)] for text in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Return mock embeddings for a query."""
        # Generate a simple deterministic vector
        return [hash(text) % 100 / 100.0 for _ in range(10)]

class SimpleVectorStore:
    """Simple vector store implementation to avoid ChromaDB dependency."""
    
    def __init__(self, texts: List[str], embeddings: Embeddings, metadatas: Optional[List[Dict]] = None):
        """Initialize the simple vector store."""
        self.texts = texts
        self.embeddings = embeddings
        self.metadatas = metadatas or [{} for _ in texts]
        self.document_embeddings = embeddings.embed_documents(texts)
    
    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """Simple similarity search."""
        query_embedding = self.embeddings.embed_query(query)
        
        # Calculate cosine similarity (simplified)
        similarities = []
        for doc_embedding in self.document_embeddings:
            # Dot product (simplified for mock embeddings)
            similarity = sum(q * d for q, d in zip(query_embedding, doc_embedding))
            similarities.append(similarity)
        
        # Get top k most similar
        indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:k]
        
        # Return documents
        return [
            {"content": self.texts[i], "metadata": self.metadatas[i]}
            for i in indices
        ]

class RAGEngine:
    """RAG-based response generator."""
    
    def __init__(self, llm: LLM, embeddings: Optional[Embeddings] = None):
        """
        Initialize the RAG engine.
        
        Args:
            llm: Language model for generation
            embeddings: Embedding model (optional, uses mock if None)
        """
        self.llm = llm
        self.embeddings = embeddings if embeddings else MockEmbeddings()
        self.context_builder = ContextBuilder()
        self.vector_store = None
        
    def prepare_context(self, query: str, query_analysis: Any, data: Dict[str, Any]) -> str:
        """
        Prepare context for RAG.
        
        Args:
            query: Original user query
            query_analysis: Structured analysis of the query
            data: Data fetched from various sources
            
        Returns:
            Formatted context string
        """
        return self.context_builder.build_context(query, query_analysis, data)
    
    def build_vector_store(self, query: str, query_analysis: Any, data: Dict[str, Any]) -> None:
        """
        Build custom vector store from fetched data.
        
        Args:
            query: Original user query
            query_analysis: Structured analysis of the query
            data: Data fetched from various sources
        """
        documents = self.context_builder.build_vector_store_documents(query, query_analysis, data)
        
        # Create the vector store
        texts = [doc["page_content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        self.vector_store = SimpleVectorStore(
            texts=texts,
            embeddings=self.embeddings,
            metadatas=metadatas
        )
    
    def generate_response(self, query: str, query_analysis: Any, data: Dict[str, Any]) -> str:
        """
        Generate a response using RAG.
        
        Args:
            query: Original user query
            query_analysis: Structured analysis of the query
            data: Data fetched from various sources
            
        Returns:
            Generated response
        """
        # For simplicity in this version, we'll just use the direct context
        # without relying on vector search
        context = self.prepare_context(query, query_analysis, data)
        
        # Still build the vector store for future use, but don't use it yet
        try:
            self.build_vector_store(query, query_analysis, data)
        except Exception as e:
            print(f"Note: Vector store creation failed (this is ok): {e}")
        
        # Create prompt
        prompt_template = PromptTemplate(
            template="""
            You are a financial analytics assistant that helps users understand their business data.
            
            Use the following data to answer the user's question.
            
            {context}
            
            User question: {query}
            
            Provide a helpful, concise response in a professional tone. Include key numbers and percentage changes.
            Break down complex information into easily understandable points.
            
            YOUR RESPONSE:
            """,
            input_variables=["query", "context"]
        )
        
        # Generate the response
        prompt = prompt_template.format(query=query, context=context)
        response = self.llm.invoke(prompt)
        
        return response
    
    def generate_follow_up_questions(self, query: str, query_analysis: Any, data: Dict[str, Any], response: str) -> List[str]:
        """
        Generate follow-up questions based on the data and response.
        
        Args:
            query: Original user query
            query_analysis: Structured analysis of the query
            data: Data fetched from various sources
            response: Generated response
            
        Returns:
            List of follow-up questions
        """
        # Create prompt for follow-up questions
        prompt_template = PromptTemplate(
            template="""
            Based on the following user question, data context, and your response, 
            suggest 3 follow-up questions the user might want to ask next.
            
            Original question: {query}
            
            Data context summary:
            {context_summary}
            
            Your response to the user:
            {response}
            
            Generate 3 useful follow-up questions that would provide additional insights 
            or explore related aspects of the data. Format them as a JSON list like:
            ["Question 1?", "Question 2?", "Question 3?"]
            
            FOLLOW-UP QUESTIONS:
            """,
            input_variables=["query", "context_summary", "response"]
        )
        
        # Create a brief summary of the context
        metrics = []
        sources = []
        
        for source_name, source_data in data.get("data", {}).items():
            if "error" in source_data:
                continue
            
            sources.append(source_name)
            
            for metric_name in source_data.get("data", {}).keys():
                if metric_name not in metrics:
                    metrics.append(metric_name)
        
        context_summary = f"Data sources: {', '.join(sources)}. Metrics: {', '.join(metrics)}."
        
        # Generate follow-up questions
        prompt = prompt_template.format(
            query=query, 
            context_summary=context_summary, 
            response=response
        )
        
        raw_response = self.llm.invoke(prompt)
        
        # Parse the response to extract questions
        try:
            # Try to find and parse a JSON list in the response
            import re
            import json
            
            # Find something that looks like a list in square brackets
            match = re.search(r'\[(.*)\]', raw_response, re.DOTALL)
            if match:
                try:
                    questions_list = json.loads('[' + match.group(1) + ']')
                    return questions_list
                except json.JSONDecodeError:
                    # If JSON parsing fails, try a simpler approach
                    pass
            
            # Fallback: look for numbered questions
            questions = []
            for line in raw_response.split('\n'):
                line = line.strip()
                # Match patterns like "1. What is..." or "1) What is..."
                if re.match(r'^\d+[\.\)]', line):
                    # Remove the number prefix
                    question = re.sub(r'^\d+[\.\)]\s*', '', line)
                    questions.append(question)
            
            # Return found questions or default questions if none found
            return questions if questions else [
                "How does this compare to industry benchmarks?",
                "What factors might have contributed to these results?",
                "What actions could improve these metrics?"
            ]
            
        except Exception as e:
            print(f"Error parsing follow-up questions: {e}")
            # Default questions if parsing fails
            return [
                "How does this compare to industry benchmarks?",
                "What factors might have contributed to these results?",
                "What actions could improve these metrics?"
            ]