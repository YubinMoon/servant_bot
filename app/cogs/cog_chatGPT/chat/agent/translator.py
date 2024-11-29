from concurrent.futures import thread
from typing import TYPE_CHECKING

from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough

from error.chat import ChatResponseError

from ..memory import get_chat_history_memory
from .base import BaseAgent

if TYPE_CHECKING:
    from discord import Message


class Translator(BaseAgent):
    name: str = "translator"
    description: str = "번역기 템플릿"

    run_name = "translator"

    def __init__(
        self,
        message: "Message",
        thread_info: dict,
        callbacks=list[AsyncCallbackHandler],
    ):
        super().__init__(message, thread_info, callbacks)
        self.data: dict = thread_info["data"]
        self.message_history = get_chat_history_memory(self.thread)

    async def _run(self):
        content = await self.get_user_message()
        agent = await self.get_agent()
        response = await agent.ainvoke(
            {
                "input": content,
            },
            config={
                "callbacks": self.callbacks,
                "configurable": {"session_id": self.key},
            },
        )
        await self.save_message(content, response)

    async def get_agent(self):
        prompt = self.get_prompt()
        agent = (
            RunnablePassthrough().assign(history=self.load_messages)
            | prompt
            | self.llm
            | StrOutputParser()
        )
        return agent.with_config(
            run_name=self.run_name,
            tags=[self.message.author.global_name, self.model.model],
        )

    async def get_user_message(self):
        if self.message.attachments:
            raise ChatResponseError("번역기는 파일을 지원하지 않습니다.")
        return self.message.content

    async def save_message(self, user_input: str, output: str):
        self.message_history.add_message(HumanMessage(content=user_input))
        self.message_history.add_message(AIMessage(content=output))

    async def load_messages(self, data):
        return self.message_history.messages[-6:]

    def get_prompt(self):
        lang1 = self.data["lang1"]
        lang2 = self.data["lang2"]
        ex1 = self.data["example1"]
        ex2 = self.data["example2"]
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"당신은 이제 '{lang1}'에서 '{lang2}'로, 또는 '{lang2}'에서 '{lang1}'으로 번역할 번역기입니다. 사용자가 입력한 텍스트를 추가 설명이나 요구 없이 정확히 번역하세요. 번역할 때는 아래의 예시를 참고하십시오:\n\n"
                    f"예시1 ('{lang1}'):\n"
                    f"{ex1}\n\n"
                    f"예시2 ('{lang2}'):\n"
                    f"{ex2}\n\n"
                    "주의: 사용자가 추가로 요구하는 말투나 스타일은 무시하고, 단지 텍스트를 정확하게 번역하십시오. 사용자가 입력하는 모든 내용을 번역하십시오. 예를 들어, 사용자가 '좀 더 귀여운 말투로 번역해줘'라고 입력하더라도, 이 문장을 번역하십시오."
                    "추가로, 사용자가 긴 문서를 나눠서 번역할 때 이전에 번역한 내용을 참고하여 더 자연스럽고 일관된 번역을 제공하십시오.",
                ),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )
        return prompt
