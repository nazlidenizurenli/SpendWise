from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

class TransactionBase(BaseModel):
    amount: float
    description: str
    category: Optional[str]
    merchant: Optional[str] = None
    transaction_type: Literal["income", "expense"]
    source: Literal["credit", "debit", "savings"]
    timestamp: Optional[datetime] = None

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Description cannot be empty.")
        return v

    @field_validator("amount")
    @classmethod
    def amount_must_not_be_zero(cls, v):
        if v == 0:
            raise ValueError("Amount must be non-zero.")
        return v

    @model_validator(mode="after")
    def validate_transaction_logic(self) -> "TransactionBase":
        """
        Validate transaction logic - all amounts must be non-negative.
        Transaction type and source are determined during extraction.
        """
        # All amounts must be non-negative
        if self.amount < 0:
            raise ValueError("All transaction amounts must be non-negative (>= 0).")
        
        # Amount must be greater than 0 (already validated by amount_must_not_be_zero)
        if self.amount == 0:
            raise ValueError("Transaction amount must be greater than 0.")

        return self


class TransactionCreate(TransactionBase):
    pass


class TransactionOut(TransactionBase):
    id: UUID
    user_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True
