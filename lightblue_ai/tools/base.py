import enum
from abc import ABC, abstractmethod

from pydantic_ai.tools import Tool


class Scope(str, enum.Enum):
    read = "read"
    """Provide context for llm, may write to disk to store context."""

    write = "write"
    """Write, may overwrite existing files"""

    exec = "exec"
    """Exec some command, most dangerous"""

    generation = "generation"
    """AI generation context"""

    web = "web"
    """Web context"""


class LightBlueTool(ABC):
    name: str
    scopes: list[Scope]
    description: str

    @abstractmethod
    async def call(self, *args, **kwargs):
        """Implementation of the tool."""

    def init_tool(self) -> Tool:
        return Tool(
            function=self.call,
            name=self.name,
            description=self.description,
            max_retries=3,
        )

    def is_read_tool(self) -> bool:
        return Scope.read in self.scopes

    def is_write_tool(self) -> bool:
        return Scope.write in self.scopes

    def is_exec_tool(self) -> bool:
        return Scope.exec in self.scopes

    def is_generation_tool(self) -> bool:
        return Scope.generation in self.scopes

    def is_web_tool(self) -> bool:
        return Scope.web in self.scopes
