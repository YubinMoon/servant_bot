import json
import os
import re
from typing import TYPE_CHECKING, Optional

from langchain.agents.openai_tools.base import create_openai_tools_agent
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores.redis import Redis
from langchain_core.documents.base import Document
from langchain_core.messages import BaseMessage, message_to_dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from database import ChatDataManager
from utils.hash import generate_key
from utils.logger import get_logger

if TYPE_CHECKING:
    from discord import Message

    from bot import ServantBot

embeddings = OpenAIEmbeddings()

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


class MemoryManager:
    def __init__(self, bot: "ServantBot", message: "Message"):
        self.bot = bot
        self.guild = message.guild
        self.channel = message.channel
        self.key: str = generate_key(str(self.channel.id), 6)
        self.logger = get_logger("memory_manager")
        self.db = ChatDataManager(bot)

    def create_session_factory(self):

        guild_name = self.guild.name

        def get_chat_history(session_id: str):
            if len(session_id) == 0:
                session_id = "messages"
            return MyChatMessageHistory(
                session_id, REDIS_URL, key_prefix=f"chat:{guild_name}:{self.key}:"
            )

        return get_chat_history

    def get_rds(self, m_type):
        rds_key = f"chat:{self.guild.name}:{m_type}:doc"
        schema = self.db.get_redis_schema(rds_key)

        if schema is None:
            docs = self.load_dummy_docs()
            rds = Redis.from_documents(
                docs,
                embeddings,
                redis_url=REDIS_URL,
                index_name="web",
                key_prefix=rds_key,
            )
            self.db.set_redis_schema(rds_key, rds.schema)
            return rds
        return Redis.from_existing_index(
            embeddings, "web", schema, rds_key, redis_url=REDIS_URL
        )

    def create_web_retriever(self):
        rds = self.get_rds("web")
        retriever = rds.as_retriever(search_kwargs={"k": 7, "distance_threshold": 0.25})
        return retriever

    def load_dummy_docs(self):
        return self.load_docs_from_web(
            [
                "https://news.sbs.co.kr/news/endPage.do?news_id=N1007636739&plink=STAND&cooper=NAVER"
            ]
        )

    def load_docs_from_web(self, urls: list[str]):
        loader = WebBaseLoader(web_paths=urls)

        documents = loader.load()
        for doc in documents:
            doc.page_content = re.sub("\n +\n", "\n\n", doc.page_content)
            doc.page_content = re.sub("\n\n+", "\n\n", doc.page_content)

        return self.splite_doc(documents)

    def splite_doc(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\nn", "\n", ",", " ", ""],
            chunk_size=250,
            chunk_overlap=50,
            length_function=len,
        )
        return text_splitter.split_documents(documents)

    def format_docs_to_string(self, docs: list[Document]):
        return "\n\n".join(
            [f"meta data: {doc.metadata}\ncontent: {doc.page_content}" for doc in docs]
        )
