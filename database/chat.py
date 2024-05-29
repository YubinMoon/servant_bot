from .base import get_redis


async def set_thread_info(guild_name: str, key: str, data: dict) -> None:
    db = await get_redis()
    db.json().set(f"chat:{guild_name}:{key}:info", "$", data)


async def get_thread_info(guild_name: str, key: str) -> dict | None:
    db = await get_redis()
    result = db.json().get(f"chat:{guild_name}:{key}:info")
    if result is None:
        return None
    return result


async def has_lock(guild_name: str, key: str) -> bool:
    db = await get_redis()
    num_of_keys = db.exists(f"chat:{guild_name}:{key}:lock")
    return num_of_keys > 0


async def lock(guild_name: str, key: str) -> None:
    db = await get_redis()
    db.set(f"chat:{guild_name}:{key}:lock", "1")


async def unlock(guild_name: str, key: str) -> None:
    db = await get_redis()
    db.delete(f"chat:{guild_name}:{key}:lock")
