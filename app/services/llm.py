# app/services/llm.py
import time
import click
from typing import List
from app.llm.chains.build_transactions import run_optimized_transaction_extraction
from app.llm.chains.clean_text import run_chain_clean_text


def call_llm_to_extract_transactions(
    raw_text: str,
    model_provider: str = None
) -> List[dict]:
    """
    Full LLM pipeline:
    1. Clean input raw text
    2. Convert each line into a structured transaction block

    Args:
        raw_text: messy PDF text
        model_provider: 'openai' or 'anthropic'
    """
    click.echo(click.style("Starting LLM pipeline...", fg="yellow"))
    click.echo(click.style("Cleaning raw text...", fg="yellow"))
    start_time = time.time()
    cleaned_lines = run_chain_clean_text(raw_text, model_provider=model_provider)
    stage0_time = time.time() - start_time
    click.echo(click.style(f"✅ Cleaned input data in {stage0_time:.2f}s", fg="green", bold=True))
    
    click.echo(click.style("Extracting transaction blocks...", fg="yellow"))
    start_time = time.time()
    transactions = run_optimized_transaction_extraction(cleaned_lines, model_provider=model_provider)
    stage1_time = time.time() - start_time
    click.echo(click.style(f"✅ Created transaction blocks in {stage1_time:.2f}s", fg="green", bold=True))
    
    return transactions
