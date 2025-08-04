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
    # TODO: Get user model preference from frontend
    # Step 1: Convert PDF to text
    extracted_text = extract_text_from_pdf(file)

    # Step 2: Clean data and build transaction blocks
    transactions = call_llm_to_extract_transactions(extracted_text, model_provider)

    # Step 3: Save to DB
    inserted = insert_transactions(transactions, db, current_user)

    return {"added": inserted}
