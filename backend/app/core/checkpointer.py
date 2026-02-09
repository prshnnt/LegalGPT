"""PostgreSQL-based checkpoint saver for LangGraph."""
from typing import Optional, Iterator, Tuple
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata
import pickle
from models import Checkpoint as CheckpointModel, Chat
from db.session import get_db_context


class PostgresCheckpointSaver(BaseCheckpointSaver):
    """Checkpoint saver that stores checkpoints in PostgreSQL."""
    
    def __init__(self, session_id: str):
        """Initialize the checkpoint saver.
        
        Args:
            session_id: The session/chat ID to associate checkpoints with
        """
        super().__init__()
        self.session_id = session_id
    
    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> dict:
        """Save a checkpoint to the database.
        
        Args:
            config: Configuration dict with thread_id
            checkpoint: The checkpoint to save
            metadata: Metadata about the checkpoint
            
        Returns:
            Updated config dict
        """
        with get_db_context() as db:
            # Get or create chat
            chat = db.query(Chat).filter(Chat.session_id == self.session_id).first()
            if not chat:
                chat = Chat(session_id=self.session_id)
                db.add(chat)
                db.flush()
            
            # Serialize checkpoint
            checkpoint_data = pickle.dumps(checkpoint)
            
            # Create checkpoint record
            checkpoint_record = CheckpointModel(
                chat_id=chat.id,
                thread_id=config.get("configurable", {}).get("thread_id", self.session_id),
                checkpoint_ns=config.get("configurable", {}).get("checkpoint_ns", ""),
                checkpoint_id=checkpoint["id"],
                parent_checkpoint_id=checkpoint.get("parent_id"),
                type=checkpoint.get("type"),
                checkpoint=checkpoint_data,
                metadata=metadata
            )
            
            db.add(checkpoint_record)
            db.commit()
            
            return config
    
    def get_tuple(self, config: dict) -> Optional[Tuple[Checkpoint, CheckpointMetadata]]:
        """Get a checkpoint from the database.
        
        Args:
            config: Configuration dict with thread_id and checkpoint_id
            
        Returns:
            Tuple of (checkpoint, metadata) or None
        """
        with get_db_context() as db:
            thread_id = config.get("configurable", {}).get("thread_id", self.session_id)
            checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
            checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
            
            query = db.query(CheckpointModel).filter(
                CheckpointModel.thread_id == thread_id,
                CheckpointModel.checkpoint_ns == checkpoint_ns
            )
            
            if checkpoint_id:
                query = query.filter(CheckpointModel.checkpoint_id == checkpoint_id)
            
            checkpoint_record = query.order_by(CheckpointModel.created_at.desc()).first()
            
            if checkpoint_record:
                checkpoint = pickle.loads(checkpoint_record.checkpoint)
                metadata = checkpoint_record.metadata or {}
                return (checkpoint, metadata)
            
            return None
    
    def list(
        self,
        config: dict,
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Tuple[Checkpoint, CheckpointMetadata]]:
        """List checkpoints from the database.
        
        Args:
            config: Configuration dict with thread_id
            filter: Optional filter criteria
            before: Optional checkpoint to list before
            limit: Maximum number of checkpoints to return
            
        Yields:
            Tuples of (checkpoint, metadata)
        """
        with get_db_context() as db:
            thread_id = config.get("configurable", {}).get("thread_id", self.session_id)
            checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
            
            query = db.query(CheckpointModel).filter(
                CheckpointModel.thread_id == thread_id,
                CheckpointModel.checkpoint_ns == checkpoint_ns
            ).order_by(CheckpointModel.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            for checkpoint_record in query:
                checkpoint = pickle.loads(checkpoint_record.checkpoint)
                metadata = checkpoint_record.metadata or {}
                yield (checkpoint, metadata)