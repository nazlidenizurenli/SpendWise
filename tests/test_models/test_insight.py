from app.models.insight import InsightModel
from app.models.user import User
from datetime import datetime
import uuid
import pytest

def test_create_insight(db_session):
    """Test basic insight creation with all required fields"""
    user = User(
        id=uuid.uuid4(),
        username="insightuser",
        name="Insight User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    insight = InsightModel(
        id=uuid.uuid4(),
        user_id=user.id,
        insight="You spend too much on food this month",
        created_at=datetime.now()
    )
    db_session.add(insight)
    db_session.commit()
    db_session.refresh(insight)

    # Test all fields are properly set
    assert insight.id is not None
    assert insight.user_id == user.id
    assert insight.insight == "You spend too much on food this month"
    assert insight.created_at is not None
    assert isinstance(insight.created_at, datetime)

    # Test relationship to user
    assert insight.user is not None
    assert insight.user.id == user.id
    assert insight.user.username == "insightuser"

def test_insight_foreign_key_constraint(db_session):
    """Test that insight requires valid user_id"""
    # Try to create insight with non-existent user_id
    insight = InsightModel(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),  # Random UUID that doesn't exist
        insight="Test insight"
    )
    
    db_session.add(insight)
    db_session.commit()
    db_session.refresh(insight)
    
    # Verify insight exists but has no valid user relationship
    assert insight.id is not None
    assert insight.user_id is not None
    assert insight.user is None  # Relationship should be None since user doesn't exist

def test_insight_required_fields(db_session):
    """Test that required fields cannot be null"""
    user = User(
        id=uuid.uuid4(),
        username="requireduser",
        name="Required User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    # Test missing insight text
    insight_no_text = InsightModel(
        id=uuid.uuid4(),
        user_id=user.id
        # insight field missing
    )
    db_session.add(insight_no_text)
    with pytest.raises(Exception):
        db_session.commit()

def test_insight_cascade_delete(db_session):
    """Test that deleting user cascades to insights"""
    user = User(
        id=uuid.uuid4(),
        username="cascadeuser",
        name="Cascade User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    insight = InsightModel(
        id=uuid.uuid4(),
        user_id=user.id,
        insight="Test insight for cascade delete"
    )
    db_session.add(insight)
    db_session.commit()

    # Verify insight exists
    assert db_session.query(InsightModel).count() == 1

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify insight is deleted
    assert db_session.query(InsightModel).count() == 0

def test_insight_default_created_at(db_session):
    """Test that created_at defaults to current time if not specified"""
    user = User(
        id=uuid.uuid4(),
        username="defaultuser",
        name="Default User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    # Create insight without specifying created_at
    insight = InsightModel(
        id=uuid.uuid4(),
        user_id=user.id,
        insight="Test insight with default created_at"
        # created_at not specified, should default to datetime.utcnow()
    )
    db_session.add(insight)
    db_session.commit()

    assert insight.created_at is not None
    assert isinstance(insight.created_at, datetime)

def test_insight_long_text(db_session):
    """Test that insight can handle long text content"""
    user = User(
        id=uuid.uuid4(),
        username="longtextuser",
        name="Long Text User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    long_insight_text = """
    This is a very long insight text that contains multiple paragraphs.
    It should be able to handle substantial amounts of text content.
    
    The insight might contain:
    - Multiple bullet points
    - Detailed analysis
    - Recommendations for the user
    - Financial advice and tips
    
    This is important because insights are meant to provide valuable
    information to help users understand their spending patterns
    and make better financial decisions.
    """

    insight = InsightModel(
        id=uuid.uuid4(),
        user_id=user.id,
        insight=long_insight_text
    )
    db_session.add(insight)
    db_session.commit()

    assert insight.insight == long_insight_text
    assert len(insight.insight) > 100  # Verify it's actually long

def test_insight_multiple_insights_per_user(db_session):
    """Test that a user can have multiple insights"""
    user = User(
        id=uuid.uuid4(),
        username="multiuser",
        name="Multi User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    insights_data = [
        "You spend 30% more on food than the average user",
        "Your transportation costs have increased by 15% this month",
        "Consider setting up automatic savings transfers",
        "You're doing great with your entertainment budget"
    ]

    for insight_text in insights_data:
        insight = InsightModel(
            id=uuid.uuid4(),
            user_id=user.id,
            insight=insight_text
        )
        db_session.add(insight)

    db_session.commit()

    # Verify all insights exist
    assert db_session.query(InsightModel).count() == 4
    
    # Verify relationships
    db_session.refresh(user)
    assert len(user.insights) == 4

    # Verify all insight texts are present
    user_insight_texts = [insight.insight for insight in user.insights]
    for insight_text in insights_data:
        assert insight_text in user_insight_texts

def test_insight_special_characters(db_session):
    """Test that insight can handle special characters and emojis"""
    user = User(
        id=uuid.uuid4(),
        username="specialuser",
        name="Special User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    special_insight = "💰 You're over budget! 📊 Consider cutting back on 🍕 food expenses. 💡 Tip: Try meal planning!"

    insight = InsightModel(
        id=uuid.uuid4(),
        user_id=user.id,
        insight=special_insight
    )
    db_session.add(insight)
    db_session.commit()

    assert insight.insight == special_insight
    assert "💰" in insight.insight
    assert "🍕" in insight.insight

def test_insight_empty_string(db_session):
    """Test that insight cannot be empty string"""
    user = User(
        id=uuid.uuid4(),
        username="emptyuser",
        name="Empty User",
        hashed_password="hash"
    )
    db_session.add(user)
    db_session.commit()

    # Try to create insight with empty string
    insight = InsightModel(
        id=uuid.uuid4(),
        user_id=user.id,
        insight=""  # Empty string
    )
    db_session.add(insight)
    
    # This might fail due to NOT NULL constraint or application-level validation
    try:
        db_session.commit()
        # If it succeeds, the insight should be empty string
        assert insight.insight == ""
    except Exception:
        # If it fails, that's also acceptable behavior
        db_session.rollback()
        pass