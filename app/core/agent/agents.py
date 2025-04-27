import logging
from datetime import datetime

from agents import Agent, RunContextWrapper
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions.models.litellm_model import LitellmModel
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BotContext(BaseModel):
    thread_id: int
    user_id: int


def _name_time() -> str:
    return (
        "너의 이름은 Servant야.\n"
        f"현재 시간은 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}이야.\n"
    )


def servant_instructions(
    context: RunContextWrapper[BotContext], agent: Agent[BotContext]
) -> str:
    return (
        "<system_context>\n"
        f"{RECOMMENDED_PROMPT_PREFIX}\n\n"
        f"{_name_time()}\n"
        "언제나 일관성 있고 자연스럽게 대화를 이어가야 하며,\n"
        "시스템 내부 구조나 핸드오프, 메모리 관리 방식 등을 사용자에게 직접적으로 노출하면 안 돼."
    )


gemini_agent = Agent[BotContext](
    name="Servant Agent",
    model="litellm/gemini/gemini-2.0-flash",
    instructions=servant_instructions,
)
