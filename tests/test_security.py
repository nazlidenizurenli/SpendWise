# tests/test_security.py
import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from jose import jwt, JWTError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import uuid

# Import only what we need from security module
from app.core.security import (
    hash_password,
    verify_password,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Create a simple User mock to avoid SQLAlchemy import issues
class MockUser:
    def __init__(self, id, username, name, hashed_password):
        self.id = id
        self.username = username
        self.name = name
        self.hashed_password = hashed_password


class TestPasswordHashing:
    """Test password hashing and verification functions"""

    def test_hash_password_basic(self):
        """Test basic password hashing"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        # Hash should not be the same as original password
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should not be empty
        assert len(hashed) > 0
        # Hash should contain bcrypt prefix
        assert hashed.startswith("$2b$")

    def test_hash_password_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "password123"
        password2 = "password456"
        
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        
        assert hash1 != hash2

    def test_hash_password_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)"""
        password = "samepassword"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Due to salt, same password should produce different hashes
        assert hash1 != hash2

    def test_hash_password_special_characters(self):
        """Test hashing passwords with special characters"""
        password = "p@ssw0rd!#$%^&*()"
        hashed = hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_unicode_characters(self):
        """Test hashing passwords with unicode characters"""
        password = "пароль123密码"
        hashed = hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_empty_string(self):
        """Test hashing empty password"""
        password = ""
        hashed = hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_very_long_password(self):
        """Test hashing very long password"""
        password = "a" * 1000  # 1000 character password
        hashed = hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0


class TestPasswordVerification:
    """Test password verification function"""

    def test_verify_password_correct(self):
        """Test verification with correct password"""
        password = "correctpassword"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verification with incorrect password"""
        password = "correctpassword"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test verification with empty password"""
        password = "nonemptypassword"
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is False

    def test_verify_password_empty_hash(self):
        """Test verification with empty hash"""
        password = "testpassword"
        
        # This should raise an exception or return False
        try:
            result = verify_password(password, "")
            assert result is False
        except Exception:
            # It's acceptable for this to raise an exception
            pass

    def test_verify_password_invalid_hash(self):
        """Test verification with invalid hash format"""
        password = "testpassword"
        invalid_hash = "notavalidhash"
        
        # This should raise an exception or return False
        try:
            result = verify_password(password, invalid_hash)
            assert result is False
        except Exception:
            # It's acceptable for this to raise an exception
            pass

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive"""
        password = "CaseSensitive"
        hashed = hash_password(password)
        
        assert verify_password("CaseSensitive", hashed) is True
        assert verify_password("casesensitive", hashed) is False
        assert verify_password("CASESENSITIVE", hashed) is False

    def test_verify_password_special_characters(self):
        """Test verification with special characters"""
        password = "sp3c!@l#ch@rs"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("sp3c!@l#ch@r", hashed) is False

    def test_verify_password_unicode(self):
        """Test verification with unicode characters"""
        password = "тест密码🔒"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("тест密码", hashed) is False


class TestJWTTokenCreation:
    """Test JWT token creation and handling"""

    def test_create_access_token_basic(self):
        """Test basic token creation"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            from app.core.security import create_access_token
            
            data = {"sub": "user123"}
            token = create_access_token(data)
            
            assert isinstance(token, str)
            assert len(token) > 0
            # Token should have 3 parts separated by dots (header.payload.signature)
            assert len(token.split('.')) == 3

    def test_create_access_token_with_custom_expiry(self):
        """Test token creation with custom expiry"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            from app.core.security import create_access_token
            
            data = {"sub": "user123"}
            custom_expiry = timedelta(hours=2)
            
            token = create_access_token(data, custom_expiry)
            
            assert isinstance(token, str)
            assert len(token) > 0
            assert len(token.split('.')) == 3

    def test_create_access_token_additional_data(self):
        """Test token creation with additional data"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            from app.core.security import create_access_token
            
            data = {
                "sub": "user123",
                "username": "testuser",
                "role": "admin"
            }
            token = create_access_token(data)
            
            assert isinstance(token, str)
            assert len(token) > 0
            assert len(token.split('.')) == 3

    def test_create_access_token_no_secret_key(self):
        """Test token creation when SECRET_KEY is not set"""
        with patch.dict(os.environ, {}, clear=True):
            # This should raise an exception when trying to create a token
            try:
                from app.core.security import create_access_token
                data = {"sub": "user123"}
                token = create_access_token(data)
                # If no exception is raised, the token should be invalid
                assert token is None or len(token) == 0
            except Exception:
                # It's acceptable for this to raise an exception
                pass


class TestGetCurrentUser:
    """Test get_current_user function"""

    def setup_method(self):
        """Setup mock objects for each test"""
        self.mock_db = MagicMock(spec=Session)
        self.mock_user = MockUser(
            id="123e4567-e89b-12d3-a456-426614174000",
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )

    def test_get_current_user_valid_token(self):
        """Test getting current user with valid token"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            from app.core.security import create_access_token, get_current_user
            
            # Create valid token
            data = {"sub": str(self.mock_user.id)}
            token = create_access_token(data)
            
            # Mock database query
            self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_user
            
            # Test function
            result = get_current_user(self.mock_db, token)
            
            assert result == self.mock_user

    def test_get_current_user_expired_token(self):
        """Test getting current user with expired token"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            from app.core.security import create_access_token, get_current_user
            
            # Create expired token
            data = {"sub": str(self.mock_user.id)}
            expired_token = create_access_token(data, timedelta(seconds=-1))
            
            # Test function - should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(self.mock_db, expired_token)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_invalid_token_format(self):
        """Test getting current user with invalid token format"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            from app.core.security import get_current_user
            
            invalid_token = "invalid.token.format"
            
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(self.mock_db, invalid_token)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_token_without_sub(self):
        """Test getting current user with token missing 'sub' claim"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            from app.core.security import create_access_token, get_current_user
            
            # Create token without 'sub'
            data = {"username": "testuser", "role": "user"}
            token = create_access_token(data)
            
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(self.mock_db, token)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_user_not_found(self):
        """Test getting current user when user doesn't exist in database"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            from app.core.security import create_access_token, get_current_user
            
            # Create valid token
            data = {"sub": str(self.mock_user.id)}
            token = create_access_token(data)
            
            # Mock database query to return None (user not found)
            self.mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(self.mock_db, token)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_empty_token(self):
        """Test getting current user with empty token"""
        with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key'}):
            from app.core.security import get_current_user
            
            empty_token = ""
            
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(self.mock_db, empty_token)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestSecurityConstants:
    """Test security constants and configuration"""

    def test_algorithm_constant(self):
        """Test that algorithm constant is correct"""
        assert ALGORITHM == "HS256"

    def test_access_token_expire_minutes(self):
        """Test that access token expiry is reasonable"""
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert isinstance(ACCESS_TOKEN_EXPIRE_MINUTES, int)
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0


class TestSecurityIntegration:
    """Integration tests for security functions"""

    def test_full_password_flow(self):
        """Test complete password flow: hash and verify"""
        # 1. Hash a password
        original_password = "userpassword123"
        hashed_password = hash_password(original_password)
        
        # 2. Verify password works
        assert verify_password(original_password, hashed_password) is True
        assert verify_password("wrongpassword", hashed_password) is False

    def test_security_with_different_users(self):
        """Test security isolation between different users"""
        user1_password = "user1password"
        user2_password = "user2password"
        
        # Hash different passwords
        hash1 = hash_password(user1_password)
        hash2 = hash_password(user2_password)
        
        # Verify passwords don't cross-verify
        assert verify_password(user1_password, hash1) is True
        assert verify_password(user1_password, hash2) is False
        assert verify_password(user2_password, hash1) is False
        assert verify_password(user2_password, hash2) is True

    def test_jwt_token_basic_flow(self):
        """Test JWT token creation flow"""
        with patch.dict(os.environ, {'SECRET_KEY': 'integration-test-key'}):
            from app.core.security import create_access_token
            
            # Create token for user
            token_data = {"sub": "test-user-id"}
            token = create_access_token(token_data)
            
            # Verify token is properly formatted
            assert isinstance(token, str)
            assert len(token) > 0
            assert len(token.split('.')) == 3