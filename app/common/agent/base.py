import logging

from agents import Agent, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel
from litellm import Reasoning
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BotContext(BaseModel):
    thread_id: int
    user_id: int


test_agent = Agent[BotContext](
    name="Test Agent",
    model="litellm/gemini/gemini-2.0-flash",
    instructions="You are a test agent. Answer the question.",
)
