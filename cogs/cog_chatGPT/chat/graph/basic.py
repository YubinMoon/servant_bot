from functools import partial
from typing import Annotated, Literal, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_core.vectorstores import VectorStore
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from sqlalchemy import true
from typing_extensions import TypedDict

from utils.logger import get_logger

from ..checkpoint import RedisSaver
from ..prompt import BasicPrompt

logger = get_logger(__name__)


class BasicState(TypedDict):
    file_data: list[Document]
    messages: Annotated[list[AnyMessage], add_messages]


async def _retrieve(
    state: BasicState, config: RunnableConfig, memory: Optional[VectorStore]
):  # -> dict[str, list] | dict[str, List[Document]]:
    if memory is None:
        print("file_data pass")
        return {"file_data": []}
    retriever = memory.as_retriever(search_kwargs={"k": 10})
    user_messgaes = []
    for message in state["messages"]:
        if isinstance(message, HumanMessage):
            user_messgaes.append(str(message.content))
    user_query = "\n\n".join(user_messgaes[-3:])
    if user_messgaes:
        result = retriever.invoke(user_query)
    else:
        result = retriever.invoke(state["messages"])
    return {"file_data": result}


async def _agent(state: BasicState, config: RunnableConfig, model: BaseChatModel):
    prompt = BasicPrompt()
    chain = prompt | model.with_config(tags=["agent_node"])
    result = await chain.ainvoke(state, config=config)
    return {"messages": result}


def get_basic_app(
    model: Literal["gpt-4o", "claude-3-5-sonnet-20240620"],
    memory: Optional[VectorStore] = None,
    tools: Optional[BaseTool] = None,
):
    if "gpt" in model:
        _model = ChatOpenAI(model=model, streaming=True, stream_usage=True)
    elif "claude" in model:
        _model = ChatAnthropic(model=model, streaming=True, stream_usage=True)
    else:
        raise ValueError(f"Invalid model '{model}'")

    if tools:
        _model = _model.bind_tools(tools)

    graph_builder = StateGraph(BasicState)

    retrieve = partial(_retrieve, memory=memory)
    agent = partial(_agent, model=_model)

    graph_builder.add_node("retrieve", retrieve)
    graph_builder.add_node("agent", agent)

    graph_builder.add_edge(START, "retrieve")
    graph_builder.add_edge("retrieve", "agent")
    if tools:
        graph_builder.add_node("tools", ToolNode(tools))
        graph_builder.add_conditional_edges("agent", tools_condition)
        graph_builder.add_edge("tools", "agent")
    else:
        graph_builder.add_edge("agent", END)

    checkpoint = AsyncSqliteSaver.from_conn_string("database/sqlite/checkpoint.db")
    # checkpoint = None

    app = graph_builder.compile(checkpointer=checkpoint)

    return app
