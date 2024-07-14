from typing import Any, Dict, Optional

from .base import get_async_redis


async def set_thread_info(guild_name: str, key: str, data: Dict[str, Any]) -> None:
    async with get_async_redis() as db:
        await db.json().set(f"chat:{guild_name}:{key}:info", "$", data)


async def get_thread_info(guild_name: str, key: str) -> Optional[Dict[str, Any]]:
    async with get_async_redis() as db:
        result = await db.json().get(f"chat:{guild_name}:{key}:info")
    return result


async def has_lock(guild_name: str, key: str) -> bool:
    async with get_async_redis() as db:
        num_of_keys = await db.exists(f"chat:{guild_name}:{key}:lock")
    return num_of_keys > 0


async def lock(guild_name: str, key: str) -> None:
    async with get_async_redis() as db:
        await db.set(f"chat:{guild_name}:{key}:lock", "1")


async def unlock(guild_name: str, key: str) -> None:
    async with get_async_redis() as db:
        await db.delete(f"chat:{guild_name}:{key}:lock")
