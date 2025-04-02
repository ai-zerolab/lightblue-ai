from collections.abc import Sequence
from typing import TypeVar

from pydantic_ai.agent import Agent, AgentRunResult
from pydantic_ai.messages import UserContent

from lightblue_ai.mcps import get_mcp_servers
from lightblue_ai.models import infer_model
from lightblue_ai.prompts import get_context, get_system_prompt
from lightblue_ai.settings import Settings
from lightblue_ai.tools.manager import LightBlueToolManager

T = TypeVar("T")


class LightBlueAgent[T]:
    def __init__(
        self,
        result_type: T = str,
        result_tool_name: str = "final_result",
        result_tool_description: str | None = None,
    ):
        self.tool_manager = LightBlueToolManager()
        self.settings = Settings()

        self.agent = Agent(
            infer_model(self.settings.default_model),
            result_type=result_type,
            result_tool_name=result_tool_name,
            result_tool_description=result_tool_description,
            system_prompt=get_system_prompt(),
            tools=self.tool_manager.get_all_tools(),
            mcp_servers=get_mcp_servers(),
        )

    async def run(self, user_prompt: str | Sequence[UserContent]) -> AgentRunResult[T]:
        async with self.agent.run_mcp_servers():
            return await self.agent.run(user_prompt)
