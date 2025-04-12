from functools import wraps

from ...core.database import get_session


def with_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        with get_session() as session:
            kwargs["session"] = session
            return await func(*args, **kwargs)

    return wrapper
