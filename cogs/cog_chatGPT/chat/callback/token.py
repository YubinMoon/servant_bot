from typing import Any, Dict, List

import tiktoken
from langchain_community.callbacks.openai_info import get_openai_token_cost_for_model
from langchain_core.callbacks.base import AsyncCallbackHandler

enc = tiktoken.get_encoding("cl100k_base")


class CalcTokenCallback(AsyncCallbackHandler):
    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.tool_tokens = 0
        self.prompt_cost = 0
        self.completion_cost = 0
        self.tool_cost = 0
        self.total_cost = 0.0
        self.chat_model = "gpt-3.5-turbo"

    def __repr__(self) -> str:
        return (
            f"Tokens Used: {self.prompt_tokens + self.completion_tokens + self.tool_tokens}\n"
            f"\tPrompt Tokens: {self.prompt_tokens}\n"
            f"\tCompletion Tokens: {self.completion_tokens}\n"
            f"\tTool Tokens: {self.tool_tokens}\n"
            f"Total Cost (USD): ${self.total_cost:f}\n"
            f"\tPrompt Cost (USD): ${self.prompt_cost:f}\n"
            f"\tCompletion Cost (USD): ${self.completion_cost:f}"
            f"\tTool Cost (USD): ${self.tool_cost:f}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "tool_tokens": self.tool_tokens,
            "total_tokens": self.prompt_tokens
            + self.completion_tokens
            + self.tool_tokens,
            "prompt_cost": self.prompt_cost,
            "completion_cost": self.completion_cost,
            "tool_cost": self.tool_cost,
            "total_cost": self.total_cost,
        }

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Count prompt token length."""
        self.prompt_tokens += len(enc.encode(prompts[0]))
        self.chat_model = serialized["kwargs"]["model_name"]

    async def on_llm_new_token(self, token: str, **kwargs):
        """Count output tokens."""
        self.completion_tokens += 1

    async def on_llm_end(self, response, **kwargs: Any) -> None:
        """Calculate total token costs."""
        self.prompt_cost = get_openai_token_cost_for_model(
            self.chat_model, self.prompt_tokens
        )
        self.completion_cost = get_openai_token_cost_for_model(
            self.chat_model, self.completion_tokens, is_completion=True
        )
        self.tool_cost = 0.00002 * self.tool_tokens
        self.total_cost = self.prompt_cost + self.completion_cost + self.tool_cost

    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        if serialized["name"] == "dall-e_Image_Generator":
            self.tool_tokens += 4_000
