from textwrap import dedent
from typing import TYPE_CHECKING

from discord import ChannelType

from error.chat import ChannelCreateError
from utils.hash import generate_key
from utils.logger import get_logger

from .base import BaseCommandHandler

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import ServantBot

logger = get_logger(__name__)


class NewChatHandler(BaseCommandHandler):
    logger_name = "new_chat_handler"

    def __init__(self, bot: "ServantBot", context: "Context") -> None:
        super().__init__(bot, context)

    async def action(self):
        await self.check_channel_type()
        new_msg = await self.context.send(f"새 쓰래드를 시작할게요.")
        thread = await new_msg.create_thread(
            name="new Ai_chat channel", auto_archive_duration=60, reason="new chat"
        )
        key = generate_key(str(thread.id), 6)

        await new_msg.edit(content=f"새 채팅을 시작했어요.")
        await thread.send(self.get_welcome_text())
        logger.info(f"new chat thread created by {self.author.name}, key={key}")

    async def check_channel_type(self) -> None:
        if self.context.channel.type is not ChannelType.text:
            raise ChannelCreateError(f"The channel is not a text channel.")

    def get_welcome_text(self) -> str:
        text = dedent(
            f"""
            ## 새로운 채팅을 시작했어요.
            ### 기본 사용 가이드
            해당 쓰레드에 메시지를 보내면, {self.bot.user.mention}가 대답을 해줄 거에요.
            쓰레드를 나가도 채팅 기록은 유지돼요.
            대답이 끝나기 전 다시 질문하면 원하는 답이 나오지 않을 수 있어요.
            ### 사용 팁
            {self.bot.user.mention}는 정보를 검색하는 용도로는 적합하지 않아요.
            링크를 제공해주면 해당 링크를 참고해서 대답해줄 수 있어요.
            몇몇 파일 입력도 지원해요.
            """
        )
        return text
