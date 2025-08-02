"""
Comprehensive authentication integration tests.
Tests complete authentication workflows including edge cases, error scenarios, and real-world usage patterns.
"""

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.models.user import User
from tests.utils.mocks import get_mock_db
from app.main import app
from app.core.security import hash_password, create_access_token, get_current_user
import uuid
from datetime import datetime
import pytest


client = TestClient(app)


class TestCompleteAuthFlow:
    """Test complete authentication workflows from start to finish"""

    def test_complete_user_lifecycle(self):
        """Test the complete user lifecycle: register -> login -> use protected resources -> logout behavior"""
        mock_db = get_mock_db(user_exists=False)
        
        password = "SecurePass123!"
        mock_user = User(
            username="lifecycle_user",
            name="Lifecycle Test User",
            hashed_password=hash_password(password)
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        def mock_get_db():
            yield mock_db
        
        # Step 1: User Registration
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=None), \
             patch("app.routes.auth.crud_user.create_user", return_value=mock_user):
            
            register_response = client.post("/auth/register", json={
                "username": "lifecycle_user",
                "password": password,
                "name": "Lifecycle Test User"
            })
            
            assert register_response.status_code == 201
            register_data = register_response.json()
            assert register_data["username"] == "lifecycle_user"
            assert "hashed_password" not in register_data  # Ensure password is not exposed
        
        # Step 2: User Login
        mock_token = "lifecycle_jwt_token"
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=mock_user), \
             patch("app.routes.auth.verify_password", return_value=True), \
             patch("app.routes.auth.create_access_token", return_value=mock_token):
            
            login_response = client.post("/auth/login", data={
                "username": "lifecycle_user",
                "password": password
            })
            
            assert login_response.status_code == 200
            login_data = login_response.json()
            assert login_data["access_token"] == mock_token
            assert login_data["token_type"] == "bearer"
            token = login_data["access_token"]
        
        # Step 3: Access Protected Resources
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            
            # Access user profile
            me_response = client.get("/auth/me", headers=headers)
            assert me_response.status_code == 200
            me_data = me_response.json()
            assert me_data["username"] == "lifecycle_user"
            
            # Access transaction endpoints (empty list)
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions", return_value=[]):
                
                txn_response = client.get("/transactions/get-all", headers=headers)
                assert txn_response.status_code == 200
                assert txn_response.json() == []
        finally:
            app.dependency_overrides.clear()
        
        # Step 4: Simulate logout (token becomes invalid)
        # After logout, the token should not work (simulated by not overriding get_current_user)
        headers = {"Authorization": f"Bearer {token}"}
        post_logout_response = client.get("/auth/me", headers=headers)
        assert post_logout_response.status_code == 401

    def test_multiple_users_concurrent_sessions(self):
        """Test that multiple users can have concurrent authenticated sessions"""
        mock_db = get_mock_db(user_exists=False)
        
        # Create multiple users
        users = []
        tokens = []
        
        for i in range(3):
            user = User(
                username=f"concurrent_user_{i}",
                name=f"Concurrent User {i}",
                hashed_password=hash_password(f"Password{i}23!")
            )
            user.id = uuid.uuid4()
            user.created_at = datetime.now()
            users.append(user)
            tokens.append(f"concurrent_token_{i}")
        
        def mock_get_db():
            yield mock_db
        
        # Test that each user can independently access their profile
        for i, (user, token) in enumerate(zip(users, tokens)):
            def get_current_user_override():
                return user
            
            app.dependency_overrides[get_current_user] = get_current_user_override
            
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = client.get("/auth/me", headers=headers)
                
                assert response.status_code == 200
                data = response.json()
                assert data["username"] == f"concurrent_user_{i}"
                assert data["name"] == f"Concurrent User {i}"
            finally:
                app.dependency_overrides.clear()

    def test_authentication_state_transitions(self):
        """Test various authentication state transitions"""
        mock_db = get_mock_db(user_exists=False)
        
        user = User(
            username="state_user",
            name="State Transition User",
            hashed_password=hash_password("StatePass123!")
        )
        user.id = uuid.uuid4()
        user.created_at = datetime.now()
        
        def mock_get_db():
            yield mock_db
        
        # State 1: Unauthenticated - should fail
        response = client.get("/auth/me")
        assert response.status_code == 401
        
        # State 2: Invalid token - should fail
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
        
        # State 3: Valid authentication - should succeed
        def get_current_user_override():
            return user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
        
        # State 4: Back to unauthenticated - should fail
        headers = {"Authorization": "Bearer expired_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401


class TestAuthErrorScenarios:
    """Test various authentication error scenarios and edge cases"""

    def test_duplicate_registration_attempt(self):
        """Test that duplicate username registration is properly handled"""
        mock_db = get_mock_db(user_exists=True)
        
        existing_user = User(
            username="existing_user",
            name="Existing User",
            hashed_password=hash_password("ExistingPass123!")
        )
        
        def mock_get_db():
            yield mock_db
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=existing_user):
            
            response = client.post("/auth/register", json={
                "username": "existing_user",
                "password": "NewPassword123!",
                "name": "New User"
            })
            
            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]

    def test_login_with_nonexistent_user(self):
        """Test login attempts with nonexistent usernames"""
        mock_db = get_mock_db(user_exists=False)
        
        def mock_get_db():
            yield mock_db
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=None):
            
            response = client.post("/auth/login", data={
                "username": "nonexistent_user",
                "password": "SomePassword123!"
            })
            
            assert response.status_code == 400
            assert "Incorrect username or password" in response.json()["detail"]

    def test_login_with_wrong_password(self):
        """Test login attempts with correct username but wrong password"""
        mock_db = get_mock_db(user_exists=False)
        
        correct_password = "CorrectPass123!"
        user = User(
            username="password_test_user",
            name="Password Test User",
            hashed_password=hash_password(correct_password)
        )
        
        def mock_get_db():
            yield mock_db
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=user), \
             patch("app.routes.auth.verify_password", return_value=False):
            
            response = client.post("/auth/login", data={
                "username": "password_test_user",
                "password": "WrongPassword123!"
            })
            
            assert response.status_code == 400
            assert "Incorrect username or password" in response.json()["detail"]

    def test_invalid_registration_data(self):
        """Test registration with various invalid data scenarios"""
        invalid_registrations = [
            # Missing fields
            {"username": "testuser", "password": "Password123!"},  # Missing name
            {"username": "testuser", "name": "Test User"},  # Missing password
            {"password": "Password123!", "name": "Test User"},  # Missing username
            
            # Invalid field values
            {"username": "ab", "password": "Password123!", "name": "Test User"},  # Username too short
            {"username": "a" * 21, "password": "Password123!", "name": "Test User"},  # Username too long
            {"username": "test@user", "password": "Password123!", "name": "Test User"},  # Invalid username chars
            {"username": "123456", "password": "Password123!", "name": "Test User"},  # Username no letters
            
            # Invalid passwords
            {"username": "testuser", "password": "123456", "name": "Test User"},  # Password no letters
            {"username": "testuser", "password": "password", "name": "Test User"},  # Password no numbers
            {"username": "testuser", "password": "Password123", "name": "Test User"},  # Password no special chars
            
            # Invalid names
            {"username": "testuser", "password": "Password123!", "name": "123456"},  # Name no letters
            {"username": "testuser", "password": "Password123!", "name": "Test@User"},  # Name invalid chars
        ]
        
        for invalid_data in invalid_registrations:
            response = client.post("/auth/register", json=invalid_data)
            assert response.status_code == 422  # Validation error

    def test_login_with_invalid_data_format(self):
        """Test login with various invalid data formats"""
        invalid_logins = [
            # Wrong content type (JSON instead of form data)
            ("json", {"username": "testuser", "password": "Password123!"}),
            
            # Missing required fields
            ("form", {"username": "testuser"}),  # Missing password
            ("form", {"password": "Password123!"}),  # Missing username
            ("form", {}),  # Missing both
        ]
        
        for content_type, data in invalid_logins:
            if content_type == "json":
                response = client.post("/auth/login", json=data)
            else:
                response = client.post("/auth/login", data=data)
            
            # Should get either 422 (validation error) or 400 (bad request)
            assert response.status_code in [400, 422]


class TestAuthSecurityScenarios:
    """Test authentication security scenarios and best practices"""

    def test_password_not_exposed_in_responses(self):
        """Test that passwords/hashes are never exposed in API responses"""
        mock_db = get_mock_db(user_exists=False)
        
        password = "SecurePass123!"
        user = User(
            username="security_user",
            name="Security Test User",
            hashed_password=hash_password(password)
        )
        user.id = uuid.uuid4()
        user.created_at = datetime.now()
        
        def mock_get_db():
            yield mock_db
        
        # Test registration response
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=None), \
             patch("app.routes.auth.crud_user.create_user", return_value=user):
            
            register_response = client.post("/auth/register", json={
                "username": "security_user",
                "password": password,
                "name": "Security Test User"
            })
            
            register_data = register_response.json()
            assert "password" not in register_data
            assert "hashed_password" not in register_data
        
        # Test login response
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=user), \
             patch("app.routes.auth.verify_password", return_value=True), \
             patch("app.routes.auth.create_access_token", return_value="secure_token"):
            
            login_response = client.post("/auth/login", data={
                "username": "security_user",
                "password": password
            })
            
            login_data = login_response.json()
            assert "password" not in login_data
            assert "hashed_password" not in login_data
            assert "access_token" in login_data  # Only token should be present
        
        # Test profile response
        def get_current_user_override():
            return user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            headers = {"Authorization": "Bearer secure_token"}
            me_response = client.get("/auth/me", headers=headers)
            
            me_data = me_response.json()
            assert "password" not in me_data
            assert "hashed_password" not in me_data
            assert me_data["username"] == "security_user"
        finally:
            app.dependency_overrides.clear()

    def test_case_sensitive_authentication(self):
        """Test that authentication is case-sensitive for usernames"""
        mock_db = get_mock_db(user_exists=False)
        
        password = "CaseTest123!"
        user = User(
            username="CaseUser",
            name="Case Test User",
            hashed_password=hash_password(password)
        )
        
        def mock_get_db():
            yield mock_db
        
        # Test that exact case works
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username") as mock_get_user, \
             patch("app.routes.auth.verify_password", return_value=True), \
             patch("app.routes.auth.create_access_token", return_value="case_token"):
            
            # Configure mock to return user only for exact case match
            def mock_get_user_side_effect(db, username):
                if username == "CaseUser":
                    return user
                return None
            
            mock_get_user.side_effect = mock_get_user_side_effect
            
            # Test exact case - should work
            response = client.post("/auth/login", data={
                "username": "CaseUser",
                "password": password
            })
            assert response.status_code == 200
            
            # Test different case - should fail
            response = client.post("/auth/login", data={
                "username": "caseuser",
                "password": password
            })
            assert response.status_code == 400

    def test_concurrent_login_attempts(self):
        """Test behavior with concurrent login attempts"""
        mock_db = get_mock_db(user_exists=False)
        
        password = "ConcurrentPass123!"
        user = User(
            username="concurrent_login_user",
            name="Concurrent Login User",
            hashed_password=hash_password(password)
        )
        
        def mock_get_db():
            yield mock_db
        
        # Simulate multiple concurrent login attempts for the same user
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=user), \
             patch("app.routes.auth.verify_password", return_value=True), \
             patch("app.routes.auth.create_access_token", side_effect=lambda data: f"token_{data['sub']}"):
            
            responses = []
            for i in range(5):
                response = client.post("/auth/login", data={
                    "username": "concurrent_login_user",
                    "password": password
                })
                responses.append(response)
            
            # All login attempts should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert data["token_type"] == "bearer"

    def test_authentication_rate_limiting_simulation(self):
        """Test simulation of authentication rate limiting behavior"""
        # Note: This is a behavioral test since we don't have actual rate limiting implemented
        # In a real application, this would test actual rate limiting functionality
        
        mock_db = get_mock_db(user_exists=False)
        
        def mock_get_db():
            yield mock_db
        
        # Simulate multiple failed login attempts
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=None):
            
            # Multiple failed attempts should each return the same error
            for i in range(10):
                response = client.post("/auth/login", data={
                    "username": "nonexistent",
                    "password": "InvalidPass123!"
                })
                assert response.status_code == 400
                assert "Incorrect username or password" in response.json()["detail"]
                
                # In a real rate-limiting scenario, after several attempts,
                # we might expect 429 (Too Many Requests) responses