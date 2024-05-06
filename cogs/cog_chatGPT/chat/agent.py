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

    from ..chat.memory import MemoryManager

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are very powerful assistant."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


class AgentManager:
    def __init__(self, bot: "ServantBot", message: "Message", memory: "MemoryManager"):
        self.bot = bot
        self.guild = message.guild
        self.channel = message.channel
        self.key: str = generate_key(str(self.channel.id), 6)
        self.logger = get_logger("agent_manager")
        self.llm = ChatOpenAI(model="gpt-4-turbo", streaming=True)
        self.memory = memory

    def get_agent(self, tools):
        retriever = self.memory.create_web_retriever()
        agent = create_openai_tools_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, tools=tools, handle_parsing_errors=True, verbose=True
        )
        return RunnableWithMessageHistory(
            agent_executor,
            self.memory.create_session_factory(),
            input_messages_key="input",
            history_messages_key="history",
        )
