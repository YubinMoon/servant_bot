from .base import get_redis


async def get_used_tokens(user_name: str):
    db = await get_redis()
    db.hgetall(f"user:{user_name}:token")


async def set_used_tokens(user_name: str, data: dict[str, int]):
    db = await get_redis()
    db.hmset(f"user:{user_name}:token", data)
