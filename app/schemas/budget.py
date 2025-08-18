from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class BudgetBase(BaseModel):
    limit: float = Field(..., gt=0, description="Budget spending limit")
    category: str = Field(..., description="Budget category")
    description: str = Field(..., description="Budget description")
    start_date: datetime = Field(..., description="Budget start date")
    end_date: datetime = Field(..., description="Budget end date")
    is_active: bool = Field(default=True, description="Whether budget is active")


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    limit: Optional[float] = Field(None, gt=0, description="Budget spending limit")
    category: Optional[str] = Field(None, description="Budget category")
    description: Optional[str] = Field(None, description="Budget description")
    start_date: Optional[datetime] = Field(None, description="Budget start date")
    end_date: Optional[datetime] = Field(None, description="Budget end date")
    is_active: Optional[bool] = Field(None, description="Whether budget is active")


class BudgetResponse(BudgetBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserCategory(BaseModel):
    category: str
    transaction_count: int
    total_amount: float
    average_amount: float


class BudgetSummary(BaseModel):
    budget: BudgetResponse
    spent_amount: float
    remaining_amount: float
    percentage_used: float
    is_over_budget: bool


class UserBudgetOverview(BaseModel):
    user_id: UUID
    categories: List[UserCategory]
    total_budgets: int
    active_budgets: int
    total_budget_amount: float
    total_spent_amount: float
    overall_remaining: float
