from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# =========================
# Context Memory Schemas
# =========================

class ContextMemoryCreate(BaseModel):
    """Schema for creating/updating context memory."""
    key: str = Field(..., description="Unique key for the memory entry")
    value: Optional[str] = Field(None, description="Memory value/content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    thread_id: Optional[int] = Field(None, description="Associated chat thread ID")
    user_id: Optional[int] = Field(None, description="Associated user ID")


class ContextMemoryResponse(BaseModel):
    """Schema for context memory API response."""
    id: int
    key: str
    value: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    thread_id: Optional[int]
    user_id: Optional[int]

    class Config:
        from_attributes = True


class ContextMemoryGetResponse(BaseModel):
    """Schema for getting memory by key."""
    key: str
    value: Optional[str]
    metadata: Optional[Dict[str, Any]]
    found: bool = True

    class Config:
        from_attributes = True


class ContextMemoryDeleteResponse(BaseModel):
    """Schema for delete response."""
    success: bool
    key: str
    message: str
