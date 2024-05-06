import asyncio
import traceback
from typing import TYPE_CHECKING

import openai
from discord import Embed

from utils.file import txt_files_from_message

from ..chat.agent import AgentManager
from ..chat.callback import CalcTokenCallback, ChatCallback
from ..chat.manager import UserTokenManager
from ..chat.memory import MemoryManager
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
        self.chat_callback = ChatCallback(bot, message=message)
        self.token_callback = CalcTokenCallback()
        self.user_token_manager = UserTokenManager(bot, message.author)
        memory_manager = MemoryManager(bot, message)
        self.agent_manager = AgentManager(bot, message, memory_manager)
        self.tool_manager = ToolManager(bot, self.thread, memory_manager)

    async def action(self):
        if await self.is_lock():
            return
        try:
            self.db.lock(self.guild.name, self.key)
            contents = await self.get_contents()
            await self.user_token_manager.check_balance()
            agent = self.agent_manager.get_agent(self.tool_manager.get_tools())
            await agent.ainvoke(
                {"input": contents},
                config={
                    "configurable": {"session_id": ""},
                    "callbacks": [self.chat_callback, self.token_callback],
                },
            )
            await self.user_token_manager.token_process(self.token_callback.to_dict())
        except openai.APIError as e:
            raise ChatResponseError(e.message)
        except Exception as e:
            traceback.print_exc()
            raise ChatBaseError(str(e))
        finally:
            self.db.unlock(self.guild.name, self.key)

    async def is_lock(self) -> bool:
        if self.db.has_lock(self.guild.name, self.key):
            asyncio.create_task(self.delete_process())
            return True
        return False

    async def get_contents(self) -> str:
        contents = []
        files = txt_files_from_message(self.message)
        for file in files:
            content: bytes = await file.read()
            contents.append(content.decode("utf-8"))

        contents.append(self.message.content)
        return "\n\n".join(contents)

    async def delete_process(self):
        embed = Embed(
            title="아직 답변이 완료되지 않았어요.",
            description="10초 뒤에 질문이 삭제됩니다.",
        )
        reply_msg = await self.message.reply(embed=embed)
        await asyncio.sleep(10)
        await reply_msg.delete()
        await self.message.delete()
