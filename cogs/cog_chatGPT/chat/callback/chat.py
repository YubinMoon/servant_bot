from time import time
from typing import TYPE_CHECKING, Any, Dict, List

from discord import Embed
from langchain_core.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs.llm_result import LLMResult

from utils import color
from utils.hash import generate_key
from utils.logger import get_logger

if TYPE_CHECKING:
    from discord import Embed, Message


class ChatCallback(AsyncCallbackHandler):
    base_response_txt = "생각 중..."
    cooltime = 1.5

    def __init__(self, message: "Message"):
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
