from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.db.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.budget import BudgetService
from app.services.background_tasks import trigger_budget_status_update
from app.schemas.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetSummary,
    UserBudgetOverview,
    UserCategory
)
from datetime import datetime

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("/categories", response_model=List[UserCategory])
async def get_user_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all categories for the current user based on their transactions"""
    budget_service = BudgetService(db)
    categories = budget_service.get_user_categories(current_user.id)
    
    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No transactions found. Upload some transactions first to see your categories."
        )
    
    return categories


@router.get("/overview", response_model=UserBudgetOverview)
async def get_user_budget_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive budget overview for the current user"""
    budget_service = BudgetService(db)
    
    # Check if user has transactions
    if not budget_service.can_user_create_budget(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transactions found. Upload some transactions first to create budgets."
        )
    
    return budget_service.get_user_budget_overview(current_user.id)



@router.post("/", response_model=BudgetResponse)
async def create_budget(
    budget_in: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new budget for the current user"""
    budget_service = BudgetService(db)
    
    # Check if user has transactions
    if not budget_service.can_user_create_budget(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transactions found. Upload some transactions first to create budgets."
        )
    
    budget = budget_service.create_budget_for_user(budget_in, current_user.id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create budget. A budget for this category might already exist."
        )
    
    return budget


@router.get("/{budget_id}", response_model=BudgetSummary)
async def get_budget_summary(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed summary for a specific budget"""
    budget_service = BudgetService(db)
    summary = budget_service.get_budget_summary(budget_id, current_user.id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found or you don't have access to it."
        )
    
    return summary


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    budget_update: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing budget"""
    budget_service = BudgetService(db)
    budget = budget_service.update_user_budget(budget_id, budget_update, current_user.id)
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found or you don't have access to it."
        )
    
    return budget


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a budget"""
    budget_service = BudgetService(db)
    success = budget_service.delete_user_budget(budget_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found or you don't have access to it."
        )
    
    return {"message": "Budget deleted successfully"}


@router.get("/", response_model=List[BudgetResponse])
async def get_user_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all budgets for the current user"""
    budget_service = BudgetService(db)
    
    # Check if user has transactions
    if not budget_service.can_user_create_budget(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transactions found. Upload some transactions first to see budgets."
        )
    
    from app.crud.budget import get_budgets_by_user
    budgets = get_budgets_by_user(db, current_user.id)
    return [BudgetResponse.model_validate(budget) for budget in budgets]


@router.post("/update-status/{budget_id}")
async def update_budget_status(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually update the status of a specific budget based on current date"""
    budget_service = BudgetService(db)
    
    # Check if user owns this budget
    budget = budget_service.get_budget_summary(budget_id, current_user.id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found or you don't have access to it."
        )
    
    updated = budget_service.update_budget_status(budget_id)
    
    if updated:
        return {"message": "Budget status updated successfully"}
    else:
        return {"message": "Budget status was already correct"}


@router.post("/update-all-statuses")
async def update_all_budget_statuses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually update the status of all budgets based on current date"""
    budget_service = BudgetService(db)
    updated_count = budget_service.update_all_budget_statuses()
    
    return {
        "message": f"Updated {updated_count} budget statuses",
        "updated_count": updated_count
    }


@router.get("/status/{budget_id}")
async def get_budget_status(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current status of a specific budget"""
    budget_service = BudgetService(db)
    
    # Check if user owns this budget
    budget = budget_service.get_budget_summary(budget_id, current_user.id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found or you don't have access to it."
        )
    
    from app.crud.budget import get_budget_by_id
    budget_model = get_budget_by_id(db, budget_id)
    
    current_date = datetime.now()
    is_within_period = budget_model.start_date <= current_date <= budget_model.end_date
    
    return {
        "budget_id": str(budget_id),
        "is_active": budget_model.is_active,
        "start_date": budget_model.start_date,
        "end_date": budget_model.end_date,
        "current_date": current_date,
        "is_within_period": is_within_period,
        "status": "active" if budget_model.is_active else "inactive",
        "period_status": "within_period" if is_within_period else "outside_period"
    }


@router.post("/trigger-background-update")
async def trigger_background_budget_update(
    current_user: User = Depends(get_current_user)
):
    """Trigger a background budget status update"""
    updated_count = await trigger_budget_status_update()
    
    return {
        "message": f"Background budget status update completed. Updated {updated_count} budgets.",
        "updated_count": updated_count
    }
