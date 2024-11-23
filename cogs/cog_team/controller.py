from typing import TYPE_CHECKING

from discord import Embed

from utils.color import Colors

if TYPE_CHECKING:
    from discord.ext.commands import Context


class BaseController:
    pass


class NewTeamController(BaseController):
    def __init__(self, context: "Context") -> None:
        self.context = context

    async def setup_embed(self, name: str) -> int:
        embed = Embed(
            title=f"{name} 팀이 구성되었어요.",
            description="**/j**로 참여... 하든가 말든가",
            color=Colors.BASE,
        )
        embed.add_field(name=f"현제 인원: 0", value="")
        embed.set_footer(text="/s로 굴릴 수 있어요. /c로 팀 등록을 취소할 수 있어요.")
        message = await self.context.send(embed=embed, silent=True)
        return message.id
