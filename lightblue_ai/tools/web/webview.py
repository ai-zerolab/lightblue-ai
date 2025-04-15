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
        self.description = """Reads a file or image from the web.
For image files, the tool will display the image for you. If you cannot read image via tool, just call the tool and it will display in next user prompt, you can wait for the next prompt.
Use this tool to read files and images from the web.
Use `read_web` related tools if you need to read web pages. Only use this tool if you need to view it directly.
"""
        self.client = httpx.AsyncClient()

    async def call(
        self,
        ctx: RunContext[PendingMessage],
        url: Annotated[str, Field(description="URL of the web resource to view")],
    ) -> str | dict | BinaryContent:
        try:
            response = await self.client.get(url, follow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "image" in content_type:
                data = BinaryContent(
                    data=response.content,
                    media_type=content_type,
                )
                if ctx.deps.multi_turn:
                    ctx.deps.add(data)
                    return "File content added to context, will provided in next user prompt"
                if ctx.deps.tool_return_data:
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


@hookimpl
def register(manager):
    manager.register(WebViewTool())
