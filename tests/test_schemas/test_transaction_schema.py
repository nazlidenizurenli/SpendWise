import pytest
from pydantic import ValidationError
from datetime import datetime
from uuid import uuid4
from app.schemas.transaction import TransactionCreate, TransactionOut, TransactionBase


class TestTransactionBaseSchema:
    """Test TransactionBase schema validation"""
    
    def test_valid_transaction_creation_income_debit(self):
        """Test creating a valid income transaction from debit"""
        transaction = TransactionBase(
            amount=100.50,
            description="Salary payment",
            category="salary",
            transaction_type="income",
            source="debit"
        )
        assert transaction.amount == 100.50
        assert transaction.description == "Salary payment"
        assert transaction.category == "salary"
        assert transaction.transaction_type == "income"
        assert transaction.source == "debit"
        assert transaction.timestamp is None

    def test_valid_transaction_creation_expense_credit(self):
        """Test creating a valid expense transaction from credit"""
        transaction = TransactionBase(
            amount=50.25,
            description="Grocery shopping",
            category="food",
            transaction_type="expense",
            source="credit"
        )
        assert transaction.amount == 50.25
        assert transaction.description == "Grocery shopping"
        assert transaction.category == "food"
        assert transaction.transaction_type == "expense"
        assert transaction.source == "credit"

    def test_valid_transaction_creation_expense_debit_negative(self):
        """Test creating a valid expense transaction from debit with negative amount"""
        transaction = TransactionBase(
            amount=-75.00,
            description="ATM withdrawal",
            category="cash",
            transaction_type="expense",
            source="debit"
        )
        assert transaction.amount == -75.00
        assert transaction.description == "ATM withdrawal"
        assert transaction.transaction_type == "expense"
        assert transaction.source == "debit"

    def test_valid_transaction_creation_income_savings(self):
        """Test creating a valid income transaction from savings"""
        transaction = TransactionBase(
            amount=200.00,
            description="Interest earned",
            category="interest",
            transaction_type="income",
            source="savings"
        )
        assert transaction.amount == 200.00
        assert transaction.description == "Interest earned"
        assert transaction.transaction_type == "income"
        assert transaction.source == "savings"

    def test_valid_transaction_with_timestamp(self):
        """Test creating transaction with custom timestamp"""
        custom_time = datetime(2024, 1, 15, 10, 30, 0)
        transaction = TransactionBase(
            amount=123.45,
            description="Test transaction",
            category="test",
            transaction_type="income",
            source="debit",
            timestamp=custom_time
        )
        assert transaction.timestamp == custom_time

    def test_valid_transaction_with_none_category(self):
        """Test creating transaction with None category"""
        transaction = TransactionBase(
            amount=100.00,
            description="Uncategorized transaction",
            category=None,
            transaction_type="income",
            source="debit"
        )
        assert transaction.category is None


class TestTransactionAmountValidation:
    """Test transaction amount validation rules"""
    
    def test_invalid_amount_zero(self):
        """Test that zero amount is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=0,
                description="Test transaction",
                category="test",
                transaction_type="income",
                source="debit"
            )
        errors = exc_info.value.errors()
        assert any("Amount must be non-zero" in str(error) for error in errors)

    def test_invalid_amount_zero_float(self):
        """Test that zero float amount is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=0.0,
                description="Test transaction",
                category="test",
                transaction_type="income",
                source="debit"
            )
        errors = exc_info.value.errors()
        assert any("Amount must be non-zero" in str(error) for error in errors)

    def test_valid_amount_positive(self):
        """Test that positive amounts are accepted"""
        transaction = TransactionBase(
            amount=0.01,  # Minimum positive amount
            description="Test transaction",
            category="test",
            transaction_type="income",
            source="debit"
        )
        assert transaction.amount == 0.01

    def test_valid_amount_negative(self):
        """Test that negative amounts are accepted"""
        transaction = TransactionBase(
            amount=-0.01,  # Minimum negative amount
            description="Test transaction",
            category="test",
            transaction_type="expense",
            source="debit"
        )
        assert transaction.amount == -0.01

    def test_valid_amount_large_positive(self):
        """Test that large positive amounts are accepted"""
        transaction = TransactionBase(
            amount=999999.99,
            description="Large transaction",
            category="test",
            transaction_type="income",
            source="debit"
        )
        assert transaction.amount == 999999.99

    def test_valid_amount_large_negative(self):
        """Test that large negative amounts are accepted"""
        transaction = TransactionBase(
            amount=-999999.99,
            description="Large expense",
            category="test",
            transaction_type="expense",
            source="debit"
        )
        assert transaction.amount == -999999.99


class TestTransactionDescriptionValidation:
    """Test transaction description validation rules"""
    
    def test_invalid_description_empty_string(self):
        """Test that empty description is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=100.00,
                description="",
                category="test",
                transaction_type="income",
                source="debit"
            )
        errors = exc_info.value.errors()
        assert any("Description cannot be empty" in str(error) for error in errors)

    def test_invalid_description_whitespace_only(self):
        """Test that whitespace-only description is rejected"""
        whitespace_descriptions = [
            " ",
            "  ",
            "\t",
            "\n",
            "   \t   \n   "
        ]
        
        for desc in whitespace_descriptions:
            with pytest.raises(ValidationError) as exc_info:
                TransactionBase(
                    amount=100.00,
                    description=desc,
                    category="test",
                    transaction_type="income",
                    source="debit"
                )
            errors = exc_info.value.errors()
            assert any("Description cannot be empty" in str(error) for error in errors)

    def test_valid_description_with_leading_trailing_spaces(self):
        """Test that description with leading/trailing spaces is valid after strip"""
        transaction = TransactionBase(
            amount=100.00,
            description="  Valid description  ",
            category="test",
            transaction_type="income",
            source="debit"
        )
        assert transaction.description == "  Valid description  "

    def test_valid_description_single_character(self):
        """Test that single character description is valid"""
        transaction = TransactionBase(
            amount=100.00,
            description="A",
            category="test",
            transaction_type="income",
            source="debit"
        )
        assert transaction.description == "A"

    def test_valid_description_long_text(self):
        """Test that long description is valid"""
        long_desc = "A" * 1000  # Very long description
        transaction = TransactionBase(
            amount=100.00,
            description=long_desc,
            category="test",
            transaction_type="income",
            source="debit"
        )
        assert transaction.description == long_desc

    def test_valid_description_special_characters(self):
        """Test that description with special characters is valid"""
        special_desc = "Payment for #123 - $50 (50% off) @store"
        transaction = TransactionBase(
            amount=50.00,
            description=special_desc,
            category="shopping",
            transaction_type="expense",
            source="credit"
        )
        assert transaction.description == special_desc


class TestTransactionTypeValidation:
    """Test transaction type validation rules"""
    
    def test_valid_type_income(self):
        """Test that 'income' type is valid"""
        transaction = TransactionBase(
            amount=100.00,
            description="Test income",
            category="test",
            transaction_type="income",
            source="debit"
        )
        assert transaction.transaction_type == "income"

    def test_valid_type_expense(self):
        """Test that 'expense' type is valid"""
        transaction = TransactionBase(
            amount=100.00,
            description="Test expense",
            category="test",
            transaction_type="expense",
            source="credit"
        )
        assert transaction.transaction_type == "expense"

    def test_invalid_type_other_values(self):
        """Test that invalid type values are rejected"""
        invalid_types = [
            "transfer",
            "payment",
            "withdrawal",
            "deposit",
            "INCOME",  # Case sensitive
            "EXPENSE",  # Case sensitive
            "",
            None
        ]
        
        for invalid_type in invalid_types:
            with pytest.raises(ValidationError):
                TransactionBase(
                    amount=100.00,
                    description="Test transaction",
                    category="test",
                    type=invalid_type,
                    source="debit"
                )


class TestTransactionSourceValidation:
    """Test transaction source validation rules"""
    
    def test_valid_source_credit(self):
        """Test that 'credit' source is valid"""
        transaction = TransactionBase(
            amount=100.00,
            description="Credit transaction",
            category="test",
            transaction_type="expense",
            source="credit"
        )
        assert transaction.source == "credit"

    def test_valid_source_debit(self):
        """Test that 'debit' source is valid"""
        transaction = TransactionBase(
            amount=100.00,
            description="Debit transaction",
            category="test",
            transaction_type="income",
            source="debit"
        )
        assert transaction.source == "debit"

    def test_valid_source_savings(self):
        """Test that 'savings' source is valid"""
        transaction = TransactionBase(
            amount=100.00,
            description="Savings transaction",
            category="test",
            transaction_type="income",
            source="savings"
        )
        assert transaction.source == "savings"

    def test_invalid_source_other_values(self):
        """Test that invalid source values are rejected"""
        invalid_sources = [
            "cash",
            "check",
            "transfer",
            "CREDIT",  # Case sensitive
            "DEBIT",   # Case sensitive
            "SAVINGS", # Case sensitive
            "",
            None
        ]
        
        for invalid_source in invalid_sources:
            with pytest.raises(ValidationError):
                TransactionBase(
                    amount=100.00,
                    description="Test transaction",
                    category="test",
                    transaction_type="income",
                    source=invalid_source
                )


class TestTransactionBusinessLogicValidation:
    """Test transaction business logic validation rules"""
    
    def test_valid_credit_transaction_positive_expense(self):
        """Test valid credit transaction: positive amount, expense type"""
        transaction = TransactionBase(
            amount=100.00,
            description="Credit card purchase",
            category="shopping",
            transaction_type="expense",
            source="credit"
        )
        assert transaction.amount == 100.00
        assert transaction.transaction_type == "expense"
        assert transaction.source == "credit"

    def test_invalid_credit_transaction_negative_amount(self):
        """Test that credit transactions with negative amounts are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=-100.00,
                description="Invalid credit transaction",
                category="test",
                transaction_type="expense",
                source="credit"
            )
        errors = exc_info.value.errors()
        assert any("Credit transactions must have a positive amount" in str(error) for error in errors)

    def test_invalid_credit_transaction_income_type(self):
        """Test that credit transactions with income type are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=100.00,
                description="Invalid credit income",
                category="test",
                transaction_type="income",
                source="credit"
            )
        errors = exc_info.value.errors()
        assert any("Credit transactions must be type 'expense'" in str(error) for error in errors)

    def test_valid_debit_transaction_positive_income(self):
        """Test valid debit transaction: positive amount, income type"""
        transaction = TransactionBase(
            amount=100.00,
            description="Salary deposit",
            category="salary",
            transaction_type="income",
            source="debit"
        )
        assert transaction.amount == 100.00
        assert transaction.transaction_type == "income"
        assert transaction.source == "debit"

    def test_valid_debit_transaction_negative_expense(self):
        """Test valid debit transaction: negative amount, expense type"""
        transaction = TransactionBase(
            amount=-50.00,
            description="ATM withdrawal",
            category="cash",
            transaction_type="expense",
            source="debit"
        )
        assert transaction.amount == -50.00
        assert transaction.transaction_type == "expense"
        assert transaction.source == "debit"

    def test_invalid_debit_transaction_positive_expense(self):
        """Test that debit transactions with positive amount and expense type are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=100.00,
                description="Invalid debit expense",
                category="test",
                transaction_type="expense",
                source="debit"
            )
        errors = exc_info.value.errors()
        assert any("Positive amounts from debit/savings must be income" in str(error) for error in errors)

    def test_invalid_debit_transaction_negative_income(self):
        """Test that debit transactions with negative amount and income type are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=-100.00,
                description="Invalid debit income",
                category="test",
                transaction_type="income",
                source="debit"
            )
        errors = exc_info.value.errors()
        assert any("Negative amounts from debit/savings must be expense" in str(error) for error in errors)

    def test_valid_savings_transaction_positive_income(self):
        """Test valid savings transaction: positive amount, income type"""
        transaction = TransactionBase(
            amount=500.00,
            description="Interest earned",
            category="interest",
            transaction_type="income",
            source="savings"
        )
        assert transaction.amount == 500.00
        assert transaction.transaction_type == "income"
        assert transaction.source == "savings"

    def test_valid_savings_transaction_negative_expense(self):
        """Test valid savings transaction: negative amount, expense type"""
        transaction = TransactionBase(
            amount=-200.00,
            description="Savings withdrawal",
            category="withdrawal",
            transaction_type="expense",
            source="savings"
        )
        assert transaction.amount == -200.00
        assert transaction.transaction_type == "expense"
        assert transaction.source == "savings"

    def test_invalid_savings_transaction_positive_expense(self):
        """Test that savings transactions with positive amount and expense type are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=100.00,
                description="Invalid savings expense",
                category="test",
                transaction_type="expense",
                source="savings"
            )
        errors = exc_info.value.errors()
        assert any("Positive amounts from debit/savings must be income" in str(error) for error in errors)

    def test_invalid_savings_transaction_negative_income(self):
        """Test that savings transactions with negative amount and income type are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=-100.00,
                description="Invalid savings income",
                category="test",
                transaction_type="income",
                source="savings"
            )
        errors = exc_info.value.errors()
        assert any("Negative amounts from debit/savings must be expense" in str(error) for error in errors)


class TestTransactionCreateSchema:
    """Test TransactionCreate schema (inherits from TransactionBase)"""
    
    def test_transaction_create_inherits_all_validation(self):
        """Test that TransactionCreate inherits all validation from TransactionBase"""
        # Test valid creation
        transaction = TransactionCreate(
            amount=100.00,
            description="Test transaction",
            category="test",
            transaction_type="income",
            source="debit"
        )
        assert isinstance(transaction, TransactionBase)
        assert transaction.amount == 100.00

        # Test invalid creation (should raise same errors as TransactionBase)
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                amount=0,  # Invalid: zero amount
                description="Test transaction",
                category="test",
                transaction_type="income",
                source="debit"
            )
        errors = exc_info.value.errors()
        assert any("Amount must be non-zero" in str(error) for error in errors)

    def test_transaction_create_business_logic_validation(self):
        """Test that TransactionCreate applies business logic validation"""
        # Test invalid credit transaction
        with pytest.raises(ValidationError) as exc_info:
            TransactionCreate(
                amount=100.00,
                description="Invalid credit",
                category="test",
                transaction_type="income",  # Invalid for credit
                source="credit"
            )
        errors = exc_info.value.errors()
        assert any("Credit transactions must be type 'expense'" in str(error) for error in errors)


class TestTransactionOutSchema:
    """Test TransactionOut schema"""
    
    def test_valid_transaction_out_creation(self):
        """Test creating a valid TransactionOut object"""
        transaction_id = uuid4()
        user_id = uuid4()
        timestamp = datetime.now()
        
        transaction = TransactionOut(
            id=transaction_id,
            user_id=user_id,
            amount=100.50,
            description="Test transaction",
            category="test",
            transaction_type="income",
            source="debit",
            timestamp=timestamp
        )
        
        assert transaction.id == transaction_id
        assert transaction.user_id == user_id
        assert transaction.amount == 100.50
        assert transaction.description == "Test transaction"
        assert transaction.category == "test"
        assert transaction.transaction_type == "income"
        assert transaction.source == "debit"
        assert transaction.timestamp == timestamp

    def test_transaction_out_missing_required_fields(self):
        """Test that TransactionOut requires all fields"""
        # Missing id
        with pytest.raises(ValidationError):
            TransactionOut(
                user_id=uuid4(),
                amount=100.00,
                description="Test",
                category="test",
                transaction_type="income",
                source="debit",
                timestamp=datetime.now()
            )

        # Missing user_id
        with pytest.raises(ValidationError):
            TransactionOut(
                id=uuid4(),
                amount=100.00,
                description="Test",
                category="test",
                transaction_type="income",
                source="debit",
                timestamp=datetime.now()
            )

        # Missing timestamp
        with pytest.raises(ValidationError):
            TransactionOut(
                id=uuid4(),
                user_id=uuid4(),
                amount=100.00,
                description="Test",
                category="test",
                transaction_type="income",
                source="debit"
            )

    def test_transaction_out_inherits_validation(self):
        """Test that TransactionOut inherits validation from TransactionBase"""
        # Test that business logic validation still applies
        with pytest.raises(ValidationError) as exc_info:
            TransactionOut(
                id=uuid4(),
                user_id=uuid4(),
                amount=-100.00,  # Invalid for credit
                description="Test transaction",
                category="test",
                transaction_type="expense",
                source="credit",
                timestamp=datetime.now()
            )
        errors = exc_info.value.errors()
        assert any("Credit transactions must have a positive amount" in str(error) for error in errors)

    def test_transaction_out_from_attributes_config(self):
        """Test that TransactionOut has proper config for ORM conversion"""
        # This tests the Config class
        assert hasattr(TransactionOut, 'model_config') or hasattr(TransactionOut, 'Config')


class TestTransactionEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_transaction_with_very_small_amounts(self):
        """Test transactions with very small amounts"""
        # Test very small positive amount
        transaction = TransactionBase(
            amount=0.001,
            description="Very small transaction",
            category="test",
            transaction_type="income",
            source="debit"
        )
        assert transaction.amount == 0.001

        # Test very small negative amount
        transaction = TransactionBase(
            amount=-0.001,
            description="Very small expense",
            category="test",
            transaction_type="expense",
            source="debit"
        )
        assert transaction.amount == -0.001

    def test_transaction_with_decimal_precision(self):
        """Test transactions with various decimal precisions"""
        amounts = [
            123.456789,
            0.123456789,
            -99.999999,
            1000000.01,
            -1000000.99
        ]
        
        for amount in amounts:
            transaction = TransactionBase(
                amount=amount,
                description="Precision test",
                category="test",
                transaction_type="income" if amount > 0 else "expense",
                source="debit"
            )
            assert transaction.amount == amount

    def test_transaction_category_edge_cases(self):
        """Test category field edge cases"""
        # Empty string category (should be valid as it's Optional)
        transaction = TransactionBase(
            amount=100.00,
            description="No category",
            category="",
            transaction_type="income",
            source="debit"
        )
        assert transaction.category == ""

        # Very long category
        long_category = "A" * 1000
        transaction = TransactionBase(
            amount=100.00,
            description="Long category test",
            category=long_category,
            transaction_type="income",
            source="debit"
        )
        assert transaction.category == long_category

    def test_transaction_description_unicode(self):
        """Test description with unicode characters"""
        unicode_descriptions = [
            "Café payment €50",
            "Müller & Co. ßäöü",
            "Payment: 支付宝",
            "🏪 Store purchase 💳",
            "Москва магазин"
        ]
        
        for desc in unicode_descriptions:
            transaction = TransactionBase(
                amount=50.00,
                description=desc,
                category="international",
                transaction_type="expense",
                source="credit"
            )
            assert transaction.description == desc

    def test_real_world_transaction_scenarios(self):
        """Test realistic transaction scenarios"""
        real_transactions = [
            {
                "amount": 2500.00,
                "description": "Monthly salary",
                "category": "salary",
                "transaction_type": "income",
                "source": "debit"
            },
            {
                "amount": 89.99,
                "description": "Amazon Prime subscription",
                "category": "subscription",
                "transaction_type": "expense",
                "source": "credit"
            },
            {
                "amount": -150.00,
                "description": "ATM cash withdrawal",
                "category": "cash",
                "transaction_type": "expense",
                "source": "debit"
            },
            {
                "amount": 12.50,
                "description": "Savings account interest",
                "category": "interest",
                "transaction_type": "income",
                "source": "savings"
            },
            {
                "amount": -1000.00,
                "description": "Investment withdrawal",
                "category": "investment",
                "transaction_type": "expense",
                "source": "savings"
            }
        ]
        
        for tx_data in real_transactions:
            transaction = TransactionBase(**tx_data)
            for key, value in tx_data.items():
                assert getattr(transaction, key) == value


class TestTransactionIntegration:
    """Test integration scenarios and complex validation combinations"""
    
    def test_multiple_validation_errors(self):
        """Test that multiple validation errors are captured"""
        with pytest.raises(ValidationError) as exc_info:
            TransactionBase(
                amount=0,  # Invalid: zero amount
                description="",  # Invalid: empty description
                category="test",
                transaction_type="invalid_type",  # Invalid: not in literal
                source="credit"
            )
        
        errors = exc_info.value.errors()
        # Should have multiple validation errors
        assert len(errors) >= 2
        error_messages = [str(error) for error in errors]
        assert any("Amount must be non-zero" in msg for msg in error_messages)
        assert any("Description cannot be empty" in msg for msg in error_messages)

    def test_model_serialization(self):
        """Test that transactions can be properly serialized"""
        transaction = TransactionBase(
            amount=123.45,
            description="Test transaction",
            category="test",
            transaction_type="income",
            source="debit",
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        # Test model_dump
        data = transaction.model_dump()
        assert data["amount"] == 123.45
        assert data["description"] == "Test transaction"
        assert data["category"] == "test"
        assert data["transaction_type"] == "income"
        assert data["source"] == "debit"
        assert isinstance(data["timestamp"], datetime)

    def test_transaction_round_trip(self):
        """Test creating transaction from dict and back to dict"""
        original_data = {
            "amount": 456.78,
            "description": "Round trip test",
            "category": "test",
            "transaction_type": "expense",
            "source": "credit",
            "timestamp": datetime(2024, 1, 15, 14, 45, 0)
        }
        
        # Create transaction from dict
        transaction = TransactionBase(**original_data)
        
        # Convert back to dict
        result_data = transaction.model_dump()
        
        # Compare (excluding timestamp precision issues)
        for key, value in original_data.items():
            assert result_data[key] == value
