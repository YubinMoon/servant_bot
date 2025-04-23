import logging
from typing import TYPE_CHECKING

from agents import Runner

from app.common.agent import BotContext, test_agent

if TYPE_CHECKING:
    from .controller import MessageData

logger = logging.getLogger(__name__)


async def call_agent(
    thread_id: int,
    user_id: int,
    messages: "list[MessageData]",
):
    context = BotContext(thread_id=thread_id, user_id=user_id)
    contents = [message.to_content() for message in messages]
    result = await Runner.run(
        test_agent,
        [
            {
                "role": "user",
                "content": contents,
            }
        ],
        context=context,
    )
    return result.final_output
