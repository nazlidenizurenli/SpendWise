"""
LLM Configuration for supporting multiple providers (OpenAI & Anthropic)
"""

import os
from typing import Union
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMConfig:
    """Configuration for LLM providers"""
    
    # Provider options
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    
    # Model mappings
    MODELS = {
        OPENAI: {
            "default": "gpt-4-turbo-preview",
            "fast": "gpt-3.5-turbo",
            "advanced": "gpt-4"
        },
        ANTHROPIC: {
            "default": "claude-3-sonnet-20240229",
            "fast": "claude-3-haiku-20240307", 
            "advanced": "claude-3-opus-20240229"
        }
    }

def get_llm(provider: str = None, model_tier: str = "default") -> Union[ChatOpenAI, ChatAnthropic]:
    """
    Get LLM instance based on provider and model tier
    
    Args:
        provider: "openai" or "anthropic" (defaults to env LLM_PROVIDER or "openai")
        model_tier: "default", "fast", or "advanced"
    
    Returns:
        Configured LLM instance
    """
    
    # Determine provider
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", LLMConfig.OPENAI)
    
    # Get model name
    model_name = LLMConfig.MODELS[provider][model_tier]
    
    if provider == LLMConfig.OPENAI:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI")
        
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=0,
            max_tokens=4096
        )
    
    elif provider == LLMConfig.ANTHROPIC:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic")
        
        return ChatAnthropic(
            model=model_name,
            api_key=api_key,
            temperature=0,
            max_tokens=4096
        )
    
    else:
        raise ValueError(f"Unsupported provider: {provider}. Use '{LLMConfig.OPENAI}' or '{LLMConfig.ANTHROPIC}'")

def get_preprocessing_llm(provider: str = None) -> Union[ChatOpenAI, ChatAnthropic]:
    """Get LLM optimized for Stage 1 preprocessing (fast tier)"""
    return get_llm(provider=provider, model_tier="fast")

def get_extraction_llm(provider: str = None) -> Union[ChatOpenAI, ChatAnthropic]:
    """Get LLM optimized for Stage 2 transaction extraction (default tier)"""
    return get_llm(provider=provider, model_tier="default")

# Model recommendations by task
def get_recommended_models():
    """Get model recommendations for different tasks"""
    return {
        "preprocessing": {
            "description": "Text cleaning and structuring",
            "openai": "gpt-3.5-turbo",  # Fast and cheap for simple tasks
            "anthropic": "claude-3-haiku-20240307"  # Fast and accurate
        },
        "extraction": {
            "description": "Complex transaction extraction and categorization", 
            "openai": "gpt-4-turbo-preview",  # Best balance of speed/accuracy
            "anthropic": "claude-3-sonnet-20240229"  # Excellent at structured data
        },
        "advanced": {
            "description": "Complex edge cases and validation",
            "openai": "gpt-4",  # Most capable
            "anthropic": "claude-3-opus-20240229"  # Most capable
        }
    }