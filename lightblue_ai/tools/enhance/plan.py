from typing import Annotated

from pydantic import Field
from pydantic_ai.tools import Tool

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class PlanTool(LightBlueTool):
    def __init__(self):
        self.name = "Plan"
        self.scopes = [Scope.read]
        self.description = (
            "Use the tool to draw a plan in markdown. "
            "It will not obtain new information or change the database, "
            "but just append the plan to the log. "
            "Use it when complex tasks like search or planning are needed. "
            "Use it multiple times to complete a complex task if necessary."
        )

    async def _plan(
        self,
        plan: Annotated[str, Field(description="A plan for the task.")],
    ) -> str:
        return str

    def init_tool(self) -> Tool:
        return Tool(
            function=self._plan,
            name=self.name,
            description=self.description,
        )


@hookimpl
def register(manager):
    manager.register(PlanTool())
