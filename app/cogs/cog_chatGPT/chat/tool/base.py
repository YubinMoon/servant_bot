from langchain_core.tools import BaseTool


class ToolBase:
    name: str
    description: str
    tool: BaseTool
