import base64
import io
import json
import logging
import os
from typing import Any

import discord
import openai
from discord import Thread
from discord.ext.commands import Bot
from dotenv import load_dotenv

load_dotenv()


class Argument:
    def __init__(
        self,
        name: str,
        type: str,
        description: str,
        required: bool = False,
        enum: list[Any] = [],
    ):
        self.name = name
        self.type = type
        self.description = description
        self.required = required
        self.enum = enum

    def check_valid(self) -> None:
        if self.type not in ["string", "integer", "boolean"]:
            raise ValueError("invalid argument type")

    def get_schema(self) -> dict:
        self.check_valid()
        return {
            self.name: {
                "type": self.type,
                "description": self.description,
                "enum": self.enum,
            }
        }


class BaseFunction:
    name = ""
    description = ""
    argument: list[Argument] = []

    def __init__(self, handler: "ToolHandler"):
        self.bot = handler.bot
        self.logger = handler.logger
        self.channel = handler.channel

    def get_tools(self):
        parameters = {}
        if self.argument:
            required = []
            parameters["type"] = "object"
            parameters["properties"] = {}
            for arg in self.argument:
                if arg.required:
                    required.append(arg.name)
                parameters["properties"].update(arg.get_schema())
            parameters["required"] = required
        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
        }

    def process(self, *args, **kwargs):
        raise NotImplementedError


class ImageGenerator(BaseFunction):
    name = "dall-e"
    description = "dall-e 3로 이미지를 생성하기 위한 함수. 생성된 이미지는 자동으로 사용자에게 보여지므로 추가로 이미지를 출력하지 않아도 됩니다."
    argument = [
        Argument(
            "prompt",
            "string",
            "이미지 생성 시 입력되는 프롬프트 입니다. 구체적인 프롬프트를 적을 수록 더 좋은 이미지가 생성됩니다.",
            True,
        ),
        Argument(
            "size",
            "string",
            "이미지 생성 크기를 설정합니다.",
            True,
            ["1024x1024", "1792x1024", "1024x1792"],
        ),
        Argument(
            "style",
            "string",
            "The style of the generated images. Vivid causes the model to lean towards generating hyper-real and dramatic images. Natural causes the model to produce more natural, less hyper-real looking images.",
            True,
            ["vivid", "natural"],
        ),
    ]

    async def process(self, prompt: str, size: str, style: str):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await self.client.images.generate(
            prompt=prompt,
            model="dall-e-3",
            quality="hd",
            response_format="b64_json",
            size=size,
            style=style,
        )
        b64 = response.data[0].b64_json
        file = discord.File(io.BytesIO(base64.b64decode(b64)), "image.png")
        await self.channel.send(
            file=file,
        )
        return "이미지 생성 및 출력 완료"


class ToolHandler:
    def __init__(self, bot: Bot, channel: Thread):
        self.bot = bot
        self.logger: logging.Logger = bot.logger
        self.channel = channel
        functions: list[BaseFunction] = [
            ImageGenerator(self),
        ]
        self.functions = {function.name: function for function in functions}

    def get_tools(self):
        tools = []
        for func in self.functions.values():
            tools.append(
                {
                    "type": "function",
                    "function": func.get_tools(),
                }
            )
        return tools

    async def process(self, tool: str, arguments: str):
        if tool not in self.functions:
            raise ValueError("invalid tool name")

        arguments = json.loads(arguments)
        return await self.functions[tool].process(**arguments)
