from typing import TYPE_CHECKING, Type

from langchain_core.callbacks.base import AsyncCallbackHandler

from .autoGPT import AutoGPTAgent
from .base import BaseAgent
from .basic import Basic, BasicLong
from .translator import Translator

if TYPE_CHECKING:
    from discord import Message


class BaseTemplate:
    name: str
    description: str
    agent: Type[BaseAgent]


class BasicTemplate(BaseTemplate):
    name: str = "basic"
    description: str = "기본 템플릿"
    agent = Basic


class BasicLongTemplate(BaseTemplate):
    name: str = "basic-long"
    description: str = "토큰 길이 제한이 없는 기본 템플릿"
    agent = BasicLong


class AutoGPTTemplate(BaseTemplate):
    name: str = "autoGPT"
    description: str = "많은 토큰을 사용하지만 자동으로 목표를 처리하는 템플릿"
    agent = Basic


class TranslatorTemplate(BaseTemplate):
    name: str = "translator"
    description: str = "번역기 템플릿"
    agent = Translator


def get_templates() -> list[BaseTemplate]:
    return [
        BasicTemplate(),
        BasicLongTemplate(),
        # AutoGPTTemplate(),
        TranslatorTemplate(),
    ]


def get_template_agent(
    name: str,
    message: "Message",
    thread_info: dict,
    callbacks: list[AsyncCallbackHandler],
) -> BaseAgent | None:
    for template in get_templates():
        if template.name == name:
            return template.agent(message, thread_info, callbacks)
    return None
