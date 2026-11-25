from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage


class ChatRepository:
    @staticmethod
    def create_session(db: Session, user_id: str, title: str = "New Conversation", dataset_id: Optional[str] = None) -> ChatSession:
        session = ChatSession(
            user_id=user_id,
            title=title,
            dataset_id=dataset_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_session(db: Session, session_id: str, user_id: Optional[str] = None) -> Optional[ChatSession]:
        query = db.query(ChatSession).filter(ChatSession.id == session_id)
        if user_id:
            query = query.filter(ChatSession.user_id == user_id)
        return query.first()

    @staticmethod
    def get_user_sessions(db: Session, user_id: str) -> List[ChatSession]:
        return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()

    @staticmethod
    def delete_session(db: Session, session_id: str, user_id: str) -> bool:
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
        if not session:
            return False
        db.delete(session)
        db.commit()
        return True

    @staticmethod
    def add_message(db: Session, session_id: str, role: str, content: str, metadata_json: Optional[str] = None) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            metadata_json=metadata_json
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_messages(db: Session, session_id: str) -> List[ChatMessage]:
        return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
