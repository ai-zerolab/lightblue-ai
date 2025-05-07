from typing import Annotated

from markitdown import MarkItDown
from pydantic import Field

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class Anything2Markdown(LightBlueTool):
    """To use this tool, you need to install poppler via `brew install poppler`"""

    def __init__(self):
        self.name = "convert_to_markdown"
        self.md = MarkItDown(enable_plugins=True)
        self.scopes = [Scope.read]
        self.description = """Use this tool when the file cannot be read with View tool.
MarkItDown is a lightweight Python utility for converting various files to Markdown.
focus on preserving important document structure and content as Markdown (including: headings, lists, tables, links, etc.) While the output is often reasonably presentable and human-friendly, it is meant to be consumed by text analysis tools
At present, MarkItDown supports:
- PDF
- PowerPoint
- Word
- Excel
- Images (EXIF metadata and OCR)
- Audio (EXIF metadata and speech transcription)
- HTML
- Text-based formats (CSV, JSON, XML)
- ZIP files (iterates over contents)
- Youtube URLs
- EPubs
"""

    async def call(
        self,
        source: Annotated[
            str,
            Field(
                description="source with following schema:"
                "local file: `file:///path/to/file` or just path of the file: `/path/to/file`"
                "url: `https://example.com/file.pdf` or `http://example.com/file.pdf`"
                "data: `data;base64,<base64-encoded-data>`"
            ),
        ],
    ) -> str:
        try:
            return (self.md.convert(source)).text_content
        except Exception as e:
            return f"Error: {e}"


@hookimpl
def register(manager):
    manager.register(Anything2Markdown())
