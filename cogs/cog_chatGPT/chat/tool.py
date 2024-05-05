import base64
import io
import json
import logging
import os
from typing import Any, Optional, Type

import discord
import openai
from discord import Thread
from discord.ext.commands import Bot
from langchain.agents import initialize_agent, load_tools

# Import things that are needed generically
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from utils.logger import get_logger


class ImageInput(BaseModel):
    prompt: str = Field(
        description="이미지 생성 시 입력되는 프롬프트 입니다. 구체적인 프롬프트를 적을 수록 더 좋은 이미지가 생성됩니다.",
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
    name = "dall-e"
    description = "dall-e 3로 이미지를 생성하기 위한 함수. 생성된 이미지는 자동으로 사용자에게 보여지므로 추가로 이미지를 출력하지 않아도 됩니다."
    args_schema: Type[BaseModel] = ImageInput
    return_direct: bool = True
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
        prompt = PromptTemplate(
            input_variables=["image_desc"],
            template="Generate a detailed prompt that must be composed in under 500 characters to generate an image based on the following description: {image_desc}",
        )
        chain: Runnable = prompt | llm | StrOutputParser()
        new_prompt = await chain.ainvoke("halloween night at a haunted museum")
        await self.generate_image(new_prompt, size, style)
        return True

    async def generate_image(self, prompt: str, size: str, style: str):
        client = openai.AsyncOpenAI()
        response = await client.images.generate(
            prompt=prompt,
            model="dall-e-2",
            quality="hd",
            response_format="b64_json",
            size=size,
            style=style,
        )
        b64 = response.data[0].b64_json
        await self.send_image(b64)

    async def send_image(self, b64: str):
        file = discord.File(io.BytesIO(base64.b64decode(b64)), "image.png")
        await self.channel.send(
            file=file,
        )


class ToolManager:
    def __init__(self, bot: Bot, channel: Thread):
        self.bot = bot
        self.logger = get_logger("tool_manager")
        self.channel = channel
        self.all_functions = [
            ImageGenerator(channel=channel),
        ]

    def get_tools(self):
        tools = []
        for function in self.all_functions:
            tools.append(function)
        return tools
