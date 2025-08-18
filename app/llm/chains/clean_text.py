"""
Stage 0: Clean and filter raw PDF text
"""

import time
import click
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
        click.echo(click.style("  🔧 Initializing Stage 0...", fg="blue"))
        start_time = time.time()
        
        llm = get_preprocessing_llm(provider=model_provider)
        
        # Create chain: Prompt → LLM
        chain = preprocess_input_prompt | llm
        
        click.echo(click.style(f"  📝 Processing {len(raw_text)} characters...", fg="blue"))
        
        # Run text cleaning
        result = chain.invoke({"text": raw_text})
        
        cleaned_text = result.content
        processing_time = time.time() - start_time
        
        click.echo(click.style(f"  ✨ Stage 0 processing: {processing_time:.2f}s", fg="blue"))
        click.echo(click.style(f"  📊 Input: {len(raw_text)} chars → Output: {len(cleaned_text)} chars", fg="blue"))
        
        return cleaned_text
        
    except Exception as e:
        click.echo(click.style(f"  ❌ Stage 0 text cleaning failed: {str(e)}", fg="red"))
        return raw_text  # Fallback to original text
