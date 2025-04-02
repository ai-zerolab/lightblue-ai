from typing import Annotated

from pydantic import Field
from pydantic_ai.agent import Agent

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
        )

        self.sub_agent = Agent(
            infer_model(self.settings.default_model),
            system_prompt=get_system_prompt(
                context=get_context(),
            ),
            tools=self.tool_manager.get_sub_agent_tools(),
        )

        @self.agent.tool_plain
        async def dispatch_agent(prompt: Annotated[str, Field(description="")]) -> str:
            """ """
            return await self.sub_agent.run(prompt)
