from typing import Annotated, Any

import httpx
from pydantic import Field
from pydantic_ai.tools import Tool

from lightblue_ai.settings import Settings
from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class PixabaySearchImageTool(LightBlueTool):
    def __init__(self):
        self.name = "search_image"
        self.scopes = [Scope.web]
        self.description = """Search images from internet via Pixabay. Use this tool if you need to find images from the internet.

query: A Search term. If omitted, all images are returned. This value may not exceed 100 characters. Example: "yellow+flower"
"""
        self.settings = Settings()
        self.client = httpx.AsyncClient()

    async def _search_image(
        self,
        query: Annotated[
            str,
            Field(description="The search query"),
        ],
    ) -> dict[str, Any]:
        params = {
            "q": query,
            "key": self.settings.pixabay_api_key,
        }

        response = await self.client.get(
            "https://pixabay.com/api/",
            params=params,
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.json()

    def init_tool(self) -> Tool:
        return Tool(
            function=self._search_image,
            name=self.name,
            description=self.description,
        )


@hookimpl
def register(manager):
    if Settings().pixabay_api_key:
        manager.register(PixabaySearchImageTool())
