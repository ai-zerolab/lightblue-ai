# We should use curl or playwright?from typing import Annotated

from typing import Annotated

import httpx
from playwright.async_api import async_playwright
from pydantic import Field
from pydantic_ai import BinaryContent

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl
from lightblue_ai.tools.media_mixin import MediaMixin


class WebFileViewTool(LightBlueTool, MediaMixin):
    def __init__(self):
        self.name = "view_web_file"
        self.scopes = [Scope.web]
        self.description = """Reads a file or image from the web.
For image files, the tool will display the image for you.
Use this tool to read files and images from the web.
Use `read_web` related tools if you need to read web pages. Only use this tool if you need to view it directly.
"""
        self.client = httpx.AsyncClient()

    async def call(
        self,
        url: Annotated[str, Field(description="URL of the web resource to view")],
    ) -> str | dict | BinaryContent:
        try:
            response = await self.client.get(url, follow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "image" in content_type:
                data = BinaryContent(
                    data=self._resized_image(response.content),
                    media_type=content_type,
                )
                return data
            else:
                return response.text
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e!s}",
                "message": f"Failed to view {url}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to view {url}",
            }


class WebPageViewTool(LightBlueTool, MediaMixin):
    def __init__(self):
        self.name = "screenshot_playwright"
        self.scopes = [Scope.web]
        self.description = (
            "Take screenshot of a web page. For images, you should use the `save_web` tool to download the image then use `view` to view it. "
            "For local html, use this tool to take screenshot for reference or review."
        )

    async def call(
        self,
        path: Annotated[
            str,
            Field(
                description="""URL of the web page or local html to take a screenshot of.
- For local html: `file:///path/to/file.html`
- For web page: `https://example.com`
"""
            ),
        ],
    ) -> BinaryContent | str:
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch()
                page = await browser.new_page()
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to take screenshot of {path}",
                }

            try:
                # Load the local HTML file
                await page.goto(path)
                # Take the screenshot and return as bytes
                screenshot_bytes = self._resized_image(await page.screenshot(full_page=True))
            except Exception as e:
                await browser.close()
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to take screenshot of {path}",
                }
            else:
                data = BinaryContent(
                    data=screenshot_bytes,
                    media_type="image/png",
                )
                return data
            finally:
                await browser.close()


@hookimpl
def register(manager):
    manager.register(WebFileViewTool())
    manager.register(WebPageViewTool())
