# app/routers/leaderboards.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.db import get_db
from app.schemas.leaderboards import CategoryLeaderboardItem, MerchantLeaderboardItem, OverallStatsOut
from app.core.security import get_current_user_id
from app.services import leaderboards as svc

router = APIRouter(prefix="/analytics/leaderboards", tags=["analytics"])

# -------------------------
# Category leaderboards
# -------------------------

@router.get(
    "/categories/total-value",
    response_model=list[CategoryLeaderboardItem],
    summary="Top categories by total value (expenses only)"
)
def categories_total_value(
    days: int = Query(60, ge=1, le=365, description="Lookback window in days"),
    limit: int = Query(3, ge=1, le=10, description="Number of rows to return"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return svc.svc_categories_total_value(db, user_id, days, limit)


@router.get(
    "/categories/tx-count",
    response_model=list[CategoryLeaderboardItem],
    summary="Top categories by transaction count"
)
def categories_tx_count(
    days: int = Query(60, ge=1, le=365),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return svc.svc_categories_tx_count(db, user_id, days, limit)


@router.get(
    "/categories/avg-cost",
    response_model=list[CategoryLeaderboardItem],
    summary="Top categories by average transaction cost"
)
def categories_avg_cost(
    days: int = Query(60, ge=1, le=365),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return svc.svc_categories_avg_cost(db, user_id, days, limit)


@router.get(
    "/categories/largest-tx",
    response_model=list[CategoryLeaderboardItem],
    summary="Top categories by largest single transaction"
)
def categories_largest_tx(
    days: int = Query(60, ge=1, le=365),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return svc.svc_categories_largest_tx(db, user_id, days, limit)


# -------------------------
# Merchant leaderboards
# -------------------------

@router.get(
    "/merchants/total-value",
    response_model=list[MerchantLeaderboardItem],
    summary="Top merchants by total value (expenses only)"
)
def merchants_total_value(
    days: int = Query(60, ge=1, le=365),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return svc.svc_merchants_total_value(db, user_id, days, limit)


@router.get(
    "/merchants/tx-count",
    response_model=list[MerchantLeaderboardItem],
    summary="Top merchants by transaction count"
)
def merchants_tx_count(
    days: int = Query(60, ge=1, le=365),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return svc.svc_merchants_tx_count(db, user_id, days, limit)


@router.get(
    "/merchants/avg-cost",
    response_model=list[MerchantLeaderboardItem],
    summary="Top merchants by average transaction cost"
)
def merchants_avg_cost(
    days: int = Query(60, ge=1, le=365),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return svc.svc_merchants_avg_cost(db, user_id, days, limit)


@router.get(
    "/merchants/largest-tx",
    response_model=list[MerchantLeaderboardItem],
    summary="Top merchants by largest single transaction"
)
def merchants_largest_tx(
    days: int = Query(60, ge=1, le=365),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return svc.svc_merchants_largest_tx(db, user_id, days, limit)

@router.get("/financial-overview", response_model=OverallStatsOut, summary="Overall income/expense totals")
def get_overall_stats(
    days: int = Query(60, ge=1, le=365, description="Rolling window for the 60d metrics"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return svc.overall_stats(db, user_id, days)