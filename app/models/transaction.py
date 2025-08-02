from sqlalchemy import Column, Float, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from app.models import Base
import uuid
from datetime import datetime

class TransactionModel(Base):
    __tablename__ = "transactions"

    # Transaction information
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)
    source = Column(String, nullable=False) # Is this the same as category?
    timestamp = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="transactions")