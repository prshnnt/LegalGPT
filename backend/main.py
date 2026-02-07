import os
import uuid
from typing import AsyncGenerator, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
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
    model = "gpt-oss:120b-cloud",
    base_url="http://localhost:11434",
    temperature=0
)

# Import tools
from Graph.tools import internet_search

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

    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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


# Non-streaming message endpoint (for testing)
@app.post("/chats/{chat_id}/message")
async def send_message(chat_id: int, message: MessageCreate, db: Session = Depends(get_db)):
    """Send a message and get complete response (non-streaming)"""
    import logging
    import traceback
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
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
    chat.updated_at = datetime.now()
    db.commit()
    
    try:
        logger.info(f"Processing message for chat {chat_id}")
        
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
        
        logger.info("Invoking agent...")
        
        # Get response from agent
        result = await agent_graph.ainvoke(
            {"messages": [HumanMessage(content=message.content)]},
            config=config
        )
        
        logger.info(f"Result: {result}")
        
        # Extract response
        response_content = ""
        if "messages" in result:
            for msg in result["messages"]:
                if hasattr(msg, "content") and msg.content:
                    response_content = msg.content
        
        # Save assistant message to database
        assistant_message = Message(
            chat_id=chat_id,
            role="assistant",
            content=response_content
        )
        db.add(assistant_message)
        db.commit()
        
        return {
            "message_id": assistant_message.id,
            "content": response_content,
            "created_at": assistant_message.created_at
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# # Agent streaming endpoint
# @app.post("/chats/{chat_id}/stream")
# async def stream_message(chat_id: int, message: MessageCreate, db: Session = Depends(get_db)):
#     """Stream agent response for a message"""
#     import logging
#     import traceback
    
#     logging.basicConfig(level=logging.DEBUG)
#     logger = logging.getLogger(__name__)
    
#     # Verify chat exists
#     chat = db.query(Chat).filter(Chat.id == chat_id).first()
#     if not chat:
#         raise HTTPException(status_code=404, detail="Chat not found")
    
#     if message.chat_id != chat_id:
#         raise HTTPException(status_code=400, detail="Chat ID mismatch")
    
#     # Save user message
#     user_message = Message(chat_id=chat_id, role="user", content=message.content)
#     db.add(user_message)
#     db.commit()
    
#     # Update chat timestamp
#     chat.updated_at = datetime.now()
#     db.commit()
    
#     async def generate_stream() -> AsyncGenerator[str, None]:
#         """Generate streaming response from agent"""
#         full_response = ""
        
#         try:
#             logger.info(f"Starting stream for chat {chat_id}")
#             yield f"data: [STARTING]\n\n"
            
#             # Create checkpointer with database connection
#             checkpointer = PostgresCheckpointer(db_session=db)
            
#             # Create agent with database-backed checkpointer
#             agent_graph = create_deep_agent(
#                 model=llm,
#                 tools=[internet_search],
#                 checkpointer=checkpointer
#             )
            
#             # Thread ID for conversation continuity
#             thread_id = f"chat_{chat_id}"
#             config = {"configurable": {"thread_id": thread_id}}
            
#             logger.info(f"Agent created, starting stream...")
            
#             # Try astream_events (for newer langgraph)
#             try:
#                 async for event in agent_graph.astream_events(
#                     {"messages": [HumanMessage(content=message.content)]},
#                     config=config,
#                     version="v2"
#                 ):
#                     # Extract and yield streamed tokens
#                     if event["event"] == "on_chat_model_stream":
#                         chunk = event["data"]["chunk"]
#                         if hasattr(chunk, "content") and chunk.content:
#                             full_response += chunk.content
#                             yield f"data: {chunk.content}\n\n"
                    
#                     # Handle tool calls
#                     elif event["event"] == "on_tool_start":
#                         tool_name = event["name"]
#                         yield f"data: [TOOL: {tool_name}]\n\n"
                    
#                     elif event["event"] == "on_tool_end":
#                         yield f"data: [TOOL COMPLETE]\n\n"
                        
#             except AttributeError as e:
#                 # Fallback to regular astream if astream_events is not available
#                 logger.warning(f"astream_events not available, using astream: {e}")
#                 yield f"data: [Using fallback streaming method]\n\n"
                
#                 async for chunk in agent_graph.astream(
#                     {"messages": [HumanMessage(content=message.content)]},
#                     config=config
#                 ):
#                     logger.debug(f"Chunk: {chunk}")
                    
#                     if "messages" in chunk:
#                         for msg in chunk["messages"]:
#                             if hasattr(msg, "content"):
#                                 content = msg.content
#                                 full_response += content
#                                 yield f"data: {content}\n\n"
            
#             # If no response generated, get final state
#             if not full_response:
#                 logger.warning("No streaming response, invoking agent...")
#                 result = await agent_graph.ainvoke(
#                     {"messages": [HumanMessage(content=message.content)]},
#                     config=config
#                 )
                
#                 if "messages" in result:
#                     for msg in result["messages"]:
#                         if hasattr(msg, "content") and msg.content:
#                             full_response += msg.content
#                             yield f"data: {msg.content}\n\n"
            
#             # Save assistant message to database
#             if full_response:
#                 assistant_message = Message(
#                     chat_id=chat_id,
#                     role="assistant",
#                     content=full_response
#                 )
#                 db.add(assistant_message)
#                 db.commit()
#                 logger.info(f"Saved response: {len(full_response)} chars")
            
#             yield "data: [DONE]\n\n"
            
#         except Exception as e:
#             error_msg = f"{str(e)}\n{traceback.format_exc()}"
#             logger.error(f"Stream error: {error_msg}")
#             yield f"data: [ERROR: {str(e)}]\n\n"
    
#     return StreamingResponse(
#         generate_stream(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no",
#         }
#     )


# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)