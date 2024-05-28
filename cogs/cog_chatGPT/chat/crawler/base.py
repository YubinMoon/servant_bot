import re

import requests
from bs4 import BeautifulSoup


class CrawlerInfo:
    def __init__(self, title, description, content):
        self.title = title
        self.description = description
        self.content = content

    def __repr__(self):
        return f"title: {self.title}\ndescription: {self.description}"


class BaseCrawler:
    def __init__(self, url):
        headers = {"User-Agent": "Mozilla/5.0"}
        req = requests.get(url, headers=headers)
        if req.status_code != 200:
            raise Exception(f"Failed to fetch the URL: {url}\ndetail: {req.text}")
        self._soup = BeautifulSoup(req.content, "html.parser")

    @property
    def info(self):
        return CrawlerInfo(self.title, self.description, self.content)

    @property
    def title(self):
        return self._soup.find("meta", property="og:title")["content"]

    @property
    def description(self):
        return self._soup.find("meta", property="og:description")["content"]

    @property
    def image(self):
        return self._soup.find("meta", property="og:image")["content"]

    @property
    def content(self):
        _content = self._soup.get_text()
        return re.sub(r"\n\n+", "\n", _content)
