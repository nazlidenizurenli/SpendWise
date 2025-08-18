from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.models.budget import BudgetModel
from app.models.transaction import TransactionModel
from app.schemas.budget import BudgetCreate, BudgetUpdate, UserCategory


def calculate_spending_amount(amount: float, transaction_type: str, source: str) -> float:
    """
    Calculate the correct spending amount based on transaction type and source.
    
    For budget calculations, we want positive values for spending (money going out).
    
    Credit cards:
    - Positive amount + "expense" = spending (money going out)
    - Negative amount + "income" = income (money coming in)
    
    Debit cards:
    - Negative amount + "expense" = spending (money going out) 
    - Positive amount + "income" = income (money coming in)
    """
    if transaction_type == "expense":
        # For expenses, we want positive values (money going out)
        if source == "credit":
            # Credit card expenses are positive amounts
            return abs(amount)
        else:  # debit or savings
            # Debit card expenses are negative amounts
            return abs(amount)
    else:  # income
        # For income, we want negative values (money coming in, not spending)
        if source == "credit":
            # Credit card income is negative amounts
            return -abs(amount)
        else:  # debit or savings
            # Debit card income is positive amounts
            return -abs(amount)


def get_user_categories(db: Session, user_id: UUID) -> List[UserCategory]:
    """Get all categories for a user based on their transactions"""
    # Calculate spending amount - all amounts are now non-negative
    spending_amount = case(
        # Expenses = spending (all amounts are non-negative)
        (
            TransactionModel.transaction_type == "expense",
            TransactionModel.amount
        ),
        # Income transactions = not spending (return 0 for spending calculations)
        (
            TransactionModel.transaction_type == "income",
            0.0
        ),
        else_=0.0
    )
    
    categories = db.query(
        TransactionModel.category,
        func.count(TransactionModel.id).label('transaction_count'),
        func.sum(spending_amount).label('total_amount'),
        func.avg(spending_amount).label('average_amount')
    ).filter(
        TransactionModel.user_id == user_id
    ).group_by(
        TransactionModel.category
    ).all()
    
    return [
        UserCategory(
            category=cat.category,
            transaction_count=cat.transaction_count,
            total_amount=float(cat.total_amount or 0),
            average_amount=float(cat.average_amount or 0)
        )
        for cat in categories
    ]


def get_budgets_by_user(db: Session, user_id: UUID) -> List[BudgetModel]:
    """Get all budgets for a user"""
    return db.query(BudgetModel).filter(BudgetModel.user_id == user_id).all()


def get_active_budgets_by_user(db: Session, user_id: UUID) -> List[BudgetModel]:
    """Get all active budgets for a user"""
    return db.query(BudgetModel).filter(
        and_(
            BudgetModel.user_id == user_id,
            BudgetModel.is_active == True
        )
    ).all()


def get_budget_by_id(db: Session, budget_id: UUID) -> Optional[BudgetModel]:
    """Get a specific budget by ID"""
    return db.query(BudgetModel).filter(BudgetModel.id == budget_id).first()


def get_budget_by_user_and_category(db: Session, user_id: UUID, category: str) -> Optional[BudgetModel]:
    """Get active budget for a user and specific category"""
    return db.query(BudgetModel).filter(
        and_(
            BudgetModel.user_id == user_id,
            BudgetModel.category == category,
            BudgetModel.is_active == True
        )
    ).first()


def create_budget(db: Session, budget_in: BudgetCreate, user_id: UUID) -> BudgetModel:
    """Create a new budget for a user"""
    budget_data = budget_in.model_dump()
    new_budget = BudgetModel(
        user_id=user_id,
        limit=budget_data["limit"],
        category=budget_data["category"],
        description=budget_data["description"],
        start_date=budget_data["start_date"],
        end_date=budget_data["end_date"],
        is_active=budget_data.get("is_active", True)
    )
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


def update_budget(db: Session, budget_id: UUID, budget_update: BudgetUpdate) -> Optional[BudgetModel]:
    """Update an existing budget"""
    budget = get_budget_by_id(db, budget_id)
    if not budget:
        return None
    
    update_data = budget_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)
    
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, budget_id: UUID) -> bool:
    """Delete a budget"""
    budget = get_budget_by_id(db, budget_id)
    if not budget:
        return False
    
    db.delete(budget)
    db.commit()
    return True


def get_user_spending_in_period(
    db: Session, 
    user_id: UUID, 
    category: str, 
    start_date: datetime, 
    end_date: datetime
) -> float:
    """Get total spending for a user in a specific category and time period"""
    # Calculate spending amount for the period - all amounts are now non-negative
    spending_amount = case(
        # Expenses = spending (all amounts are non-negative)
        (
            TransactionModel.transaction_type == "expense",
            TransactionModel.amount
        ),
        # Income transactions = not spending (return 0 for spending calculations)
        (
            TransactionModel.transaction_type == "income",
            0.0
        ),
        else_=0.0
    )

    result = db.query(func.sum(spending_amount)).filter(
        and_(
            TransactionModel.user_id == user_id,
            TransactionModel.category == category,
            TransactionModel.timestamp >= start_date,
            TransactionModel.timestamp <= end_date
        )
    ).scalar()
    
    return float(result or 0)


def check_user_has_transactions(db: Session, user_id: UUID) -> bool:
    """Check if a user has any transactions"""
    count = db.query(TransactionModel).filter(
        TransactionModel.user_id == user_id
    ).count()
    return count > 0
