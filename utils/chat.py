import re


def find_urls(text: str) -> list[str]:
    url_regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$\-@\._&+:/?=]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"

    reg = re.compile(url_regex)

    res = reg.findall(text)
    return res
