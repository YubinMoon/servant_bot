import asyncio
import os
from typing import TYPE_CHECKING

import openai
from discord import Embed
from httpx import delete

from ..chat.agent import AgentManager
from ..chat.callback import ChatCallback
from ..chat.manager import ChatManager
from ..chat.tool import ToolManager
from ..error import ChatBaseError, ChatResponseError
from .base import BaseMessageHandler

if TYPE_CHECKING:
    from discord import Message

    from bot import ServantBot


class ChatHandler(BaseMessageHandler):
    logger_name = "chat_handler"
    base_response_txt = "생각 중..."

    def __init__(self, bot: "ServantBot", message: "Message") -> None:
        super().__init__(bot, message)
        self.cooldown = 1.5
        self.response_txt = self.base_response_txt
        self.old_response_txt = self.response_txt
        self.tool_handler = ToolManager(bot, self.thread)
        self.agent_manager = AgentManager(bot, message)
        self.chat_callback = ChatCallback(bot, message)

    async def action(self):
        if await self.is_lock():
            return
        try:
            self.db.lock(self.guild.name, self.key)
            agent = self.agent_manager.get_agent()
            await agent.ainvoke(
                {"input": self.message.content},
                config={
                    "configurable": {"session_id": ""},
                    "callbacks": [self.chat_callback],
                },
            )
        except openai.APIError as e:
            raise ChatResponseError(e.message)
        except Exception as e:
            raise ChatBaseError(str(e))
        finally:
            self.db.unlock(self.guild.name, self.key)

    async def is_lock(self) -> bool:
        if self.db.has_lock(self.guild.name, self.key):
            asyncio.create_task(self.delete_process())
            return True
        return False

    async def delete_process(self):
        embed = Embed(
            title="아직 답변이 완료되지 않았어요.",
            description="10초 뒤에 질문이 삭제됩니다.",
        )
        reply_msg = await self.message.reply(embed=embed)
        await asyncio.sleep(10)
        await reply_msg.delete()
        await self.message.delete()

    async def handle_file(self) -> None:
        files = self.message.attachments
        for file in files:
            if file.filename.endswith(".txt"):
                content = await file.read()
                self.chat_manager.append_user_message(
                    content.decode("utf-8"), self.message.id
                )
                if self.message.content == "":
                    embed = Embed(
                        title="'txt' 파일 업로드 완료",
                        description="채팅 질문과 함께 입력돼요.",
                    )
                    await self.message.reply(embed=embed)

    async def handle_content(self) -> None:
        content = self.message.content
        if content == "":
            return
        self.chat_manager.append_user_message(self.message.content, self.message.id)

    async def update_channel_name(self) -> None:
        new_name = await self.chat_manager.get_channel_name()
        self.logger.info(f"channel name: {self.thread.name} -> {new_name}")
        # set to db
