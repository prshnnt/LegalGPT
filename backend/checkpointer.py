import json
from typing import Optional, Iterator, Tuple, Any, AsyncIterator
from datetime import datetime

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
from sqlalchemy.orm import Session
from models import Checkpoint as CheckpointModel


class PostgresCheckpointer(BaseCheckpointSaver):
    """
    A checkpointer that stores conversation state in PostgreSQL database.
    This enables persistent memory across sessions.
    """
    
    def __init__(self, db_session: Session):
        super().__init__()
        self.db_session = db_session
    
    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> dict:
        """Save a checkpoint to the database"""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        
        # Serialize checkpoint data
        checkpoint_data = {
            "v": checkpoint.get("v", 1),
            "ts": checkpoint.get("ts"),
            "id": checkpoint.get("id"),
            "channel_values": self._serialize_channel_values(checkpoint.get("channel_values", {})),
            "channel_versions": checkpoint.get("channel_versions", {}),
            "versions_seen": checkpoint.get("versions_seen", {}),
        }
        
        # Create checkpoint record
        db_checkpoint = CheckpointModel(
            thread_id=thread_id,
            checkpoint_ns=checkpoint_ns,
            checkpoint_id=checkpoint["id"],
            parent_checkpoint_id=config["configurable"].get("checkpoint_id"),
            checkpoint_data=checkpoint_data,
            checkpoint_metadata=metadata or {}  # Use checkpoint_metadata
        )
        
        self.db_session.add(db_checkpoint)
        self.db_session.commit()
        
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }
    
    async def aput(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> dict:
        """Async version of put"""
        return self.put(config, checkpoint, metadata, new_versions)
    
    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """Retrieve a checkpoint from the database"""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")
        
        query = self.db_session.query(CheckpointModel).filter(
            CheckpointModel.thread_id == thread_id,
            CheckpointModel.checkpoint_ns == checkpoint_ns
        )
        
        if checkpoint_id:
            query = query.filter(CheckpointModel.checkpoint_id == checkpoint_id)
        else:
            # Get the latest checkpoint
            query = query.order_by(CheckpointModel.created_at.desc())
        
        db_checkpoint = query.first()
        
        if not db_checkpoint:
            return None
        
        # Deserialize checkpoint data
        checkpoint_data = db_checkpoint.checkpoint_data
        checkpoint = {
            "v": checkpoint_data.get("v", 1),
            "ts": checkpoint_data.get("ts"),
            "id": checkpoint_data.get("id"),
            "channel_values": self._deserialize_channel_values(checkpoint_data.get("channel_values", {})),
            "channel_versions": checkpoint_data.get("channel_versions", {}),
            "versions_seen": checkpoint_data.get("versions_seen", {}),
        }
        
        metadata = db_checkpoint.checkpoint_metadata or {}  # Use checkpoint_metadata
        
        parent_config = None
        if db_checkpoint.parent_checkpoint_id:
            parent_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": db_checkpoint.parent_checkpoint_id,
                }
            }
        
        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": db_checkpoint.checkpoint_id,
                }
            },
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=parent_config,
        )
    
    async def aget_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """Async version of get_tuple"""
        return self.get_tuple(config)
    
    def list(
        self,
        config: Optional[dict] = None,
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints from the database"""
        query = self.db_session.query(CheckpointModel)
        
        if config:
            thread_id = config["configurable"]["thread_id"]
            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
            query = query.filter(
                CheckpointModel.thread_id == thread_id,
                CheckpointModel.checkpoint_ns == checkpoint_ns
            )
        
        if before:
            before_checkpoint_id = before["configurable"].get("checkpoint_id")
            if before_checkpoint_id:
                before_checkpoint = self.db_session.query(CheckpointModel).filter(
                    CheckpointModel.checkpoint_id == before_checkpoint_id
                ).first()
                if before_checkpoint:
                    query = query.filter(CheckpointModel.created_at < before_checkpoint.created_at)
        
        query = query.order_by(CheckpointModel.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        for db_checkpoint in query:
            checkpoint_data = db_checkpoint.checkpoint_data
            checkpoint = {
                "v": checkpoint_data.get("v", 1),
                "ts": checkpoint_data.get("ts"),
                "id": checkpoint_data.get("id"),
                "channel_values": self._deserialize_channel_values(checkpoint_data.get("channel_values", {})),
                "channel_versions": checkpoint_data.get("channel_versions", {}),
                "versions_seen": checkpoint_data.get("versions_seen", {}),
            }
            
            metadata = db_checkpoint.checkpoint_metadata or {}  # Use checkpoint_metadata
            
            parent_config = None
            if db_checkpoint.parent_checkpoint_id:
                parent_config = {
                    "configurable": {
                        "thread_id": db_checkpoint.thread_id,
                        "checkpoint_ns": db_checkpoint.checkpoint_ns,
                        "checkpoint_id": db_checkpoint.parent_checkpoint_id,
                    }
                }
            
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": db_checkpoint.thread_id,
                        "checkpoint_ns": db_checkpoint.checkpoint_ns,
                        "checkpoint_id": db_checkpoint.checkpoint_id,
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=parent_config,
            )
    
    async def alist(
        self,
        config: Optional[dict] = None,
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """Async version of list"""
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item
    
    def _serialize_channel_values(self, channel_values: dict) -> dict:
        """Serialize channel values for JSON storage"""
        from langchain_core.messages import BaseMessage
        import json
        
        def serialize_value(value):
            """Recursively serialize values"""
            # Handle LangChain messages
            if isinstance(value, BaseMessage):
                return {
                    "type": value.__class__.__name__,
                    "content": value.content,
                    "additional_kwargs": value.additional_kwargs if hasattr(value, 'additional_kwargs') else {},
                }
            # Handle lists
            elif isinstance(value, list):
                return [serialize_value(item) for item in value]
            # Handle dicts
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            # Handle objects with dict() method
            elif hasattr(value, "dict"):
                try:
                    return value.dict()
                except:
                    pass
            # Handle objects with __dict__
            elif hasattr(value, "__dict__"):
                try:
                    return serialize_value(value.__dict__)
                except:
                    pass
            # Handle primitives
            elif isinstance(value, (str, int, float, bool, type(None))):
                return value
            # Fallback to string
            else:
                return str(value)
        
        serialized = {}
        for key, value in channel_values.items():
            try:
                serialized[key] = serialize_value(value)
            except Exception as e:
                # Fallback to string representation
                serialized[key] = str(value)
        
        return serialized
    
    def _deserialize_channel_values(self, channel_values: dict) -> dict:
        """Deserialize channel values from JSON storage"""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
        
        def deserialize_value(value):
            """Recursively deserialize values"""
            # Handle message dictionaries
            if isinstance(value, dict) and "type" in value:
                msg_type = value.get("type")
                content = value.get("content", "")
                additional_kwargs = value.get("additional_kwargs", {})
                
                if msg_type == "HumanMessage":
                    return HumanMessage(content=content, additional_kwargs=additional_kwargs)
                elif msg_type == "AIMessage":
                    return AIMessage(content=content, additional_kwargs=additional_kwargs)
                elif msg_type == "SystemMessage":
                    return SystemMessage(content=content, additional_kwargs=additional_kwargs)
                elif msg_type == "ToolMessage":
                    return ToolMessage(content=content, additional_kwargs=additional_kwargs, tool_call_id=additional_kwargs.get("tool_call_id", ""))
                else:
                    return value
            # Handle lists
            elif isinstance(value, list):
                return [deserialize_value(item) for item in value]
            # Handle dicts
            elif isinstance(value, dict):
                return {k: deserialize_value(v) for k, v in value.items()}
            # Return as-is
            else:
                return value
        
        deserialized = {}
        for key, value in channel_values.items():
            try:
                deserialized[key] = deserialize_value(value)
            except Exception as e:
                # Fallback to original value
                deserialized[key] = value
        
        return deserialized