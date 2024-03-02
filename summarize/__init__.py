import datetime
import json
import os
from typing import TYPE_CHECKING

import discord
import openai

if TYPE_CHECKING:
    from discord.abc import MessageableChannel
    from openai.types.chat import ChatCompletionMessageParam

MAX_DAYS = 10
ALLOW_CHANNEL_TYPES = [discord.ChannelType.text]
SYSTEM_MESSAGE = """당신은 채팅을 요약하는 서포터 입니다.
채팅은 json 형식으로 제공됩니다.
당신은 채팅의 시간과 작성자를 보며 채팅의 맥락을 이해해야 하고 채팅을 보지 못한 유저가 쉽게 이해할 수 있도록 채팅 내용을 요약해야 합니다.
요약한 내용은 text 형식으로 제공되어야 하며 채팅을 작성한 유저를 언급하기 위해선 <@유저아이디> 형식으로 작성해야 합니다. (ex. <@1234567890>가 인사합니다.)
요약은 2000자 이내로 작성해야 합니다."""


def check_time(time: int) -> bool:
    return time <= 24 * MAX_DAYS


def check_channel(channel: "MessageableChannel") -> bool:
    return channel.type in ALLOW_CHANNEL_TYPES


async def get_channel_messages(
    channel: "MessageableChannel", time: int
) -> list[discord.Message]:
    now = datetime.datetime.now()
    base = now - datetime.timedelta(hours=time)
    messages = []
    async for message in channel.history(limit=None, after=base, oldest_first=True):
        messages.append(message)
    return messages


async def get_summary(messages: list[discord.Message]) -> str:
    message_data = get_message_data(messages)
    json_data = json.dumps(message_data, ensure_ascii=False, indent=4, default=str)
    result = await get_response(json_data)
    return result


def get_message_data(messages: list[discord.Message]) -> list[dict]:
    message_data = []
    for message in messages:
        data = {
            "id": message.id,
            "author": message.author.id,
            "content": message.content,
            "created_at": message.created_at,
            "file": message.attachments,
            "type": message.type.name,
        }
        if message.reference is not None:
            data["reply_from"] = message.reference.message_id
        message_data.append(data)
    return message_data


async def get_response(message_data: str) -> str:
    client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=get_chat_message(message_data),
    )
    return completion.choices[0].message.content or ""


def get_chat_message(message_data: str) -> list["ChatCompletionMessageParam"]:
    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": message_data},
    ]
