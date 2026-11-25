from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def create(db: Session, name: str, email: str, hashed_password: str) -> User:
        user = User(
            name=name.strip(),
            email=email.lower().strip(),
            hashed_password=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
