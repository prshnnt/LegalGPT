import json
import logging
import asyncio
from typing import AsyncGenerator, Dict, List, Any, Optional

# Deep Agents & LangChain Imports
from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage
)
# App Imports
from app.core.config import settings
from app.core.prompts import get_system_prompt
from sqlalchemy.orm import Session
from app.core.checkpointer import PostgresCheckpointSaver
from app.tools import internet_search
from app.prompts import get_system_prompt
from app.schemas.chat import StreamChunk
from app.models.services import ChatService, MessageService
from datetime import timezone as datetime




# Configure Logging
logger = logging.getLogger(__name__)

# List of available tools
tools = [internet_search]

# System prompt for the agent
SYSTEM_PROMPT = get_system_prompt()

def llm_factory(**kwargs):
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.0,
        **kwargs
    )



# # Optional: Create subagents for specialized tasks
# def create_research_subagent():
#     """Create a specialized research subagent.
    
#     This is an example of how to create subagents in DeepAgent.
#     Subagents are useful for delegating specialized tasks.
#     """
#     return {
#         "name": "research-agent",
#         "description": "Specialized agent for in-depth research tasks",
#         "system_prompt": "You are a research specialist. Provide detailed, well-researched answers.",
#         "tools": [search_web],  # Only give this subagent access to search
#         # model can be optionally overridden here
#     }




class DeepAgentService:
    """
    Service for handling AI interactions using LangChain Deep Agents and Ollama.
    
    This service replaces the direct Anthropic integration with a graph-based 
    agentic workflow (LangGraph) powered by local Llama 3.1 inference. It maintains
    backward compatibility with the frontend's SSE streaming contract.
    """

    def __init__(self):
        self.llm = llm_factory()
        # Define the tools list using the direct python functions.
        # create_deep_agent will automatically generate the JSON schemas from docstrings.
        self.tools = tools

    def _create_deep_agent(self, system_prompt: str,session_id: str,subagents: Optional[List[Dict]] = None):
        """
        Creates a new Deep Agent graph instance with the configured LLM and tools.
        
        The deep agent automatically includes 'write_todos' (planning) and filesystem
        tools unless explicitly disabled. We retain them to allow recursive planning
        for complex legal research tasks.
        """
        checkpointer = PostgresCheckpointSaver(session_id)
        
        return create_deep_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            checkpointer=checkpointer,
            subagents=subagents
        )

    async def stream_chat_response(
            self,
            message_content: str,
            session_id: str,
            db: Session
        ) -> AsyncGenerator[str, None]:
        """Stream chat response with stage notifications using DeepAgent SDK.
        
        Args:
            message_content: User message
            session_id: Chat session ID
            db: Database session
            
        Yields:
            JSON-encoded StreamChunk objects
        """
        try:
            # Get or create chat
            chat = ChatService.get_or_create_chat(db=db, session_id=session_id)
            
            # Save user message
            MessageService.create_message(
                db=db,
                chat_id=chat.id,
                role="user",
                content=message_content
            )
            
            # Send start event
            start_chunk = StreamChunk(
                type="start",
                session_id=session_id,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            yield f"data: {start_chunk.model_dump_json()}\n\n"
            
            # Get DeepAgent with checkpointer
            agent = self._create_deep_agent(SYSTEM_PROMPT,session_id)
            
            # Prepare config
            config = {
                "configurable": {
                    "thread_id": session_id,
                    "checkpoint_ns": ""
                }
            }
            
            # Stream agent response
            full_response = ""
            tool_calls_made = []
            
            # DeepAgent uses astream_events for streaming
            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=message_content)]},
                config=config,
                version="v1"
            ):
                event_type = event.get("event")
                # event_name = event.get("name", "")
                
                # Handle LLM token streaming
                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", {})
                    if hasattr(chunk, "content") and chunk.content:
                        full_response += chunk.content
                        content_chunk = StreamChunk(
                            type="content",
                            content=chunk.content,
                            session_id=session_id
                        )
                        yield f"data: {content_chunk.model_dump_json()}\n\n"
                
                # Handle tool calls - DeepAgent includes built-in planning and file tools
                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    
                    tool_calls_made.append({
                        "tool": tool_name,
                        "input": tool_input
                    })
                    
                    tool_call_chunk = StreamChunk(
                        type="tool_call",
                        tool_name=tool_name,
                        tool_input=tool_input,
                        session_id=session_id,
                        metadata={"timestamp": datetime.utcnow().isoformat()}
                    )
                    yield f"data: {tool_call_chunk.model_dump_json()}\n\n"
                
                # Handle tool results
                elif event_type == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    tool_output = str(event.get("data", {}).get("output", ""))
                    
                    tool_result_chunk = StreamChunk(
                        type="tool_result",
                        tool_name=tool_name,
                        tool_output=tool_output,
                        session_id=session_id,
                        metadata={"timestamp": datetime.utcnow().isoformat()}
                    )
                    yield f"data: {tool_result_chunk.model_dump_json()}\n\n"
            
            # Save assistant message
            if full_response:
                MessageService.create_message(
                    db=db,
                    chat_id=chat.id,
                    role="assistant",
                    content=full_response,
                    tool_calls=tool_calls_made if tool_calls_made else None
                )
            
            # Send end event
            end_chunk = StreamChunk(
                type="end",
                session_id=session_id,
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "tools_used": len(tool_calls_made)
                }
            )
            yield f"data: {end_chunk.model_dump_json()}\n\n"
            
        except Exception as e:
            # Send error event
            error_chunk = StreamChunk(
                type="error",
                content=str(e),
                session_id=session_id,
                metadata={"timestamp": datetime.utcnow().isoformat()}
            )
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    def _format_sse(self, event_type: str, data: Dict) -> str:
        """
        Formats a dictionary into a standard Server-Sent Event string.
        Ensures strict adherence to the SSE protocol (double newline termination).
        """
        try:
            data_str = json.dumps(data)
            return f"event: {event_type}\ndata: {data_str}\n\n"
        except TypeError:
            # Fallback for non-serializable data
            return f"event: error\ndata: {{\"message\": \"Serialization error\"}}\n\n"

# Singleton instance for import in API routes
deep_agent_service = DeepAgentService()