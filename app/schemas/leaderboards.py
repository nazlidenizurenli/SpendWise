# app/schemas/leaderboards.py
from pydantic import BaseModel
from typing import Optional

class CategoryLeaderboardItem(BaseModel):
    category: str
    amount: float

class MerchantLeaderboardItem(BaseModel):
    merchant: Optional[str] = None
    category: Optional[str] = None
    amount: float

class OverallStatsOut(BaseModel):
    income_30d: float
    income_month: float
    income_year: float
    expense_30d: float
    expense_month: float
    expense_year: float
