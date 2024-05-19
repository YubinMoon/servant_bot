import asyncio
import traceback
from typing import TYPE_CHECKING

import openai
from discord import Embed
from langchain_openai import ChatOpenAI

from database import chat as db
from utils.hash import generate_key

from ..chat.callback import CalcTokenCallback, ChatCallback
from ..error import ChatBaseError, ChatResponseError
from ..models import get_model

if TYPE_CHECKING:
    from discord import Message


class BaseAgent:
    def __init__(self, message: "Message", thread_info: dict):
        self.message = message
        self.thread = message.channel
        self.guild = message.guild
        self.key = generate_key(str(self.thread.id), 6)
        self.thread_info = thread_info
        self.llm = self._get_llm(thread_info)

    async def run(self):
        if await db.has_lock(self.guild.name, self.key):
            asyncio.create_task(self._delete_process())
        try:
            await db.lock(self.guild.name, self.key)
            await self._run()
        except openai.APIError as e:
            raise ChatResponseError(e.message)
        except Exception as e:
            traceback.print_exc()
            raise ChatBaseError(str(e))
        finally:
            await db.unlock(self.guild.name, self.key)

    def _get_llm(self, thread_info: dict):
        self.model = get_model(thread_info["model"])
        if self.model.provider == "openai":
            return ChatOpenAI(model=self.model.model)
        else:
            raise ValueError(f"Invalid model '{self.model}'")

    async def _delete_process(self):
        embed = Embed(
            title="아직 답변이 완료되지 않았어요.",
            description="10초 뒤에 질문이 삭제됩니다.",
        )
        reply_msg = await self.message.reply(embed=embed)
        await asyncio.sleep(10)
        await reply_msg.delete()
        await self.message.delete()

    def _get_callbacks(self):
        token_callback = CalcTokenCallback()
        chat_callback = ChatCallback(self.message)
        return [token_callback, chat_callback]
