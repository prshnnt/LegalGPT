from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_threads = relationship("ChatThread", back_populates="user", cascade="all, delete-orphan")


class ChatThread(Base):
    __tablename__ = "chat_threads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat_threads")
    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    checkpoints = relationship("ChatCheckpoint", back_populates="thread", cascade="all, delete-orphan")


class MessageRole(enum.Enum):
    HUMAN = "human"
    AI = "ai"
    TOOL = "tool"


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("chat_threads.id"), nullable=False)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # For tool calls
    tool_name = Column(String(100), nullable=True)
    tool_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    thread = relationship("ChatThread", back_populates="messages")


class ChatCheckpoint(Base):
    """Store LangGraph checkpoints for conversation state"""
    __tablename__ = "chat_checkpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("chat_threads.id"), nullable=False)
    checkpoint_ns = Column(String(255),default="",index=True)
    parent_checkpoint_id = Column(String(255),nullable=True)
    checkpoint_data = Column(JSON, nullable=False)
    checkpoint_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    thread = relationship("ChatThread", back_populates="checkpoints")
