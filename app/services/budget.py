from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
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
        """Update budget status based on current date and start/end dates"""
        budget = get_budget_by_id(self.db, budget_id)
        if not budget:
            return False
        
        current_date = datetime.now()
        should_be_active = budget.start_date <= current_date <= budget.end_date
        
        # Only update if status needs to change
        if budget.is_active != should_be_active:
            budget.is_active = should_be_active
            self.db.commit()
            return True
        
        return False

    def update_all_budget_statuses(self) -> int:
        """Update status of all budgets based on current date"""
        from app.models.budget import BudgetModel
        
        current_date = datetime.now()
        updated_count = 0
        
        # Get all budgets
        all_budgets = self.db.query(BudgetModel).all()
        
        for budget in all_budgets:
            should_be_active = budget.start_date <= current_date <= budget.end_date
            
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

    def get_suggested_budgets(self, user_id: UUID) -> List[BudgetCreate]:
        """Generate suggested budgets based on user's spending patterns"""
        categories = self.get_user_categories(user_id)
        suggestions = []
        
        for category in categories:
            # Only suggest budgets for categories with actual spending
            if category.total_amount <= 0:
                continue
                
            # Suggest budget based on average monthly spending
            # Multiply by 1.2 to give some buffer
            suggested_limit = category.average_amount * 1.2
            
            # Ensure minimum budget amount (at least $10)
            if suggested_limit < 10.0:
                suggested_limit = 10.0
            
            # Create a monthly budget suggestion
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(month=start_date.month + 1) if start_date.month < 12 else start_date.replace(year=start_date.year + 1, month=1)
            
            suggestion = BudgetCreate(
                limit=suggested_limit,
                category=category.category,
                description=f"Suggested budget for {category.category} based on your spending patterns",
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            suggestions.append(suggestion)
        
        return suggestions
