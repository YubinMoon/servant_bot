from langchain_community.tools.tavily_search import TavilySearchResults

from .base import ToolBase


class TavilySearch(ToolBase):
    name: str = "tavily 검색"
    description: str = "AI용 온라인 검색 도구"
    tool = TavilySearchResults()
