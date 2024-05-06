import base64
import io
import json
import random
import re
from typing import TYPE_CHECKING, List, Optional, Type

import discord
import magic
import openai
import requests
from discord import Thread
from discord.ext.commands import Bot
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.html import BS4HTMLParser
from langchain_community.document_loaders.parsers.pdf import PDFMinerParser
from langchain_community.document_loaders.parsers.txt import TextParser
from langchain_community.tools import BaseTool, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.vectorstores import FAISS
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain_core.document_loaders.blob_loaders import Blob
from langchain_core.documents.base import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.tools import Tool, tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from pydantic import BaseModel, Field

from utils.chat import token_length
from utils.logger import get_logger

from .memory import MemoryManager

if TYPE_CHECKING:
    from langchain_community.document_loaders.base import BaseBlobParser

embeddings = OpenAIEmbeddings()


class ImageInput(BaseModel):
    prompt: str = Field(
        description="Write a description for the image so that an image can be generated. It should be written in detail to obtain better images.",
    )
    size: str = Field(
        description="Image size of the generated images.",
        enum=["1024x1024", "1792x1024", "1024x1792"],
    )
    style: str = Field(
        description="The style of the generated images. Vivid causes the model to lean towards generating hyper-real and dramatic images. Natural causes the model to produce more natural, less hyper-real looking images.",
        enum=["vivid", "natural"],
    )


class ImageGenerator(BaseTool):
    name = "dall-e_Image_Generator"
    description = "Generate images with dall-e-3. The generated images are automatically displayed to the user immediately, so there is no need to print additional images."
    args_schema: Type[BaseModel] = ImageInput
    need_token: bool = True
    channel: Thread = Field(exclude=True)

    async def _run(
        self,
        prompt: str,
        size: str,
        style: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        raise NotImplementedError()

    async def _arun(
        self,
        prompt: str,
        size: str,
        style: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.9)
        image_prompt = PromptTemplate(
            input_variables=["image_desc"],
            template="Generate a detailed prompt that must be composed in under 500 characters to generate an image based on the following description: {image_desc}",
        )
        chain: Runnable = image_prompt | llm | StrOutputParser()
        new_prompt = await chain.ainvoke(prompt)
        await self.generate_image(new_prompt, size, style)
        return True

    async def generate_image(self, prompt: str, size: str, style: str):
        client = openai.AsyncOpenAI()
        response = await client.images.generate(
            prompt=prompt,
            model="dall-e-2",
            quality="hd",
            response_format="b64_json",
            # size=size,
            size="256x256",
            style=style,
        )
        b64 = response.data[0].b64_json
        await self.send_image(b64)

    async def send_image(self, b64: str):
        file = discord.File(io.BytesIO(base64.b64decode(b64)), "image.png")
        await self.channel.send(
            file=file,
        )


class WebInput(BaseModel):
    urls: list[str] = Field(
        description="A list of URLs to fetch the contents of a web page."
    )


class WebFetch(BaseTool):
    name = "web_fetch"
    description = "Useful to fetches the contents of a web page. The full contents will be saved in memory. Short contents description are return. You need to retrieve the contents to retrieve_from_memory tool for more information."
    args_schema: Type[BaseModel] = WebInput
    memory_manager: MemoryManager = Field(exclude=True)

    async def _run(
        self,
        urls: list[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        rds = self.memory_manager.get_rds("web")
        docs = self.memory_manager.load_docs_from_web(urls)
        rds.add_documents(docs)
        metadata = [json.dumps(doc.metadata) for doc in docs]
        return set(metadata)

    async def _arun(
        self,
        urls: list[str],
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        rds = self.memory_manager.get_rds("web")
        docs = self.memory_manager.load_docs_from_web(urls)
        rds.add_documents(docs)
        metadata = [json.dumps(doc.metadata) for doc in docs]
        return set(metadata)


class SearchInput(BaseModel):
    query: str = Field(
        description="A search query to search the web memory. This should not url."
    )


class MemorySearch(BaseTool):
    name = "retrieve_from_memory"
    description = "Retrieve at memory contains every infomation you needed. When you need information just use this tool."
    args_schema: Type[BaseModel] = SearchInput
    memory_manager: MemoryManager = Field(exclude=True)

    async def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        retriever = self.memory_manager.create_web_retriever()
        docs = retriever.invoke(query)
        return self.memory_manager.format_docs_to_string(docs)

    async def _arun(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ):
        retriever = self.memory_manager.create_web_retriever()
        docs = retriever.invoke(query)
        return self.memory_manager.format_docs_to_string(docs)


api_wrapper = WikipediaAPIWrapper(
    top_k_results=3, doc_content_chars_max=1500, lang="ko"
)
wiki_tool = WikipediaQueryRun(
    api_wrapper=api_wrapper,
    description="A wrapper around Wikipedia. "
    "Useful for when you need to answer general questions about "
    "people, places, companies, facts, historical events, or other subjects. "
    "Input should be a search query.",
)

google_search = GoogleSearchAPIWrapper()


def top5_results(query):
    return google_search.results(query, 5)


google_search_tool = Tool(
    name="Google_Search_Snippets",
    description="Search Google for recent results.",
    func=top5_results,
)


class ToolManager:
    def __init__(self, bot: Bot, channel: Thread, memory: "MemoryManager"):
        self.bot = bot
        self.logger = get_logger("tool_manager")
        self.channel = channel
        self.all_tools = [
            ImageGenerator(channel=channel),
            WebFetch(memory_manager=memory),
            MemorySearch(memory_manager=memory),
            wiki_tool,
            google_search_tool,
        ]

    def get_tools(self):
        tools = []
        for function in self.all_tools:
            tools.append(function)
        return tools
