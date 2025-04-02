from collections.abc import Sequence

from pydantic_ai.agent import Agent, AgentRunResult
from pydantic_ai.messages import UserContent

from lightblue.mcps import get_mcp_servers
from lightblue.models import infer_model
from lightblue.prompts import get_context, get_system_prompt
from lightblue.settings import Settings
from lightblue.tools.manager import LightBlueToolManager


class LightBlueAgent:
    def __init__(self):
        self.tool_manager = LightBlueToolManager()
        self.settings = Settings()

        self.agent = Agent(
            infer_model(self.settings.default_model),
            system_prompt=get_system_prompt(
                context=get_context(),
            ),
            tools=self.tool_manager.get_all_tools(),
            mcp_servers=get_mcp_servers(),
        )

    async def run(self, user_prompt: str | Sequence[UserContent]) -> AgentRunResult[str]:
        async with self.agent.run_mcp_servers():
            return await self.agent.run(user_prompt)


if __name__ == "__main__":
    import asyncio

    async def main():
        agent = LightBlueAgent()
        result = await agent.run("Who you are")
        print(result.data)

        print(f"All messages: {result.all_messages()}")
        print(f"Usage: {result.usage()}")

    asyncio.run(main())
