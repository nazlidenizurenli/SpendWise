# app/llm/tools.py
from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from langchain_core.tools import tool

from app.services.leaderboards import overall_stats
from app.crud.budget import get_active_budgets_by_user, get_user_spending_in_period

def _now_utc() -> datetime:
    return datetime.utcnow().replace(microsecond=0)

def _current_month_window(now: datetime) -> tuple[datetime, datetime]:
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    y, m = start.year, start.month + 1
    if m == 13:
        y, m = y + 1, 1
    end = start.replace(year=y, month=m)
    return start, end

@tool("get_overall_stats")
def get_overall_stats_tool(days: int = 30, *, db: Session, user_id: UUID) -> Dict[str, float]:
    """
    Return overall totals for the user:
    { income_30d, income_month, income_year, expense_30d, expense_month, expense_year }.
    'days' controls the rolling window used for the 30d metrics.
    """
    return overall_stats(db, user_id, days)

@tool("check_budget_tracking_status")
def check_budget_tracking_status_tool(*, db: Session, user_id: UUID) -> Dict[str, Any]:
    """
    Check if user is on track with their budgets. Returns comprehensive budget analysis.
    
    Returns:
    - has_budgets: bool - whether user has any active budgets
    - budget_count: int - number of active budgets
    - budgets: list - detailed budget analysis for each active budget
    - overall_status: str - overall budget health status
    - message: str - summary message about budget status
    """
    # Get all active budgets for the user
    active_budgets = get_active_budgets_by_user(db, user_id)
    
    if not active_budgets:
        return {
            "has_budgets": False,
            "budget_count": 0,
            "budgets": [],
            "overall_status": "no_budgets",
            "message": "User has no active budgets. Cannot determine whether on track or not."
        }
    
    now = _now_utc()
    budget_analyses = []
    total_overage = 0.0
    total_remaining = 0.0
    budgets_exceeded = 0
    
    for budget in active_budgets:
        # Calculate spending for this budget's category and time period
        spent_amount = get_user_spending_in_period(
            db, user_id, budget.category, budget.start_date, budget.end_date
        )
        
        # Calculate difference (remaining = limit - spent)
        # Negative means exceeded budget
        difference = budget.limit - spent_amount
        percent_used = (spent_amount / budget.limit * 100) if budget.limit > 0 else 0
        
        # Determine status
        if difference < 0:
            status = "exceeded"
            budgets_exceeded += 1
            total_overage += abs(difference)
        elif percent_used > 90:
            status = "warning"
        elif percent_used > 75:
            status = "caution"
        else:
            status = "on_track"
            total_remaining += difference
        
        # Check if budget period is current
        is_current = budget.start_date <= now <= budget.end_date
        
        # Calculate period based on date range
        duration_days = (budget.end_date - budget.start_date).days
        if duration_days <= 1:
            period = "daily"
        elif duration_days <= 7:
            period = "weekly"
        elif duration_days <= 31:
            period = "monthly"
        else:
            period = "custom"

        budget_analysis = {
            "budget_id": str(budget.id),
            "category": budget.category,
            "limit": float(budget.limit),
            "spent": float(spent_amount),
            "remaining": float(difference),
            "percent_used": round(percent_used, 1),
            "status": status,
            "is_current": is_current,
            "start_date": budget.start_date.isoformat(),
            "end_date": budget.end_date.isoformat(),
            "period": period,
            "description": budget.description
        }
        
        budget_analyses.append(budget_analysis)
    
    # Determine overall status
    if budgets_exceeded == 0:
        overall_status = "all_on_track"
        message = f"All {len(active_budgets)} budgets are on track. Total remaining across all budgets: ${total_remaining:.2f}"
    elif budgets_exceeded == len(active_budgets):
        overall_status = "all_exceeded"
        message = f"All {len(active_budgets)} budgets have been exceeded. Total overage: ${total_overage:.2f}"
    else:
        overall_status = "mixed"
        message = f"{budgets_exceeded} out of {len(active_budgets)} budgets exceeded. Total overage: ${total_overage:.2f}, Total remaining: ${total_remaining:.2f}"
    
    return {
        "has_budgets": True,
        "budget_count": len(active_budgets),
        "budgets": budget_analyses,
        "overall_status": overall_status,
        "budgets_exceeded": budgets_exceeded,
        "total_overage": round(total_overage, 2),
        "total_remaining": round(total_remaining, 2),
        "message": message
    }

@tool("get_budget_details_by_category")
def get_budget_details_by_category_tool(category: str, *, db: Session, user_id: UUID) -> Dict[str, Any]:
    """
    Get detailed budget information for a specific category.
    
    Args:
        category: The budget category to analyze
        
    Returns detailed budget analysis for the specified category.
    """
    active_budgets = get_active_budgets_by_user(db, user_id)
    
    # Find budget for the specified category
    target_budget = None
    for budget in active_budgets:
        if budget.category.lower() == category.lower():
            target_budget = budget
            break
    
    if not target_budget:
        return {
            "found": False,
            "message": f"No active budget found for category '{category}'"
        }
    
    # Calculate spending for this budget
    spent_amount = get_user_spending_in_period(
        db, user_id, target_budget.category, target_budget.start_date, target_budget.end_date
    )
    
    difference = target_budget.limit - spent_amount
    percent_used = (spent_amount / target_budget.limit * 100) if target_budget.limit > 0 else 0
    
    now = _now_utc()
    is_current = target_budget.start_date <= now <= target_budget.end_date
    
    # Calculate period based on date range
    duration_days = (target_budget.end_date - target_budget.start_date).days
    if duration_days <= 1:
        period = "daily"
    elif duration_days <= 7:
        period = "weekly"
    elif duration_days <= 31:
        period = "monthly"
    else:
        period = "custom"
    
    return {
        "found": True,
        "category": target_budget.category,
        "limit": float(target_budget.limit),
        "spent": float(spent_amount),
        "remaining": float(difference),
        "percent_used": round(percent_used, 1),
        "exceeded": difference < 0,
        "overage_amount": float(abs(difference)) if difference < 0 else 0.0,
        "is_current": is_current,
        "start_date": target_budget.start_date.isoformat(),
        "end_date": target_budget.end_date.isoformat(),
        "period": period,
        "description": target_budget.description
    }
