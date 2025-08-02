"""
Integration tests for JWT token flows and end-to-end authentication scenarios.
Tests the complete flow from registration -> login -> using protected endpoints.
"""

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.models.user import User
from app.models.transaction import TransactionModel
from tests.utils.mocks import get_mock_db
from app.main import app
from app.core.security import hash_password, create_access_token, get_current_user
import uuid
from datetime import datetime, timedelta
import pytest
from jose import jwt
import os


client = TestClient(app)


class TestJWTTokenFlow:
    """Test complete JWT token flows"""

    def test_register_login_access_protected_endpoint_flow(self):
        """Test the complete flow: register -> login -> access protected endpoint"""
        mock_db = get_mock_db(user_exists=False)
        
        # Step 1: Register a new user
        password = "Password123!"
        mock_created_user = User(
            username="testuser",
            name="Test User", 
            hashed_password=hash_password(password)
        )
        mock_created_user.id = uuid.uuid4()
        mock_created_user.created_at = datetime.now()
        
        def mock_get_db():
            yield mock_db
            
        # Register user
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=None), \
             patch("app.routes.auth.crud_user.create_user", return_value=mock_created_user):
            
            register_response = client.post("/auth/register", json={
                "username": "testuser",
                "password": password,
                "name": "Test User"
            })
            
            assert register_response.status_code == 201
            register_data = register_response.json()
            assert register_data["username"] == "testuser"
            assert register_data["name"] == "Test User"
        
        # Step 2: Login with the registered user
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTY0MDk5NTIwMH0.test"
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=mock_created_user), \
             patch("app.routes.auth.verify_password", return_value=True), \
             patch("app.routes.auth.create_access_token", return_value=mock_token):
            
            login_response = client.post("/auth/login", data={
                "username": "testuser",
                "password": password
            })
            
            assert login_response.status_code == 200
            login_data = login_response.json()
            assert "access_token" in login_data
            assert login_data["token_type"] == "bearer"
            token = login_data["access_token"]
        
        # Step 3: Use the token to access protected endpoint (/auth/me)
        # Override get_current_user to return our mock user
        def get_current_user_override():
            return mock_created_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            me_response = client.get("/auth/me", headers=headers)
            
            assert me_response.status_code == 200
            me_data = me_response.json()
            assert me_data["username"] == "testuser"
            assert me_data["name"] == "Test User"
        finally:
            app.dependency_overrides.clear()

    def test_register_login_create_transaction_flow(self):
        """Test complete flow: register -> login -> create transaction"""
        mock_db = get_mock_db(user_exists=False)
        
        # Step 1: Register user (same as previous test)
        password = "Password123!"
        mock_user = User(
            username="txnuser",
            name="Transaction User",
            hashed_password=hash_password(password)
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        def mock_get_db():
            yield mock_db
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=None), \
             patch("app.routes.auth.crud_user.create_user", return_value=mock_user):
            
            register_response = client.post("/auth/register", json={
                "username": "txnuser",
                "password": password,
                "name": "Transaction User"
            })
            assert register_response.status_code == 201
        
        # Step 2: Login
        mock_token = "jwt_token_for_transactions"
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=mock_user), \
             patch("app.routes.auth.verify_password", return_value=True), \
             patch("app.routes.auth.create_access_token", return_value=mock_token):
            
            login_response = client.post("/auth/login", data={
                "username": "txnuser",
                "password": password
            })
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
        
        # Step 3: Create transaction using the token
        mock_transaction = TransactionModel(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            amount=250.00,
            description="Salary from full flow",
            category="salary",
            transaction_type="income",
            source="debit",
            timestamp=datetime.now()
        )
        
        # Override dependencies
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.create_transaction_for_user", return_value=mock_transaction):
                
                headers = {"Authorization": f"Bearer {token}"}
                txn_response = client.post("/transactions/submit", 
                    headers=headers,
                    json={
                        "amount": 250.00,
                        "description": "Salary from full flow",
                        "category": "salary",
                        "transaction_type": "income",
                        "source": "debit"
                    }
                )
                
                assert txn_response.status_code == 200
                txn_data = txn_response.json()
                assert txn_data["amount"] == 250.00
                assert txn_data["description"] == "Salary from full flow"
                assert txn_data["transaction_type"] == "income"
        finally:
            app.dependency_overrides.clear()

    def test_login_retrieve_transactions_flow(self):
        """Test flow: login -> retrieve all transactions"""
        mock_db = get_mock_db(user_exists=False)
        
        # Create user with existing transactions
        password = "Password123!"
        mock_user = User(
            username="txnuser2",
            name="Transaction User 2",
            hashed_password=hash_password(password)
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Mock existing transactions
        mock_transactions = [
            TransactionModel(
                id=uuid.uuid4(),
                user_id=mock_user.id,
                amount=100.00,
                description="Existing transaction 1",
                category="food",
                transaction_type="expense",
                source="credit",
                timestamp=datetime.now()
            ),
            TransactionModel(
                id=uuid.uuid4(),
                user_id=mock_user.id,
                amount=500.00,
                description="Existing transaction 2",
                category="salary",
                transaction_type="income",
                source="debit",
                timestamp=datetime.now()
            )
        ]
        
        def mock_get_db():
            yield mock_db
        
        # Step 1: Login
        mock_token = "jwt_token_for_get_transactions"
        
        with patch("app.routes.auth.get_db", side_effect=mock_get_db), \
             patch("app.routes.auth.crud_user.get_user_by_username", return_value=mock_user), \
             patch("app.routes.auth.verify_password", return_value=True), \
             patch("app.routes.auth.create_access_token", return_value=mock_token):
            
            login_response = client.post("/auth/login", data={
                "username": "txnuser2",
                "password": password
            })
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
        
        # Step 2: Get all transactions using the token
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions", return_value=mock_transactions):
                
                headers = {"Authorization": f"Bearer {token}"}
                txn_response = client.get("/transactions/get-all", headers=headers)
                
                assert txn_response.status_code == 200
                txn_data = txn_response.json()
                assert len(txn_data) == 2
                assert txn_data[0]["description"] == "Existing transaction 1"
                assert txn_data[1]["description"] == "Existing transaction 2"
        finally:
            app.dependency_overrides.clear()


class TestJWTTokenValidation:
    """Test JWT token validation scenarios"""

    def test_expired_token_rejected(self):
        """Test that expired tokens are properly rejected"""
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Create an expired token
        past_time = datetime.utcnow() - timedelta(hours=1)
        expired_token_data = {
            "sub": str(mock_user.id),
            "exp": past_time
        }
        
        # Mock the secret key for token creation
        with patch.dict(os.environ, {"SECRET_KEY": "test_secret_key"}):
            expired_token = jwt.encode(expired_token_data, "test_secret_key", algorithm="HS256")
        
        # Test that the expired token is rejected
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    def test_invalid_token_signature_rejected(self):
        """Test that tokens with invalid signatures are rejected"""
        # Create a token with wrong signature
        invalid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciJ9.invalid_signature"
        
        headers = {"Authorization": f"Bearer {invalid_token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    def test_malformed_token_rejected(self):
        """Test that malformed tokens are rejected"""
        malformed_tokens = [
            "not.a.jwt",
            "Bearer invalid_token",
            "invalid_format",
            "",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Incomplete JWT
        ]
        
        for token in malformed_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 401

    def test_token_without_bearer_prefix_rejected(self):
        """Test that tokens without Bearer prefix are rejected"""
        valid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciJ9.signature"
        
        # Test various invalid authorization headers
        invalid_headers = [
            {"Authorization": valid_token},  # Missing Bearer
            {"Authorization": f"Basic {valid_token}"},  # Wrong scheme
            {"Authorization": f"Token {valid_token}"},  # Wrong scheme
        ]
        
        for headers in invalid_headers:
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 401


class TestUserIsolationWithTokens:
    """Test that JWT tokens properly isolate users"""

    def test_different_users_cannot_access_each_others_data(self):
        """Test that different JWT tokens isolate user data correctly"""
        mock_db = get_mock_db(user_exists=False)
        
        # Create two different users
        user1 = User(username="user1", name="User One", hashed_password="hash1")
        user1.id = uuid.uuid4()
        user1.created_at = datetime.now()
        
        user2 = User(username="user2", name="User Two", hashed_password="hash2") 
        user2.id = uuid.uuid4()
        user2.created_at = datetime.now()
        
        # Create transactions for each user
        user1_transactions = [
            TransactionModel(
                id=uuid.uuid4(),
                user_id=user1.id,
                amount=100.00,
                description="User 1 transaction",
                category="test",
                transaction_type="income",
                source="debit",
                timestamp=datetime.now()
            )
        ]
        
        user2_transactions = [
            TransactionModel(
                id=uuid.uuid4(),
                user_id=user2.id,
                amount=200.00,
                description="User 2 transaction", 
                category="test",
                transaction_type="income",
                source="debit",
                timestamp=datetime.now()
            )
        ]
        
        def mock_get_db():
            yield mock_db
        
        # Test User 1 access
        def get_current_user_override_user1():
            return user1
        
        app.dependency_overrides[get_current_user] = get_current_user_override_user1
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions", return_value=user1_transactions):
                
                user1_token = "user1_jwt_token"
                headers = {"Authorization": f"Bearer {user1_token}"}
                response = client.get("/transactions/get-all", headers=headers)
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["description"] == "User 1 transaction"
                assert data[0]["amount"] == 100.00
        finally:
            app.dependency_overrides.clear()
        
        # Test User 2 access
        def get_current_user_override_user2():
            return user2
        
        app.dependency_overrides[get_current_user] = get_current_user_override_user2
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions", return_value=user2_transactions):
                
                user2_token = "user2_jwt_token"
                headers = {"Authorization": f"Bearer {user2_token}"}
                response = client.get("/transactions/get-all", headers=headers)
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["description"] == "User 2 transaction"
                assert data[0]["amount"] == 200.00
        finally:
            app.dependency_overrides.clear()

    def test_user_can_only_access_own_profile_with_token(self):
        """Test that users can only access their own profile with their JWT token"""
        # Create two users
        user1 = User(username="profile_user1", name="Profile User 1", hashed_password="hash1")
        user1.id = uuid.uuid4()
        user1.created_at = datetime.now()
        
        user2 = User(username="profile_user2", name="Profile User 2", hashed_password="hash2")
        user2.id = uuid.uuid4()  
        user2.created_at = datetime.now()
        
        # Test User 1 accessing their own profile
        def get_current_user_override_user1():
            return user1
        
        app.dependency_overrides[get_current_user] = get_current_user_override_user1
        
        try:
            user1_token = "user1_profile_token"
            headers = {"Authorization": f"Bearer {user1_token}"}
            response = client.get("/auth/me", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "profile_user1"
            assert data["name"] == "Profile User 1"
        finally:
            app.dependency_overrides.clear()
        
        # Test User 2 accessing their own profile  
        def get_current_user_override_user2():
            return user2
        
        app.dependency_overrides[get_current_user] = get_current_user_override_user2
        
        try:
            user2_token = "user2_profile_token"
            headers = {"Authorization": f"Bearer {user2_token}"}
            response = client.get("/auth/me", headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "profile_user2"
            assert data["name"] == "Profile User 2"
        finally:
            app.dependency_overrides.clear()


class TestTokenSecurityScenarios:
    """Test various security scenarios with JWT tokens"""

    def test_token_reuse_across_sessions(self):
        """Test that valid tokens work across multiple requests"""
        mock_user = User(
            username="session_user",
            name="Session User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Override get_current_user
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            token = "persistent_session_token"
            headers = {"Authorization": f"Bearer {token}"}
            
            # Make multiple requests with the same token
            for i in range(3):
                response = client.get("/auth/me", headers=headers)
                assert response.status_code == 200
                data = response.json()
                assert data["username"] == "session_user"
        finally:
            app.dependency_overrides.clear()

    def test_no_token_access_denied(self):
        """Test that requests without tokens are properly denied"""
        protected_endpoints = [
            ("/auth/me", "GET"),
            ("/transactions/submit", "POST"),
            ("/transactions/get-all", "GET"),
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={
                    "amount": 100.00,
                    "description": "Test",
                    "category": "test", 
                    "transaction_type": "income",
                    "source": "debit"
                })
            
            assert response.status_code == 401  # Unauthorized

    def test_empty_authorization_header_denied(self):
        """Test that empty authorization headers are denied"""
        invalid_headers = [
            {"Authorization": ""},
            {"Authorization": "Bearer "},
            {"Authorization": "Bearer"},
            {},  # No authorization header
        ]
        
        for headers in invalid_headers:
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 401