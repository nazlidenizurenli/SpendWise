# tests/test_models/test_user.py
import pytest
from app.models.user import User
import uuid
from datetime import datetime

def test_create_user(db_session):
    """Test basic user creation with all required fields"""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        name="Test User",
        hashed_password="password_fake_hash"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Test all fields are properly set
    assert user.id is not None
    assert user.username == "testuser"
    assert user.name == "Test User"
    assert user.hashed_password == "password_fake_hash"
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)

    # Test relationships are properly initialized
    assert isinstance(user.transactions, list)
    assert user.transactions == []
    assert isinstance(user.budgets, list)
    assert user.budgets == []
    assert isinstance(user.insights, list)
    assert user.insights == []

def test_user_unique_username_constraint(db_session):
    """Test that username uniqueness constraint works"""
    # Create first user
    user1 = User(
        id=uuid.uuid4(),
        username="uniqueuser",
        name="User One",
        hashed_password="hash1"
    )
    db_session.add(user1)
    db_session.commit()

    # Try to create second user with same username
    user2 = User(
        id=uuid.uuid4(),
        username="uniqueuser",  # Same username
        name="User Two",
        hashed_password="hash2"
    )
    db_session.add(user2)
    
    # Should raise integrity error
    with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
        db_session.commit()

def test_user_relationships_with_related_objects(db_session):
    """Test user relationships when related objects exist"""
    from app.models.transaction import TransactionModel
    from app.models.budget import BudgetModel
    from app.models.insight import InsightModel
    
    # Create user
    user = User(
        id=uuid.uuid4(),
        username="reluser",
        name="Relationship User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    # Create related objects
    transaction = TransactionModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=100.0,
        description="Test Transaction",
        category="Food",
        transaction_type="expense",
        source="debit",
        timestamp=datetime.now()
    )
    
    budget = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=500.0,
        category="Food",
        description="Monthly food budget",
        start_date=datetime.now(),
        end_date=datetime.now(),
        is_active=True
    )
    
    insight = InsightModel(
        id=uuid.uuid4(),
        user_id=user.id,
        insight="You spend too much on food"
    )
    
    db_session.add_all([transaction, budget, insight])
    db_session.commit()
    db_session.refresh(user)

    # Test relationships contain the objects
    assert len(user.transactions) == 1
    assert user.transactions[0].id == transaction.id
    assert len(user.budgets) == 1
    assert user.budgets[0].id == budget.id
    assert len(user.insights) == 1
    assert user.insights[0].id == insight.id

def test_user_cascade_delete(db_session):
    """Test that deleting user cascades to related objects"""
    from app.models.transaction import TransactionModel
    from app.models.budget import BudgetModel
    from app.models.insight import InsightModel
    
    # Create user with related objects
    user = User(
        id=uuid.uuid4(),
        username="cascadeuser",
        name="Cascade User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    transaction = TransactionModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=100.0,
        description="Test Transaction",
        category="Food",
        transaction_type="expense",
        source="debit",
        timestamp=datetime.now()
    )
    
    budget = BudgetModel(
        id=uuid.uuid4(),
        user_id=user.id,
        amount=500.0,
        category="Food",
        description="Monthly food budget",
        start_date=datetime.now(),
        end_date=datetime.now(),
        is_active=True
    )
    
    insight = InsightModel(
        id=uuid.uuid4(),
        user_id=user.id,
        insight="Test insight"
    )
    
    db_session.add_all([transaction, budget, insight])
    db_session.commit()

    # Verify objects exist
    assert db_session.query(TransactionModel).count() == 1
    assert db_session.query(BudgetModel).count() == 1
    assert db_session.query(InsightModel).count() == 1

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify related objects are deleted
    assert db_session.query(TransactionModel).count() == 0
    assert db_session.query(BudgetModel).count() == 0
    assert db_session.query(InsightModel).count() == 0

def test_user_required_fields(db_session):
    """Test that required fields cannot be null"""
    # Test missing username
    user_no_username = User(
        id=uuid.uuid4(),
        name="Test User",
        hashed_password="hash"
    )
    db_session.add(user_no_username)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()

    # Test missing name
    user_no_name = User(
        id=uuid.uuid4(),
        username="testuser",
        hashed_password="hash"
    )
    db_session.add(user_no_name)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()

    # Test missing password
    user_no_password = User(
        id=uuid.uuid4(),
        username="testuser",
        name="Test User"
    )
    db_session.add(user_no_password)
    with pytest.raises(Exception):
        db_session.commit()
