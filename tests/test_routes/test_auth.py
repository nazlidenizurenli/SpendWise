from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.models.user import User
from tests.utils.mocks import get_mock_db
from app.main import app
from app.core.security import hash_password, create_access_token
import uuid
from datetime import datetime
import pytest


client = TestClient(app)

def test_register_success():
    mock_db = get_mock_db(user_exists=False)
    
    # Mock the user that will be created
    mock_created_user = User(
        username="mockuser",
        name="Mock User",
        hashed_password="hashed_password123"
    )
    mock_created_user.id = uuid.uuid4()
    mock_created_user.created_at = datetime.now()
    
    def mock_get_db():
        yield mock_db
    
    # Mock the CRUD functions directly
    with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
         patch("app.routes.auth.crud_user.get_user_by_username", return_value=None), \
         patch("app.routes.auth.crud_user.create_user", return_value=mock_created_user):
        
        response = client.post("/auth/register", json={
            "username": "mockuser",
            "password": "Password123!",
            "name": "Mock User"
        })

        assert response.status_code == 201
        # The actual response should be a UserOut object, not a message
        response_data = response.json()
        assert "username" in response_data
        assert response_data["username"] == "mockuser"
        assert "name" in response_data
        assert response_data["name"] == "Mock User"

def test_invalid_operation_register_existing_user():
    mock_db = get_mock_db(user_exists=True)
    
    # Mock an existing user
    existing_user = User(
        username="mockuser",
        name="Mock User",
        hashed_password="existing_hash"
    )
    existing_user.id = uuid.uuid4()
    existing_user.created_at = datetime.now()
    
    def mock_get_db():
        yield mock_db
    
    # Mock the CRUD functions directly
    with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
         patch("app.routes.auth.crud_user.get_user_by_username", return_value=existing_user):
        
        response = client.post("/auth/register", json={
            "username": "mockuser",
            "password": "Password123!",
            "name": "Mock User"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Username already exists"


class TestAuthLogin:
    """Test authentication login endpoint"""

    def test_login_success(self):
        """Test successful login with valid credentials"""
        mock_db = get_mock_db(user_exists=False)
        
        # Create a mock user with hashed password
        password = "Password123!"
        hashed_pw = hash_password(password)
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password=hashed_pw
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        def mock_get_db():
            yield mock_db
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=mock_user), \
             patch("app.routes.auth.verify_password", return_value=True), \
             patch("app.routes.auth.create_access_token", return_value="mock_jwt_token"):
            
            # Use form data format for OAuth2PasswordRequestForm
            response = client.post("/auth/login", data={
                "username": "testuser",
                "password": password
            })
            
            assert response.status_code == 200
            response_data = response.json()
            assert "access_token" in response_data
            assert "token_type" in response_data
            assert response_data["access_token"] == "mock_jwt_token"
            assert response_data["token_type"] == "bearer"

    def test_login_invalid_username(self):
        """Test login with nonexistent username"""
        mock_db = get_mock_db(user_exists=False)
        
        def mock_get_db():
            yield mock_db
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=None):
            
            response = client.post("/auth/login", data={
                "username": "nonexistent",
                "password": "Password123!"
            })
            
            assert response.status_code == 400
            assert response.json()["detail"] == "Incorrect username or password"

    def test_login_invalid_password(self):
        """Test login with correct username but wrong password"""
        mock_db = get_mock_db(user_exists=False)
        
        # Create a mock user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        def mock_get_db():
            yield mock_db
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=mock_user), \
             patch("app.routes.auth.verify_password", return_value=False):
            
            response = client.post("/auth/login", data={
                "username": "testuser",
                "password": "WrongPassword!"
            })
            
            assert response.status_code == 400
            assert response.json()["detail"] == "Incorrect username or password"

    def test_login_missing_credentials(self):
        """Test login with missing username or password"""
        # Missing username
        response = client.post("/auth/login", data={
            "password": "Password123!"
        })
        assert response.status_code == 422  # Validation error
        
        # Missing password
        response = client.post("/auth/login", data={
            "username": "testuser"
        })
        assert response.status_code == 422  # Validation error
        
        # Missing both
        response = client.post("/auth/login", data={})
        assert response.status_code == 422  # Validation error

    def test_login_empty_credentials(self):
        """Test login with empty username or password"""
        # Empty username - OAuth2PasswordRequestForm accepts empty strings but login fails
        response = client.post("/auth/login", data={
            "username": "",
            "password": "Password123!"
        })
        assert response.status_code == 400  # Bad request - treated as invalid login
        assert response.json()["detail"] == "Incorrect username or password"
        
        # Empty password - OAuth2PasswordRequestForm accepts empty strings but login fails
        response = client.post("/auth/login", data={
            "username": "testuser",
            "password": ""
        })
        assert response.status_code == 400  # Bad request - treated as invalid login
        assert response.json()["detail"] == "Incorrect username or password"

    def test_login_wrong_content_type(self):
        """Test login with JSON instead of form data"""
        # OAuth2PasswordRequestForm expects form data, not JSON
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "Password123!"
        })
        assert response.status_code == 422  # Validation error


class TestAuthMe:
    """Test /auth/me protected endpoint"""

    def test_auth_me_success(self):
        """Test successful access to /auth/me with valid token"""
        from app.core.security import get_current_user
        
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Override the dependency for this test
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            # Create a valid token for authorization header
            token = "mock_jwt_token"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = client.get("/auth/me", headers=headers)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["username"] == "testuser"
            assert response_data["name"] == "Test User"
            assert "created_at" in response_data  # UserOut includes created_at
            assert "hashed_password" not in response_data
        finally:
            # Clean up the dependency override
            app.dependency_overrides.clear()

    def test_auth_me_missing_token(self):
        """Test /auth/me without authorization header"""
        response = client.get("/auth/me")
        assert response.status_code == 401  # Unauthorized

    def test_auth_me_invalid_token_format(self):
        """Test /auth/me with invalid token format"""
        invalid_headers = [
            {"Authorization": "invalid_token"},  # Missing Bearer
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "Basic invalid_token"},  # Wrong scheme
            {"Authorization": ""},  # Empty
        ]
        
        for headers in invalid_headers:
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 401  # Unauthorized

    def test_auth_me_expired_token(self):
        """Test /auth/me with expired token"""
        from fastapi import HTTPException, status
        
        # Mock get_current_user to raise an HTTPException for expired token
        def mock_expired_token(*args, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        with patch("app.routes.auth.get_current_user", side_effect=mock_expired_token):
            token = "expired_jwt_token"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 401
            assert "Could not validate credentials" in response.json()["detail"]

    def test_auth_me_user_not_found(self):
        """Test /auth/me when token is valid but user doesn't exist"""
        from fastapi import HTTPException, status
        
        # Mock get_current_user to raise an HTTPException for user not found
        def mock_user_not_found(*args, **kwargs):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        with patch("app.routes.auth.get_current_user", side_effect=mock_user_not_found):
            token = "valid_token_but_user_deleted"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 401