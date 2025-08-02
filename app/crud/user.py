from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    db_user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        name=user_in.name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
