from pathlib import Path
from typing import Annotated, Any

from pdf2image import convert_from_path
from pydantic import Field
from pydantic_ai import Tool

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class Pdf2ImageTool(LightBlueTool):
    """To use this tool, you need to install poppler via `brew install poppler`"""

    def __init__(self):
        self.scopes = [Scope.read]
        self.description = (
            "Converts a PDF file to a PNG image file. "
            "The file_path parameter must be an absolute path to a PDF file. "
            "The output_path parameter is optional and will default to the same directory as the input file if not provided. "
        )

    async def _pdf2images(
        self,
        file_path: Annotated[str, Field(description="Absolute path to the PDF file to convert")],
        output_path: Annotated[
            str | None,
            Field(
                description="Optional. Absolute path to the directory to save the images. "
                "If not provided, the images will be saved in the same directory as the PDF file."
            ),
        ],
    ) -> dict[str, Any]:
        try:
            path = Path(file_path).expanduser()
            if not path.exists():
                return {
                    "error": f"File not found: {file_path}",
                    "success": False,
                }

            # Check if output_path is provided
            if output_path:
                output_path = Path(output_path).expanduser()
                if not output_path.exists():
                    output_path.mkdir(parents=True, exist_ok=True)
            else:
                # If output_path is not provided, use the same directory as the input file
                output_path = path.parent

            # Convert PDF to images
            files = []
            images = convert_from_path(path, dpi=300)

            # Save each page as a PNG file
            for i, image in enumerate(images):
                image.save(f"{output_path}/output_page_{i + 1}.png", "PNG")
                files.append(f"{output_path}/output_page_{i + 1}.png")

            return {
                "success": True,
                "files": files,
                "message": f"PDF converted to {len(images)} images successfully.",
            }
        except Exception as e:
            return {
                "error": f"Failed to convert PDF to images: {e!s}",
                "success": False,
            }

    def init_tool(self) -> Tool:
        return Tool(
            function=self._pdf2images,
            name="PDF2Image",
            description=self.description,
        )


@hookimpl
def register(manager):
    manager.register(Pdf2ImageTool())
