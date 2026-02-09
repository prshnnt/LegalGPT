from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.database import User, ChatThread, ChatMessage, MessageRole
from app.schemas.chat import (
    ChatThreadCreate, ChatThreadResponse, ChatMessageCreate,
    ChatMessageResponse, ChatHistoryResponse
)
from app.api.dependencies import get_current_user
from app.services.agent import deep_agent_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/threads", response_model=ChatThreadResponse, status_code=status.HTTP_201_CREATED)
def create_thread(
    thread_data: ChatThreadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat thread."""
    new_thread = ChatThread(
        user_id=current_user.id,
        title=thread_data.title
    )
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)
    
    return new_thread


@router.get("/threads", response_model=List[ChatThreadResponse])
def get_threads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat threads for current user."""
    threads = db.query(ChatThread).filter(
        ChatThread.user_id == current_user.id
    ).order_by(ChatThread.updated_at.desc()).all()
    
    return threads


@router.get("/threads/{thread_id}", response_model=ChatHistoryResponse)
def get_thread_history(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for a specific thread."""
    thread = db.query(ChatThread).filter(
        ChatThread.id == thread_id,
        ChatThread.user_id == current_user.id
    ).first()
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat thread not found"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.thread_id == thread_id
    ).order_by(ChatMessage.created_at).all()
    
    return {
        "thread": thread,
        "messages": messages
    }


@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat thread."""
    thread = db.query(ChatThread).filter(
        ChatThread.id == thread_id,
        ChatThread.user_id == current_user.id
    ).first()
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat thread not found"
        )
    
    db.delete(thread)
    db.commit()
    
    return None


@router.post("/threads/{thread_id}/messages")
async def send_message(
    thread_id: int,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message and stream AI response.
    Returns Server-Sent Events (SSE) stream.
    """
    # Verify thread ownership
    thread = db.query(ChatThread).filter(
        ChatThread.id == thread_id,
        ChatThread.user_id == current_user.id
    ).first()
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat thread not found"
        )
    
    # Save user message
    user_message = ChatMessage(
        thread_id=thread_id,
        role=MessageRole.HUMAN,
        content=message_data.content
    )
    db.add(user_message)
    db.commit()
    
    # Get conversation history
    messages = db.query(ChatMessage).filter(
        ChatMessage.thread_id == thread_id
    ).order_by(ChatMessage.created_at).all()
    
    history = [
        {
            "role": msg.role.value,
            "content": msg.content,
            "tool_name": msg.tool_name,
            "tool_data": msg.tool_data
        }
        for msg in messages[:-1]  # Exclude the just-added user message
    ]
    
    # Stream AI response
    async def generate():
        async for event in deep_agent_service.stream_chat_response(
            user_message=message_data.content,
            conversation_history=history,
            db=db,
            thread_id=thread_id
        ):
            yield event
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/threads/{thread_id}/messages", response_model=List[ChatMessageResponse])
def get_messages(
    thread_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a thread."""
    # Verify thread ownership
    thread = db.query(ChatThread).filter(
        ChatThread.id == thread_id,
        ChatThread.user_id == current_user.id
    ).first()
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat thread not found"
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.thread_id == thread_id
    ).order_by(ChatMessage.created_at).all()
    
    return messages
