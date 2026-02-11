"""PostgreSQL-based checkpoint saver for LangGraph."""
import asyncio
from typing import Optional, Iterator, AsyncIterator, Sequence, Tuple, Any

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from app.models.database import ChatCheckpoint
from app.db.session import get_db_context


class PostgresCheckpointSaver(BaseCheckpointSaver):
    """Checkpoint saver that stores LangGraph checkpoints in PostgreSQL."""

    serde = JsonPlusSerializer()

    def __init__(self, thread_id: int):
        super().__init__()
        self.thread_id = thread_id

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> dict:
        type_str, data_bytes = self.serde.dumps_typed(checkpoint)
        return {"__type__": type_str, "__data__": data_bytes.decode("latin-1")}

    def _deserialize_checkpoint(self, stored: dict) -> Checkpoint:
        if isinstance(stored, dict) and "__type__" in stored:
            data_bytes = stored["__data__"].encode("latin-1")
            return self.serde.loads_typed((stored["__type__"], data_bytes))
        return stored

    def _serialize_metadata(self, metadata: dict) -> dict:
        type_str, data_bytes = self.serde.dumps_typed(dict(metadata or {}))
        return {"__type__": type_str, "__data__": data_bytes.decode("latin-1")}

    def _deserialize_metadata(self, stored: dict) -> dict:
        if isinstance(stored, dict) and "__type__" in stored:
            data_bytes = stored["__data__"].encode("latin-1")
            return self.serde.loads_typed((stored["__type__"], data_bytes))
        return stored or {}

    # ------------------------------------------------------------------
    # Sync interface
    # ------------------------------------------------------------------

    def put(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> dict:
        """Persist a checkpoint."""
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        with get_db_context() as db:
            record = ChatCheckpoint(
                thread_id=self.thread_id,
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=checkpoint["id"],
                parent_checkpoint_id=checkpoint.get("parent_id"),
                checkpoint_data=self._serialize_checkpoint(checkpoint),
                checkpoint_metadata=self._serialize_metadata(dict(metadata or {})),
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

    def put_writes(
        self,
        config: dict,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """
        Store intermediate writes (pending writes between checkpoints).
        These are ephemeral within a single graph execution step — we store
        them serialized in the checkpoint's metadata field of the SAME record
        so no extra table is needed. If you later need to inspect pending
        writes per task, add a separate ChatCheckpointWrite table.
        """
        # Minimal implementation: serialize and upsert into a writes column.
        # Since our schema doesn't have a separate writes table we just
        # persist them as part of the metadata on the matching checkpoint.
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")
        if not checkpoint_id:
            return  # Nothing to attach to yet

        try:
            type_str, data_bytes = self.serde.dumps_typed(list(writes))
            serialized_writes = {
                "__type__": type_str,
                "__data__": data_bytes.decode("latin-1"),
            }
            with get_db_context() as db:
                record = (
                    db.query(ChatCheckpoint)
                    .filter(
                        ChatCheckpoint.thread_id == self.thread_id,
                        ChatCheckpoint.checkpoint_ns == checkpoint_ns,
                        ChatCheckpoint.checkpoint_id == checkpoint_id,
                    )
                    .first()
                )
                if record:
                    # Merge writes into existing metadata
                    existing = self._deserialize_metadata(record.checkpoint_metadata)
                    existing["__pending_writes__"] = serialized_writes
                    record.checkpoint_metadata = self._serialize_metadata(existing)
                    db.commit()
        except Exception:
            # put_writes failing should never crash the graph
            pass

    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """Retrieve the latest or a specific checkpoint."""
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
                checkpoint=self._deserialize_checkpoint(record.checkpoint_data),
                metadata=self._deserialize_metadata(record.checkpoint_metadata),
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
        """List checkpoints in reverse chronological order."""
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
                    checkpoint=self._deserialize_checkpoint(record.checkpoint_data),
                    metadata=self._deserialize_metadata(record.checkpoint_metadata),
                    parent_config=parent_config,
                )

    # ------------------------------------------------------------------
    # Async interface — all four are required for astream / astream_events
    # ------------------------------------------------------------------

    async def aput(
        self,
        config: dict,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict,
    ) -> dict:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.put, config, checkpoint, metadata, new_versions
        )

    async def aput_writes(
        self,
        config: dict,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Async version of put_writes — this was the missing method causing the crash."""
        await asyncio.get_event_loop().run_in_executor(
            None, self.put_writes, config, writes, task_id
        )

    async def aget_tuple(self, config: dict) -> Optional[CheckpointTuple]:
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
        tuples = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: list(self.list(config, filter=filter, before=before, limit=limit)),
        )
        for t in tuples:
            yield t