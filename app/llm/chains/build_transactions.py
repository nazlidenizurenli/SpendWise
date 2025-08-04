"""
Stage 2: Convert cleaned transaction text into structured transaction objects
"""

import json
import re
from typing import List, Dict
from app.llm.llm_config import get_extraction_llm
from app.llm.prompts.deliver_transactions import deliver_transactions_prompt

def split_transaction_blocks(text: str, max_transactions_per_chunk: int = 25) -> list:
    """
    Split transaction blocks into chunks for processing
    
    Args:
        text: Transaction blocks text from Stage 1
        max_transactions_per_chunk: Maximum transactions per chunk
        
    Returns:
        List of text chunks containing transaction blocks
    """
    # Split by TRANSACTION_START to get individual transactions
    transactions = text.split('TRANSACTION_START')
    
    # Remove empty first element and re-add TRANSACTION_START to each
    transaction_blocks = []
    for i, tx in enumerate(transactions):
        if i == 0 and not tx.strip():
            continue
        
        # Re-add TRANSACTION_START prefix
        if i > 0:
            tx = 'TRANSACTION_START' + tx
        transaction_blocks.append(tx.strip())
    
    # Group transactions into chunks
    chunks = []
    current_chunk = []
    
    for tx_block in transaction_blocks:
        current_chunk.append(tx_block)
        
        if len(current_chunk) >= max_transactions_per_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
    
    # Add remaining transactions
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return [chunk for chunk in chunks if chunk.strip()]

def run_chain_lines_to_transactions(cleaned_text: str, model_provider: str = None) -> List[Dict]:
    """
    Stage 2: Extract structured transactions from cleaned text
    
    Args:
        cleaned_text: Clean transaction blocks from Stage 1
        model_provider: "openai" or "anthropic" (defaults to env LLM_PROVIDER)
        
    Returns:
        List of transaction dictionaries
    """
    try:
        # Get LLM instance optimized for extraction
        llm = get_extraction_llm(provider=model_provider)
        
        # Create chain: Prompt → LLM  
        chain = deliver_transactions_prompt | llm
        
        # Split into chunks to handle large inputs
        chunks = split_transaction_blocks(cleaned_text, max_transactions_per_chunk=25)
        print(f"Stage 2: Processing {len(chunks)} chunks")
        
        # Process each chunk
        all_transactions = []
        for i, chunk in enumerate(chunks):
            try:
                print(f"Stage 2: Processing chunk {i+1}/{len(chunks)}")
                result = chain.invoke({"cleaned_text": chunk})
                
                # Parse and validate JSON response for this chunk
                chunk_transactions = _parse_transaction_json(result.content)
                validated_transactions = _validate_transactions(chunk_transactions)
                
                all_transactions.extend(validated_transactions)
                print(f"Stage 2: Chunk {i+1} converted {len(validated_transactions)} transactions")
                
            except Exception as chunk_error:
                print(f"Stage 2: Chunk {i+1} failed: {str(chunk_error)}")
                continue
        
        print(f"Stage 2: Successfully processed {len(chunks)} chunks, total {len(all_transactions)} transactions")
        return all_transactions
        
    except Exception as e:
        print(f"Stage 2 extraction failed: {str(e)}")
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
            print(f"Expected list, got {type(transactions)}")
            return []
            
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        json_patterns = [
            r'```json\s*(.*?)\s*```',  # ```json ... ```
            r'```\s*(.*?)\s*```',      # ``` ... ```
            r'\[(.*?)\]'               # [ ... ] (simple array)
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, llm_response, re.DOTALL)
            if match:
                try:
                    json_text = match.group(1)
                    if pattern == r'\[(.*?)\]':
                        json_text = f"[{json_text}]"
                    
                    transactions = json.loads(json_text)
                    if isinstance(transactions, list):
                        return transactions
                except json.JSONDecodeError:
                    continue
        
        # Log failure for debugging
        print(f"Failed to parse JSON from LLM response:")
        print(f"Response preview: {llm_response[:500]}...")
        print(f"Full response length: {len(llm_response)} characters")
        
        # Try to save the full response for debugging
        with open("debug_stage2_response.txt", "w") as f:
            f.write(llm_response)
        print("Full response saved to debug_stage2_response.txt")
        
        return []

def _validate_transactions(transactions: List[Dict]) -> List[Dict]:
    """
    Validate and clean transaction objects
    
    Args:
        transactions: Raw transaction list from LLM
        
    Returns:
        Validated transaction list
    """
    validated = []
    required_fields = ["amount", "description", "transaction_type", "source", "timestamp", "category"]
    
    for tx in transactions:
        try:
            # Check required fields
            if not all(field in tx for field in required_fields):
                print(f"Skipping transaction missing required fields: {tx}")
                continue
            
            # Validate amount
            if not isinstance(tx["amount"], (int, float)):
                print(f"Skipping transaction with invalid amount: {tx}")
                continue
            
            # Validate transaction_type
            if tx["transaction_type"] not in ["income", "expense"]:
                print(f"Skipping transaction with invalid type: {tx}")
                continue
                
            # Validate source
            if tx["source"] not in ["credit", "debit", "savings"]:
                print(f"Skipping transaction with invalid source: {tx}")
                continue
            
            validated.append(tx)
            
        except Exception as e:
            print(f"Error validating transaction {tx}: {e}")
            continue
    
    return validated
