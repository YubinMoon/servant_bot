import logging
from typing import TYPE_CHECKING

from agents import Runner, TResponseInputItem
from pydantic import BaseModel

from app.core.agent.agents import BotContext, gemini_agent

if TYPE_CHECKING:
    from .controller import MessageData

logger = logging.getLogger(__name__)

message_db: dict[int, list[TResponseInputItem]] = {}


class ThreadInfo(BaseModel):
    title: str
    nofication: str


async def gen_thread_info(thread_id: int, user_id: int, message: str) -> ThreadInfo:
    context = BotContext(thread_id=thread_id, user_id=user_id)
    generator = gemini_agent.clone(
        instructions="너는 훌룡한 제목 및 문구 생성기야 사용자의 요구에 따라 적절한 문구를 생성해야 해",
        output_type=ThreadInfo,
    )

    result = await Runner.run(
        generator,
        (
            f"<goal>{message}</goal>\n"
            "위 내용을 바탕으로 적절한 제목과 문구를 생성해줘.\n"
            "제목은 디스코드 Thread 제목으로 사용될거야.\n"
            "문구는 Thread를 생성하기 위한 Message로 사용될거야.\n"
            "Thread가 생성되는 이유는 유저가 AI Agent와 새로운 대화를 시작하기 위함이야\n"
            "goal tag가 비어있더라도 적절한 제목과 문구를 생성해줘\n"
            "너무 딱딱하게 작성하지 말고, 친근한 느낌으로 작성해줘\n"
            "이제 제목을 생성해봐."
        ),
        context=context,
    )
    return result.final_output


def call_agent(
    thread_id: int,
    user_id: int,
    messages: "list[TResponseInputItem]",
):
    context = BotContext(thread_id=thread_id, user_id=user_id)
    result = Runner.run_streamed(
        gemini_agent,
        messages,
        context=context,
    )
    return result


def get_message(thread_id: int) -> list[TResponseInputItem]:
    return message_db.get(thread_id, [])[-12:]


def save_message(thread_id: int, messages: list[TResponseInputItem]) -> None:
    message_db[thread_id] = messages
