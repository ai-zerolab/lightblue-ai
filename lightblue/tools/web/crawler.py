from typing import Annotated, Any, Literal

from pydantic import Field
from pydantic_ai import Tool
from tavily import AsyncTavilyClient

from lightblue.settings import Settings
from lightblue.tools.base import LightBlueTool, Scope
from lightblue.tools.extensions import hookimpl


class TavilyTool(LightBlueTool):
    def __init__(self):
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
            name="search_with_tavily",
            description=self.description,
        )


@hookimpl
def register(manager):
    settings = Settings()
    if settings.tavily_api_key:
        manager.register(TavilyTool())
