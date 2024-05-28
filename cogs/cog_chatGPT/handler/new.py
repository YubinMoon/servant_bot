from typing import TYPE_CHECKING

from discord import ChannelType

from error.chat import ChannelCreateError
from utils.hash import generate_key

from ..view import ModelSelectView
from .base import BaseCommandHandler

if TYPE_CHECKING:
    from discord import Message, Thread
    from discord.ext.commands import Context

    from bot import ServantBot


class NewChatHandler(BaseCommandHandler):
    logger_name = "new_chat_handler"

    def __init__(self, bot: "ServantBot", context: "Context") -> None:
        super().__init__(bot, context)

    async def action(self):
        await self.check_channel_type()
        new_msg = await self.context.send(f"새 쓰래드를 시작할게요.")
        thread = await new_msg.create_thread(
            name="chat with GPT", auto_archive_duration=60, reason="new chat"
        )
        key = generate_key(str(thread.id), 6)

        await new_msg.edit(content=f"새 쓰래드를 시작했어요. (key={key})")
        await thread.send(self.get_welcome_text())
        await thread.send(content="모델을 선택해주세요.", view=ModelSelectView())
        self.logger.info(f"new chat thread created by {self.author.name}, key={key}")

    async def check_channel_type(self) -> None:
        if self.context.channel.type is not ChannelType.text:
            raise ChannelCreateError(f"The channel is not a text channel.")

    def get_welcome_text(self) -> str:
        text = [
            "# 새로운 채팅을 시작했어요.",
            "## 기본 사용 가이드",
            f"해당 쓰레드에 메시지를 보내면, {self.bot.user.mention}가 대답을 해줄 거에요.",
            "쓰레드를 나가도 채팅 기록은 유지돼요.",
            f"{self.bot.user.mention}의 대답이 끝나기 전 물어본 질문은 무시되고 삭제돼요.",
            "## 사용 팁",
            f"{self.bot.user.mention}는 정보를 검색하는 용도로는 적합하지 않아요.",
            "정보가 있는 텍스트를 미리 입력한 뒤 그 정보를 바탕으로 대화하는 것이 더 효율적이에요.",
            "최대한 자세히 요구사항을 적을 수록 더 정확한 답변을 받을 수 있어요.",
            "`txt`파일을 업로드 하면 다음 질문과 함께 입력돼요.",
            "## 명령어",
            "- ?: 사용 가능한 명령어를 보여줘요.",
        ]

        return "\n".join(text)
