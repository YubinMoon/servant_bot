import time
from pprint import pprint
from textwrap import dedent
from typing import Any, Callable, List

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts.chat import BaseChatPromptTemplate

from utils.chat import get_token_count
from utils.logger import get_logger

logger = get_logger(__name__)


class BasicPrompt(BaseChatPromptTemplate):
    input_variables: List[str] = ["file_data", "messages"]
    send_token_limit: int = 10000
    min_relevant_docs: int = 3
    min_history_messages: int = 6

    def format_messages(self, **kwargs: Any) -> List[BaseMessage]:
        rest_tokens = self.send_token_limit

        system_prompt = self.get_system_message()
        rest_tokens -= get_token_count(str(system_prompt.content))

        relevant_docs: list[Document] = kwargs["file_data"]
        relevant_memory = []
        for relevant_doc in relevant_docs:
            relevant_memory.append(
                f"Source: {relevant_doc.metadata['source']} "
                f"({relevant_doc.metadata['page']}Page) - "
                f"{relevant_doc.page_content}"
            )
        min_relevant_tokens = sum(
            [get_token_count(doc) for doc in relevant_memory[: self.min_relevant_docs]]
        )

        previous_messages: list[BaseMessage] = kwargs["messages"]
        min_history_tokens = 0
        for message in previous_messages[-self.min_history_messages :][::-1]:
            if min_history_tokens + min_relevant_tokens > rest_tokens:
                break
            if isinstance(message.content, list):
                for content in message.content:
                    min_history_tokens += get_token_count(str(content.get("text", "")))
            else:
                min_history_tokens += get_token_count(str(message.content))

        relevant_memory_tokens = self.get_relevant_tokens(relevant_memory)
        while min_history_tokens + relevant_memory_tokens > rest_tokens:
            relevant_memory = relevant_memory[:-1]
            relevant_memory_tokens = self.get_relevant_tokens(relevant_memory)
        relevant_contents = self.get_relevant_contents(relevant_memory)
        memory_message = HumanMessage(content=relevant_contents)
        rest_tokens -= get_token_count(str(memory_message.content))

        historical_messages: list[BaseMessage] = []
        historical_tokens = 0
        for message in previous_messages[-15:][::-1]:

            if isinstance(message.content, list):
                for content in message.content:
                    historical_tokens += get_token_count(str(content.get("text", "")))
            else:
                historical_tokens += get_token_count(str(message.content))
            if historical_tokens > rest_tokens:
                break
            historical_messages = [message] + historical_messages

        messages: List[BaseMessage] = [system_prompt, memory_message]
        messages += historical_messages
        return messages

    def get_system_message(self) -> SystemMessage:
        return SystemMessage(
            content=dedent(
                f"""
                You are a chat assistant named 'Servant'.
                You need to receive the user's question, clearly understand their intent, and provide the optimal answer that the user needs.
                To fully grasp the user's intent, you may request additional questions from the user.

                You must follow these guidelines to respond to the user:
                - Before answering the user, you should think step-by-step within the <thinking> tag.
                - The final answer you provide to the user should be output within the <answer> tag.
                - You can use the additional materials provided by the user in <documents> to answer.
                - The names of the files provided by the user will be listed within the <file> tag. The content of the files will be automatically selected and displayed in the <document> tag, so you should refer to this when responding.
                
                Important! You must think and respond in the language the user has asked in.
                
                The following is an example.
                <example>
                <documents>
                    (Additional materials provided by the user)
                </documents>
                <file>
                    (Additional file name list provided by the user)
                </file>
                <user>
                    (A user's question)
                </user>
                <thinking>
                    (Your thought process)
                </thinking>
                <answer>
                    (Your final answer)
                </answer>
                </example>
                <example>
                <user>
                    What is the capital of France?
                </user>
                <thinking>
                    I need to find the capital of France.
                </thinking>
                <answer>
                    The capital of France is Paris.
                </answer>
                
                The current time and date is {time.strftime('%c')}
                """
            )
        )

    def get_relevant_tokens(self, relevat_memory: list[Document]):
        contents = self.get_relevant_contents(relevat_memory)
        return get_token_count(contents)

    def get_relevant_contents(self, relevant_memory: list):
        return dedent(
            f"""
            <documents>
            {relevant_memory}
            </documents>
            """
        )
