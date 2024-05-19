from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool

wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())


def get_tools():
    return [wikipedia]
