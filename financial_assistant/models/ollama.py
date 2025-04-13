# financial_assistant/models/ollama.py

from langchain_community.llms import Ollama

def get_ollama_model(model_name="mistral:7b", base_url="http://localhost:11434"):
    """
    Initialize an Ollama model.
    
    Args:
        model_name (str): Name of the model to use
        base_url (str): URL for the Ollama server
        
    Returns:
        Ollama: An initialized Ollama model
    """
    return Ollama(model=model_name, base_url=base_url)