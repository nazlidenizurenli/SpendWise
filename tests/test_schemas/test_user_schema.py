import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.user import UserCreate, UserOut


class TestUserCreateSchema:
    """Test UserCreate schema validation"""
    
    def test_valid_user_creation(self):
        """Test creating a user with all valid fields"""
        user_in = UserCreate(
            username="testuser",
            password="Password123!",
            name="Test User"
        )
        assert user_in.model_dump() == {
            "username": "testuser", 
            "password": "Password123!", 
            "name": "Test User"
        }

    def test_valid_user_creation_with_special_characters(self):
        """Test creating user with valid special characters"""
        user_in = UserCreate(
            username="test_user123",
            password="MyP@ssw0rd!",
            name="John-Paul Smith"
        )
        assert user_in.username == "test_user123"
        assert user_in.password == "MyP@ssw0rd!"
        assert user_in.name == "John-Paul Smith"

    def test_valid_user_creation_minimum_length(self):
        """Test creating user with minimum allowed lengths"""
        user_in = UserCreate(
            username="abc",  # Minimum 3 chars
            password="A1!",  # Minimum requirements: letter, digit, special char
            name="A"  # Minimum 1 letter
        )
        assert user_in.username == "abc"
        assert user_in.password == "A1!"
        assert user_in.name == "A"

    def test_valid_user_creation_maximum_length(self):
        """Test creating user with maximum allowed lengths"""
        user_in = UserCreate(
            username="a" * 20,  # Maximum 20 chars
            password="Password123!",
            name="Very Long Name Here"
        )
        assert len(user_in.username) == 20
        assert user_in.password == "Password123!"


class TestUsernameValidation:
    """Test username validation rules"""
    
    def test_invalid_username_too_short(self):
        """Test username validation fails for too short username"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="ab",  # Too short (< 3 chars)
                password="Password123!",
                name="Test User"
            )
        errors = exc_info.value.errors()
        assert any("String should have at least 3 characters" in str(error) for error in errors)

    def test_invalid_username_too_long(self):
        """Test username validation fails for too long username"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="a" * 21,  # Too long (> 20 chars)
                password="Password123!",
                name="Test User"
            )
        errors = exc_info.value.errors()
        assert any("String should have at most 20 characters" in str(error) for error in errors)

    def test_invalid_username_special_characters(self):
        """Test username validation fails for invalid characters"""
        invalid_usernames = [
            "test@user",  # @ not allowed
            "test user",  # Space not allowed
            "test-user",  # Hyphen not allowed
            "test.user",  # Dot not allowed
            "test+user",  # Plus not allowed
        ]
        
        for invalid_username in invalid_usernames:
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(
                    username=invalid_username,
                    password="Password123!",
                    name="Test User"
                )
            errors = exc_info.value.errors()
            assert any("String should match pattern" in str(error) for error in errors)

    def test_invalid_username_no_letters(self):
        """Test username validation fails when no letters are present"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="123_",  # No letters
                password="Password123!",
                name="Test User"
            )
        errors = exc_info.value.errors()
        assert any("Username must contain at least one letter" in str(error) for error in errors)

    def test_valid_username_with_numbers_and_underscore(self):
        """Test that username with letters, numbers, and underscores is valid"""
        user_in = UserCreate(
            username="user123_test",
            password="Password123!",
            name="Test User"
        )
        assert user_in.username == "user123_test"


class TestPasswordValidation:
    """Test password validation rules"""
    
    def test_invalid_password_no_letters(self):
        """Test password validation fails when no letters are present"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                password="123!@#",  # No letters
                name="Test User"
            )
        errors = exc_info.value.errors()
        assert any("Password must contain at least one letter" in str(error) for error in errors)

    def test_invalid_password_no_digits(self):
        """Test password validation fails when no digits are present"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                password="Password!",  # No digits
                name="Test User"
            )
        errors = exc_info.value.errors()
        assert any("Password must contain at least one number" in str(error) for error in errors)

    def test_invalid_password_no_special_characters(self):
        """Test password validation fails when no special characters are present"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                password="Password123",  # No special characters
                name="Test User"
            )
        errors = exc_info.value.errors()
        assert any("Password must contain at least one special character" in str(error) for error in errors)

    def test_invalid_password_only_special_characters(self):
        """Test password validation fails when only special characters are present"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                username="testuser",
                password="!@#$%^&*()",  # Only special characters
                name="Test User"
            )
        errors = exc_info.value.errors()
        assert any("Password must contain at least one letter" in str(error) for error in errors)

    def test_valid_password_all_requirements(self):
        """Test that password with all requirements is valid"""
        valid_passwords = [
            "Password123!",
            "MyP@ssw0rd1",
            "Test123#",
            "Abc1!",
            "Hello2@World",
        ]
        
        for password in valid_passwords:
            user_in = UserCreate(
                username="testuser",
                password=password,
                name="Test User"
            )
            assert user_in.password == password

    def test_valid_password_all_special_characters(self):
        """Test password with all allowed special characters"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        password = f"Pass1{special_chars}"
        
        user_in = UserCreate(
            username="testuser",
            password=password,
            name="Test User"
        )
        assert user_in.password == password


class TestNameValidation:
    """Test name validation rules"""
    
    def test_invalid_name_no_letters(self):
        """Test name validation fails when no letters are present"""
        invalid_names = [
            "123",      # Only numbers
            "   ",      # Only spaces
            "---",      # Only hyphens
            "123 - ",   # Numbers, spaces, hyphens but no letters
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(
                    username="testuser",
                    password="Password123!",
                    name=invalid_name
                )
            errors = exc_info.value.errors()
            assert any("Name must contain at least one letter" in str(error) for error in errors)

    def test_invalid_name_special_characters(self):
        """Test name validation fails for invalid characters"""
        invalid_names = [
            "John@Doe",     # @ not allowed
            "John.Doe",     # . not allowed
            "John_Doe",     # _ not allowed
            "John+Doe",     # + not allowed
            "John123",      # Numbers not allowed
            "John!Doe",     # ! not allowed
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                UserCreate(
                    username="testuser",
                    password="Password123!",
                    name=invalid_name
                )
            errors = exc_info.value.errors()
            assert any("Name must only contain letters, spaces, and hyphens" in str(error) for error in errors)

    def test_valid_name_formats(self):
        """Test valid name formats"""
        valid_names = [
            "John",
            "John Doe",
            "John-Paul",
            "Mary Jane Smith",
            "Jean-Luc",
            "O Connor",  # Space instead of apostrophe
            "Van Der Berg",
            "a",  # Single letter
            "A B C D E F",  # Multiple spaces
            "Anne-Marie-Louise",  # Multiple hyphens
        ]
        
        for valid_name in valid_names:
            user_in = UserCreate(
                username="testuser",
                password="Password123!",
                name=valid_name
            )
            assert user_in.name == valid_name

    def test_valid_name_mixed_case(self):
        """Test name with mixed case letters"""
        user_in = UserCreate(
            username="testuser",
            password="Password123!",
            name="mCdONALD"
        )
        assert user_in.name == "mCdONALD"


class TestUserOutSchema:
    """Test UserOut schema"""
    
    def test_user_out_schema_valid(self):
        """Test UserOut schema with valid data"""
        user_data = {
            "username": "testuser",
            "name": "Test User",
            "created_at": datetime.now()
        }
        
        user_out = UserOut(**user_data)
        assert user_out.username == "testuser"
        assert user_out.name == "Test User"
        assert isinstance(user_out.created_at, datetime)

    def test_user_out_schema_missing_fields(self):
        """Test UserOut schema fails with missing required fields"""
        # Missing username
        with pytest.raises(ValidationError):
            UserOut(
                name="Test User",
                created_at=datetime.now()
            )
        
        # Missing name
        with pytest.raises(ValidationError):
            UserOut(
                username="testuser",
                created_at=datetime.now()
            )
        
        # Missing created_at
        with pytest.raises(ValidationError):
            UserOut(
                username="testuser",
                name="Test User"
            )


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_string_validation(self):
        """Test validation with empty strings"""
        with pytest.raises(ValidationError):
            UserCreate(
                username="",
                password="Password123!",
                name="Test User"
            )
        
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                password="",
                name="Test User"
            )
        
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                password="Password123!",
                name=""
            )

    def test_unicode_characters(self):
        """Test validation with unicode characters"""
        # Valid unicode letters in name
        user_in = UserCreate(
            username="testuser",
            password="Password123!",
            name="José María"
        )
        assert user_in.name == "José María"

    def test_whitespace_handling(self):
        """Test validation with various whitespace scenarios"""
        # Leading/trailing spaces in name should be preserved
        user_in = UserCreate(
            username="testuser",
            password="Password123!",
            name=" John Doe "
        )
        assert user_in.name == " John Doe "
        
        # Multiple spaces in name
        user_in = UserCreate(
            username="testuser",
            password="Password123!",
            name="John    Doe"
        )
        assert user_in.name == "John    Doe"

    def test_case_sensitivity(self):
        """Test that validation is case sensitive where appropriate"""
        # Username with mixed case
        user_in = UserCreate(
            username="TestUser123",
            password="Password123!",
            name="Test User"
        )
        assert user_in.username == "TestUser123"

    def test_complex_valid_scenarios(self):
        """Test complex but valid user creation scenarios"""
        complex_users = [
            {
                "username": "A1_",
                "password": "Z9!",
                "name": "X"
            },
            {
                "username": "user_underscore",
                "password": "VeryComplexP@ssw0rd123!",
                "name": "Jean-Paul Pierre-Marie"
            },
            {
                "username": "MixedCASE123",
                "password": "P@$$w0rd!",
                "name": "O Brien"
            }
        ]
        
        for user_data in complex_users:
            user_in = UserCreate(**user_data)
            assert user_in.username == user_data["username"]
            assert user_in.password == user_data["password"]
            assert user_in.name == user_data["name"]