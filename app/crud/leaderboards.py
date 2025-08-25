# app/crud/leaderboards.py
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, desc, asc 
from app.models.transaction import TransactionModel

def _spending_amount():
    return case(
        (TransactionModel.transaction_type == "expense", TransactionModel.amount),
        else_=0.0
    )

def _range(user_id: UUID, start: datetime, end: datetime):
    return and_(
        TransactionModel.user_id == user_id,
        TransactionModel.timestamp >= start,
        TransactionModel.timestamp < end,
    )

def top_categories_by_total_value(db: Session, user_id: UUID, start: datetime, end: datetime, limit: int):
    amt = _spending_amount()
    rows = (
        db.query(
            TransactionModel.category.label("category"),
            func.coalesce(func.sum(amt), 0.0).label("amount"),
        )
        .filter(_range(user_id, start, end))
        .filter(TransactionModel.transaction_type == "expense")  # Only expenses
        .group_by(TransactionModel.category)
        .having(func.sum(amt) > 0)  # Only include categories with spending > 0
        .order_by(desc(func.sum(amt)), asc(TransactionModel.category))
        .limit(limit)
        .all()
    )
    return [{"category": r.category, "amount": float(r.amount or 0)} for r in rows]

def top_categories_by_tx_count(db: Session, user_id: UUID, start: datetime, end: datetime, limit: int):
    rows = (
        db.query(
            TransactionModel.category.label("category"),
            func.count().label("amount"),
        )
        .filter(_range(user_id, start, end))
        .filter(TransactionModel.transaction_type == "expense")
        .group_by(TransactionModel.category)
        .order_by(desc(func.count()), asc(TransactionModel.category))
        .limit(limit)
        .all()
    )
    return [{"category": r.category, "amount": float(r.amount)} for r in rows]

def top_categories_by_avg_cost(db: Session, user_id: UUID, start: datetime, end: datetime, limit: int):
    rows = (
        db.query(
            TransactionModel.category.label("category"),
            func.coalesce(func.avg(TransactionModel.amount), 0.0).label("amount"),
        )
        .filter(_range(user_id, start, end))
        .filter(TransactionModel.transaction_type == "expense")
        .group_by(TransactionModel.category)
        .order_by(desc(func.avg(TransactionModel.amount)), asc(TransactionModel.category))
        .limit(limit)
        .all()
    )
    return [{"category": r.category, "amount": float(r.amount or 0)} for r in rows]

def top_categories_by_largest_tx(db: Session, user_id: UUID, start: datetime, end: datetime, limit: int):
    rows = (
        db.query(
            TransactionModel.category.label("category"),
            func.coalesce(func.max(TransactionModel.amount), 0.0).label("amount"),
        )
        .filter(_range(user_id, start, end))
        .filter(TransactionModel.transaction_type == "expense")
        .group_by(TransactionModel.category)
        .order_by(desc(func.max(TransactionModel.amount)), asc(TransactionModel.category))
        .limit(limit)
        .all()
    )
    return [{"category": r.category, "amount": float(r.amount or 0)} for r in rows]

def _merchant_category_map_subq(db: Session, user_id: UUID, start: datetime, end: datetime):
    cc = (
        db.query(
            TransactionModel.merchant.label("merchant"),
            TransactionModel.category.label("category"),
            func.count().label("cnt"),
        )
        .filter(_range(user_id, start, end))
        .filter(TransactionModel.transaction_type == "expense")
        .group_by(TransactionModel.merchant, TransactionModel.category)
    ).subquery()

    ranked = db.query(
        cc.c.merchant,
        cc.c.category,
        cc.c.cnt,
        func.row_number().over(
            partition_by=cc.c.merchant,
            order_by=(cc.c.cnt.desc(), cc.c.category.asc())
        ).label("rn")
    ).subquery()

    return db.query(ranked).filter(ranked.c.rn == 1).subquery()


def top_merchants_by_total_value(db: Session, user_id: UUID, start: datetime, end: datetime, limit: int):
    amt = _spending_amount()
    cat_map = _merchant_category_map_subq(db, user_id, start, end)
    rows = (
        db.query(
            TransactionModel.merchant.label("merchant"),
            func.coalesce(func.sum(amt), 0.0).label("amount"),
            cat_map.c.category.label("category"),
        )
        .filter(_range(user_id, start, end))
        .outerjoin(cat_map, cat_map.c.merchant == TransactionModel.merchant)
        .group_by(TransactionModel.merchant, cat_map.c.category)
        .order_by(desc(func.sum(amt)), asc(TransactionModel.merchant))
        .limit(limit)
        .all()
    )
    return [{"merchant": r.merchant, "category": r.category, "amount": float(r.amount or 0)} for r in rows]

def top_merchants_by_tx_count(db: Session, user_id: UUID, start: datetime, end: datetime, limit: int):
    cat_map = _merchant_category_map_subq(db, user_id, start, end)
    rows = (
        db.query(
            TransactionModel.merchant.label("merchant"),
            func.count().label("amount"),
            cat_map.c.category.label("category"),
        )
        .filter(_range(user_id, start, end))
        .filter(TransactionModel.transaction_type == "expense")
        .outerjoin(cat_map, cat_map.c.merchant == TransactionModel.merchant)
        .group_by(TransactionModel.merchant, cat_map.c.category)
        .order_by(desc(func.count()), asc(TransactionModel.merchant))
        .limit(limit)
        .all()
    )
    return [{"merchant": r.merchant, "category": r.category, "amount": float(r.amount)} for r in rows]

def top_merchants_by_avg_cost(db: Session, user_id: UUID, start: datetime, end: datetime, limit: int):
    cat_map = _merchant_category_map_subq(db, user_id, start, end)
    rows = (
        db.query(
            TransactionModel.merchant.label("merchant"),
            func.coalesce(func.avg(TransactionModel.amount), 0.0).label("amount"),
            cat_map.c.category.label("category"),
        )
        .filter(_range(user_id, start, end))
        .filter(TransactionModel.transaction_type == "expense")
        .outerjoin(cat_map, cat_map.c.merchant == TransactionModel.merchant)
        .group_by(TransactionModel.merchant, cat_map.c.category)
        .order_by(desc(func.avg(TransactionModel.amount)), asc(TransactionModel.merchant))
        .limit(limit)
        .all()
    )
    return [{"merchant": r.merchant, "category": r.category, "amount": float(r.amount or 0)} for r in rows]

def top_merchants_by_largest_tx(db: Session, user_id: UUID, start: datetime, end: datetime, limit: int):
    cat_map = _merchant_category_map_subq(db, user_id, start, end)
    rows = (
        db.query(
            TransactionModel.merchant.label("merchant"),
            func.coalesce(func.max(TransactionModel.amount), 0.0).label("amount"),
            cat_map.c.category.label("category"),
        )
        .filter(_range(user_id, start, end))
        .filter(TransactionModel.transaction_type == "expense")
        .outerjoin(cat_map, cat_map.c.merchant == TransactionModel.merchant)
        .group_by(TransactionModel.merchant, cat_map.c.category)
        .order_by(desc(func.max(TransactionModel.amount)), asc(TransactionModel.merchant))
        .limit(limit)
        .all()
    )
    return [{"merchant": r.merchant, "category": r.category, "amount": float(r.amount or 0)} for r in rows]

def _range_filter(user_id: UUID, start: datetime, end: datetime):
    return and_(
        TransactionModel.user_id == user_id,
        TransactionModel.timestamp >= start,
        TransactionModel.timestamp < end,
    )

def _sum_income_expense(db: Session, user_id: UUID, start: datetime, end: datetime):
    income_case = case(
        (TransactionModel.transaction_type == "income", TransactionModel.amount),
        else_=0.0
    )
    expense_case = case(
        (TransactionModel.transaction_type == "expense", TransactionModel.amount),
        else_=0.0
    )

    row = (
        db.query(
            func.coalesce(func.sum(income_case), 0.0).label("income"),
            func.coalesce(func.sum(expense_case), 0.0).label("expense"),
        )
        .filter(_range_filter(user_id, start, end))
        .one()
    )
    m = row._mapping
    return float(m["income"] or 0), float(m["expense"] or 0)

def totals_last_30d(db: Session, user_id: UUID, start: datetime, end: datetime):
    # start/end provided by service
    return _sum_income_expense(db, user_id, start, end)

def totals_this_month(db: Session, user_id: UUID, month_start: datetime, now: datetime):
    return _sum_income_expense(db, user_id, month_start, now)

def totals_this_year(db: Session, user_id: UUID, year_start: datetime, now: datetime):
    return _sum_income_expense(db, user_id, year_start, now)