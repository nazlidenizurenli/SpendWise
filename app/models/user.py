import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models import Base

class User(Base):
    __tablename__ = "users"

    # User information
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Meta information
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transactions = relationship("TransactionModel", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("BudgetModel", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("InsightModel", back_populates="user", cascade="all, delete-orphan")
