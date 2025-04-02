from collections.abc import Sequence

from pydantic_ai.agent import Agent, AgentRunResult
from pydantic_ai.messages import UserContent

from lightblue_ai.mcps import get_mcp_servers
from lightblue_ai.models import infer_model
from lightblue_ai.prompts import get_context, get_system_prompt
from lightblue_ai.settings import Settings
from lightblue_ai.tools.manager import LightBlueToolManager


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
