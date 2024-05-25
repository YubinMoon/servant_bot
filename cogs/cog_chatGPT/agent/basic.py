from operator import itemgetter
from typing import TYPE_CHECKING

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..chat.memory import get_chat_history_memory, get_memory
from .base import BaseAgent
from .prompt import BasicPrompt
from .tools import get_tools

if TYPE_CHECKING:
    from discord import Attachment, Message


class Basic(BaseAgent):
    max_token = 5000
    memory_docs_num = 4
    splitter_chunk_size = 600
    run_name = "basic"

    def __init__(
        self,
        message: "Message",
        thread_info: dict,
        callbacks=list[AsyncCallbackHandler],
    ):
        super().__init__(message, thread_info, callbacks)
        self.tools = get_tools(thread_info["tools"])
        self.token_counter = self.llm.get_num_tokens
        self.prompt = BasicPrompt(
            token_counter=self.token_counter,
            send_token_limit=self.max_token,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=[".", "!", "?", "\n", ",", " "],
            chunk_size=self.splitter_chunk_size,
            chunk_overlap=400,
            length_function=self.token_counter,
        )

        self.memory = get_memory(self.thread)
        self.message_history = get_chat_history_memory(self.thread)

    async def _run(self):
        # TODO  token check 추가 필요

        user_messages = await self.get_user_messages()

        agent_executor = await self.get_agent_executor()
        response = await agent_executor.ainvoke(
            {
                "user_messages": user_messages,
            },
            config={
                "callbacks": self.callbacks,
                "configurable": {"session_id": self.key},
            },
        )
        await self.save_message(user_messages, response["output"])

    async def get_agent_executor(self):
        retriever = self.memory.as_retriever(search_kwargs={"k": self.memory_docs_num})
        if self.tools:
            llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            llm_with_tools = self.llm
        agent = (
            RunnablePassthrough()
            .assign(
                agent_scratchpad=lambda x: format_to_openai_tool_messages(
                    x["intermediate_steps"]
                ),
                messages=self.load_messages,
            )
            .assign(
                file_data=(
                    itemgetter("messages")
                    | RunnableLambda(lambda x: str(x[:10])).with_config(
                        run_name="slice history"
                    )
                    | retriever
                ),
            )
            | self.prompt
            | llm_with_tools.with_config(run_name="llm_with_tools")
            | OpenAIToolsAgentOutputParser()
        )
        agent_executor = AgentExecutor(
            agent=agent, tools=self.tools, verbose=True
        ).with_config(
            run_name=self.run_name,
            tags=[self.message.author.global_name, self.model.model],
        )
        return agent_executor

    async def save_message(self, user_messagse, output):
        self.message_history.add_messages(user_messagse)
        self.message_history.add_message(AIMessage(content=output))

    async def load_messages(self, data):
        return self.message_history.messages

    async def get_user_messages(self):
        messages = await self.load_attachments()
        messages.append(HumanMessage(content=self.message.content))
        return messages

    async def load_attachments(self):
        text_file_types = (
            "text/",
            "application/json",
            "application/xml",
        )

        messages: list[BaseMessage] = []

        for attachment in self.message.attachments:
            file_type = attachment.content_type.split()[0]
            if file_type.startswith(text_file_types):
                message = await self._load_text_file(attachment)
                messages.append(message)
            elif file_type.startswith("application/pdf"):
                message = await self._load_pdf_file(attachment)
                messages.append(message)
            else:
                self.message.reply(
                    f"지원하지 않는 파일 형식입니다. ({attachment.filename})"
                )
        return messages

    async def _load_text_file(self, attachment: "Attachment"):
        contents = await attachment.read()
        contents = contents.decode("utf-8")
        document = Document(
            page_content=contents,
            metadata={"source": attachment.filename, "page": 0},
        )
        return await self._insert_content([document])

    async def _load_pdf_file(self, attachment: "Attachment"):
        loader = PyPDFLoader(attachment.url)
        documents = loader.load()
        for document in documents:
            document.metadata["source"] = attachment.filename
        return await self._insert_content(documents)

    async def _insert_content(self, documents: "list[Document]"):
        total_token = 0
        for document in documents:
            total_token += self.token_counter(document.page_content)

        splitted_docs = self.text_splitter.split_documents(documents)
        await self.memory.aadd_documents(splitted_docs)

        if total_token < self.memory_docs_num * 3:
            content = "\n".join([doc.page_content for doc in documents])
            return SystemMessage(
                content=f"filename: {documents[0].metadata['source']}\n"
                f"file contents: {content}"
            )
        else:
            await self._send_overflow_token_message(total_token, splitted_docs)
            return SystemMessage(
                content=f"'{documents[0].metadata['source']}'"
                f"파일이 memory에 추가되었습니다."
            )

    async def _send_overflow_token_message(self, token, documents: "list[Document]"):
        await self.message.reply(
            f"파일 길이가 {token}토큰으로 기준치를 초과했습니다.\n"
            f"파일을 {len(documents)}개로 분할하여 저장합니다.\n"
            "저장된 파일은 자동 선별되어 사용됩니다."
        )


class BasicLong(Basic):
    max_token = 15000
    memory_docs_num = 10
    splitter_chunk_size = 800
    run_name = "basic_long"
