"""Service layer for chat operations."""

from sqlalchemy.orm import Session
from typing import Optional, List, Tuple

from app.models.database import (
    ChatThread,
    ChatMessage,
    User,
    MessageRole,
)


class ChatService:
    """Service for chat thread operations."""

    @staticmethod
    def create_chat(
        db: Session,
        user: User,
        title: Optional[str] = None,
    ) -> ChatThread:
        """Create a new chat thread for a user."""
        chat = ChatThread(
            user_id=user.id,
            title=title or "New Chat",
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat
    @staticmethod
    def get_chat_by_id(
        db: Session,
        chat_id: int,
        user_id: int,
    ) -> Optional[ChatThread]:
        """Get a chat thread by ID (scoped to user)."""
        return (
            db.query(ChatThread)
            .filter(
                ChatThread.id == chat_id,
                ChatThread.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def list_chats(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ChatThread]:
        """List chat threads for a user."""
        return (
            db.query(ChatThread)
            .filter(ChatThread.user_id == user_id)
            .order_by(ChatThread.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_chat(
        db: Session,
        chat_id: int,
        user_id: int,
    ) -> bool:
        """Delete a chat thread and all related data."""
        chat = ChatService.get_chat_by_id(db, chat_id, user_id)
        if not chat:
            return False

        db.delete(chat)
        db.commit()
        return True


class MessageService:
    """Service for chat message operations."""

    @staticmethod
    def create_message(
        db: Session,
        thread_id: int,
        role: MessageRole,
        content: str,
        tool_name: Optional[str] = None,
        tool_data: Optional[dict] = None,
    ) -> ChatMessage:
        """Create a new message in a chat thread."""
        message = ChatMessage(
            thread_id=thread_id,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_data=tool_data,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_messages_by_thread_id(
        db: Session,
        thread_id: int,
    ) -> List[ChatMessage]:
        """Get all messages for a chat thread."""
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

    @staticmethod
    def get_chat_history(
        db: Session,
        chat_id: int,
        user_id: int,
    ) -> Tuple[Optional[ChatThread], List[ChatMessage]]:
        """Get a chat thread and its messages."""
        chat = ChatService.get_chat_by_id(db, chat_id, user_id)
        if not chat:
            return None, []

        messages = MessageService.get_messages_by_thread_id(db, chat.id)
        return chat, messages
