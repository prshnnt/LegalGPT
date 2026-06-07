import logging
from typing import Optional, Dict, Any, List
from langchain_core.tools import tool

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@tool
def save_context_memory(
    key: str,
    value: str,
    metadata: Optional[Dict[str, Any]] = None,
    thread_id: Optional[int] = None,
    user_id: Optional[int] = None,
):
    """
    Save a context memory entry for the AI bot.

    This tool stores information in a persistent database that the AI can
    recall across messages within the same session.

    Args:
        key: Unique identifier for this memory (e.g., "user_preferences", "project_context")
        value: The actual memory content to store
        metadata: Optional additional structured data (tags, categories, etc.)
        thread_id: Optional chat thread ID for thread-scoped memory
        user_id: Optional user ID for user-scoped memory

    Returns:
        dict with confirmation and memory details
    """
    try:
        logger.info(
            "Saving context memory: key=%s, thread_id=%s, user_id=%s",
            key, thread_id, user_id
        )

        from app.db.session import SessionLocal
        from app.services.context_memory import create_or_update_context_memory
        from app.schemas.context_memory import ContextMemoryCreate

        db = SessionLocal()
        try:
            create_data = ContextMemoryCreate(
                key=key,
                value=value,
                metadata=metadata,
                thread_id=thread_id,
                user_id=user_id,
            )
            memory = create_or_update_context_memory(db, create_data)

            result = {
                "success": True,
                "message": f"Context memory '{key}' saved successfully",
                "memory_id": memory.id,
                "key": memory.key,
                "thread_id": memory.thread_id,
                "user_id": memory.user_id,
            }
            logger.info("Context memory saved with ID: %s", memory.id)
            return result
        finally:
            db.close()

    except Exception as e:
        logger.exception("Failed to save context memory '%s': %s", key, e)
        raise


@tool
def load_context_memory(
    key: str,
    thread_id: Optional[int] = None,
    user_id: Optional[int] = None,
):
    """
    Load a context memory entry by key.

    Args:
        key: The unique identifier for the memory
        thread_id: Optional thread ID to scope the lookup
        user_id: Optional user ID to scope the lookup

    Returns:
        dict with memory value and metadata, or found=False if not found
    """
    try:
        logger.info(
            "Loading context memory: key=%s, thread_id=%s, user_id=%s",
            key, thread_id, user_id
        )

        from app.db.session import SessionLocal
        from app.services.context_memory import get_context_memory, get_context_memory_by_thread, get_context_memory_by_user

        db = SessionLocal()
        try:
            if thread_id:
                memories = get_context_memory_by_thread(db, thread_id, key)
            elif user_id:
                memories = get_context_memory_by_user(db, user_id, key)
            else:
                memories = [get_context_memory(db, key)]

            memory = memories[0] if memories else None

            if memory:
                result = {
                    "found": True,
                    "key": memory.key,
                    "value": memory.value,
                    "metadata": memory.meta_data,
                    "created_at": memory.created_at.isoformat() if memory.created_at else None,
                    "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
                }
                logger.info("Context memory loaded: key=%s", key)
                return result
            else:
                result = {
                    "found": False,
                    "key": key,
                    "value": None,
                    "metadata": None,
                    "message": f"No context memory found for key: {key}",
                }
                logger.info("Context memory not found: key=%s", key)
                return result
        finally:
            db.close()

    except Exception as e:
        logger.exception("Failed to load context memory '%s': %s", key, e)
        raise


@tool
def delete_context_memory(
    key: str,
    thread_id: Optional[int] = None,
    user_id: Optional[int] = None,
):
    """
    Delete a context memory entry by key.

    Args:
        key: The unique identifier for the memory
        thread_id: Optional thread ID to scope the deletion
        user_id: Optional user ID to scope the deletion

    Returns:
        dict with deletion confirmation
    """
    try:
        logger.info(
            "Deleting context memory: key=%s, thread_id=%s, user_id=%s",
            key, thread_id, user_id
        )

        from app.db.session import SessionLocal
        from app.services.context_memory import (
            delete_context_memory,
            delete_context_memory_by_thread,
            delete_context_memory_by_user,
        )

        db = SessionLocal()
        try:
            if thread_id:
                deleted = delete_context_memory_by_thread(db, thread_id)
                message = f"Deleted {deleted} context memory(s) for thread {thread_id}"
            elif user_id:
                deleted = delete_context_memory_by_user(db, user_id)
                message = f"Deleted {deleted} context memory(s) for user {user_id}"
            else:
                deleted = delete_context_memory(db, key)
                message = (
                    f"Context memory '{key}' deleted successfully"
                    if deleted
                    else f"No context memory found for key: {key}"
                )

            logger.info("Context memory deleted: key=%s", key)
            return {
                "success": deleted,
                "message": message,
                "key": key,
            }
        finally:
            db.close()

    except Exception as e:
        logger.exception("Failed to delete context memory '%s': %s", key, e)
        raise


@tool
def list_context_memories(
    thread_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: int = 10,
):
    """
    List all context memories, optionally scoped by thread or user.

    Args:
        thread_id: Optional thread ID to filter memories
        user_id: Optional user ID to filter memories
        limit: Maximum number of memories to return (default: 10)

    Returns:
        dict with list of memories
    """
    try:
        logger.info(
            "Listing context memories: thread_id=%s, user_id=%s, limit=%d",
            thread_id, user_id, limit
        )

        from app.db.session import SessionLocal
        from app.services.context_memory import (
            list_all_context_memories,
            get_context_memory_by_thread,
            get_context_memory_by_user,
        )

        db = SessionLocal()
        try:
            if thread_id:
                memories = get_context_memory_by_thread(db, thread_id)
            elif user_id:
                memories = get_context_memory_by_user(db, user_id)
            else:
                memories = list_all_context_memories(db, limit)

            result = {
                "count": len(memories),
                "memories": [
                    {
                        "id": m.id,
                        "key": m.key,
                        "value": m.value,
                        "metadata": m.meta_data,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
                        "thread_id": m.thread_id,
                        "user_id": m.user_id,
                    }
                    for m in memories
                ],
            }
            logger.info("Retrieved %d context memories", len(memories))
            return result
        finally:
            db.close()

    except Exception as e:
        logger.exception("Failed to list context memories: %s", e)
        raise
