"""
OpenAI API utilities for handling different model parameter requirements
"""
from typing import Dict, Any


def get_openai_completion_params(model: str, max_tokens: int, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
    """
    Get the correct parameters for OpenAI API calls based on model type.
    
    Args:
        model: The OpenAI model name
        max_tokens: Maximum number of tokens to generate
        temperature: Sampling temperature (ignored for GPT-5 models)
        **kwargs: Additional parameters
    
    Returns:
        Dictionary with correct parameters for the specific model
    """
    base_params = {
        "model": model,
        **kwargs
    }
    
    # GPT-5 series models don't support temperature parameter and use max_completion_tokens
    if model.startswith("gpt-5"):
        base_params["max_completion_tokens"] = max_tokens
        # Temperature parameter is not supported for GPT-5 models
    elif model.startswith("gpt-4.1"):
        # GPT-4.1 series models use max_completion_tokens and support temperature
        base_params["max_completion_tokens"] = max_tokens
        base_params["temperature"] = temperature
    elif model.startswith("o1"):
        base_params["max_completion_tokens"] = max_tokens
        # Temperature parameter is not supported for o1 reasoning models
    else:
        # GPT-4, GPT-3.5, and other traditional models support temperature and use max_tokens
        base_params["max_tokens"] = max_tokens
        base_params["temperature"] = temperature
    
    return base_params


def is_reasoning_model(model: str) -> bool:
    """
    Check if a model is a reasoning model that uses max_completion_tokens.
    
    Args:
        model: The OpenAI model name
        
    Returns:
        True if the model is a reasoning model
    """
    return model.startswith("gpt-5") or model.startswith("o1")


def get_max_tokens_for_model(model: str) -> int:
    """
    Get the maximum tokens supported by a model.
    
    Args:
        model: The OpenAI model name
        
    Returns:
        Maximum tokens supported by the model
    """
    if model.startswith("gpt-5"):
        return 128000  # GPT-5 can emit up to 128K tokens
    elif model.startswith("gpt-4.1"):
        return 128000  # GPT-4.1 series supports up to 128K tokens (1M context)
    elif model.startswith("gpt-4"):
        return 4096   # GPT-4 standard limit
    elif model.startswith("gpt-3.5"):
        return 4096   # GPT-3.5 limit
    elif model.startswith("o1"):
        return 100000 # o1 models limit
    else:
        return 2000   # Safe default