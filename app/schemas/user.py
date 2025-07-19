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


class UserOut(BaseModel):
    id: UUID
    username: str
    name: str
    created_at: datetime

    class Config:
        orm_mode = True
