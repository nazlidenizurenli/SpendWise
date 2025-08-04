"""
Stage 1: Extract and clean transaction lines from raw PDF text
"""

from app.llm.llm_config import get_preprocessing_llm
from app.llm.prompts.build_transaction_blocks import build_transaction_blocks_prompt


def split_text_intelligently(text: str, max_chunk_size: int = 8000) -> list:
    """
    Split text into chunks using intelligent boundary detection
    
    Args:
        text: Raw text to split
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of text chunks that respect data boundaries
    """
    
    # First try page-based splitting if PAGE markers exist
    if '--- PAGE' in text:
        page_chunks = []
        pages = text.split('--- PAGE')
        
        for i, page in enumerate(pages):
            if i == 0 and page.strip():
                page_chunks.append(page.strip())
            elif i > 0:
                page_chunks.append(('--- PAGE' + page).strip())
        
        # Check if page chunks are reasonable size
        oversized_chunks = [chunk for chunk in page_chunks if len(chunk) > max_chunk_size]
        if not oversized_chunks:
            return [chunk for chunk in page_chunks if chunk]
    
    # Fallback to intelligent character-based chunking
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs (double newlines) first
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Check if adding this paragraph would exceed limit
        potential_chunk = current_chunk + '\n\n' + paragraph if current_chunk else paragraph
        
        if len(potential_chunk) <= max_chunk_size:
            current_chunk = potential_chunk
        else:
            # Current chunk is full, save it
            if current_chunk:
                chunks.append(current_chunk)
            
            # Handle oversized paragraphs
            if len(paragraph) > max_chunk_size:
                # Split oversized paragraph by sentences/lines
                lines = paragraph.split('\n')
                temp_chunk = ""
                
                for line in lines:
                    if len(temp_chunk + '\n' + line) <= max_chunk_size:
                        temp_chunk = temp_chunk + '\n' + line if temp_chunk else line
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        temp_chunk = line
                
                current_chunk = temp_chunk
            else:
                current_chunk = paragraph
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    # Ensure no empty chunks
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def run_chain_extract_transaction_lines(raw_text: str, model_provider: str = None) -> str:
    """
    Stage 1: Clean and structure raw PDF text for transaction extraction
    
    Args:
        raw_text: Raw text from PDF extraction
        model_provider: "openai" or "anthropic" (defaults to env LLM_PROVIDER)
        
    Returns:
        Clean, structured text with transaction blocks
    """
    try:
        # Get LLM instance optimized for preprocessing
        llm = get_preprocessing_llm(provider=model_provider)
        
        # Create chain: Prompt → LLM
        chain = build_transaction_blocks_prompt | llm
        
        # Split text into chunks to avoid output token limits
        # Note: Stage 1 expands text ~3x, so use smaller chunk size
        chunks = split_text_intelligently(raw_text, max_chunk_size=3000)
        print(f"Stage 1: Processing {len(chunks)} chunks")
        
        # Process each chunk
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            try:
                print(f"Stage 1: Processing chunk {i+1}/{len(chunks)}")
                result = chain.invoke({"text": chunk})
                processed_chunks.append(result.content)
            except Exception as chunk_error:
                print(f"Stage 1: Chunk {i+1} failed: {str(chunk_error)}")
                # Include original chunk as fallback
                processed_chunks.append(chunk)
        
        # Merge all processed chunks
        merged_result = "\n\n".join(processed_chunks)
        
        print(f"Stage 1: Successfully processed {len(chunks)} chunks")
        return merged_result
        
    except Exception as e:
        print(f"Stage 1 preprocessing failed: {str(e)}")
        return raw_text  # Fallback to original text
