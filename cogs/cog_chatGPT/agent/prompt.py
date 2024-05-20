import time
from logging import Logger
from typing import TYPE_CHECKING, Any, Callable, List, cast

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts.chat import BaseChatPromptTemplate
from langchain_experimental.pydantic_v1 import BaseModel

from utils.logger import get_logger


class BasicPrompt(BaseChatPromptTemplate, BaseModel):
    input_variables: List[str] = ["file_data", "messages", "user_messages"]
    token_counter: Callable[[str], int]
    send_token_limit: int = 4196
    min_relevant_docs: int = 3
    min_history_messages: int = 4
    logger: Logger = get_logger("basic_long_prompt")

    def format_messages(self, **kwargs: Any) -> List[BaseMessage]:
        rest_tokens = self.send_token_limit

        base_prompt = SystemMessage(
            content="You are very powerful assistant."
            "If you need more information, you can ask to user."
        )
        time_prompt = SystemMessage(
            content=f"The current time and date is {time.strftime('%c')}"
        )
        rest_tokens -= self.token_counter(
            cast(str, base_prompt.content)
        ) + self.token_counter(cast(str, time_prompt.content))

        input_messages: list[BaseMessage] = kwargs["user_messages"]
        for input_message in input_messages:
            rest_tokens -= self.token_counter(cast(str, input_message.content))

        agent_scratchpad: list[BaseMessage] = kwargs["agent_scratchpad"]
        rest_tokens -= sum(
            [
                self.token_counter(cast(str, message.content))
                for message in agent_scratchpad
            ]
        )

        relevant_docs: list[Document] = kwargs["file_data"]
        relevant_memory = []
        for relevant_doc in relevant_docs:
            relevant_memory.append(
                f"Source: {relevant_doc.metadata['source']} "
                f"({relevant_doc.metadata['page']}Page) - "
                f"{relevant_doc.page_content}\n"
            )
        min_relevant_tokens = sum(
            [
                self.token_counter(doc)
                for doc in relevant_memory[: self.min_relevant_docs]
            ]
        )

        previous_messages: list[BaseMessage] = kwargs["messages"]
        min_history_tokens = 0
        for message in previous_messages[-self.min_history_messages :][::-1]:
            if min_history_tokens + min_relevant_tokens > rest_tokens:
                break
            min_history_tokens += self.token_counter(message.content)

        relevant_memory_tokens = self.get_relevant_tokens(relevant_memory)
        while min_history_tokens + relevant_memory_tokens > rest_tokens:
            relevant_memory = relevant_memory[:-1]
            relevant_memory_tokens = self.get_relevant_tokens(relevant_memory)
        relevant_contents = self.get_relevant_contents(relevant_memory)
        memory_message = SystemMessage(content=relevant_contents)
        rest_tokens -= self.token_counter(cast(str, memory_message.content))

        historical_messages: list[BaseMessage] = []
        historical_tokens = 0
        for message in previous_messages[-15:][::-1]:
            historical_tokens += self.token_counter(cast(str, message.content))
            if historical_tokens > rest_tokens:
                break
            historical_messages = [message] + historical_messages

        messages: List[BaseMessage] = [base_prompt, time_prompt, memory_message]
        messages += historical_messages
        messages.extend(input_messages)
        messages.extend(agent_scratchpad)
        self.logger.debug(f"formatted messages: {messages}")
        return messages

    def get_relevant_tokens(self, relevat_memory: list[Document]):
        contents = self.get_relevant_contents(relevat_memory)
        return self.token_counter(contents)

    def get_relevant_contents(self, relevant_memory: list[Document]):
        return (
            f"You can refer to these documents "
            f"from your memory:\n{relevant_memory}\n\n"
        )


class TranslatorPrompt(BaseChatPromptTemplate, BaseModel):
    pass
