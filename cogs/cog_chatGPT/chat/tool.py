import base64
import io
import random
from typing import Optional, Type

import discord
import openai
from discord import Thread
from discord.ext.commands import Bot
from langchain_community.tools import BaseTool
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# Import things that are needed generically
from pydantic import BaseModel, Field

from utils.logger import get_logger


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


class ToolManager:
    def __init__(self, bot: Bot, channel: Thread):
        self.bot = bot
        self.logger = get_logger("tool_manager")
        self.channel = channel
        self.all_tools = [
            ImageGenerator(channel=channel),
            get_items,
            where_cat_is_hiding,
        ]

    def get_tools(self):
        tools = []
        for function in self.all_tools:
            tools.append(function)
        return tools
