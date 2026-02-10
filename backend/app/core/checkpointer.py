"""PostgreSQL-based checkpoint saver for LangGraph."""
from typing import Optional, Iterator, Tuple

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
)

from app.models.database import ChatCheckpoint
from app.db.session import get_db_context


class PostgresCheckpointSaver(BaseCheckpointSaver):
    """Checkpoint saver that stores LangGraph checkpoints in PostgreSQL."""

    def __init__(self, thread_id: int):
        super().__init__()
        self.thread_id = thread_id

    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> dict:
        """Persist a checkpoint."""

        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")

        with get_db_context() as db:
            record = ChatCheckpoint(
                thread_id=self.thread_id,
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=checkpoint["id"],
                parent_checkpoint_id=checkpoint.get("parent_id"),
                checkpoint_data=checkpoint,          # JSON, not pickle
                checkpoint_metadata=metadata or {},
            )

            db.add(record)
            db.commit()

        return config

    def get_tuple(
        self, config: dict
    ) -> Optional[Tuple[Checkpoint, CheckpointMetadata]]:
        """Retrieve the latest or specified checkpoint."""

        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

        with get_db_context() as db:
            query = db.query(ChatCheckpoint).filter(
                ChatCheckpoint.thread_id == self.thread_id,
                ChatCheckpoint.checkpoint_ns == checkpoint_ns,
            )

            if checkpoint_id:
                query = query.filter(
                    ChatCheckpoint.checkpoint_id == checkpoint_id
                )

            record = (
                query.order_by(ChatCheckpoint.created_at.desc())
                .first()
            )

            if not record:
                return None

            return (
                record.checkpoint_data,
                record.checkpoint_metadata or {},
            )

    def list(
        self,
        config: dict,
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Tuple[Checkpoint, CheckpointMetadata]]:
        """List checkpoints in reverse chronological order."""

        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")

        with get_db_context() as db:
            query = db.query(ChatCheckpoint).filter(
                ChatCheckpoint.thread_id == self.thread_id,
                ChatCheckpoint.checkpoint_ns == checkpoint_ns,
            ).order_by(ChatCheckpoint.created_at.desc())

            if limit:
                query = query.limit(limit)

            for record in query:
                yield (
                    record.checkpoint_data,
                    record.checkpoint_metadata or {},
                )
