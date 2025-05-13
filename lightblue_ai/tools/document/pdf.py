import os
from pathlib import Path
from typing import Annotated, Any

import pymupdf4llm
from pdf2image import convert_from_path
from pydantic import Field

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class Pdf2ImageTool(LightBlueTool):
    """To use this tool, you need to install poppler via `brew install poppler`"""

    def __init__(self):
        self.name = "convert_pdf_to_images"
        self.scopes = [Scope.read]
        self.description = (
            "Converts a PDF file to multiple PNG image files. "
            "The file_path parameter must be an absolute path to a PDF file. "
            "The output_path parameter is optional and will default to the same directory as the input file if not provided."
            "For PDF file, try convert_to_markdown tool first. "
            "For using this tool, you should to use View tool to view the images."
        )

    async def call(
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


class Mupdf4LLMTool(LightBlueTool):
    def __init__(self):
        self.name = "convert_pdf_to_markdown"
        self.scopes = [Scope.read]
        self.description = (
            "Converts a PDF file to markdown format via pymupdf4llm. "
            "This is the best tool to use for PDF file. You should always use this tool first. "
            "This tool will also convert the PDF to images and save them in the `image_path` directory. "
            "You can View the images using the `view` tool. "
        )
        if pymupdf_pro_password := os.getenv("PYMUPDF_PRO_PASSWORD"):
            import pymupdf.pro

            pymupdf.pro.unlock(pymupdf_pro_password)
            self.description += "\n **This tool now supports DOC/DOCX, XLS/XLSX, PPT/PPTX, HWP/HWPX as PRO version.**"

    async def call(
        self,
        file_path: Annotated[str, Field(description="Absolute path to the PDF file to convert")],
        image_path: Annotated[
            str | None,
            Field(
                description="Optional. Absolute path to the directory to save the images. "
                "If not provided, the images will be saved in the same directory as the PDF file."
            ),
        ] = None,
    ) -> dict[str, Any]:
        file_path: Path = Path(file_path).expanduser().resolve()
        if not file_path.exists():
            return {
                "error": f"File not found: {file_path}",
                "success": False,
            }
        image_path = Path(image_path).expanduser().resolve() if image_path else file_path.parent
        try:
            return {
                "success": True,
                "markdown": pymupdf4llm.to_markdown(file_path, write_images=True, image_path=image_path.as_posix()),
            }
        except Exception as e:
            return {
                "error": f"Failed to convert PDF to markdown: {e!s}",
                "success": False,
            }


@hookimpl
def register(manager):
    manager.register(Pdf2ImageTool())
    manager.register(Mupdf4LLMTool())
