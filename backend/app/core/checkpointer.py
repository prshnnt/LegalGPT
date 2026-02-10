"""PostgreSQL-based checkpoint saver for LangGraph."""
import asyncio
from typing import Optional, Iterator, AsyncIterator, Tuple

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from app.models.database import ChatCheckpoint
from app.db.session import get_db_context


class PostgresCheckpointSaver(BaseCheckpointSaver):
    """Checkpoint saver that stores LangGraph checkpoints in PostgreSQL.

    Implements BOTH sync and async interfaces because DeepAgent uses
    astream_events (async), which calls aget_tuple / aput / alist.
    Without async methods the base class has no fallback and silently
    fails, causing the immediate 'error' SSE event you were seeing.
    """

    def __init__(self, thread_id: int):
        super().__init__()
        self.thread_id = thread_id

    # ------------------------------------------------------------------
    # Sync interface (required by BaseCheckpointSaver)
    # ------------------------------------------------------------------

    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,          # ← required 4th arg in current LangGraph
    ) -> dict:
        """Persist a checkpoint synchronously."""
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        with get_db_context() as db:
            record = ChatCheckpoint(
                thread_id=self.thread_id,
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=checkpoint["id"],
                parent_checkpoint_id=checkpoint.get("parent_id"),
                checkpoint_data=checkpoint,
                checkpoint_metadata=metadata or {},
            )
            db.add(record)
            db.commit()
        return {
            **config,
            "configurable": {
                **config.get("configurable", {}),
                "checkpoint_id": checkpoint["id"],
                "checkpoint_ns": checkpoint_ns,
            },
        }

    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """Retrieve the latest or specified checkpoint synchronously."""
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
            record = query.order_by(ChatCheckpoint.created_at.desc()).first()

            if not record:
                return None

            # Build the config that points at this specific checkpoint
            checkpoint_config = {
                **config,
                "configurable": {
                    **config.get("configurable", {}),
                    "checkpoint_id": record.checkpoint_id,
                    "checkpoint_ns": checkpoint_ns,
                },
            }
            parent_config = None
            if record.parent_checkpoint_id:
                parent_config = {
                    "configurable": {
                        "thread_id": self.thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": record.parent_checkpoint_id,
                    }
                }

            return CheckpointTuple(
                config=checkpoint_config,
                checkpoint=record.checkpoint_data,
                metadata=record.checkpoint_metadata or {},
                parent_config=parent_config,
            )

    def list(
        self,
        config: dict,
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints in reverse chronological order synchronously."""
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")

        with get_db_context() as db:
            query = (
                db.query(ChatCheckpoint)
                .filter(
                    ChatCheckpoint.thread_id == self.thread_id,
                    ChatCheckpoint.checkpoint_ns == checkpoint_ns,
                )
                .order_by(ChatCheckpoint.created_at.desc())
            )
            if limit:
                query = query.limit(limit)

            for record in query:
                checkpoint_config = {
                    "configurable": {
                        "thread_id": self.thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": record.checkpoint_id,
                    }
                }
                parent_config = None
                if record.parent_checkpoint_id:
                    parent_config = {
                        "configurable": {
                            "thread_id": self.thread_id,
                            "checkpoint_ns": checkpoint_ns,
                            "checkpoint_id": record.parent_checkpoint_id,
                        }
                    }
                yield CheckpointTuple(
                    config=checkpoint_config,
                    checkpoint=record.checkpoint_data,
                    metadata=record.checkpoint_metadata or {},
                    parent_config=parent_config,
                )

    # ------------------------------------------------------------------
    # Async interface — REQUIRED when using astream / astream_events
    # ------------------------------------------------------------------

    async def aput(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> dict:
        """Persist a checkpoint asynchronously (runs sync version in thread)."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.put, config, checkpoint, metadata, new_versions
        )

    async def aget_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """Retrieve checkpoint asynchronously (runs sync version in thread)."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get_tuple, config
        )

    async def alist(
        self,
        config: dict,
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints asynchronously."""
        # Collect sync results in an executor, then yield them
        tuples = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: list(self.list(config, filter=filter, before=before, limit=limit)),
        )
        for t in tuples:
            yield t