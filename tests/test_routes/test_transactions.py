from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, ANY
from app.models.user import User
from app.models.transaction import TransactionModel
from tests.utils.mocks import get_mock_db
from app.main import app
from app.core.security import get_current_user
from app.crud.transaction import create_transaction_for_user, get_transactions
import uuid
from datetime import datetime
import pytest


client = TestClient(app)


class TestTransactionSubmit:
    """Test POST /transactions/submit endpoint"""

    def test_submit_transaction_success_income_debit(self):
        """Test successful creation of income transaction from debit"""
        mock_db = get_mock_db(user_exists=False)
        
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Mock created transaction
        mock_transaction = TransactionModel(
            amount=100.50,
            description="Salary payment",
            category="salary",
            transaction_type="income",
            source="debit",
            timestamp=datetime.now(),
            user_id=mock_user.id
        )
        mock_transaction.id = uuid.uuid4()
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.create_transaction_for_user", return_value=mock_transaction):
                
                response = client.post("/transactions/submit", json={
                    "amount": 100.50,
                    "description": "Salary payment",
                    "category": "salary",
                    "transaction_type": "income",
                    "source": "debit"
                })
                
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["amount"] == 100.50
                assert response_data["description"] == "Salary payment"
                assert response_data["category"] == "salary"
                assert response_data["transaction_type"] == "income"
                assert response_data["source"] == "debit"
                assert "id" in response_data
                assert "user_id" in response_data
                assert "timestamp" in response_data
        finally:
            app.dependency_overrides.clear()

    def test_submit_transaction_success_expense_credit(self):
        """Test successful creation of expense transaction from credit"""
        mock_db = get_mock_db(user_exists=False)
        
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Mock created transaction
        mock_transaction = TransactionModel(
            amount=75.99,
            description="Grocery shopping",
            category="food",
            transaction_type="expense",
            source="credit",
            timestamp=datetime.now(),
            user_id=mock_user.id
        )
        mock_transaction.id = uuid.uuid4()
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.create_transaction_for_user", return_value=mock_transaction):
                
                response = client.post("/transactions/submit", json={
                    "amount": 75.99,
                    "description": "Grocery shopping",
                    "category": "food",
                    "transaction_type": "expense",
                    "source": "credit"
                })
                
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["amount"] == 75.99
                assert response_data["description"] == "Grocery shopping"
                assert response_data["category"] == "food"
                assert response_data["transaction_type"] == "expense"
                assert response_data["source"] == "credit"
        finally:
            app.dependency_overrides.clear()

    def test_submit_transaction_success_expense_debit_negative(self):
        """Test successful creation of expense transaction from debit with negative amount"""
        mock_db = get_mock_db(user_exists=False)
        
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Mock created transaction
        mock_transaction = TransactionModel(
            amount=-150.00,
            description="ATM withdrawal",
            category="cash",
            transaction_type="expense",
            source="debit",
            timestamp=datetime.now(),
            user_id=mock_user.id
        )
        mock_transaction.id = uuid.uuid4()
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.create_transaction_for_user", return_value=mock_transaction):
                
                response = client.post("/transactions/submit", json={
                    "amount": -150.00,
                    "description": "ATM withdrawal",
                    "category": "cash",
                    "transaction_type": "expense",
                    "source": "debit"
                })
                
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["amount"] == -150.00
                assert response_data["description"] == "ATM withdrawal"
                assert response_data["transaction_type"] == "expense"
                assert response_data["source"] == "debit"
        finally:
            app.dependency_overrides.clear()

    def test_submit_transaction_invalid_schema_validation(self):
        """Test transaction submission with invalid schema data"""
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            # Test invalid amount (zero)
            response = client.post("/transactions/submit", json={
                "amount": 0,
                "description": "Invalid transaction",
                "category": "test",
                "transaction_type": "income",
                "source": "debit"
            })
            assert response.status_code == 422  # Validation error
            
            # Test invalid description (empty)
            response = client.post("/transactions/submit", json={
                "amount": 100.00,
                "description": "",
                "category": "test",
                "transaction_type": "income",
                "source": "debit"
            })
            assert response.status_code == 422  # Validation error
            
            # Test invalid type
            response = client.post("/transactions/submit", json={
                "amount": 100.00,
                "description": "Test transaction",
                "category": "test",
                "transaction_type": "invalid_type",
                "source": "debit"
            })
            assert response.status_code == 422  # Validation error
            
            # Test invalid source
            response = client.post("/transactions/submit", json={
                "amount": 100.00,
                "description": "Test transaction",
                "category": "test",
                "transaction_type": "income",
                "source": "invalid_source"
            })
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()

    def test_submit_transaction_business_logic_validation(self):
        """Test transaction submission with invalid business logic"""
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            # Test invalid credit transaction (negative amount)
            response = client.post("/transactions/submit", json={
                "amount": -100.00,
                "description": "Invalid credit transaction",
                "category": "test",
                "transaction_type": "expense",
                "source": "credit"
            })
            assert response.status_code == 422  # Validation error
            
            # Test invalid credit transaction (income type)
            response = client.post("/transactions/submit", json={
                "amount": 100.00,
                "description": "Invalid credit income",
                "category": "test",
                "transaction_type": "income",
                "source": "credit"
            })
            assert response.status_code == 422  # Validation error
            
            # Test invalid debit transaction (positive amount with expense)
            response = client.post("/transactions/submit", json={
                "amount": 100.00,
                "description": "Invalid debit expense",
                "category": "test",
                "transaction_type": "expense",
                "source": "debit"
            })
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()

    def test_submit_transaction_missing_authentication(self):
        """Test transaction submission without authentication"""
        response = client.post("/transactions/submit", json={
            "amount": 100.00,
            "description": "Test transaction",
            "category": "test",
            "transaction_type": "income",
            "source": "debit"
        })
        assert response.status_code == 401  # Unauthorized

    def test_submit_transaction_missing_required_fields(self):
        """Test transaction submission with missing required fields"""
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            # Missing amount
            response = client.post("/transactions/submit", json={
                "description": "Test transaction",
                "category": "test",
                "transaction_type": "income",
                "source": "debit"
            })
            assert response.status_code == 422  # Validation error
            
            # Missing description
            response = client.post("/transactions/submit", json={
                "amount": 100.00,
                "category": "test",
                "transaction_type": "income",
                "source": "debit"
            })
            assert response.status_code == 422  # Validation error
            
            # Missing transaction_type
            response = client.post("/transactions/submit", json={
                "amount": 100.00,
                "description": "Test transaction",
                "category": "test",
                "source": "debit"
            })
            assert response.status_code == 422  # Validation error
            
            # Missing source
            response = client.post("/transactions/submit", json={
                "amount": 100.00,
                "description": "Test transaction",
                "category": "test",
                "transaction_type": "income"
            })
            assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()


class TestTransactionGetAll:
    """Test GET /transactions/get-all endpoint"""

    def test_get_all_transactions_success_with_data(self):
        """Test successful retrieval of user transactions with data"""
        mock_db = get_mock_db(user_exists=False)
        
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Mock transactions
        mock_transactions = [
            TransactionModel(
                id=uuid.uuid4(),
                user_id=mock_user.id,
                amount=100.50,
                description="Salary payment",
                category="salary",
                transaction_type="income",
                source="debit",
                timestamp=datetime.now()
            ),
            TransactionModel(
                id=uuid.uuid4(),
                user_id=mock_user.id,
                amount=50.25,
                description="Grocery shopping",
                category="food",
                transaction_type="expense",
                source="credit",
                timestamp=datetime.now()
            ),
            TransactionModel(
                id=uuid.uuid4(),
                user_id=mock_user.id,
                amount=-75.00,
                description="ATM withdrawal",
                category="cash",
                transaction_type="expense",
                source="debit",
                timestamp=datetime.now()
            )
        ]
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions", return_value=mock_transactions):
                
                response = client.get("/transactions/get-all")
                
                assert response.status_code == 200
                response_data = response.json()
                assert isinstance(response_data, list)
                assert len(response_data) == 3
                
                # Check first transaction
                assert response_data[0]["amount"] == 100.50
                assert response_data[0]["description"] == "Salary payment"
                assert response_data[0]["category"] == "salary"
                assert response_data[0]["transaction_type"] == "income"
                assert response_data[0]["source"] == "debit"
                
                # Check second transaction
                assert response_data[1]["amount"] == 50.25
                assert response_data[1]["description"] == "Grocery shopping"
                assert response_data[1]["transaction_type"] == "expense"
                assert response_data[1]["source"] == "credit"
                
                # Check third transaction
                assert response_data[2]["amount"] == -75.00
                assert response_data[2]["description"] == "ATM withdrawal"
                assert response_data[2]["transaction_type"] == "expense"
                assert response_data[2]["source"] == "debit"
        finally:
            app.dependency_overrides.clear()

    def test_get_all_transactions_success_empty_list(self):
        """Test successful retrieval with no transactions"""
        mock_db = get_mock_db(user_exists=False)
        
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions", return_value=[]):
                
                response = client.get("/transactions/get-all")
                
                assert response.status_code == 200
                response_data = response.json()
                assert isinstance(response_data, list)
                assert len(response_data) == 0
        finally:
            app.dependency_overrides.clear()

    def test_get_all_transactions_missing_authentication(self):
        """Test get all transactions without authentication"""
        response = client.get("/transactions/get-all")
        assert response.status_code == 401  # Unauthorized

    def test_get_all_transactions_user_isolation(self):
        """Test that users only see their own transactions"""
        mock_db = get_mock_db(user_exists=False)
        
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Mock only transactions for this specific user
        user_transactions = [
            TransactionModel(
                id=uuid.uuid4(),
                user_id=mock_user.id,  # Same user ID
                amount=100.00,
                description="User's transaction",
                category="test",
                transaction_type="income",
                source="debit",
                timestamp=datetime.now()
            )
        ]
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            # Mock the CRUD function to verify it's called with the correct user_id
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions", return_value=user_transactions) as mock_get_transactions:
                
                response = client.get("/transactions/get-all")
                
                assert response.status_code == 200
                response_data = response.json()
                assert len(response_data) == 1
                assert response_data[0]["description"] == "User's transaction"
                
                # Verify the CRUD function was called with the correct user_id
                mock_get_transactions.assert_called_once_with(ANY, user_id=mock_user.id)
        finally:
            app.dependency_overrides.clear()


class TestTransactionEndpointsIntegration:
    """Test integration scenarios for transaction endpoints"""

    def test_create_and_retrieve_transaction_flow(self):
        """Test the complete flow of creating and then retrieving transactions"""
        mock_db = get_mock_db(user_exists=False)
        
        # Mock current user
        mock_user = User(
            username="testuser",
            name="Test User",
            hashed_password="hashed_password"
        )
        mock_user.id = uuid.uuid4()
        mock_user.created_at = datetime.now()
        
        # Mock created transaction
        created_transaction = TransactionModel(
            id=uuid.uuid4(),
            user_id=mock_user.id,
            amount=100.50,
            description="Salary payment",
            category="salary",
            transaction_type="income",
            source="debit",
            timestamp=datetime.now()
        )
        
        def mock_get_db():
            yield mock_db
        
        # Override the get_current_user dependency
        def get_current_user_override():
            return mock_user
        
        app.dependency_overrides[get_current_user] = get_current_user_override
        
        try:
            # First, create a transaction
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.create_transaction_for_user", return_value=created_transaction):
                
                create_response = client.post("/transactions/submit", json={
                    "amount": 100.50,
                    "description": "Salary payment",
                    "category": "salary",
                    "transaction_type": "income",
                    "source": "debit"
                })
                
                assert create_response.status_code == 200
                created_data = create_response.json()
                assert created_data["amount"] == 100.50
                assert created_data["description"] == "Salary payment"
            
            # Then, retrieve all transactions (should include the created one)
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions", return_value=[created_transaction]):
                
                get_response = client.get("/transactions/get-all")
                
                assert get_response.status_code == 200
                retrieved_data = get_response.json()
                assert len(retrieved_data) == 1
                assert retrieved_data[0]["amount"] == 100.50
                assert retrieved_data[0]["description"] == "Salary payment"
        finally:
            app.dependency_overrides.clear()

    def test_invalid_token_affects_all_endpoints(self):
        """Test that invalid authentication affects all transaction endpoints"""
        from fastapi import HTTPException, status
        
        # Mock get_current_user to raise an HTTPException for invalid token
        def mock_invalid_token():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        app.dependency_overrides[get_current_user] = mock_invalid_token
        
        try:
            # Test submit endpoint
            response = client.post("/transactions/submit", json={
                "amount": 100.00,
                "description": "Test transaction",
                "category": "test",
                "transaction_type": "income",
                "source": "debit"
            })
            assert response.status_code == 401
            
            # Test get-all endpoint
            response = client.get("/transactions/get-all")
            assert response.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_different_users_have_isolated_data(self):
        """Test that different users have completely isolated transaction data"""
        mock_db = get_mock_db(user_exists=False)
        
        # First user
        user1 = User(username="user1", name="User One", hashed_password="hash1")
        user1.id = uuid.uuid4()
        user1.created_at = datetime.now()
        
        # Second user  
        user2 = User(username="user2", name="User Two", hashed_password="hash2")
        user2.id = uuid.uuid4()
        user2.created_at = datetime.now()
        
        # User 1's transactions
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
        
        # User 2's transactions
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
        
        # Test User 1
        def get_current_user_override_user1():
            return user1
        
        app.dependency_overrides[get_current_user] = get_current_user_override_user1
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions") as mock_get_transactions:
                
                mock_get_transactions.return_value = user1_transactions
                
                response = client.get("/transactions/get-all")
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["description"] == "User 1 transaction"
                assert data[0]["amount"] == 100.00
                
                # Verify it was called with user1's ID
                mock_get_transactions.assert_called_with(ANY, user_id=user1.id)
        finally:
            app.dependency_overrides.clear()
        
        # Test User 2
        def get_current_user_override_user2():
            return user2
        
        app.dependency_overrides[get_current_user] = get_current_user_override_user2
        
        try:
            with patch("app.routes.transactions.get_db", side_effect=mock_get_db), \
                 patch("app.routes.transactions.crud_transaction.get_transactions") as mock_get_transactions:
                
                mock_get_transactions.return_value = user2_transactions
                
                response = client.get("/transactions/get-all")
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["description"] == "User 2 transaction"
                assert data[0]["amount"] == 200.00
                
                # Verify it was called with user2's ID
                mock_get_transactions.assert_called_with(ANY, user_id=user2.id)
        finally:
            app.dependency_overrides.clear()
