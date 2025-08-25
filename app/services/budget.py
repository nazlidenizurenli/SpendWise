from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Optional

from app.crud.budget import (
    get_user_categories,
    get_budgets_by_user,
    get_active_budgets_by_user,
    get_budget_by_id,
    get_budget_by_user_and_category,
    create_budget,
    update_budget,
    delete_budget,
    get_user_spending_in_period,
    check_user_has_transactions
)
from app.schemas.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetSummary,
    UserBudgetOverview,
    UserCategory
)


class BudgetService:
    def __init__(self, db: Session):
        self.db = db

    def update_budget_status(self, budget_id: UUID) -> bool:
        """Update budget status based on current date and start/end dates with 60-day grace period"""
        budget = get_budget_by_id(self.db, budget_id)
        if not budget:
            return False
        
        current_date = datetime.now()
        # Budget is active if current date is within budget period OR within 60 days after end date
        grace_period_end = budget.end_date + timedelta(days=60)
        should_be_active = budget.start_date <= current_date <= grace_period_end
        
        # Only update if status needs to change
        if budget.is_active != should_be_active:
            budget.is_active = should_be_active
            self.db.commit()
            return True
        
        return False

    def update_all_budget_statuses(self) -> int:
        """Update status of all budgets based on current date with 60-day grace period"""
        from app.models.budget import BudgetModel
        
        current_date = datetime.now()
        updated_count = 0
        
        # Get all budgets
        all_budgets = self.db.query(BudgetModel).all()
        
        for budget in all_budgets:
            # Budget is active if current date is within budget period OR within 60 days after end date
            grace_period_end = budget.end_date + timedelta(days=60)
            should_be_active = budget.start_date <= current_date <= grace_period_end
            
            # Only update if status needs to change
            if budget.is_active != should_be_active:
                budget.is_active = should_be_active
                updated_count += 1
        
        if updated_count > 0:
            self.db.commit()
        
        return updated_count

    def get_user_categories(self, user_id: UUID) -> List[UserCategory]:
        """Get all categories for a user based on their transactions"""
        return get_user_categories(self.db, user_id)

    def can_user_create_budget(self, user_id: UUID) -> bool:
        """Check if a user can create budgets (has transactions)"""
        return check_user_has_transactions(self.db, user_id)

    def get_user_budget_overview(self, user_id: UUID) -> UserBudgetOverview:
        """Get comprehensive budget overview for a user"""
        # Update budget statuses before getting overview
        self.update_all_budget_statuses()
        
        categories = self.get_user_categories(user_id)
        all_budgets = get_budgets_by_user(self.db, user_id)
        active_budgets = get_active_budgets_by_user(self.db, user_id)
        
        # Calculate totals
        total_budget_amount = sum(budget.limit for budget in active_budgets)
        total_spent_amount = 0
        
        # Calculate spent amount for each active budget
        for budget in active_budgets:
            spent = get_user_spending_in_period(
                self.db, user_id, budget.category, 
                budget.start_date, budget.end_date
            )
            total_spent_amount += spent
        
        overall_remaining = total_budget_amount - total_spent_amount
        
        return UserBudgetOverview(
            user_id=user_id,
            categories=categories,
            total_budgets=len(all_budgets),
            active_budgets=len(active_budgets),
            total_budget_amount=total_budget_amount,
            total_spent_amount=total_spent_amount,
            overall_remaining=overall_remaining
        )

    def get_budget_summary(self, budget_id: UUID, user_id: UUID) -> Optional[BudgetSummary]:
        """Get detailed summary for a specific budget"""
        # Update this budget's status first
        self.update_budget_status(budget_id)
        
        budget = get_budget_by_id(self.db, budget_id)
        if not budget or budget.user_id != user_id:
            return None
        
        # Calculate spent amount for this budget
        spent_amount = get_user_spending_in_period(
            self.db, user_id, budget.category, 
            budget.start_date, budget.end_date
        )
        
        remaining_amount = budget.limit - spent_amount
        percentage_used = (spent_amount / budget.limit) * 100 if budget.limit > 0 else 0
        is_over_budget = spent_amount > budget.limit
        
        return BudgetSummary(
            budget=BudgetResponse.model_validate(budget),
            spent_amount=spent_amount,
            remaining_amount=remaining_amount,
            percentage_used=percentage_used,
            is_over_budget=is_over_budget
        )

    def create_budget_for_user(self, budget_in: BudgetCreate, user_id: UUID) -> Optional[BudgetResponse]:
        """Create a new budget for a user"""
        # Check if user has transactions
        if not self.can_user_create_budget(user_id):
            return None
        
        # Check if budget already exists for this category
        existing_budget = get_budget_by_user_and_category(self.db, user_id, budget_in.category)
        if existing_budget:
            return None
        
        budget = create_budget(self.db, budget_in, user_id)
        return BudgetResponse.model_validate(budget)

    def update_user_budget(self, budget_id: UUID, budget_update: BudgetUpdate, user_id: UUID) -> Optional[BudgetResponse]:
        """Update a user's budget"""
        budget = get_budget_by_id(self.db, budget_id)
        if not budget or budget.user_id != user_id:
            return None
        
        updated_budget = update_budget(self.db, budget_id, budget_update)
        if updated_budget:
            return BudgetResponse.model_validate(updated_budget)
        return None

    def delete_user_budget(self, budget_id: UUID, user_id: UUID) -> bool:
        """Delete a user's budget"""
        budget = get_budget_by_id(self.db, budget_id)
        if not budget or budget.user_id != user_id:
            return False
        
        return delete_budget(self.db, budget_id)

