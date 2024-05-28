import json
import os
from typing import TYPE_CHECKING, Any, Optional

from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.vectorstores.redis import Redis
from langchain_core.messages import BaseMessage, message_to_dict
from langchain_openai import OpenAIEmbeddings

from utils.hash import generate_key

if TYPE_CHECKING:
    from discord import Thread


embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6380)

REDIS_URL = f"redis://{redis_host}:{redis_port}"


class MyChatMessageHistory(RedisChatMessageHistory):
    def __init__(
        self,
        session_id: str,
        url: str = "redis://localhost:6379/0",
        key_prefix: str = "message_store:",
        ttl: Optional[int] = None,
    ):
        super().__init__(session_id, url, key_prefix, ttl)

    def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in Redis"""
        self.redis_client.lpush(
            self.key, json.dumps(message_to_dict(message), ensure_ascii=False)
        )
        if self.ttl:
            self.redis_client.expire(self.key, self.ttl)


def _get_rds(index_name: str, r_key: str, schema: dict[str, Any]):
    redis = Redis(
        REDIS_URL,
        index_name,
        embeddings,
        schema,
        key_prefix=r_key,
    )
    redis._create_index_if_not_exist(3072)
    return redis


def get_chat_history_memory(thread: "Thread"):
    key = generate_key(str(thread.id), 6)
    guild_name = thread.guild.name
    return MyChatMessageHistory(
        session_id=key, url=REDIS_URL, key_prefix=f"chat:{guild_name}:{key}:"
    )


def get_memory(thread: "Thread", type: str = "docs"):
    key = generate_key(str(thread.id), 6)
    rds = _get_rds(
        key,
        f"chat:{thread.guild.name}:{key}:{type}",
        {"text": [{"name": "source"}], "numeric": [{"name": "page"}]},
    )
    return rds
