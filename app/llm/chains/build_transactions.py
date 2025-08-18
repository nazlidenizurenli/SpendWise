"""
Optimized Single-Stage: Direct transaction extraction from cleaned text
"""

import json
import re
import time
import click
from typing import List, Dict
from app.llm.llm_config import get_extraction_llm
from app.llm.prompts.build_transactions import build_transactions_prompt

# Global constants for chunking
MAX_OUTPUT_TOKENS = 4096
MAX_TRANSACTIONS_PER_CHUNK = 20


def create_transaction_chunks(text: str, max_transactions_per_chunk: int = MAX_TRANSACTIONS_PER_CHUNK) -> List[str]:
    """
    Create chunks of transactions for processing
    
    Args:
        text: Clean text from Stage 0
        max_transactions_per_chunk: Maximum transactions per chunk
        
    Returns:
        List of text chunks, each with header + transactions
    """
    lines = text.split('\n')
    header = lines[:2]  # ACCOUNT_TYPE and empty line
    transaction_lines = lines[2:]  # All remaining lines are transactions
    
    chunks = []
    for i in range(0, len(transaction_lines), max_transactions_per_chunk):
        chunk_transactions = transaction_lines[i:i + max_transactions_per_chunk]
        chunk_text = '\n'.join(header + chunk_transactions)
        chunks.append(chunk_text)
    
    return chunks


def run_optimized_transaction_extraction(cleaned_text: str, model_provider: str = None) -> List[Dict]:
    """
    Optimized single-stage transaction extraction
    
    Args:
        cleaned_text: Clean text from Stage 0
        model_provider: "openai" or "anthropic" (defaults to env LLM_PROVIDER)
        
    Returns:
        List of transaction dictionaries
    """
    try:
        click.echo(click.style("  🔧 Initializing Optimized Transaction Extraction...", fg="blue"))
        start_time = time.time()
        
        # Count total transactions
        total_transactions = len(cleaned_text.split('\n')) - 2
        click.echo(click.style(f"  📊 Total transactions detected: {total_transactions}", fg="blue"))
        
        # Get LLM instance optimized for extraction
        llm = get_extraction_llm(provider=model_provider)
        
        # Create chain: Prompt → LLM
        chain = build_transactions_prompt | llm
        
        # Create transaction chunks
        chunks = create_transaction_chunks(cleaned_text, MAX_TRANSACTIONS_PER_CHUNK)
        click.echo(click.style(f"  📦 Split into {len(chunks)} chunks (max {MAX_TRANSACTIONS_PER_CHUNK} transactions per chunk)", fg="blue"))
    
        # Process each chunk
        all_transactions = []
        chunk_times = []
        
        for i, chunk in enumerate(chunks):
            try:
                chunk_start = time.time()
                chunk_transaction_count = len(chunk.split('\n')) - 2
                click.echo(click.style(f"  🔄 Processing chunk {i+1}/{len(chunks)} ({chunk_transaction_count} transactions)...", fg="blue"))
                
                result = chain.invoke({"text": chunk})
            
                # Parse and validate JSON response for this chunk
                chunk_transactions = _parse_transaction_json(result.content)
                validated_transactions = validate_transactions(chunk_transactions)
                
                all_transactions.extend(validated_transactions)
                
                chunk_time = time.time() - chunk_start
                chunk_times.append(chunk_time)
                click.echo(click.style(f"  ✅ Chunk {i+1} completed in {chunk_time:.2f}s ({len(validated_transactions)} transactions)", fg="green"))
                
            except Exception as chunk_error:
                click.echo(click.style(f"  ❌ Chunk {i+1} failed: {str(chunk_error)}", fg="red"))
                continue
        
        total_time = time.time() - start_time
        click.echo(click.style(f"  ✨ Optimized extraction completed in {total_time:.2f}s", fg="blue"))
        click.echo(click.style(f"  📊 Total transactions extracted: {len(all_transactions)}", fg="blue"))
        if chunk_times:
            avg_chunk_time = sum(chunk_times) / len(chunk_times)
            click.echo(click.style(f"  ⏱️  Avg chunk time: {avg_chunk_time:.2f}s", fg="blue"))
        
        return all_transactions
        
    except Exception as e:
        click.echo(click.style(f"  ❌ Optimized extraction failed: {str(e)}", fg="red"))
        return []


def _parse_transaction_json(llm_response: str) -> List[Dict]:
    """
    Parse JSON from LLM response, handling various response formats
    
    Args:
        llm_response: Raw response from LLM
        
    Returns:
        List of transaction dictionaries
    """
    try:
        # Try direct JSON parsing first
        transactions = json.loads(llm_response)
        if isinstance(transactions, list):
            return transactions
        else:
            click.echo(click.style(f"  ⚠️  Expected list, got {type(transactions)}", fg="yellow"))
            return []
            
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        json_patterns = [
            r'```json\s*(.*?)\s*```',  # ```json ... ```
            r'```\s*(.*?)\s*```',      # ``` ... ```
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, llm_response, re.DOTALL)
            if match:
                try:
                    json_text = match.group(1).strip()
                    transactions = json.loads(json_text)
                    if isinstance(transactions, list):
                        click.echo(click.style(f"  ✅ Successfully parsed JSON from {pattern}", fg="green"))
                        return transactions
                except json.JSONDecodeError as e:
                    click.echo(click.style(f"  ⚠️  JSON decode error with pattern {pattern}: {e}", fg="yellow"))
                    continue
        
        # Log failure for debugging
        click.echo(click.style(f"  ❌ Failed to parse JSON from LLM response", fg="red"))
        click.echo(click.style(f"  📝 Response preview: {llm_response[:200]}...", fg="yellow"))
        
        return []


def validate_transactions(transactions: List[Dict]) -> List[Dict]:
    """
    Validate and clean transaction objects
    
    Args:
        transactions: Raw transaction list from LLM
        
    Returns:
        Validated transaction list
    """
    validated = []
    required_fields = ["amount", "description", "merchant", "transaction_type", "source", "timestamp", "category"]
    
    for tx in transactions:
        try:
            # Check required fields
            if not all(field in tx for field in required_fields):
                click.echo(click.style(f"  ⚠️  Skipping transaction missing required fields", fg="yellow"))
                continue
            
            # Validate amount
            if not isinstance(tx["amount"], (int, float)):
                click.echo(click.style(f"  ⚠️  Skipping transaction with invalid amount", fg="yellow"))
                continue
            
            # Validate transaction_type
            if tx["transaction_type"] not in ["income", "expense"]:
                click.echo(click.style(f"  ⚠️  Skipping transaction with invalid type", fg="yellow"))
                continue
                
            # Validate source
            if tx["source"] not in ["credit", "debit", "savings"]:
                click.echo(click.style(f"  ⚠️  Skipping transaction with invalid source", fg="yellow"))
                continue
            
            # Validate timestamp format
            if not re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', tx["timestamp"]):
                click.echo(click.style(f"  ⚠️  Skipping transaction with invalid timestamp format", fg="yellow"))
                continue
            
            # Validate description length
            if len(tx["description"]) > 100:
                tx["description"] = tx["description"][:97] + "..."
            
            # Validate merchant length
            if len(tx["merchant"]) > 50:
                tx["merchant"] = tx["merchant"][:47] + "..."
            
            # Validate category length
            if len(tx["category"]) > 20:
                tx["category"] = tx["category"][:17] + "..."
            
            validated.append(tx)
            
        except Exception as e:
            click.echo(click.style(f"  ❌ Error validating transaction: {e}", fg="red"))
            continue
    
    return validated
