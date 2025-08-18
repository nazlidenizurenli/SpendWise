import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from app.crud.budget import (
    get_user_categories,
    get_budgets_by_user,
    get_active_budgets_by_user,
    get_budget_by_id,
    create_budget,
    update_budget,
    delete_budget,
    get_user_spending_in_period,
    check_user_has_transactions
)
from app.models.budget import BudgetModel
from app.models.user import User
from app.models.transaction import TransactionModel
from app.schemas.budget import BudgetCreate, BudgetUpdate


class TestBudgetCRUD:
    def test_get_user_categories(self, db_session):
        """Test getting user categories from transactions"""
        # Create user
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create transactions with different categories
        transactions = [
            TransactionModel(
                id=uuid4(),
                user_id=user.id,
                amount=50.0,  # Positive amount for expense (non-negative system)
                description="Grocery shopping",
                merchant="Grocery Store",
                category="Food",
                transaction_type="expense",
                source="debit",
                timestamp=datetime.now()
            ),
            TransactionModel(
                id=uuid4(),
                user_id=user.id,
                amount=30.0,  # Positive amount for expense (non-negative system)
                description="Gas station",
                merchant="Gas Station",
                category="Transport",
                transaction_type="expense",
                source="debit",
                timestamp=datetime.now()
            ),
            TransactionModel(
                id=uuid4(),
                user_id=user.id,
                amount=25.0,  # Positive amount for expense (non-negative system)
                description="More groceries",
                merchant="Grocery Store",
                category="Food",
                transaction_type="expense",
                source="debit",
                timestamp=datetime.now()
            )
        ]
        
        for transaction in transactions:
            db_session.add(transaction)
        db_session.commit()
        
        # Get categories
        categories = get_user_categories(db_session, user.id)
        
        assert len(categories) == 2  # Food and Transport
        food_category = next(cat for cat in categories if cat.category == "Food")
        transport_category = next(cat for cat in categories if cat.category == "Transport")
        
        assert food_category.transaction_count == 2
        assert food_category.total_amount == 75.0  # 50.0 + 25.0
        assert food_category.average_amount == 37.5
        
        assert transport_category.transaction_count == 1
        assert transport_category.total_amount == 30.0
        assert transport_category.average_amount == 30.0

    def test_create_and_get_budget(self, db_session):
        """Test creating and retrieving a budget"""
        # Create user
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create budget
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        budget_data = BudgetCreate(
            limit=1000.0,
            category="Food",
            description="Monthly food budget",
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        budget = create_budget(db_session, budget_data, user.id)
        
        assert budget.user_id == user.id
        assert budget.limit == 1000.0
        assert budget.category == "Food"
        
        # Get budget by ID
        retrieved_budget = get_budget_by_id(db_session, budget.id)
        assert retrieved_budget is not None
        assert retrieved_budget.id == budget.id

    def test_get_budgets_by_user(self, db_session):
        """Test getting all budgets for a user"""
        # Create user
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create multiple budgets
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        budget1_data = BudgetCreate(
            limit=1000.0,
            category="Food",
            description="Food budget",
            start_date=start_date,
            end_date=end_date
        )
        
        budget2_data = BudgetCreate(
            limit=500.0,
            category="Transport",
            description="Transport budget",
            start_date=start_date,
            end_date=end_date
        )
        
        create_budget(db_session, budget1_data, user.id)
        create_budget(db_session, budget2_data, user.id)
        
        # Get all budgets
        budgets = get_budgets_by_user(db_session, user.id)
        assert len(budgets) == 2
        
        # Get active budgets
        active_budgets = get_active_budgets_by_user(db_session, user.id)
        assert len(active_budgets) == 2

    def test_update_budget(self, db_session):
        """Test updating a budget"""
        # Create user and budget
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        budget_data = BudgetCreate(
            limit=1000.0,
            category="Food",
            description="Food budget",
            start_date=start_date,
            end_date=end_date
        )
        
        budget = create_budget(db_session, budget_data, user.id)
        
        # Update budget
        update_data = BudgetUpdate(limit=1200.0, description="Updated food budget")
        updated_budget = update_budget(db_session, budget.id, update_data)
        
        assert updated_budget is not None
        assert updated_budget.limit == 1200.0
        assert updated_budget.description == "Updated food budget"
        assert updated_budget.category == "Food"  # Should remain unchanged

    def test_delete_budget(self, db_session):
        """Test deleting a budget"""
        # Create user and budget
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        budget_data = BudgetCreate(
            limit=1000.0,
            category="Food",
            description="Food budget",
            start_date=start_date,
            end_date=end_date
        )
        
        budget = create_budget(db_session, budget_data, user.id)
        
        # Delete budget
        success = delete_budget(db_session, budget.id)
        assert success is True
        
        # Verify budget is deleted
        retrieved_budget = get_budget_by_id(db_session, budget.id)
        assert retrieved_budget is None

    def test_get_user_spending_in_period(self, db_session):
        """Test getting user spending in a specific period"""
        # Create user
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create transactions in different time periods
        now = datetime.now()
        past_date = now - timedelta(days=60)
        future_date = now + timedelta(days=30)
        
        transactions = [
            TransactionModel(
                id=uuid4(),
                user_id=user.id,
                amount=50.0,  # Positive amount for expense (non-negative system)
                description="Old transaction",
                merchant="Grocery Store",
                category="Food",
                transaction_type="expense",
                source="debit",
                timestamp=past_date
            ),
            TransactionModel(
                id=uuid4(),
                user_id=user.id,
                amount=30.0,  # Positive amount for expense (non-negative system)
                description="Current transaction",
                merchant="Grocery Store",
                category="Food",
                transaction_type="expense",
                source="debit",
                timestamp=now
            ),
            TransactionModel(
                id=uuid4(),
                user_id=user.id,
                amount=25.0,  # Positive amount for expense (non-negative system)
                description="Future transaction",
                merchant="Grocery Store",
                category="Food",
                transaction_type="expense",
                source="debit",
                timestamp=future_date
            )
        ]
        
        for transaction in transactions:
            db_session.add(transaction)
        db_session.commit()
        
        # Test spending in current period
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)
        spending = get_user_spending_in_period(db_session, user.id, "Food", start_date, end_date)
        
        assert spending == 30.0  # Only the current transaction

    def test_check_user_has_transactions(self, db_session):
        """Test checking if user has transactions"""
        # Create user without transactions
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Check before adding transactions
        has_transactions = check_user_has_transactions(db_session, user.id)
        assert has_transactions is False
        
        # Add a transaction
        transaction = TransactionModel(
            id=uuid4(),
            user_id=user.id,
            amount=50.0,
            description="Test transaction",
            merchant="Test Merchant",
            category="Food",
            transaction_type="debit",
            source="Food",
            timestamp=datetime.now()
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Check after adding transaction
        has_transactions = check_user_has_transactions(db_session, user.id)
        assert has_transactions is True

    def test_sign_aware_spending_calculations(self, db_session):
        """Test that spending calculations correctly handle credit vs debit sign conventions"""
        from app.crud.budget import get_user_categories, get_user_spending_in_period
        from app.models.transaction import TransactionModel
        from datetime import datetime, timedelta
        
        # Create user
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create test transactions with different sources and types (non-negative system)
        transactions = [
            # Credit card expenses (positive amounts) - should count as spending
            TransactionModel(
                user_id=user.id,
                amount=50.0,  # Positive = spending
                description="Credit card purchase",
                merchant="Restaurant",
                category="Food",
                transaction_type="expense",
                source="credit",
                timestamp=datetime.now()
            ),
            # Credit card income (positive amounts) - should NOT count as spending
            TransactionModel(
                user_id=user.id,
                amount=100.0,  # Positive = income (non-negative system)
                description="Credit card refund",
                merchant="Restaurant",
                category="Food",
                transaction_type="income",
                source="credit",
                timestamp=datetime.now()
            ),
            # Debit card expenses (positive amounts) - should count as spending
            TransactionModel(
                user_id=user.id,
                amount=30.0,  # Positive = spending (non-negative system)
                description="Debit card purchase",
                merchant="Grocery Store",
                category="Food",
                transaction_type="expense",
                source="debit",
                timestamp=datetime.now()
            ),
            # Debit card income (positive amounts) - should NOT count as spending
            TransactionModel(
                user_id=user.id,
                amount=200.0,  # Positive = income
                description="Salary deposit",
                merchant="Employer",
                category="Income",
                transaction_type="income",
                source="debit",
                timestamp=datetime.now()
            ),
            # Savings account expense (positive amounts) - should count as spending
            TransactionModel(
                user_id=user.id,
                amount=25.0,  # Positive = spending (non-negative system)
                description="Savings withdrawal",
                merchant="Movie Theater",
                category="Entertainment",
                transaction_type="expense",
                source="savings",
                timestamp=datetime.now()
            )
        ]
        
        for transaction in transactions:
            db_session.add(transaction)
        db_session.commit()
        
        # Test get_user_categories
        categories = get_user_categories(db_session, user.id)
        
        # Should have 3 categories: Food, Entertainment, and Income (Income will have 0.0 spending)
        assert len(categories) == 3
        
        # Find Food category
        food_category = next((cat for cat in categories if cat.category == "Food"), None)
        assert food_category is not None
        # Food spending: 50.0 (credit expense) + 30.0 (debit expense) = 80.0
        # Credit income (100.0) should NOT be counted as spending
        assert food_category.total_amount == 80.0
        assert food_category.transaction_count == 3  # All 3 food transactions
        assert food_category.average_amount == 80.0 / 3  # Average of spending amounts only
        
        # Find Entertainment category
        entertainment_category = next((cat for cat in categories if cat.category == "Entertainment"), None)
        assert entertainment_category is not None
        # Entertainment spending: 25.0 (savings expense)
        assert entertainment_category.total_amount == 25.0
        assert entertainment_category.transaction_count == 1
        assert entertainment_category.average_amount == 25.0
        
        # Find Income category (should have 0.0 spending)
        income_category = next((cat for cat in categories if cat.category == "Income"), None)
        assert income_category is not None
        # Income category should have 0.0 spending (income transactions don't count as spending)
        assert income_category.total_amount == 0.0
        assert income_category.transaction_count == 1
        assert income_category.average_amount == 0.0
        
        # Test get_user_spending_in_period
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now() + timedelta(days=1)
        
        # Food spending in period
        food_spending = get_user_spending_in_period(
            db_session, user.id, "Food", start_date, end_date
        )
        assert food_spending == 80.0  # Only expenses, not income
        
        # Entertainment spending in period
        entertainment_spending = get_user_spending_in_period(
            db_session, user.id, "Entertainment", start_date, end_date
        )
        assert entertainment_spending == 25.0
        
        # Income category should return 0 (no spending)
        income_spending = get_user_spending_in_period(
            db_session, user.id, "Income", start_date, end_date
        )
        assert income_spending == 0.0

    def test_suggested_budgets_with_zero_spending(self, db_session):
        """Test that suggested budgets handle categories with zero spending correctly"""
        from app.services.budget import BudgetService
        from app.models.transaction import TransactionModel
        from datetime import datetime
        
        # Create user
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create transactions: one with spending, one with only income
        transactions = [
            # Category with spending
            TransactionModel(
                user_id=user.id,
                amount=50.0,  # Debit expense (non-negative system)
                description="Food purchase",
                merchant="Grocery Store",
                category="Food",
                transaction_type="expense",
                source="debit",
                timestamp=datetime.now()
            ),
            # Category with only income (should be excluded from suggestions)
            TransactionModel(
                user_id=user.id,
                amount=200.0,  # Debit income
                description="Salary",
                merchant="Employer",
                category="Income",
                transaction_type="income",
                source="debit",
                timestamp=datetime.now()
            )
        ]
        
        for transaction in transactions:
            db_session.add(transaction)
        db_session.commit()
        
        # Test suggested budgets
        budget_service = BudgetService(db_session)
        suggestions = budget_service.get_suggested_budgets(user.id)
        
        # Should only suggest budget for Food category (not Income)
        assert len(suggestions) == 1
        assert suggestions[0].category == "Food"
        assert suggestions[0].limit >= 10.0  # Should have minimum budget amount

    def test_budget_status_management(self, db_session):
        """Test budget status management based on date ranges"""
        from app.services.budget import BudgetService
        from app.models.transaction import TransactionModel
        from datetime import datetime, timedelta
        
        # Create user
        user = User(
            id=uuid4(),
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create a transaction
        transaction = TransactionModel(
            user_id=user.id,
            amount=-50.0,
            description="Test transaction",
            merchant="Test Merchant",
            category="Food",
            transaction_type="expense",
            source="debit",
            timestamp=datetime.now()
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Create budget service
        budget_service = BudgetService(db_session)
        
        # Create budgets with different date ranges
        now = datetime.now()
        past_start = now - timedelta(days=30)
        past_end = now - timedelta(days=1)
        future_start = now + timedelta(days=1)
        future_end = now + timedelta(days=30)
        current_start = now - timedelta(days=15)
        current_end = now + timedelta(days=15)
        
        # Create past budget (should be inactive)
        past_budget = BudgetModel(
            user_id=user.id,
            limit=100.0,
            category="Food",
            description="Past budget",
            start_date=past_start,
            end_date=past_end,
            is_active=True  # Will be updated to False
        )
        db_session.add(past_budget)
        
        # Create future budget (should be inactive)
        future_budget = BudgetModel(
            user_id=user.id,
            limit=100.0,
            category="Transportation",
            description="Future budget",
            start_date=future_start,
            end_date=future_end,
            is_active=True  # Will be updated to False
        )
        db_session.add(future_budget)
        
        # Create current budget (should be active)
        current_budget = BudgetModel(
            user_id=user.id,
            limit=100.0,
            category="Entertainment",
            description="Current budget",
            start_date=current_start,
            end_date=current_end,
            is_active=False  # Will be updated to True
        )
        db_session.add(current_budget)
        
        db_session.commit()
        
        # Test individual budget status update
        updated = budget_service.update_budget_status(past_budget.id)
        assert updated is True
        assert past_budget.is_active is False
        
        updated = budget_service.update_budget_status(future_budget.id)
        assert updated is True
        assert future_budget.is_active is False
        
        updated = budget_service.update_budget_status(current_budget.id)
        assert updated is True
        assert current_budget.is_active is True
        
        # Test bulk status update
        # Reset statuses for testing
        past_budget.is_active = True
        future_budget.is_active = True
        current_budget.is_active = False
        db_session.commit()
        
        updated_count = budget_service.update_all_budget_statuses()
        assert updated_count == 3
        
        # Verify final statuses
        db_session.refresh(past_budget)
        db_session.refresh(future_budget)
        db_session.refresh(current_budget)
        
        assert past_budget.is_active is False
        assert future_budget.is_active is False
        assert current_budget.is_active is True
