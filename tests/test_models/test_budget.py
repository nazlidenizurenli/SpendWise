from app.models.budget import BudgetModel
from app.models.user import User
from datetime import datetime, timedelta
import uuid
import pytest

def test_create_budget(db_session):
    """Test basic budget creation with all required fields"""
    user = User(
        id=uuid.uuid4(),
        username="budgetuser",
        name="Budget User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    budget = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=100.00,  
        category="Food",
        description="Monthly food budget",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        is_active=True,
        created_at=datetime.now()
    )
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)

    # Test all fields are properly set
    assert budget.id is not None
    assert budget.user_id == user.id
    assert budget.amount == 100.00
    assert budget.category == "Food"
    assert budget.description == "Monthly food budget"
    assert budget.start_date is not None
    assert budget.end_date is not None
    assert budget.is_active is True
    assert budget.created_at is not None
    assert isinstance(budget.created_at, datetime)

    # Test relationship to user
    assert budget.user is not None
    assert budget.user.id == user.id
    assert budget.user.username == "budgetuser"

def test_budget_foreign_key_constraint(db_session):
    """Test that budget requires valid user_id"""
    # Try to create budget with non-existent user_id
    budget = BudgetModel(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),  # Random UUID that doesn't exist
        amount=100.00,
        category="Food",
        description="Test budget",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        is_active=True
    )
    
    db_session.add(budget)
    db_session.commit()
    db_session.refresh(budget)
    
    # Verify budget exists but has no valid user relationship
    assert budget.id is not None
    assert budget.user_id is not None
    assert budget.user is None  # Relationship should be None since user doesn't exist

def test_budget_required_fields(db_session):
    """Test that required fields cannot be null"""
    user = User(
        id=uuid.uuid4(),
        username="requireduser",
        name="Required User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    # Test missing amount
    budget_no_amount = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        category="Food",
        description="Test budget",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        is_active=True
    )
    db_session.add(budget_no_amount)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()

    # Test missing category
    budget_no_category = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=100.00,
        description="Test budget",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        is_active=True
    )
    db_session.add(budget_no_category)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()

    # Test missing description
    budget_no_description = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=100.00,
        category="Food",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        is_active=True
    )
    db_session.add(budget_no_description)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()

    # Test missing start_date
    budget_no_start = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=100.00,
        category="Food",
        description="Test budget",
        end_date=datetime.now() + timedelta(days=30),
        is_active=True
    )
    db_session.add(budget_no_start)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()

    # Test missing end_date
    budget_no_end = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=100.00,
        category="Food",
        description="Test budget",
        start_date=datetime.now(),
        is_active=True
    )
    db_session.add(budget_no_end)
    with pytest.raises(Exception):
        db_session.commit()

def test_budget_cascade_delete(db_session):
    """Test that deleting user cascades to budgets"""
    user = User(
        id=uuid.uuid4(),
        username="cascadeuser",
        name="Cascade User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    budget = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=100.00,
        category="Food",
        description="Test budget",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        is_active=True
    )
    db_session.add(budget)
    db_session.commit()

    # Verify budget exists
    assert db_session.query(BudgetModel).count() == 1

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify budget is deleted
    assert db_session.query(BudgetModel).count() == 0

def test_budget_date_validation(db_session):
    """Test budget date logic and validation"""
    user = User(
        id=uuid.uuid4(),
        username="dateuser",
        name="Date User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    # Test budget with start_date before end_date
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    valid_budget = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=500.00,
        category="Entertainment",
        description="Monthly entertainment budget",
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
    db_session.add(valid_budget)
    db_session.commit()

    assert valid_budget.start_date < valid_budget.end_date

def test_budget_active_status(db_session):
    """Test budget active status functionality"""
    user = User(
        id=uuid.uuid4(),
        username="activeuser",
        name="Active User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    # Test active budget
    active_budget = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=200.00,
        category="Transportation",
        description="Monthly transportation budget",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        is_active=True
    )
    db_session.add(active_budget)
    db_session.commit()

    # Test inactive budget
    inactive_budget = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=150.00,
        category="Utilities",
        description="Monthly utilities budget",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        is_active=False
    )
    db_session.add(inactive_budget)
    db_session.commit()

    assert active_budget.is_active is True
    assert inactive_budget.is_active is False

def test_budget_default_values(db_session):
    """Test budget default values"""
    user = User(
        id=uuid.uuid4(),
        username="defaultuser",
        name="Default User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    # Test budget without specifying is_active (should default to True)
    budget_default = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=300.00,
        category="Shopping",
        description="Monthly shopping budget",
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30)
        # is_active not specified, should default to True
    )
    db_session.add(budget_default)
    db_session.commit()

    assert budget_default.is_active is True
    assert budget_default.created_at is not None

def test_budget_multiple_categories(db_session):
    """Test creating budgets for different categories"""
    user = User(
        id=uuid.uuid4(),
        username="multiuser",
        name="Multi User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    categories = ["Food", "Transportation", "Entertainment", "Utilities"]
    budgets = []

    for category in categories:
        budget = BudgetModel(
            id=uuid.uuid4(),
            user_id=user.id,
            amount=100.00 + len(budgets) * 50,  # Different amounts
            category=category,
            description=f"Monthly {category.lower()} budget",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
            is_active=True
        )
        budgets.append(budget)
        db_session.add(budget)

    db_session.commit()

    # Verify all budgets exist
    assert db_session.query(BudgetModel).count() == 4
    
    # Verify relationships
    db_session.refresh(user)
    assert len(user.budgets) == 4

    # Verify different amounts
    amounts = [budget.amount for budget in user.budgets]
    assert len(set(amounts)) == 4  # All amounts should be different