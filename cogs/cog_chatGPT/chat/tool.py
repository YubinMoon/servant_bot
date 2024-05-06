import base64
import io
import random
from typing import TYPE_CHECKING, Optional, Type

import discord
import magic
import openai
import requests
from discord import Thread
from discord.ext.commands import Bot
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.html import BS4HTMLParser
from langchain_community.document_loaders.parsers.pdf import PDFMinerParser
from langchain_community.document_loaders.parsers.txt import TextParser
from langchain_community.tools import BaseTool, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain_core.document_loaders.blob_loaders import Blob
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.tools import Tool, tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from utils.logger import get_logger

if TYPE_CHECKING:
    from langchain_community.document_loaders.base import BaseBlobParser


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


@tool
def where_cat_is_hiding() -> str:
    """Where is the cat hiding right now?"""
    return random.choice(["under the bed", "on the shelf"])


@tool
def get_items(place: str) -> str:
    """Use this tool to look up which items are in the given place."""
    if "bed" in place:  # For under the bed
        return "socks, shoes and dust bunnies"
    if "shelf" in place:  # For 'shelf'
        return "books, penciles and pictures"
    else:  # if the agent decides to ask about a different place
        return "cat snacks"


@tool
def web_request(url: str) -> str:
    """Use this tool to make a web request to the given URL."""
    response = requests.get(url)
    data = response.content
    HANDLERS: "dict[str,BaseBlobParser]" = {
        "application/pdf": PDFMinerParser(),
        "text/plain": TextParser(),
        "text/html": BS4HTMLParser(),
    }

    # Instantiate a mimetype based parser with the given parsers
    MIMETYPE_BASED_PARSER = MimeTypeBasedParser(
        handlers=HANDLERS,
        fallback_parser=None,
    )

    mime = magic.Magic(mime=True)
    mime_type = mime.from_buffer(data)

    # A blob represents binary data by either reference (path on file system)
    # or value (bytes in memory).
    blob = Blob.from_data(
        data=data,
        mime_type=mime_type,
    )

    parser = HANDLERS[mime_type]
    documents = parser.parse(blob=blob)


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
    def __init__(self, bot: Bot, channel: Thread):
        self.bot = bot
        self.logger = get_logger("tool_manager")
        self.channel = channel
        self.all_tools = [
            ImageGenerator(channel=channel),
            get_items,
            where_cat_is_hiding,
            wiki_tool,
            google_search_tool,
        ]

    def get_tools(self):
        tools = []
        for function in self.all_tools:
            tools.append(function)
        return tools
