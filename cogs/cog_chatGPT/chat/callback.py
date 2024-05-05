from time import time
from typing import TYPE_CHECKING, Any, Dict, List

import tiktoken
from discord import Embed
from langchain_community.callbacks.openai_info import (
    get_openai_token_cost_for_model,
    standardize_model_name,
)
from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs.llm_result import LLMResult

from utils import color
from utils.hash import generate_key
from utils.logger import get_logger

if TYPE_CHECKING:
    from discord import Embed, Message

    from bot import ServantBot

enc = tiktoken.encoding_for_model("gpt-3.5-turbo")


class CalcTokenCallback(AsyncCallbackHandler):
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.tool_tokens = 0
        self.prompt_cost = 0
        self.completion_cost = 0
        self.tool_cost = 0
        self.total_cost = 0.0
        self.chat_model = "gpt-3.5-turbo"

    def __repr__(self) -> str:
        return (
            f"Tokens Used: {self.prompt_tokens + self.completion_tokens + self.tool_tokens}\n"
            f"\tPrompt Tokens: {self.prompt_tokens}\n"
            f"\tCompletion Tokens: {self.completion_tokens}\n"
            f"\tTool Tokens: {self.tool_tokens}\n"
            f"Total Cost (USD): ${self.total_cost:f}\n"
            f"\tPrompt Cost (USD): ${self.prompt_cost:f}\n"
            f"\tCompletion Cost (USD): ${self.completion_cost:f}"
            f"\tTool Cost (USD): ${self.tool_cost:f}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "tool_tokens": self.tool_tokens,
            "total_tokens": self.prompt_tokens
            + self.completion_tokens
            + self.tool_tokens,
            "prompt_cost": self.prompt_cost,
            "completion_cost": self.completion_cost,
            "tool_cost": self.tool_cost,
            "total_cost": self.total_cost,
            "chat_model": self.chat_model,
        }

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Count prompt token length."""
        self.prompt_tokens += len(enc.encode(prompts[0]))
        self.chat_model = serialized["kwargs"]["model"]

    async def on_llm_new_token(self, token: str, **kwargs):
        """Count output tokens."""
        self.completion_tokens += 1

    async def on_llm_end(self, response, **kwargs: Any) -> None:
        """Calculate total token costs."""
        model_name = standardize_model_name("gpt-3.5-turbo")
        self.prompt_cost = get_openai_token_cost_for_model(
            model_name, self.prompt_tokens
        )
        self.completion_cost = get_openai_token_cost_for_model(
            model_name, self.completion_tokens, is_completion=True
        )
        self.tool_cost = 0.00002 * self.tool_tokens
        self.total_cost = self.prompt_cost + self.total_cost

    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        if serialized["name"] == "dall-e_Image_Generator":
            self.tool_tokens += 4_000


class ChatCallback(AsyncCallbackHandler):
    base_response_txt = "생각 중..."
    cooltime = 1.5

    def __init__(self, bot: "ServantBot", message: "Message"):
        self.bot = bot
        self.guild = message.guild
        self.channel = message.channel
        self.key: str = generate_key(str(self.channel.id), 6)
        self.logger = get_logger("chat_callback")
        self.response_txt = ""
        self.last_time = time()
        self.tool_message = None
        self.chat_message = None
        self.tool_list = []

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> Any:
        if self.chat_message is None:
            self.chat_message = await self.channel.send(self.base_response_txt)

    async def on_llm_new_token(self, token, **kwargs: Any) -> Any:
        self.response_txt += token
        if time() - self.last_time > self.cooltime and len(self.response_txt) > 0:
            await self.chat_message.edit(content=self.response_txt)
            self.last_time = time()

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        if len(self.response_txt) > 0:
            await self.chat_message.edit(content=self.response_txt)

        gen = response.generations[0][0]
        finish_reason = gen.generation_info["finish_reason"]
        if finish_reason == "tool_calls" and self.tool_message is None:
            self.tool_message = self.chat_message
            await self.tool_message.edit(content="기능 호출 중...")
            if len(self.response_txt) > 0:
                self.chat_message = await self.channel.send(self.response_txt)
            else:
                self.chat_message = None

    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        called_tool = serialized.copy()
        called_tool["args"] = input_str
        self.tool_list.append(called_tool)
        embed = Embed(title="기능 호출", color=color.BASE)
        for tool in self.tool_list:
            name = tool["name"]
            args = tool["args"]
            embed.add_field(name=name, value=f"`{args}`", inline=False)
        await self.tool_message.edit(content="", embed=embed)
