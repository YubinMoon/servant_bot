from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import BaseTool


class ToolBase:
    name: str
    description: str
    tool: BaseTool


class TavilySearch(ToolBase):
    name: str = "tavily 검색"
    description: str = "AI용 온라인 검색 도구"
    tool = TavilySearchResults()


def get_all_tools() -> list[ToolBase]:
    return [
        TavilySearch(),
    ]


def get_tools(tools_name: list[str]):
    tools = []
    for tool in get_all_tools():
        if tool.name in tools_name:
            tools.append(tool.tool)
    return tools
