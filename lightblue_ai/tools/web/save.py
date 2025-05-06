import asyncio
from pathlib import Path
from typing import Annotated, Any

import httpx
from pydantic import Field

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class SaveWebTool(LightBlueTool):
    def __init__(self):
        self.name = "save_web_to_file"
        self.scopes = [Scope.web]
        self.description = (
            "Downloads files from the web (HTML, images, documents, etc.) and saves them to the specified path. "
            "Supports various file types including HTML, PNG, JPEG, PDF, and more. "
            "Use `read_web` related tools if you need to read web pages. Only use this tool if you need to download files from the internet."
            "Use `view_web_file` if you want to view files from the internet directly."
        )
        self.client = httpx.AsyncClient()

    async def call(
        self,
        urls: Annotated[list[str], Field(description="List of URLs to download")],
        save_dir: Annotated[
            str,
            Field(description="Dir where the file should be saved"),
        ],
    ) -> list[dict[str, str]]:
        return await asyncio.gather(*[self.downaload_one(url, save_dir) for url in urls])

    async def downaload_one(
        self,
        url: Annotated[str, Field(description="URL of the web resource to download")],
        save_dir: Annotated[str, Field(description="Directory where the file should be saved")],
    ) -> dict[str, str]:
        """
        Download a file from a URL and save it to the specified path.

        Args:
            url: URL of the web resource to download
            save_path: Path where the file should be saved

        Returns:
            Dictionary with information about the saved file
        """
        try:
            # Make the request
            response = await self.client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Get content type from headers or infer from URL
            content_type = response.headers.get("Content-Type", "")

            # Create directory if it doesn't exist

            save_dir = Path(save_dir)
            save_path_obj = Path(save_dir) / Path(url).name
            save_path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Save the content to the specified path
            with save_path_obj.open("wb") as f:
                f.write(response.content)

            # Get file size
            file_size = len(response.content)
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {e!s}",
                "message": f"Failed to download from {url}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to save file to {save_path_obj.as_posix()}",
            }
        else:
            return {
                "success": True,
                "path": save_path_obj.as_posix(),
                "size": file_size,
                "content_type": content_type,
                "message": f"File successfully saved to {save_path_obj.as_posix()}",
            }


class HTTPRequestTool(LightBlueTool):
    def __init__(self):
        self.name = "http_request_tool"
        self.scopes = [Scope.web]
        self.description = ()
        self.client = httpx.AsyncClient()

    async def call(
        self,
        url: Annotated[str, Field(description="")],
    ) -> dict[str, Any]:
        pass


@hookimpl
def register(manager):
    manager.register(SaveWebTool())
