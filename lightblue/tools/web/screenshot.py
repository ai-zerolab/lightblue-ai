# Once we take screenshots, we need to re-prompt llm as BinaryContent

from pydantic_ai import RunContext
from pydantic_ai.tools import Tool

from lightblue.deps import AgentContext
from lightblue.tools.base import LightBlueTool, Scope
from lightblue.tools.extensions import hookimpl


class ScreenshotTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.read]
        self.description = "Take screenshot of the current page"

    def _screenshot(self, ctx: RunContext[AgentContext]):
        """We attatch it to AgentContext for next round prompt"""
        pass

    def init_tool(self) -> Tool:
        return Tool(
            function=self._screenshot,
            name="screenshot",
            description=self.description,
        )


@hookimpl
def register(manager):
    manager.register(ScreenshotTool())
