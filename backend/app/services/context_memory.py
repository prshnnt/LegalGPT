from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.database import ContextMemory
from app.schemas.context_memory import ContextMemoryCreate


def get_context_memory(db: Session, key: str) -> Optional[ContextMemory]:
    """Get context memory by key."""
    return db.query(ContextMemory).filter(ContextMemory.key == key).first()


def get_context_memory_by_thread(
    db: Session, thread_id: int, key: Optional[str] = None
) -> List[ContextMemory]:
    """Get context memories for a specific thread."""
    query = db.query(ContextMemory).filter(ContextMemory.thread_id == thread_id)
    if key:
        query = query.filter(ContextMemory.key == key)
    return query.all()


def get_context_memory_by_user(
    db: Session, user_id: int, key: Optional[str] = None
) -> List[ContextMemory]:
    """Get context memories for a specific user."""
    query = db.query(ContextMemory).filter(ContextMemory.user_id == user_id)
    if key:
        query = query.filter(ContextMemory.key == key)
    return query.all()


def create_or_update_context_memory(
    db: Session, create_data: ContextMemoryCreate
) -> ContextMemory:
    """Create new or update existing context memory."""
    existing = db.query(ContextMemory).filter(
        ContextMemory.key == create_data.key
    ).first()

    if existing:
        # Update existing
        if create_data.value is not None:
            existing.value = create_data.value
        if create_data.metadata is not None:
            existing.meta_data = create_data.metadata
        if create_data.thread_id is not None:
            existing.thread_id = create_data.thread_id
        if create_data.user_id is not None:
            existing.user_id = create_data.user_id
        existing.updated_at = datetime.utcnow()
    else:
        # Create new
        new_memory = ContextMemory(
            key=create_data.key,
            value=create_data.value,
            meta_data=create_data.metadata,
            thread_id=create_data.thread_id,
            user_id=create_data.user_id,
        )
        db.add(new_memory)

    db.commit()
    db.refresh(new_memory if not existing else existing)
    return new_memory if not existing else existing


def delete_context_memory(db: Session, key: str) -> bool:
    """Delete context memory by key."""
    memory = db.query(ContextMemory).filter(ContextMemory.key == key).first()
    if memory:
        db.delete(memory)
        db.commit()
        return True
    return False


def delete_context_memory_by_thread(db: Session, thread_id: int) -> int:
    """Delete all context memories for a specific thread."""
    count = db.query(ContextMemory).filter(
        ContextMemory.thread_id == thread_id
    ).delete()
    db.commit()
    return count


def delete_context_memory_by_user(db: Session, user_id: int) -> int:
    """Delete all context memories for a specific user."""
    count = db.query(ContextMemory).filter(
        ContextMemory.user_id == user_id
    ).delete()
    db.commit()
    return count


def list_all_context_memories(db: Session, limit: int = 100) -> List[ContextMemory]:
    """List all context memories with optional limit."""
    return db.query(ContextMemory).order_by(ContextMemory.updated_at.desc()).limit(limit).all()
