from .base import ToolBase
from .tavily_search import TavilySearch


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
