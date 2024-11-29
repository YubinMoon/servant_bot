import re

import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o")


def find_urls(text: str) -> list[str]:
    url_regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$\-@\._&+:/?=]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

    reg = re.compile(url_regex)

    res = reg.findall(text)
    return res


def get_token_count(text: str) -> int:
    return len(enc.encode(text))
