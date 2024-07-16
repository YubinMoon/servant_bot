from textwrap import dedent
from typing import Annotated

import requests
from bs4 import BeautifulSoup
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from utils.chat import get_token_count

model = ChatOpenAI(model="gpt-3.5-turbo")


def truncate_by_token(text: str, max_tokens: int, token_counter_func) -> str:
    if token_counter_func(text) <= max_tokens:
        return text

    left, right = 0, len(text)
    while right - left > 1:
        mid = (left + right) // 2
        if token_counter_func(text[:mid]) > max_tokens:
            right = mid
        else:
            left = mid

    return text[:left]


@tool
def summarize_web(
    url: Annotated[str, "url to summarize"],
    query: Annotated[str, "query to summarize"] = "",
):
    """
    A tool for summarizing website content using AI.
    By entering a query, you can obtain data by summarizing the site with a focus on the necessary content.
    example: {"url":"https://openai.com/api/pricing/","query":"Tell me the types of models that handle audio and the price of each model.
    "}
    """
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        site = soup.get_text(separator="\n", strip=True)
    else:
        return f"Error: failed to fetch the '{url}' content."

    site = truncate_by_token(site, 9000, get_token_count)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=dedent(
                    """
                    You are a website summarizer.
                    You have summarized numerous websites so far, gaining the ability to include all necessary information while summarizing the content of websites.
                    Now, you need to summarize the content of the website presented by the user to assist them.
                    Utilize your experience to remove unnecessary content from the website and preserve all important information to provide a reconstructed summary to the user.

                    Follow these guidelines:
                    - The content of the website is contained within the <site> tag. You need to organize the content within this tag to write your response.
                    - <query> is the specific information the user wants to obtain from the site, and you should refer to this content when writing your response.
                    - The final response should be written within the <answer> tag.

                    Input example:
                    <site>
                    (User-provided site content)
                    </site>
                    <query>
                    (Specific information the user wants)
                    </query>
                    Output example:
                    <answer>
                    Your summarized site content
                    </answer>
                    """
                )
            ),
            (
                "human",
                "<site>\n{site}\n</site>\n<query>\n{query}\n</query>",
            ),
        ]
    )
    chain = prompt | model
    result = chain.invoke({"site": site, "query": query})
    content = result.content
    return content.replace("<answer>", "").replace("</answer>", "").strip()
