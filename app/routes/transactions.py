from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.schemas.transaction import TransactionCreate, TransactionOut
from app.models.user import User
from app.db.db import get_db
from app.crud import transaction as crud_transaction
from app.core.security import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/submit", response_model=TransactionOut)
def create_transaction(
    transaction_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transaction = crud_transaction.create_transaction_for_user(
        db=db,
        transaction_in=transaction_in,
        user_id=current_user.id
    )
    return transaction


@router.get("/get-all", response_model=list[TransactionOut])
def read_user_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transactions = crud_transaction.get_transactions(db, user_id=current_user.id)
    return transactions
