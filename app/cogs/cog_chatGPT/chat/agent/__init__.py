from typing import Type

from .autoGPT import AutoGPTAgent
from .base import BaseAgent
from .basic import Basic, BasicLong
from .translator import Translator


def get_agents() -> list[Type[BaseAgent]]:
    return [
        Basic,
        BasicLong,
        AutoGPTAgent,
        Translator,
    ]


def get_agent_by_name(name: str) -> Type[BaseAgent] | None:
    for agent in get_agents():
        if agent.name == name:
            return agent
    return None
