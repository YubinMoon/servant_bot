import re

from bs4 import Tag

from .base import BaseCrawler


class BlogCrawler(BaseCrawler):
    def __init__(self, url):
        super().__init__(url)

    @property
    def content(self):
        lines = self._get_article().children
        _content = ""
        for line in lines:
            text = line.get_text().strip()
            if line.name is None or line.name in ["div", "figure"] or len(text) == 0:
                continue
            if line.name == "pre":
                _content += f"```\n{text}\n```\n"
                continue
            for i in range(4):
                if line.name == f"h{i}":
                    _content += f"\n\n{'#' * i} {text}\n"
                    break
            else:
                _content += f"{text}\n"
        return _content

    def _get_article(self) -> Tag:
        raise NotImplementedError


class VelogCrawler(BlogCrawler):
    def __init__(self, url):
        super().__init__(url)

    def _get_article(self):
        return self._soup.find("div", "atom-one")


class TistoryCrawler(BlogCrawler):
    def __init__(self, url):
        super().__init__(url)

    def _get_article(self):
        return (
            self._soup.select_one("div.contents_style")
            or self._soup.select_one("div.article_view")
            or self._soup.select_one("article")
        )


class NaverCrawler(BlogCrawler):
    def __init__(self, url):
        super().__init__(url)

    @property
    def content(self):
        _content = self._get_article().get_text()
        return re.sub(r"\n\n+", "\n", _content)

    def _get_article(self):
        return self._soup.select_one("div.se-main-container") or self._soup.select_one(
            "div.post_ct"
        )


class MediumCrawler(BlogCrawler):
    def __init__(self, url):
        BlogCrawler.__init__(self, url)

    @property
    def content(self):
        return self._get_article().get_text()

    def _get_article(self):
        return self._soup.select_one("article")
