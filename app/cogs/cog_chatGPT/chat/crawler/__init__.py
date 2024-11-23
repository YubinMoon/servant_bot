from .base import BaseCrawler, CrawlerInfo
from .blog import *


def get_url_info(url: str) -> CrawlerInfo:
    if "blog.naver.com" in url:
        return NaverCrawler(url).info
    elif "tistory.com" in url:
        return TistoryCrawler(url).info
    elif "velog.io" in url:
        return VelogCrawler(url).info
    elif "medium.com" in url:
        return BaseCrawler(url).info
    return BaseCrawler(url).info
