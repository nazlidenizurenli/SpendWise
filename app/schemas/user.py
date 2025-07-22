from pydantic import BaseModel, constr, field_validator
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    password: str
    name: str

    @field_validator("username")
    @classmethod
    def username_must_contain_letter(cls, v: str) -> str:
        if not any(char.isalpha() for char in v):
            raise ValueError("Username must contain at least one letter.")
        return v
    
    @field_validator("password")
    @classmethod
    def password_must_contain_letter(cls, v: str) -> str:
        if not any(char.isalpha() for char in v):
            raise ValueError("Password must contain at least one letter.")
        
        # Password must contain at least one number and one special character
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number.")
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in v):
            raise ValueError("Password must contain at least one special character.")
        return v
    
    @field_validator("name")
    @classmethod
    def name_must_contain_letter(cls, v: str) -> str:
        if not any(char.isalpha() for char in v):
            raise ValueError("Name must contain at least one letter.")
        
        # Check that name only contains letters, spaces, and hyphens
        if not all(char.isalpha() or char == ' ' or char == '-' for char in v):
            raise ValueError("Name must only contain letters, spaces, and hyphens.")
        return v


class UserOut(BaseModel):
    username: str
    name: str
    created_at: datetime

    class Config:
        orm_mode = True
