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
from langchain_core.runnables.config import RunnableConfig

# App Imports
from app.core.config import settings
from app.core.prompts import get_system_prompt
from app.models.database import ChatMessage, MessageRole, ChatCheckpoint
from sqlalchemy.orm import Session
from app.core.checkpointer import PostgresCheckpointSaver
from app.tools import internet_search
from app.prompts import get_system_prompt



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


def get_agent_with_checkpointer(session_id: str):
    """Get DeepAgent with PostgreSQL checkpointer and Ollama model.
    
    Args:
        session_id: The session ID for checkpoint storage
        
    Returns:
        Compiled DeepAgent graph with checkpointer
    """
    
    model = llm_factory()
    # Initialize PostgreSQL checkpointer
    checkpointer = PostgresCheckpointSaver(session_id)
    
    # Create DeepAgent with custom configuration
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        # DeepAgent comes with built-in planning and file system tools
        # These are automatically included unless disabled
    )
    
    return agent


def create_agent_graph():
    """Create a basic DeepAgent without checkpointer.
    
    Returns:
        Compiled DeepAgent graph
    """
    # Initialize Ollama model
    model = llm_factory()
    
    # Create DeepAgent
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    
    return agent


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


def get_agent_with_subagents(session_id: str):
    """Get DeepAgent with subagents for complex task delegation.
    
    Args:
        session_id: The session ID for checkpoint storage
        
    Returns:
        Compiled DeepAgent graph with subagents
    """
    model = llm_factory()
    
    checkpointer = PostgresCheckpointSaver(session_id)
    
    # Create subagents for specialized tasks
    subagents = []
    
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        subagents=subagents,  # Enable task delegation
    )
    agent.
    
    return agent


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

    def _create_agent_graph(self, system_prompt: str):
        """
        Creates a new Deep Agent graph instance with the configured LLM and tools.
        
        The deep agent automatically includes 'write_todos' (planning) and filesystem
        tools unless explicitly disabled. We retain them to allow recursive planning
        for complex legal research tasks.
        """
        return create_deep_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
        )

    async def stream_chat_response(
        self,
        user_message: str,
        conversation_history: List,
        db: Session,
        thread_id: int,
        include_memory: bool = False,
        memory_content: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from Deep Agent (Ollama) with tool use support.
        
        This method acts as an adapter, translating LangGraph v2 events into the
        Server-Sent Events (SSE) format expected by the LegalGPT frontend.
        
        Args:
            user_message: The current query from the user.
            conversation_history: List of dicts representing past chat context.
            db: Database session for persisting tool outputs and final answers.
            thread_id: ID of the current chat thread.
            include_memory: Flag to include long-term memory context.
            memory_content: Actual text of the memory.
        
        Yields:
            SSE formatted strings (event:... data:...).
        """
        
        
        # 3. Graph Instantiation
        agent = self._create_agent_graph(system_prompt)

        # 4. Stream Execution
        # We use astream_events(version="v2") to access granular execution steps.
        # This allows us to intercept tool calls and streaming tokens in real-time.
        
        current_response_content = ""
        has_sent_message_start = False
        
        # Define the input payload for the graph
        inputs = {"messages": langchain_history}
        
        try:
            async for event in agent.astream_events(inputs, version="v2"):
                event_type = event["event"]
                event_data = event["data"]
                event_name = event.get("name", "")

                # --- EVENT MAPPING LOGIC ---

                # A. Message Start
                # We lazily send this on the first token to ensure we don't send it 
                # during internal silent thought processes.
                if event_type == "on_chat_model_start" and not has_sent_message_start:
                    # Filter out internal summarization or planning steps if they appear as separate models
                    pass 

                # B. Content Delta (Streaming Text)
                elif event_type == "on_chat_model_stream":
                    chunk = event_data.get("chunk")
                    if chunk and isinstance(chunk, AIMessage) and chunk.content:
                        content = chunk.content
                        if isinstance(content, str) and content:
                            if not has_sent_message_start:
                                yield self._format_sse("message_start", {"role": "assistant"})
                                has_sent_message_start = True
                            
                            current_response_content += content
                            # Send standard content delta
                            yield self._format_sse("content_delta", {"text": content})

                # C. Tool Use Start
                elif event_type == "on_tool_start":
                    # We only stream events for our defined legal tools.
                    # Internal tools like 'write_todos' can be hidden or shown depending on UX preference.
                    # Here we show them to demonstrate "Agentic Thinking".
                    target_tools = ["search_legal_documents", "get_document_by_reference", "write_todos","internet_search"]
                    
                    if event_name in target_tools:
                        yield self._format_sse("tool_use_start", {
                            "tool_name": event_name,
                            "input": event_data.get("input")
                        })

                # D. Tool Use End
                elif event_type == "on_tool_end":
                    target_tools = ["search_legal_documents", "get_document_by_reference", "write_todos","internet_search"]
                    
                    if event_name in target_tools:
                        output = event_data.get("output")
                        
                        # Normalize output (handle ToolMessage objects vs raw strings)
                        result_data = output
                        if hasattr(output, "content"):
                            result_data = output.content
                        
                        # PERSISTENCE: Save Tool Execution to SQL DB
                        # This maintains the history log for future turns.
                        # We skip 'write_todos' for persistence if it's considered internal thought,
                        # but saving it creates a better audit trail.
                        self._save_tool_interaction(
                            db, thread_id, event_name, 
                            event_data.get("input"), result_data
                        )

                        yield self._format_sse("tool_use_end", {
                            "tool_name": event_name,
                            "result": result_data
                        })

            # 5. Finalize and Save AI Response
            # Once the stream concludes, the aggregated content is the final answer.
            if current_response_content:
                ai_message = ChatMessage(
                    thread_id=thread_id,
                    role=MessageRole.AI,
                    content=current_response_content
                )
                db.add(ai_message)
                db.commit()

            yield self._format_sse("message_end", {
                "content": current_response_content
            })

            # 6. Save Checkpoint
            # While we rely on SQL for history, saving the graph checkpoint allows
            # for advanced features like "Rewind" or "Fork" in the future.
            self._save_checkpoint(db, thread_id, langchain_history)

        except Exception as e:
            logger.error(f"Deep Agent Stream Error: {str(e)}", exc_info=True)
            yield self._format_sse("error", {"message": f"Agent Error: {str(e)}"})

    def _convert_history_to_messages(self, history: List) -> List:
        """
        Converts the dict-based history (from SQL DB) into LangChain Message objects.
        This handles the mapping of 'human', 'ai', and 'tool' roles to their class equivalents.
        """
        messages: List[BaseMessage] = []

        for msg in history:
            role = msg["role"]
            content = msg["content"]
            
            if role == "human":
                messages.append(HumanMessage(content=content))
            elif role == "ai":
                messages.append(AIMessage(content=content))
            elif role == "tool":
                # Reconstruct ToolMessage
                # The SQL schema stores tool_name and tool_data.
                # We need a tool_call_id to satisfy LangChain's strict schema.
                # If historical data lacks an ID, we synthesize one.
                messages.append(ToolMessage(
                    content=content,
                    tool_call_id=msg.get("tool_call_id", f"call_{msg.get('id', 'unknown')}"),
                    name=msg.get("tool_name", "unknown_tool")
                ))
        return messages

    def _save_tool_interaction(self, db: Session, thread_id: int, name: str, input_data: Any, output_data: Any):
        """
        Persists a tool execution event to the relational database.
        """
        # Ensure data is JSON serializable
        tool_data = input_data if isinstance(input_data, dict) else {"input": input_data}
        
        # Normalize output content
        content_str = str(output_data)
        if isinstance(output_data, (dict, list)):
            content_str = json.dumps(output_data)
            
        tool_message = ChatMessage(
            thread_id=thread_id,
            role=MessageRole.TOOL,
            content=content_str,
            tool_name=name,
            tool_data=tool_data
        )
        db.add(tool_message)
        db.commit()

    def _save_checkpoint(self, db: Session, thread_id: int, messages: List):
        """
        Saves the conversation checkpoint to the database.
        This enables the 'DeepAgent' to resume complex multi-turn plans if persistence is enabled.
        """
        from langchain_core.messages import messages_to_dict
        checkpoint_data = {"messages": messages_to_dict(messages)}
        
        checkpoint = ChatCheckpoint(
            thread_id=thread_id,
            checkpoint_data=checkpoint_data
        )
        db.add(checkpoint)
        db.commit()

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