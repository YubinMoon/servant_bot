import logging
from typing import Any, AsyncGenerator, Generator, Optional, Union

import redis
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from redis.asyncio import ConnectionPool as AsyncConnectionPool
from redis.asyncio import Redis as AsyncRedis

from database import get_async_redis, get_sync_redis
from utils.logger import get_logger

logger = get_logger(__name__)


class JsonAndBinarySerializer(JsonPlusSerializer):
    def _default(self, obj: Any) -> Any:
        if isinstance(obj, (bytes, bytearray)):
            return self._encode_constructor_args(
                obj.__class__, method="fromhex", args=[obj.hex()]
            )
        return super()._default(obj)

    def dumps(self, obj: Any) -> str:
        try:
            if isinstance(obj, (bytes, bytearray)):
                return obj.hex()
            return super().dumps(obj)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise

    def loads(self, s: str, is_binary: bool = False) -> Any:
        try:
            if is_binary:
                return bytes.fromhex(s)
            return super().loads(s)
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise


class RedisSaver(BaseCheckpointSaver):
    def __init__(
        self,
    ):
        super().__init__(serde=JsonAndBinarySerializer())

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        parent_ts = config["configurable"].get("thread_ts")
        key = f"checkpoint:{thread_id}:{checkpoint['ts']}"
        try:
            with get_sync_redis() as conn:
                conn.hset(
                    key,
                    mapping={
                        "checkpoint": self.serde.dumps(checkpoint),
                        "metadata": self.serde.dumps(metadata),
                        "parent_ts": parent_ts if parent_ts else "",
                    },
                )
                logger.info(
                    f"Checkpoint stored successfully for thread_id: {thread_id}, ts: {checkpoint['ts']}"
                )
        except Exception as e:
            logger.error(f"Failed to put checkpoint: {e}")
            raise
        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": checkpoint["ts"],
            },
        }

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        parent_ts = config["configurable"].get("thread_ts")
        key = f"checkpoint:{thread_id}:{checkpoint['ts']}"
        try:
            async with get_async_redis() as conn:
                await conn.hset(
                    key,
                    mapping={
                        "checkpoint": self.serde.dumps(checkpoint),
                        "metadata": self.serde.dumps(metadata),
                        "parent_ts": parent_ts if parent_ts else "",
                    },
                )
                logger.info(
                    f"Checkpoint stored successfully for thread_id: {thread_id}, ts: {checkpoint['ts']}"
                )
        except Exception as e:
            logger.error(f"Failed to aput checkpoint: {e}")
            raise
        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": checkpoint["ts"],
            },
        }

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        thread_ts = config["configurable"].get("thread_ts", None)
        try:
            with get_sync_redis() as conn:
                if thread_ts:
                    key = f"checkpoint:{thread_id}:{thread_ts}"
                else:
                    all_keys = conn.keys(f"checkpoint:{thread_id}:*")
                    if not all_keys:
                        logger.info(f"No checkpoints found for thread_id: {thread_id}")
                        return None
                    latest_key = max(all_keys, key=lambda k: k.split(":")[-1])
                    key = latest_key
                checkpoint_data = conn.hgetall(key)
                if not checkpoint_data:
                    logger.info(f"No valid checkpoint data found for key: {key}")
                    return None
                checkpoint = self.serde.loads(checkpoint_data["checkpoint"])
                metadata = self.serde.loads(checkpoint_data["metadata"])
                parent_ts = checkpoint_data.get("parent_ts", "")
                parent_config = (
                    {"configurable": {"thread_id": thread_id, "thread_ts": parent_ts}}
                    if parent_ts
                    else None
                )
                logger.info(
                    f"Checkpoint retrieved successfully for thread_id: {thread_id}, ts: {thread_ts}"
                )
                return CheckpointTuple(
                    config=config,
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=parent_config,
                )
        except Exception as e:
            logger.error(f"Failed to get checkpoint tuple: {e}")
            raise

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        thread_id = config["configurable"]["thread_id"]
        thread_ts = config["configurable"].get("thread_ts", None)
        try:
            async with get_async_redis() as conn:
                if thread_ts:
                    key = f"checkpoint:{thread_id}:{thread_ts}"
                else:
                    all_keys = await conn.keys(f"checkpoint:{thread_id}:*")
                    if not all_keys:
                        logger.info(f"No checkpoints found for thread_id: {thread_id}")
                        return None
                    latest_key = max(all_keys, key=lambda k: k.split(":")[-1])
                    key = latest_key
                checkpoint_data = await conn.hgetall(key)
                if not checkpoint_data:
                    logger.info(f"No valid checkpoint data found for key: {key}")
                    return None
                checkpoint = self.serde.loads(checkpoint_data["checkpoint"])
                metadata = self.serde.loads(checkpoint_data["metadata"])
                parent_ts = checkpoint_data.get("parent_ts", "")
                parent_config = (
                    {"configurable": {"thread_id": thread_id, "thread_ts": parent_ts}}
                    if parent_ts
                    else None
                )
                logger.info(
                    f"Checkpoint retrieved successfully for thread_id: {thread_id}, ts: {thread_ts}"
                )
                return CheckpointTuple(
                    config=config,
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=parent_config,
                )
        except Exception as e:
            logger.error(f"Failed to get checkpoint tuple: {e}")
            raise

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Generator[CheckpointTuple, None, None]:
        thread_id = config["configurable"]["thread_id"] if config else "*"
        pattern = f"checkpoint:{thread_id}:*"
        try:
            with get_sync_redis() as conn:
                keys = conn.keys(pattern)
                if before:
                    keys = [
                        k
                        for k in keys
                        if k.split(":")[-1] < before["configurable"]["thread_ts"]
                    ]
                keys = sorted(keys, key=lambda k: k.split(":")[-1], reverse=True)
                if limit:
                    keys = keys[:limit]
                for key in keys:
                    data = conn.hgetall(key)
                    if data and "checkpoint" in data and "metadata" in data:
                        thread_ts = key.split(":")[-1]
                        yield CheckpointTuple(
                            config={
                                "configurable": {
                                    "thread_id": thread_id,
                                    "thread_ts": thread_ts,
                                }
                            },
                            checkpoint=self.serde.loads(data["checkpoint"]),
                            metadata=self.serde.loads(data["metadata"]),
                            parent_config=(
                                {
                                    "configurable": {
                                        "thread_id": thread_id,
                                        "thread_ts": data.get("parent_ts", ""),
                                    }
                                }
                                if data.get("parent_ts")
                                else None
                            ),
                        )
                        logger.info(
                            f"Checkpoint listed for thread_id: {thread_id}, ts: {thread_ts}"
                        )
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            raise

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncGenerator[CheckpointTuple, None]:
        thread_id = config["configurable"]["thread_id"] if config else "*"
        pattern = f"checkpoint:{thread_id}:*"
        try:
            async with get_async_redis() as conn:
                keys = await conn.keys(pattern)
                if before:
                    keys = [
                        k
                        for k in keys
                        if k.split(":")[-1] < before["configurable"]["thread_ts"]
                    ]
                keys = sorted(keys, key=lambda k: k.split(":")[-1], reverse=True)
                if limit:
                    keys = keys[:limit]
                for key in keys:
                    data = await conn.hgetall(key)
                    if data and "checkpoint" in data and "metadata" in data:
                        thread_ts = key.split(":")[-1]
                        yield CheckpointTuple(
                            config={
                                "configurable": {
                                    "thread_id": thread_id,
                                    "thread_ts": thread_ts,
                                }
                            },
                            checkpoint=self.serde.loads(data["checkpoint"]),
                            metadata=self.serde.loads(data["metadata"]),
                            parent_config=(
                                {
                                    "configurable": {
                                        "thread_id": thread_id,
                                        "thread_ts": data.get("parent_ts", ""),
                                    }
                                }
                                if data.get("parent_ts")
                                else None
                            ),
                        )
                        logger.info(
                            f"Checkpoint listed for thread_id: {thread_id}, ts: {thread_ts}"
                        )
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            raise
