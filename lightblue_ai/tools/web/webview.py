# We should use curl or playwright?from typing import Annotated

from typing import Annotated

import httpx
from pydantic import Field
from pydantic_ai import BinaryContent, RunContext

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl
from lightblue_ai.utils import PendingMessage


class WebViewTool(LightBlueTool):
    def __init__(self):
        self.name = "view_web_file"
        self.scopes = [Scope.web]
        self.description = ""
        self.client = httpx.AsyncClient()

    async def call(
        self,
        ctx: RunContext[PendingMessage],
        url: Annotated[str, Field(description="URL of the web resource to view")],
    ) -> str | BinaryContent:
        pass


@hookimpl
def register(manager):
    manager.register(WebViewTool())
