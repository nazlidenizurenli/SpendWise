import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.user import User
from app.models.transaction import TransactionModel
from app.core.security import create_access_token, get_current_user
from tests.utils.mocks import get_mock_db

client = TestClient(app)


class TestBudgetRoutes:
    def test_get_user_categories_no_transactions(self):
        """Test getting categories when user has no transactions"""
        # Create mock user
        mock_user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        
        # Mock the database and service
        mock_db = get_mock_db()
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.budget.get_db", side_effect=mock_get_db), \
                 patch("app.services.budget.BudgetService.get_user_categories", return_value=[]):
                
                response = client.get("/budgets/categories")
                
                assert response.status_code == 404
                assert "No transactions found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_user_categories_with_transactions(self):
        """Test getting categories when user has transactions"""
        # Create mock user
        mock_user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        
        # Mock categories
        from app.schemas.budget import UserCategory
        mock_categories = [
            UserCategory(category="Food", transaction_count=1, total_amount=50.0, average_amount=50.0),
            UserCategory(category="Transport", transaction_count=1, total_amount=30.0, average_amount=30.0)
        ]
        
        # Mock the database and service
        mock_db = get_mock_db()
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.budget.get_db", side_effect=mock_get_db), \
                 patch("app.services.budget.BudgetService.get_user_categories", return_value=mock_categories):
                
                response = client.get("/budgets/categories")
                
                assert response.status_code == 200
                categories = response.json()
                assert len(categories) == 2
                
                # Check categories
                categories_dict = {cat["category"]: cat for cat in categories}
                assert "Food" in categories_dict
                assert "Transport" in categories_dict
                assert categories_dict["Food"]["transaction_count"] == 1
                assert categories_dict["Food"]["total_amount"] == 50.0
        finally:
            app.dependency_overrides.clear()

    def test_create_budget_no_transactions(self):
        """Test creating budget when user has no transactions"""
        # Create mock user
        mock_user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        
        budget_data = {
            "limit": 1000.0,
            "category": "Food",
            "description": "Monthly food budget",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "is_active": True
        }
        
        # Mock the database and service
        mock_db = get_mock_db()
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.budget.get_db", side_effect=mock_get_db), \
                 patch("app.services.budget.BudgetService.can_user_create_budget", return_value=False):
                
                response = client.post("/budgets/", json=budget_data)
                
                assert response.status_code == 400
                assert "No transactions found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_create_budget_with_transactions(self):
        """Test creating budget when user has transactions"""
        # Create mock user
        mock_user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        
        budget_data = {
            "limit": 1000.0,
            "category": "Food",
            "description": "Monthly food budget",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "is_active": True
        }
        
        # Mock budget response
        from app.schemas.budget import BudgetResponse
        mock_budget = BudgetResponse(
            id=uuid4(),
            user_id=mock_user.id,
            limit=1000.0,
            category="Food",
            description="Monthly food budget",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            is_active=True,
            created_at=datetime.now()
        )
        
        # Mock the database and service
        mock_db = get_mock_db()
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.budget.get_db", side_effect=mock_get_db), \
                 patch("app.services.budget.BudgetService.can_user_create_budget", return_value=True), \
                 patch("app.services.budget.BudgetService.create_budget_for_user", return_value=mock_budget):
                
                response = client.post("/budgets/", json=budget_data)
                
                assert response.status_code == 200
                budget = response.json()
                assert budget["limit"] == 1000.0
                assert budget["category"] == "Food"
                assert budget["user_id"] == str(mock_user.id)
        finally:
            app.dependency_overrides.clear()

    def test_get_budget_overview_no_transactions(self):
        """Test getting budget overview when user has no transactions"""
        # Create mock user
        mock_user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        
        # Mock the database and service
        mock_db = get_mock_db()
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.budget.get_db", side_effect=mock_get_db), \
                 patch("app.services.budget.BudgetService.can_user_create_budget", return_value=False):
                
                response = client.get("/budgets/overview")
                
                assert response.status_code == 400
                assert "No transactions found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


