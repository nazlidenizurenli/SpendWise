# app/routes/insights.py
from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.db import get_db
from app.core.security import get_current_user_id
from app.services.insights import run_on_track

router = APIRouter(prefix="/insights", tags=["insights"])

class LLMResponse(BaseModel):
    text: str

@router.get("/on-track", response_model=LLMResponse, summary="Answer 'Am I on track?' using tools (and optional LLM).")
def on_track_endpoint(
    days: int = Query(60, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    return run_on_track(db, user_id, days=days, provider='openai')

@router.get("/budget-suggestion", response_model=LLMResponse, summary="Get budget optimization suggestions and new budget recommendations.")
def budget_suggestion_endpoint():
    # TODO: Implement budget suggestion endpoint
    pass

@router.get("/build-user-profile", response_model=LLMResponse, summary="Build comprehensive user financial profile.")
def build_user_profile_endpoint():
    # TODO: Implement build user profile endpoint
    pass
