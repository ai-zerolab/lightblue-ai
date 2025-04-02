from typing import Annotated

from pydantic import Field
from pydantic_ai.tools import Tool

from lightblue.tools.base import LightBlueTool, Scope
from lightblue.tools.extensions import hookimpl


class ThinkingTool(LightBlueTool):
    """https://www.anthropic.com/engineering/claude-think-tool"""

    def __init__(self):
        self.scopes = [Scope.read]

    async def _think(
        self,
        thought: Annotated[str, Field(description="A thought to think about.")],
    ) -> dict[str, str]:
        return {
            "thought": thought,
        }

    def init_tool(self) -> Tool:
        return Tool(
            function=self._think,
            name="thinking",
            description="Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed.",
        )


@hookimpl
def register(manager):
    manager.register(ThinkingTool())
