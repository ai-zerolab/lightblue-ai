from typing import Annotated

import httpx
from pydantic import Field
from pydantic_ai import BinaryContent
from pydantic_ai.tools import Tool

from lightblue_ai.settings import Settings
from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl

URLBOX_URL = "https://api.urlbox.io/v1/render/sync"


class UrlboxAPI:
    def __init__(self, api_key: str):
        self.url = URLBOX_URL
        self.api_key = api_key
        self.client = httpx.AsyncClient()

    async def _get_screenshot(self, url: str) -> bytes:
        """
        Generate a screenshot of a website using the URLbox API.

        Args:
            url (str): The URL of the website to screenshot

        Returns:
            bytes: The screenshot image data
        """
        request_body = {
            "url": url,
            "width": 1600,
            "height": 900,
            "thumb_width": 800,
            "format": "png",
            "hide_cookie_banners": True,
            "block_ads": True,
            "wait_until": "loaded",
            "full_page": True,
            "full_width": True,
        }

        # Get the render URL
        response = await self.client.post(
            self.url,
            json=request_body,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        response.raise_for_status()
        response_data = response.json()

        if "renderUrl" not in response_data:
            raise httpx.HTTPError("No renderUrl in response")

        # Download the screenshot
        image_response = await self.client.get(response_data["renderUrl"], timeout=30.0)
        image_response.raise_for_status()
        return image_response.content


class ScreenshotTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.web]
        self.description = "Take screenshot of a web page. For images, you should use the `save_web` tool to download the image then use `view` to view it."
        self.settings = Settings()

        self.urlbox = UrlboxAPI(self.settings.urlbox_api_key)

    async def _screenshot(
        self,
        url: Annotated[str, Field(description="URL of the web page to take a screenshot of")],
    ) -> BinaryContent:
        return BinaryContent(
            data=await self.urlbox._get_screenshot(url),
            media_type="image/png",
        )

    def init_tool(self) -> Tool:
        return Tool(
            function=self._screenshot,
            name="screenshot",
            description=self.description,
        )


@hookimpl
def register(manager):
    manager.register(ScreenshotTool())
