from sqlalchemy.orm import Session
from uuid import UUID
from app.models.transaction import TransactionModel
from app.schemas.transaction import TransactionCreate


def get_transactions(db: Session, user_id: UUID) -> list[TransactionModel]:
    return db.query(TransactionModel).filter(TransactionModel.user_id == user_id).all()


def get_transaction_by_id(db: Session, transaction_id: UUID) -> TransactionModel | None:
    return db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()


def create_transaction_for_user(
    db: Session, transaction_in: TransactionCreate, user_id: UUID
) -> TransactionModel:
    new_transaction = TransactionModel(**transaction_in.dict(), user_id=user_id)
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction
