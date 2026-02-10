"""PostgreSQL-based checkpoint saver for LangGraph."""
import asyncio
from typing import Optional, Iterator, AsyncIterator, Tuple

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
    """Checkpoint saver that stores LangGraph checkpoints in PostgreSQL.

    Uses JsonPlusSerializer to handle LangChain message types (HumanMessage,
    AIMessage, etc.) which are not natively JSON-serializable.
    """

    serde = JsonPlusSerializer()

    def __init__(self, thread_id: int):
        super().__init__()
        self.thread_id = thread_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _serialize(self, obj: dict) -> dict:
        """Serialize a checkpoint/metadata dict to a plain JSON-safe dict."""
        # dumps() returns (type_str, bytes) — encode bytes to latin-1 str so
        # Postgres JSON column can store it, then wrap with the type tag so we
        # can round-trip it on the way out.
        serialized = {}
        for key, value in obj.items():
            type_str, data_bytes = self.serde.dumps_typed(value)
            serialized[key] = {
                "__type__": type_str,
                "__data__": data_bytes.decode("latin-1"),
            }
        return serialized

    def _deserialize(self, obj: dict) -> dict:
        """Deserialize a checkpoint/metadata dict back to Python objects."""
        deserialized = {}
        for key, value in obj.items():
            if isinstance(value, dict) and "__type__" in value:
                data_bytes = value["__data__"].encode("latin-1")
                deserialized[key] = self.serde.loads_typed(
                    (value["__type__"], data_bytes)
                )
            else:
                # Fallback: value stored without wrapper (e.g. plain scalars)
                deserialized[key] = value
        return deserialized

    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> dict:
        """
        Serialize a full checkpoint dict.
        channel_values contains LangChain messages; everything else is plain.
        We serialize the whole checkpoint as one blob via dumps_typed so we
        don't have to recurse into every nested field ourselves.
        """
        type_str, data_bytes = self.serde.dumps_typed(checkpoint)
        return {
            "__type__": type_str,
            "__data__": data_bytes.decode("latin-1"),
        }

    def _deserialize_checkpoint(self, stored: dict) -> Checkpoint:
        """Deserialize a checkpoint blob back to a Checkpoint dict."""
        if isinstance(stored, dict) and "__type__" in stored:
            data_bytes = stored["__data__"].encode("latin-1")
            return self.serde.loads_typed((stored["__type__"], data_bytes))
        # Already a plain dict (e.g. stored before this fix was applied)
        return stored

    def _serialize_metadata(self, metadata: dict) -> dict:
        """Serialize checkpoint metadata (usually plain scalars, but safe to wrap)."""
        type_str, data_bytes = self.serde.dumps_typed(metadata)
        return {
            "__type__": type_str,
            "__data__": data_bytes.decode("latin-1"),
        }

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
        """Persist a checkpoint synchronously."""
        checkpoint_ns = config.get("configurable", {}).get("checkpoint_ns", "")

        with get_db_context() as db:
            record = ChatCheckpoint(
                thread_id=self.thread_id,
                checkpoint_ns=checkpoint_ns,
                checkpoint_id=checkpoint["id"],
                parent_checkpoint_id=checkpoint.get("parent_id"),
                # ← Serialize to plain JSON-safe dicts before storing
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
                # ← Deserialize back to Python objects on the way out
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
                    checkpoint=self._deserialize_checkpoint(record.checkpoint_data),
                    metadata=self._deserialize_metadata(record.checkpoint_metadata),
                    parent_config=parent_config,
                )

    # ------------------------------------------------------------------
    # Async interface — required when using astream / astream_events
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