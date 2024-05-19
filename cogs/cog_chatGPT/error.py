from discord import Embed

from utils import color


class ChatBaseError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"

    def get_embed(self):
        embed = Embed(
            title="에러가 발생했어요.",
            description=f"```\n{self.message}\n```",
            color=color.ERROR,
        )
        return embed


class UnknownCommandError(ChatBaseError):
    def __init__(self, message: str):
        super().__init__(message)

    def get_embed(self):
        embed = Embed(
            title="알 수 없는 명령어에요.",
            description="**'?'**으로 사용 가능한 명령어를 확인해 주세요.",
            color=color.ERROR,
        )
        return embed


class ChatResponseError(ChatBaseError):
    def __init__(self, message: str):
        super().__init__(message)

    def get_embed(self):
        embed = Embed(
            title="챗봇 응답에 문제가 있어요.",
            description=f"```\n{self.message}\n```",
            color=color.ERROR,
        )
        return embed


class ContentFilterError(ChatBaseError):
    def __init__(self, message: str):
        super().__init__(message)

    def get_embed(self):
        embed = Embed(
            title="여러므로 문자가 되는 질문이에요.",
            description=f"정상적인 질문을 입력해 주세요.",
            color=color.ERROR,
        )
        return embed


class NoHistoryError(ChatBaseError):
    def __init__(self, message: str):
        super().__init__(message)

    def get_embed(self):
        embed = Embed(
            title="이전 대화가 없어요.",
            description=f"새로운 대화를 시작해 주세요.",
            color=color.ERROR,
        )
        return embed


class ChannelCreateError(ChatBaseError):
    def __init__(self, message: str):
        super().__init__(message)

    def get_embed(self):
        embed = Embed(
            title="채널 생성에 실패했어요.",
            description=f"```\n{self.message}\n```",
            color=color.ERROR,
        )
        return embed


class NoAITypeError(ChatBaseError):
    def __init__(self, message: str):
        super().__init__(message)

    def get_embed(self):
        embed = Embed(
            title="AI 모델을 선택하지 않았어요.",
            description=f"AI 모델을 선택해 주세요.",
            color=color.ERROR,
        )
        return embed
