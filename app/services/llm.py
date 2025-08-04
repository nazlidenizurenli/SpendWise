# app/services/llm.py
from typing import List
from app.llm.chains.format_transactions import run_chain_extract_transaction_lines
from app.llm.chains.build_transactions import run_chain_lines_to_transactions
from app.llm.chains.clean_text import run_chain_clean_text


def call_llm_to_extract_transactions(
    raw_text: str,
    model_provider: str = None
) -> List[dict]:
    """
    Full LLM pipeline:
    1. Extract transaction-like lines from raw PDF text
    2. Convert each line into a structured transaction dict

    Args:
        raw_text: messy PDF text
        model_provider: 'openai' or 'anthropic'
    """
    cleaned_lines = run_chain_clean_text(raw_text, model_provider=model_provider)
    transaction_blocks = run_chain_extract_transaction_lines(cleaned_lines, model_provider=model_provider)
    completed_transactions = run_chain_lines_to_transactions(transaction_blocks, model_provider=model_provider)
    return completed_transactions
