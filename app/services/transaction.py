from sqlalchemy.orm import Session
from app.models import TransactionModel
from app.schemas.transaction import TransactionCreate
from app.models import User

def insert_transactions(transaction_dicts: list[dict], db: Session, user: User):
    """
    Add validation with Pydantic before inserting
    Handle duplicate detection
    Log or batch insert for speed
    """
    inserted_count = 0
    for tx in transaction_dicts:
        try:
            validated = TransactionCreate(**tx)
            db.add(TransactionModel(**validated.model_dump(), user_id=user.id))
            inserted_count += 1
        except Exception as e:
            print(f"Skipping invalid tx: {e}")
    db.commit()
    return inserted_count

    
