from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    @staticmethod
    def register_user(db: Session, name: str, email: str, password: str) -> User:
        existing = UserRepository.get_by_email(db, email)
        if existing:
            raise ValueError("A user with this email already exists.")

        hashed = hash_password(password)
        return UserRepository.create(db, name=name, email=email, hashed_password=hashed)

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = UserRepository.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def generate_token_for_user(user: User) -> str:
        return create_access_token(subject=user.id)
