"""
Stage 0: Clean and filter raw PDF text
"""

from app.llm.llm_config import get_preprocessing_llm
from app.llm.prompts.preprocess_input import preprocess_input_prompt


def run_chain_clean_text(raw_text: str, model_provider: str = None) -> str:
    """
    Stage 0: Clean raw PDF text by removing legal disclaimers, headers, and metadata
    
    Args:
        raw_text: Raw text from PDF extraction
        model_provider: "openai" or "anthropic" (defaults to env LLM_PROVIDER)
        
    Returns:
        Clean text with legal content removed but transaction data preserved
    """
    try:
        llm = get_preprocessing_llm(provider=model_provider)
        
        # Create chain: Prompt → LLM
        chain = preprocess_input_prompt | llm
        
        print(f"Stage 0: Cleaning raw text ({len(raw_text)} characters)")
        
        # Run text cleaning
        result = chain.invoke({"text": raw_text})
        
        cleaned_text = result.content
        print(f"Stage 0: Cleaned text output ({len(cleaned_text)} characters)")
        
        return cleaned_text
        
    except Exception as e:
        print(f"Stage 0 text cleaning failed: {str(e)}")
        return raw_text  # Fallback to original text
