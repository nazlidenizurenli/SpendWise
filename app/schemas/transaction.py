from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

class TransactionBase(BaseModel):
    amount: float
    description: str
    category: Optional[str]
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
        if self.source == "credit":
            if self.amount < 0 and self.transaction_type != "income":
                raise ValueError("Credit transactions must have a negative amount for income and positive for expense.")
            if self.amount > 0 and self.transaction_type != "expense":
                raise ValueError("Credit transactions must be type expense.")
            if self.amount == 0:
                raise ValueError("Credit transactions must have a non-zero amount.")

        if self.source == "debit":
            if self.amount > 0 and self.transaction_type != "income":
                raise ValueError("Positive amounts from debit/savings must be income.")
            if self.amount < 0 and self.transaction_type != "expense":
                raise ValueError("Negative amounts from debit/savings must be expense.")

        return self


class TransactionCreate(TransactionBase):
    pass


class TransactionOut(TransactionBase):
    id: UUID
    user_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True
