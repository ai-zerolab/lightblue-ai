from typing import Annotated, Any, Literal

import httpx
from pydantic import Field
from pydantic_ai import Tool
from tavily import AsyncTavilyClient

from lightblue_ai.settings import Settings
from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class TavilyTool(LightBlueTool):
    def __init__(self):
        self.name = "search_with_tavily"
        self.settings = Settings()
        self.scopes = [Scope.web]
        self.description = """Performs web searches using Tavily.
If the initial query is too broad or results are not ideal, the LLM can refine the search by progressively reducing keywords to improve accuracy.
Useful for retrieving up-to-date information, specific data, or detailed background research.
"""

    async def _search_with_tavily(
        self,
        query: Annotated[str, Field(description="The search query")],
        search_deep: Annotated[
            Literal["basic", "advanced"],
            Field(default="basic", description="The search depth"),
        ] = "basic",
        topic: Annotated[
            Literal["general", "news"],
            Field(default="general", description="The topic"),
        ] = "general",
        time_range: Annotated[
            Literal["day", "week", "month", "year", "d", "w", "m", "y"] | None,
            Field(default=None, description="The time range"),
        ] = None,
    ) -> list[dict[str, Any]]:
        client = AsyncTavilyClient(self.settings.tavily_api_key)
        results = await client.search(query, search_depth=search_deep, topic=topic, time_range=time_range)
        if not results["results"]:
            return {
                "success": False,
                "error": "No search results found.",
            }
        return results["results"]

    def init_tool(self) -> Tool:
        return Tool(
            function=self._search_with_tavily,
            name=self.name,
            description=self.description,
        )


class JinaSearchTool(LightBlueTool):
    def __init__(self):
        self.name = "search_with_jina"
        self.settings = Settings()
        self.scopes = [Scope.web]
        self.description = """Performs web searches using Jina.
If the initial query is too broad or results are not ideal, the LLM can refine the search by progressively reducing keywords to improve accuracy.
Useful for retrieving up-to-date information, specific data, or detailed background research.
"""
        self.client = httpx.AsyncClient()

    async def _search_with_jina(
        self,
        query: Annotated[str, Field(description="The search query")],
        page: Annotated[int, Field(default=1, description="The page number")] = 1,
    ) -> list[dict[str, Any]]:
        params = {
            "q": query,
            "page": page,
        }

        response = await self.client.get(
            "https://s.jina.ai/",
            params=params,
            headers={
                "Authorization": f"Bearer {self.settings.jina_api_key}",
                "Accept": "application/json",
                "X-Engine": "direct",
            },
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.json()

    def init_tool(self) -> Tool:
        return Tool(
            function=self._search_with_jina,
            name=self.name,
            description=self.description,
        )


class JinaReaderTool(LightBlueTool):
    def __init__(self):
        self.name = "read_web_with_jina"
        self.settings = Settings()
        self.scopes = [Scope.web]
        self.description = """Reads web pages using Jina. Results are in Markdown format. Use this tool to forcus on the content of the page."""
        self.client = httpx.AsyncClient()

    async def _read_web(
        self,
        url: Annotated[str, Field(description="URL of the web page to read")],
    ) -> str:
        target_url = f"https://r.jina.ai/{url}"

        response = await self.client.get(
            target_url,
            headers={
                "Authorization": f"Bearer {self.settings.jina_api_key}",
            },
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.text

    def init_tool(self) -> Tool:
        return Tool(
            function=self._read_web,
            name=self.name,
            description=self.description,
        )


@hookimpl
def register(manager):
    settings = Settings()
    if settings.tavily_api_key:
        manager.register(TavilyTool())
    if settings.jina_api_key:
        manager.register(JinaSearchTool())
        manager.register(JinaReaderTool())
