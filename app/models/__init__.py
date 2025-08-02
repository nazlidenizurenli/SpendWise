from sqlalchemy.orm import declarative_base
Base = declarative_base()
from app.models.user import User
from app.models.transaction import TransactionModel
from app.models.budget import BudgetModel
from app.models.insight import InsightModel
