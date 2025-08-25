# app/services/leaderboards.py
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from typing import List

from app.schemas.leaderboards import CategoryLeaderboardItem, MerchantLeaderboardItem
from app.crud import leaderboards as lb

def compute_window(days: int, now: datetime | None = None) -> tuple[datetime, datetime]:
    """
    Compute a time window for leaderboard queries.
    
    Args:
        days: Number of days to look back from now
        now: Current time (defaults to UTC now)
        
    Returns:
        Tuple of (start_time, end_time) both timezone-aware in UTC
    """
    if now is None:
        end = datetime.now(timezone.utc).replace(microsecond=0)
    else:
        # Ensure the provided datetime is timezone-aware (convert to UTC if needed)
        if now.tzinfo is None:
            # Assume naive datetime is UTC
            end = now.replace(tzinfo=timezone.utc, microsecond=0)
        else:
            # Convert to UTC
            end = now.astimezone(timezone.utc).replace(microsecond=0)
    
    start = end - timedelta(days=days)
    return start, end

# ---- Category services ----
def svc_categories_total_value(db: Session, user_id: UUID, days: int, limit: int) -> List[CategoryLeaderboardItem]:
    start, end = compute_window(days)
    rows = lb.top_categories_by_total_value(db, user_id, start, end, limit)
    return [CategoryLeaderboardItem(**r) for r in rows]

def svc_categories_tx_count(db: Session, user_id: UUID, days: int, limit: int) -> List[CategoryLeaderboardItem]:
    start, end = compute_window(days)
    rows = lb.top_categories_by_tx_count(db, user_id, start, end, limit)
    return [CategoryLeaderboardItem(**r) for r in rows]

def svc_categories_avg_cost(db: Session, user_id: UUID, days: int, limit: int) -> List[CategoryLeaderboardItem]:
    start, end = compute_window(days)
    rows = lb.top_categories_by_avg_cost(db, user_id, start, end, limit)
    return [CategoryLeaderboardItem(**r) for r in rows]

def svc_categories_largest_tx(db: Session, user_id: UUID, days: int, limit: int) -> List[CategoryLeaderboardItem]:
    start, end = compute_window(days)
    rows = lb.top_categories_by_largest_tx(db, user_id, start, end, limit)
    return [CategoryLeaderboardItem(**r) for r in rows]

# ---- Merchant services ----
def svc_merchants_total_value(db: Session, user_id: UUID, days: int, limit: int) -> List[MerchantLeaderboardItem]:
    start, end = compute_window(days)
    rows = lb.top_merchants_by_total_value(db, user_id, start, end, limit)
    return [MerchantLeaderboardItem(**r) for r in rows]

def svc_merchants_tx_count(db: Session, user_id: UUID, days: int, limit: int) -> List[MerchantLeaderboardItem]:
    start, end = compute_window(days)
    rows = lb.top_merchants_by_tx_count(db, user_id, start, end, limit)
    return [MerchantLeaderboardItem(**r) for r in rows]

def svc_merchants_avg_cost(db: Session, user_id: UUID, days: int, limit: int) -> List[MerchantLeaderboardItem]:
    start, end = compute_window(days)
    rows = lb.top_merchants_by_avg_cost(db, user_id, start, end, limit)
    return [MerchantLeaderboardItem(**r) for r in rows]

def svc_merchants_largest_tx(db: Session, user_id: UUID, days: int, limit: int) -> List[MerchantLeaderboardItem]:
    start, end = compute_window(days)
    rows = lb.top_merchants_by_largest_tx(db, user_id, start, end, limit)
    return [MerchantLeaderboardItem(**r) for r in rows]

def _now_utc() -> datetime:
    return datetime.utcnow().replace(microsecond=0)

def _month_start(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def _year_start(dt: datetime) -> datetime:
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

def overall_stats(db: Session, user_id: UUID, days: int = 30):
    now = _now_utc()

    start_30d = now - timedelta(days=days)
    month_start = _month_start(now)
    year_start = _year_start(now)

    inc_30d, exp_30d   = lb.totals_last_30d(db, user_id, start_30d, now)
    inc_m, exp_m       = lb.totals_this_month(db, user_id, month_start, now)
    inc_y, exp_y       = lb.totals_this_year(db, user_id, year_start, now)

    return {
        "income_30d": inc_30d,
        "income_month": inc_m,
        "income_year": inc_y,
        "expense_30d": exp_30d,
        "expense_month": exp_m,
        "expense_year": exp_y,
    }