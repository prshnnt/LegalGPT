import json
import logging
import asyncio
from typing import AsyncGenerator, Dict, List, Any, Optional

from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage
)
from app.core.config import settings
from app.core.prompts import get_system_prompt
from sqlalchemy.orm import Session
from app.core.checkpointer import PostgresCheckpointSaver
from app.models.database import ChatThread, MessageRole
from app.tools import internet_search
from app.prompts import get_system_prompt
from app.schemas.chat import StreamChunk
from app.models.services import ChatService, MessageService
from datetime import datetime

logger = logging.getLogger(__name__)

tools = [internet_search]
SYSTEM_PROMPT = get_system_prompt()


def llm_factory(**kwargs):
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.0,
        **kwargs
    )


class DeepAgentService:

    def __init__(self):
        self.llm = llm_factory()
        self.tools = tools

    def _create_deep_agent(
        self,
        system_prompt: str,
        thread_id: str,
        subagents: Optional[List[Dict]] = None
    ):
        checkpointer = PostgresCheckpointSaver(thread_id)
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
        thread: ChatThread,
        db: Session
    ) -> AsyncGenerator[str, None]:

        # Send start event — outside try so a failure here is a true server error
        start_chunk = StreamChunk(
            type="start",
            session_id=thread.id,
            content=message_content,
            checkpointer_metadata={"timestamp": datetime.utcnow().isoformat()}
        )
        yield f"data: {start_chunk.model_dump_json()}\n\n"

        full_response = ""
        tool_calls_made = []

        try:
            agent = self._create_deep_agent(SYSTEM_PROMPT, thread.id)

            config = {
                "configurable": {
                    "thread_id": thread.id,
                    "checkpoint_ns": ""
                }
            }

            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=message_content)]},
                config=config,
                version="v1"
            ):
                event_type = event.get("event")

                if event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", {})
                    if hasattr(chunk, "content") and chunk.content:
                        full_response += chunk.content
                        yield f"data: {StreamChunk(type='content', content=chunk.content, session_id=thread.id).model_dump_json()}\n\n"

                elif event_type == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    tool_calls_made.append({"tool": tool_name, "input": tool_input})
                    yield f"data: {StreamChunk(type='tool_call', tool_name=tool_name, tool_input=tool_input, session_id=thread.id, checkpointer_metadata={'timestamp': datetime.utcnow().isoformat()}).model_dump_json()}\n\n"

                elif event_type == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    tool_output = str(event.get("data", {}).get("output", ""))
                    yield f"data: {StreamChunk(type='tool_result', tool_name=tool_name, tool_output=tool_output, session_id=thread.id, checkpointer_metadata={'timestamp': datetime.utcnow().isoformat()}).model_dump_json()}\n\n"

        except Exception as e:
            logger.exception("Error during agent stream for thread %s", thread.id)
            yield f"data: {StreamChunk(type='error', content=str(e), session_id=thread.id, checkpointer_metadata={'timestamp': datetime.utcnow().isoformat()}).model_dump_json()}\n\n"
            # Early return — don't send 'end' after an error so the client
            # knows the stream did not complete successfully
            return

        # ----------------------------------------------------------------
        # Only reached on clean completion (no exception)
        # ----------------------------------------------------------------

        # Save assistant message in a separate try so a DB failure doesn't
        # retroactively make the stream look like it errored
        try:
            if full_response:
                MessageService.create_message(
                    db=db,
                    thread_id=thread.id,
                    role=MessageRole.AI,
                    content=full_response,
                    # Remove this kwarg if create_message doesn't accept it
                    # tool_calls=tool_calls_made if tool_calls_made else None
                )
        except Exception as db_err:
            # Log but don't surface to client — the stream itself succeeded
            logger.error(
                "Failed to persist AI message for thread %s: %s",
                thread.id, db_err
            )

        yield f"data: {StreamChunk(type='end', session_id=thread.id, checkpointer_metadata={'timestamp': datetime.utcnow().isoformat(), 'tools_used': len(tool_calls_made)}).model_dump_json()}\n\n"

    def _format_sse(self, event_type: str, data: Dict) -> str:
        try:
            return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        except TypeError:
            return f"event: error\ndata: {{\"message\": \"Serialization error\"}}\n\n"


deep_agent_service = DeepAgentService()