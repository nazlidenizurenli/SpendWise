import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from app.models.budget import BudgetModel
from app.models.user import User


class TestBudgetModel:
    def test_budget_creation(self, db_session):
        """Test creating a budget"""
        # Create a user first
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a budget
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        budget = BudgetModel(
            id=uuid4(),
            user_id=user.id,
            limit=1000.0,
            category="Food",
            description="Monthly food budget",
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        db_session.add(budget)
        db_session.commit()
        db_session.refresh(budget)
        
        assert budget.user_id == user.id
        assert budget.limit == 1000.0
        assert budget.category == "Food"
        assert budget.description == "Monthly food budget"
        assert budget.is_active is True
        assert budget.created_at is not None

    def test_budget_relationships(self, db_session):
        """Test budget relationships with user"""
        # Create a user
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create multiple budgets for the user
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        budget1 = BudgetModel(
            id=uuid4(),
            user_id=user.id,
            limit=1000.0,
            category="Food",
            description="Food budget",
            start_date=start_date,
            end_date=end_date
        )
        
        budget2 = BudgetModel(
            id=uuid4(),
            user_id=user.id,
            limit=500.0,
            category="Transport",
            description="Transport budget",
            start_date=start_date,
            end_date=end_date
        )
        
        db_session.add_all([budget1, budget2])
        db_session.commit()
        
        # Test relationship
        assert len(user.budgets) == 2
        assert budget1.user == user
        assert budget2.user == user