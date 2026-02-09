from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# =========================
# Auth Schemas (auth router)
# =========================

class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


# =========================
# Chat Thread Schemas
# =========================

class ChatThreadCreate(BaseModel):
    title: Optional[str] = "New Chat"


class ChatThreadResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================
# Message Schemas
# =========================

class MessageRoleEnum(str, Enum):
    HUMAN = "human"
    AI = "ai"
    TOOL = "tool"


class ChatMessageCreate(BaseModel):
    """
    Incoming user message.
    Role is ALWAYS HUMAN in the router.
    """
    content: str


class ChatMessageResponse(BaseModel):
    id: int
    role: MessageRoleEnum
    content: str
    tool_name: Optional[str] = None
    tool_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    thread: ChatThreadResponse
    messages: List[ChatMessageResponse]

    class Config:
        from_attributes = True


# =========================
# Streaming Schemas
# (LEFT UNCHANGED ON PURPOSE)
# =========================

class StreamEventType(str, Enum):
    MESSAGE_START = "message_start"
    CONTENT_BLOCK_START = "content_block_start"
    CONTENT_BLOCK_DELTA = "content_block_delta"
    CONTENT_BLOCK_END = "content_block_end"
    TOOL_USE_START = "tool_use_start"
    TOOL_USE_END = "tool_use_end"
    MESSAGE_END = "message_end"
    ERROR = "error"


class StreamEvent(BaseModel):
    type: StreamEventType
    data: Any


class StreamChunk(BaseModel):
    """A chunk of streamed response."""
    type: str = Field(..., description="Type of chunk: 'start', 'content', 'tool_call', 'tool_result', 'end', 'error'")
    content: Optional[str] = Field(None, description="Content for content chunks")
    tool_name: Optional[str] = Field(None, description="Tool name for tool_call chunks")
    tool_input: Optional[Dict[str, Any]] = Field(None, description="Tool input for tool_call chunks")
    tool_output: Optional[str] = Field(None, description="Tool output for tool_result chunks")
    checkpointer_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    session_id: Optional[str] = Field(None, description="Session ID")
