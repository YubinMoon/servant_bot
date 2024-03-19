import json

import tiktoken

encoding = tiktoken.get_encoding("cl100k_base")


def num_tokens_from_string(string: str) -> int:
    num_tokens = len(encoding.encode(string))
    return num_tokens


def num_tokens_from_messages(messages: list[dict[str, str | dict]]):
    tokens_per_message = 3
    tokens_per_name = 1
    num_tokens = 0

    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if value is str:
                num_tokens += len(encoding.encode(value))
            else:
                json_value = json.dumps(value)
                num_tokens += len(encoding.encode(json_value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
