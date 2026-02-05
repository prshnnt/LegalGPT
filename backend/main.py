import os
import uuid
from typing import AsyncGenerator, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

from database import get_db, init_db
from models import User, Chat, Message
from checkpointer import PostgresCheckpointer

load_dotenv()

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="DeepAgent API", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM
llm = ChatOllama(
    model="gpt-oss:120b-cloud",
    base_url="http://localhost:11434",
    temperature=0
)

# Import tools
from tools import internet_search

# Pydantic models
class ChatCreate(BaseModel):
    user_id: int
    title: Optional[str] = "New Chat"

class MessageCreate(BaseModel):
    chat_id: int
    content: str

class UserCreate(BaseModel):
    username: str
    email: str

class ChatResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# User endpoints
@app.post("/users/", response_model=dict)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    db_user = User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email}

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "email": user.email}


# Chat endpoints
@app.post("/chats/", response_model=ChatResponse)
def create_chat(chat: ChatCreate, db: Session = Depends(get_db)):
    """Create a new chat session"""
    # Verify user exists
    user = db.query(User).filter(User.id == chat.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_chat = Chat(user_id=chat.user_id, title=chat.title)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

@app.get("/chats/user/{user_id}", response_model=list[ChatResponse])
def get_user_chats(user_id: int, db: Session = Depends(get_db)):
    """Get all chats for a user"""
    chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.updated_at.desc()).all()
    return chats

@app.get("/chats/{chat_id}", response_model=ChatResponse)
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    """Get a specific chat"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    """Delete a chat and all its messages"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted successfully"}


# Message endpoints
@app.get("/chats/{chat_id}/messages", response_model=list[MessageResponse])
def get_chat_messages(chat_id: int, db: Session = Depends(get_db)):
    """Get all messages for a chat"""
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).all()
    return messages


# Agent streaming endpoint
@app.post("/chats/{chat_id}/stream")
async def stream_message(chat_id: int, message: MessageCreate, db: Session = Depends(get_db)):
    """Stream agent response for a message"""
    
    # Verify chat exists
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    if message.chat_id != chat_id:
        raise HTTPException(status_code=400, detail="Chat ID mismatch")
    
    # Save user message
    user_message = Message(chat_id=chat_id, role="user", content=message.content)
    db.add(user_message)
    db.commit()
    
    # Update chat timestamp
    chat.updated_at = datetime.utcnow()
    db.commit()
    
    # Create checkpointer with database connection
    checkpointer = PostgresCheckpointer(db_session=db)
    
    # Create agent with database-backed checkpointer
    agent_graph = create_deep_agent(
        model=llm,
        tools=[internet_search],
        checkpointer=checkpointer
    )
    
    # Thread ID for conversation continuity
    thread_id = f"chat_{chat_id}"
    config = {"configurable": {"thread_id": thread_id}}
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response from agent"""
        full_response = ""
        
        try:
            # Stream events from the agent
            async for event in agent_graph.astream_events(
                {"messages": [HumanMessage(content=message.content)]},
                config=config,
                version="v2"
            ):
                # Extract and yield streamed tokens
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        full_response += chunk.content
                        yield f"data: {chunk.content}\n\n"
                
                # You can also handle tool calls here if needed
                elif event["event"] == "on_tool_start":
                    tool_name = event["name"]
                    yield f"data: [TOOL: {tool_name}]\n\n"
                
                elif event["event"] == "on_tool_end":
                    yield f"data: [TOOL COMPLETE]\n\n"
            
            # Save assistant message to database
            assistant_message = Message(
                chat_id=chat_id,
                role="assistant",
                content=full_response
            )
            db.add(assistant_message)
            db.commit()
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: [ERROR: {str(e)}]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)