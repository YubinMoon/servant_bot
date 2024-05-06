import json
import os
from operator import itemgetter
from typing import TYPE_CHECKING, Optional

from langchain.agents.agent import AgentExecutor
from langchain.agents.openai_tools.base import create_openai_tools_agent
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.vectorstores.redis import Redis
from langchain_core.messages import BaseMessage, message_to_dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from database import ChatDataManager
from utils.hash import generate_key
from utils.logger import get_logger

if TYPE_CHECKING:
    from discord import Message

    from bot import ServantBot

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are very powerful assistant."
            "Answer the question based only on the following context:"
            "{context}",
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
embeddings = OpenAIEmbeddings()


redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6380)

redis_url = f"redis://{redis_host}:{redis_port}"

rds = Redis(redis_url, "users", embeddings, key_prefix="test")

retriever = rds.as_retriever(
    search_type="mmr", search_kwargs={"k": 5, "lambda_mult": 0.15}
)


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


class AgentManager:
    def __init__(self, bot: "ServantBot", message: "Message"):
        self.bot = bot
        self.guild = message.guild
        self.channel = message.channel
        self.key: str = generate_key(str(self.channel.id), 6)
        self.logger = get_logger("agent_manager")
        self.db = ChatDataManager(bot)
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", streaming=True)

    def create_session_factory(self):
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = os.getenv("REDIS_PORT", 6380)

        redis_url = f"redis://{redis_host}:{redis_port}"
        guild_name = self.guild.name

        def get_chat_history(session_id: str):
            if len(session_id) == 0:
                session_id = "messages"
            return MyChatMessageHistory(
                session_id, url=redis_url, key_prefix=f"chat:{guild_name}:{self.key}:"
            )

        return get_chat_history

    def get_agent(self, tools):
        agent = create_openai_tools_agent(self.llm, tools, prompt)
        agent = (
            RunnablePassthrough().assign(context=itemgetter("input") | retriever)
            | agent
        )
        agent_executor = AgentExecutor(
            agent=agent, tools=tools, handle_parsing_errors=True, verbose=True
        )
        return RunnableWithMessageHistory(
            agent_executor,
            self.create_session_factory(),
            input_messages_key="input",
            history_messages_key="history",
        )

    async def get_retriever(self, data):
        input_data = data["input"]
        result = await retriever.ainvoke(input_data)
        data["context"] = await self.format_docs(result)
        return data

    async def format_docs(self, docs):
        result = []
        for d in docs:
            result.append(f"{d.page_content}\n{d.metadata}")
        return "\n\n".join(
            [f"meta_data: {d.metadata}\ncontents: {d.page_content}" for d in docs]
        )
