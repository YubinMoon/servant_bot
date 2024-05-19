from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord import Message


class AutoGPTAgent:
    def __init__(self, message: "Message", thread_info: dict):
        self.message = message

    async def run(self):
        pass
        # if await self.is_lock():
        #     return
        # try:
        #     self.db.lock(self.guild.name, self.key)
        #     contents = await self.get_contents()
        #     await self.user_token_manager.check_balance()
        #     agent = self.agent_manager.get_agent(self.tool_manager.get_tools())
        #     await agent.ainvoke(
        #         {"input": contents},
        #         config={
        #             "configurable": {"session_id": ""},
        #             "callbacks": [self.chat_callback, self.token_callback],
        #         },
        #     )
        #     await self.user_token_manager.token_process(self.token_callback.to_dict())
        # except openai.APIError as e:
        #     raise ChatResponseError(e.message)
        # except Exception as e:
        #     traceback.print_exc()
        #     raise ChatBaseError(str(e))
        # finally:
        #     self.db.unlock(self.guild.name, self.key)
