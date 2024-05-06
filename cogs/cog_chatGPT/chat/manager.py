from typing import TYPE_CHECKING

from database import UserDataManager

from ..error import ChatResponseError

if TYPE_CHECKING:
    from discord import User

    from bot import ServantBot


class UserTokenManager:
    def __init__(self, bot: "ServantBot", user: "User"):
        self.bot = bot
        self.user = user
        self.db = UserDataManager(bot, user)

    async def token_process(self, data: dict[str, int]) -> None:
        await self.record_tokens(data)
        await self.use_balance(data)

    async def check_balance(self) -> None:
        balance = await self.get_balance()
        if balance <= 0:
            raise ChatResponseError("잔액이 부족합니다.")

    async def get_balance(self) -> int:
        balance = self.db.get_token()
        if balance is None:
            balance = self.bot.config["default_token_balance"]
            self.db.set_token(balance)
        return int(balance)

    async def use_balance(self, usage: dict[str, int]) -> None:
        balance = await self.get_balance()
        total_tokens = usage["total_tokens"]
        balance = max(0, balance - total_tokens)
        self.db.set_token(balance)

    async def record_tokens(self, usage: dict[str, int]) -> None:
        model = usage["chat_model"]
        data = self.db.get_used_tokens(model)
        if data is None:
            data = dict()

        new_data = usage.copy()

        new_data["prompt_tokens"] += float(data.get("prompt_tokens", 0))
        new_data["completion_tokens"] += float(data.get("completion_tokens", 0))
        new_data["tool_tokens"] += float(data.get("tool_tokens", 0))
        new_data["total_tokens"] += float(data.get("total_tokens", 0))
        new_data["prompt_cost"] += float(data.get("prompt_cost", 0))
        new_data["completion_cost"] += float(data.get("completion_cost", 0))
        new_data["tool_cost"] += float(data.get("tool_cost", 0))
        new_data["total_cost"] += float(data.get("total_cost", 0))

        self.db.set_used_tokens(model, new_data)
