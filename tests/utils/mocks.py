from unittest.mock import MagicMock
from app.models.user import User
import uuid
from datetime import datetime

def get_mock_db(user_exists: bool = False):
    mock_db = MagicMock()
    
    # Create a mock query object
    mock_query = MagicMock()
    mock_filter = MagicMock()
    
    # Set up the query chaining: db.query(User).filter(...).first()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    
    # Mock User query result
    if user_exists:
        mock_filter.first.return_value = User(
            username="mockuser",
            name="Mock User",
            hashed_password="mocked_hashed"
        )
    else:
        mock_filter.first.return_value = None

    # Mock database operations
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    
    # Mock refresh to simulate setting fields on the user object
    def mock_refresh(user_obj):
        if not hasattr(user_obj, 'id') or user_obj.id is None:
            user_obj.id = uuid.uuid4()
        if not hasattr(user_obj, 'created_at') or user_obj.created_at is None:
            user_obj.created_at = datetime.utcnow()
    
    mock_db.refresh.side_effect = mock_refresh

    return mock_db
