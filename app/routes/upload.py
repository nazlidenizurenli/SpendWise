import time
import click
from app.core.security import get_current_user
from app.services.llm import call_llm_to_extract_transactions
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.models import User
from app.db.db import get_db
from app.services.pdf_parser import extract_text_from_pdf
from app.services.transaction import insert_transactions

router = APIRouter()

@router.post("/process/pdf")
def process_uploaded_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    model_provider: str = "openai"
):
    click.echo(click.style("Starting PDF processing pipeline...", fg="yellow", bold=True))
    
    # Step 1: Convert PDF to text
    click.echo(click.style("Step 1: Extracting text from PDF...", fg="yellow"))
    start_time = time.time()
    extracted_text = extract_text_from_pdf(file)
    text_extraction_time = time.time() - start_time
    click.echo(click.style(f"✅ Text extraction completed in {text_extraction_time:.2f}s", fg="green", bold=True))
    click.echo(click.style(f"   Extracted {len(extracted_text)} characters", fg="blue"))

    # Step 2: Clean data and build transaction blocks
    click.echo(click.style("Step 2: Processing with LLM pipeline...", fg="yellow"))
    start_time = time.time()
    transactions = call_llm_to_extract_transactions(extracted_text, model_provider)
    llm_processing_time = time.time() - start_time
    click.echo(click.style(f"✅ LLM processing completed in {llm_processing_time:.2f}s", fg="green", bold=True))
    click.echo(click.style(f"   Extracted {len(transactions)} transactions", fg="blue"))

    # Step 3: Save to DB
    click.echo(click.style("Step 3: Saving transactions to database...", fg="yellow"))
    start_time = time.time()
    inserted = insert_transactions(transactions, db, current_user)
    db_insertion_time = time.time() - start_time
    click.echo(click.style(f"✅ Database insertion completed in {db_insertion_time:.2f}s", fg="green", bold=True))
    click.echo(click.style(f"   Successfully inserted {inserted} transactions", fg="blue"))

    # Summary
    total_time = text_extraction_time + llm_processing_time + db_insertion_time
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style("📊 PERFORMANCE SUMMARY", fg="cyan", bold=True))
    click.echo(click.style("=" * 60, fg="cyan"))
    click.echo(click.style(f"Text Extraction: {text_extraction_time:.2f}s", fg="white"))
    click.echo(click.style(f"LLM Processing:  {llm_processing_time:.2f}s ({llm_processing_time/total_time*100:.1f}%)", fg="white"))
    click.echo(click.style(f"DB Insertion:    {db_insertion_time:.2f}s", fg="white"))
    click.echo(click.style(f"TOTAL TIME:      {total_time:.2f}s", fg="yellow", bold=True))
    click.echo(click.style("=" * 60, fg="cyan"))

    return {"added": inserted}
