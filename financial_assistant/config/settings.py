# financial_assistant/config/settings.py

import os
from typing import Dict, Any

def load_environment_variables() -> Dict[str, str]:
    """Load environment variables for API keys."""
    return {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "GOOGLE_ANALYTICS_KEY_PATH": os.environ.get("GOOGLE_ANALYTICS_KEY_PATH", ""),
        "STRIPE_API_KEY": os.environ.get("STRIPE_API_KEY", ""),
        "OLLAMA_BASE_URL": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    }

def get_connector_configs() -> Dict[str, Any]:
    """Get configurations for data connectors."""
    env_vars = load_environment_variables()
    
    return {
        "google_analytics": {
            "key_file": env_vars["GOOGLE_ANALYTICS_KEY_PATH"],
            "property_id": os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", "")
        },
        "stripe": {
            "api_key": env_vars["STRIPE_API_KEY"]
        }
    }

def get_model_config() -> Dict[str, Any]:
    """Get configuration for the LLM."""
    env_vars = load_environment_variables()
    
    return {
        "ollama": {
            "base_url": env_vars["OLLAMA_BASE_URL"],
            "model": os.environ.get("OLLAMA_MODEL", "mistral:7b")
        },
        "openai": {
            "api_key": env_vars["OPENAI_API_KEY"],
            "model": os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
        }
    }