from .base import get_redis


async def get_used_tokens(user_name: str):
    async with get_redis() as db:
        db.hgetall(f"user:{user_name}:token")


async def set_used_tokens(user_name: str, data: dict[str, int]):
    async with get_redis() as db:
        db.hmset(f"user:{user_name}:token", data)
