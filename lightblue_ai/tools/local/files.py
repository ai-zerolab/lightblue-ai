import fnmatch
import re
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field
from pydantic_ai import BinaryContent, RunContext, Tool

from lightblue_ai.log import logger
from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl
from lightblue_ai.utils import PendingMessage


class GlobTool(LightBlueTool):
    def __init__(self):
        self.name = "GlobTool"
        self.scopes = [Scope.read]
        self.description = """- Fast file pattern matching tool that works with any codebase size
- Supports glob patterns like "**/*.js" or "src/**/*.ts"
- Returns matching file paths sorted by modification time
- Use this tool when you need to find files by name patterns
- When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead
"""

    async def _glob(
        self,
        pattern: Annotated[str, Field(description="Glob pattern to match files (e.g. '**/*.py')")],
    ) -> list[str]:
        """
        Find files matching the given glob pattern, sorted by modification time.

        Args:
            pattern: Glob pattern to match files (e.g. '**/*.py')

        Returns:
            List of matching file paths sorted by modification time (newest first)
        """
        # Use Path to find matching files
        matching_files = [str(p) for p in Path().glob(pattern)]

        # Sort files by modification time (newest first)
        matching_files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)

        return matching_files

    def init_tool(self) -> Tool:
        return Tool(
            function=self._glob,
            name=self.name,
            description=self.description,
        )


class GrepTool(LightBlueTool):
    def __init__(self):
        self.name = "GrepTool"
        self.scopes = [Scope.read]
        self.description = """- Fast content search tool that works with any codebase size
- Searches file contents using regular expressions
- Supports full regex syntax (eg. "log.*Error", "function\\s+\\w+", etc.)
- Filter files by pattern with the include parameter (eg. "*.js", "*.{ts,tsx}")
- Returns matching file paths sorted by modification time
- Use this tool when you need to find files containing specific patterns
- When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead
"""

    async def _grep(
        self,
        pattern: Annotated[str, Field(description="Regular expression pattern to search for")],
        include: Annotated[
            str,
            Field(description="Optional glob pattern to filter files", default="**/*"),
        ],
        context_lines: Annotated[
            int,
            Field(
                description="Number of context lines to include before and after matches",
                default=2,
            ),
        ],
    ) -> list[dict]:
        """
        Search file contents using regular expressions.

        Args:
            pattern: Regular expression pattern to search for
            include: Optional glob pattern to filter files (default: all files)
            context_lines: Number of context lines to include before and after matches

        Returns:
            List of matches with file paths, line numbers, and context
        """
        # Compile the regex pattern
        regex = re.compile(pattern)

        # Find files matching the include pattern
        files = list(Path().glob(include))

        # Sort files by modification time (newest first)
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        results = []

        # Search through each file
        for file_path in files:
            try:
                # Skip directories
                if file_path.is_dir():
                    continue

                # Read the file content
                with file_path.open("r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                # Search for matches in each line
                for i, line in enumerate(lines):
                    if regex.search(line):
                        # Calculate context line ranges
                        start = max(0, i - context_lines)
                        end = min(len(lines), i + context_lines + 1)

                        # Extract context lines
                        context = {
                            "file_path": str(file_path),
                            "line_number": i + 1,
                            "matching_line": line.rstrip("\n"),
                            "context": [lines[j].rstrip("\n") for j in range(start, end)],
                            "context_start_line": start + 1,
                        }

                        results.append(context)
            except Exception as e:
                # Skip files that can't be read
                logger.warning(f"Failed to read file {file_path}: {e}")
                continue

        return results

    def init_tool(self) -> Tool:
        return Tool(
            function=self._grep,
            name=self.name,
            description=self.description,
        )


def _get_file_info(path: Path) -> dict[str, Any]:
    """Get information about a file or directory.

    Args:
        path: Path to the file or directory

    Returns:
        Dictionary containing file information
    """
    info = {
        "name": path.name,
        "path": str(path),
        "type": "directory" if path.is_dir() else "file",
    }

    # Add file-specific information
    if path.is_file():
        try:
            stat = path.stat()
            info["size"] = stat.st_size
            info["modified"] = stat.st_mtime
        except Exception as e:
            info["error"] = f"Failed to get file stats: {e!s}"

    return info


class ListTool(LightBlueTool):
    def __init__(self):
        self.name = "LS"
        self.scopes = [Scope.read]
        self.description = "Lists files and directories in a given path. The path parameter must be an absolute path, not a relative path. You should generally prefer the Glob and Grep tools, if you know which directories to search"

    async def _list(  # noqa: C901
        self,
        path: Annotated[str, Field(description="Directory path")],
        recursive: Annotated[bool, Field(default=False, description="Whether to list recursively")] = False,
        max_depth: Annotated[int, Field(default=-1, description="Maximum recursion depth")] = -1,
        include_hidden: Annotated[bool, Field(default=False, description="Whether to include hidden files")] = False,
        ignore_patterns: Annotated[
            list[str] | None,
            Field(
                default=[
                    "node_modules",
                    "dist",
                    "build",
                    "public",
                    "static",
                    ".next",
                    ".git",
                    ".vscode",
                    ".idea",
                    ".DS_Store",
                    ".env",
                    ".venv",
                ],
                description="Glob patterns to ignore (e.g. ['node_modules', '*.tmp'])",
            ),
        ] = None,
    ) -> dict[str, Any]:
        """List directory contents with detailed information.

        Args:
            path: Directory path
            recursive: Optional. Whether to list recursively (default: False)
            max_depth: Optional. Maximum recursion depth (default: -1, which means no limit)
            include_hidden: Optional. Whether to include hidden files (default: False)
            ignore_patterns: Optional. Glob patterns to ignore (default: ['node_modules', 'dist', 'build', 'public', 'static', '.next', '.git', '.vscode', '.idea', '.DS_Store', '.env', '.venv'])

        Returns:
            Dictionary containing directory contents and metadata
        """
        ignore_patterns = (
            ignore_patterns
            if ignore_patterns is not None
            else [
                "node_modules",
                "dist",
                "build",
                "public",
                "static",
                ".next",
                ".git",
                ".vscode",
                ".idea",
                ".DS_Store",
                ".env",
                ".venv",
            ]
        )
        try:
            dir_path = Path(path).expanduser()

            if not dir_path.exists():
                return {
                    "error": f"Directory not found: {path}",
                    "entries": [],
                    "success": False,
                }

            if not dir_path.is_dir():
                return {
                    "error": f"Path is not a directory: {path}",
                    "entries": [],
                    "success": False,
                }

            entries = []

            def should_ignore(path: Path) -> bool:
                """Check if a path should be ignored based on ignore patterns.

                Args:
                    path: Path to check

                Returns:
                    True if the path should be ignored, False otherwise
                """
                if not ignore_patterns:
                    return False

                return any(fnmatch.fnmatch(path.name, pattern) for pattern in ignore_patterns)

            def process_directory(current_path: Path, current_depth: int = 0) -> None:
                """Process a directory and its contents recursively.

                Args:
                    current_path: Path to the current directory
                    current_depth: Current recursion depth
                """
                nonlocal entries

                # Check if we've reached the maximum depth
                if max_depth >= 0 and current_depth > max_depth:
                    return

                try:
                    # List directory contents
                    for item in current_path.iterdir():
                        # Skip hidden files if not included
                        if not include_hidden and item.name.startswith("."):
                            continue

                        # Skip ignored patterns
                        if should_ignore(item):
                            continue

                        # Get file information
                        file_info = _get_file_info(item)
                        file_info["depth"] = current_depth
                        entries.append(file_info)

                        # Recursively process subdirectories
                        if recursive and item.is_dir():
                            process_directory(item, current_depth + 1)
                except PermissionError:
                    # Add an entry indicating permission denied
                    entries.append({
                        "name": current_path.name,
                        "path": str(current_path),
                        "type": "directory",
                        "error": "Permission denied",
                        "depth": current_depth,
                    })

            # Start processing from the root directory
            process_directory(dir_path)

            return {
                "path": str(dir_path),
                "entries": entries,
                "count": len(entries),
                "success": True,
            }
        except Exception as e:
            return {
                "error": f"Failed to list directory: {e!s}",
                "entries": [],
                "success": False,
            }

    def init_tool(self) -> Tool:
        return Tool(
            function=self._list,
            name=self.name,
            description=self.description,
        )


class ViewTool(LightBlueTool):
    def __init__(self):
        self.name = "View"
        self.scopes = [Scope.read]
        self.description = (
            "Reads a file from the local filesystem. "
            "The file_path parameter must be an absolute path, not a relative path. "
            "By default, it reads up to 2000 lines starting from the beginning of the file. "
            "You can optionally specify a line offset and limit (especially handy for long files), "
            "but it's recommended to read the whole file by not providing these parameters. "
            "Any lines longer than 2000 characters will be truncated. "
            "For image files, the tool will display the image for you. "
            "For very large PDF files, you need to use the PDF2Images tool to convert them into multiple images and read the images to understand the PDF."
        )

    async def _view(  # noqa: C901
        self,
        ctx: RunContext[PendingMessage],
        file_path: Annotated[str, Field(description="Absolute path to the file to read")],
        line_offset: Annotated[
            int | None,
            Field(
                description="Line number to start reading from (0-indexed)",
                default=None,
            ),
        ] = None,
        line_limit: Annotated[int, Field(description="Maximum number of lines to read", default=2000)] = 2000,
    ) -> str | BinaryContent:
        """Read a file from the local filesystem.

        Args:
            file_path: Absolute path to the file to read
            line_offset: Optional line number to start reading from (0-indexed)
            line_limit: Maximum number of lines to read (default: 2000)

        Returns:
            File content as string for text files or BinaryContent for binary files
        """
        try:
            path = Path(file_path).expanduser()

            if not path.exists():
                return f"Error: File not found: {file_path}"

            if path.is_dir():
                return f"Error: Path is a directory, not a file: {file_path}"

            # Check if the file is likely binary based on extension
            binary_extensions = {
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".ico",
                ".webp",  # Images
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",  # Documents
                ".zip",
                ".tar",
                ".gz",
                ".rar",
                ".7z",  # Archives
                ".exe",
                ".dll",
                ".so",
                ".dylib",  # Executables
                ".mp3",
                ".mp4",
                ".avi",
                ".mov",
                ".flv",
                ".wav",  # Media
            }

            if path.suffix.lower() in binary_extensions:
                # Return binary content for binary files
                with path.open("rb") as f:
                    content = f.read()
                data = BinaryContent(data=content, media_type=self._get_mime_type(path))
                if ctx.deps.enabled:
                    ctx.deps.add(data)
                    return "File content added to context, please read it from next user message."
                else:
                    return data

            # Read text file
            with path.open("r", encoding="utf-8", errors="replace") as f:
                if line_offset is not None:
                    # Skip lines if offset is provided
                    for _ in range(line_offset):
                        if not f.readline():
                            break

                # Read up to line_limit lines
                lines = []
                for _ in range(line_limit):
                    line = f.readline()
                    if not line:
                        break

                    # Truncate long lines
                    if len(line) > 2000:
                        line = line[:2000] + "... (line truncated)\n"

                    lines.append(line)

                return "".join(lines)

        except Exception as e:
            return f"Error reading file: {e!s}"

    def _get_mime_type(self, path: Path) -> str:
        """Get the MIME type for a file based on its extension.

        Args:
            path: Path to the file

        Returns:
            MIME type string
        """
        extension_to_mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".ico": "image/x-icon",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".zip": "application/zip",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
            ".rar": "application/vnd.rar",
            ".7z": "application/x-7z-compressed",
            ".mp3": "audio/mpeg",
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".flv": "video/x-flv",
            ".wav": "audio/wav",
        }

        suffix = path.suffix.lower()
        return extension_to_mime.get(suffix, "application/octet-stream")

    def init_tool(self) -> Tool:
        return Tool(
            function=self._view,
            name=self.name,
            description=self.description,
        )


class EditTool(LightBlueTool):
    def __init__(self):
        self.name = "Edit"
        self.scopes = [Scope.write]
        self.description = """This is a tool for editing files. For moving or renaming files, you should generally use the Bash tool with the 'mv' command instead. For larger edits, use the Write tool to overwrite files. For Jupyter notebooks (.ipynb files), use the NotebookEditCell instead.

Before using this tool:

1. Use the View tool to understand the file's contents and context.
2. Verify the directory path is correct (only applicable when creating new files):
    - Use the LS tool to verify the parent directory exists and is the correct location.

To make a file edit, provide the following:
1. file_path: The absolute path to the file to modify (must be absolute, not relative).
2. old_string: The text to replace (must be unique within the file, and must match the file contents exactly, including all whitespace and indentation).
3. new_string: The edited text to replace the old_string.

The tool will replace ONE occurrence of old_string with new_string in the specified file.

CRITICAL REQUIREMENTS FOR USING THIS TOOL:

1. UNIQUENESS: The old_string MUST uniquely identify the specific instance you want to change. This means:
    - Include AT LEAST 3-5 lines of context BEFORE the change point.
    - Include AT LEAST 3-5 lines of context AFTER the change point.
    - Include all whitespace, indentation, and surrounding code exactly as it appears in the file.

2. SINGLE INSTANCE: This tool can only change ONE instance at a time. If you need to change multiple instances:
    - Make separate calls to this tool for each instance.
    - Each call must uniquely identify its specific instance using extensive context.

3. VERIFICATION: Before using this tool:
    - Check how many instances of the target text exist in the file.
    - If multiple instances exist, gather enough context to uniquely identify each one.
    - Plan separate tool calls for each instance.

WARNING: If you do not follow these requirements:
    - The tool will fail if old_string matches multiple locations.
    - The tool will fail if old_string doesn't match exactly (including whitespace).
    - You may change the wrong instance if you don't include enough context.

When making edits:
    - Ensure the edit results in idiomatic, correct code.
    - Do not leave the code in a broken state.
    - Always use absolute file paths (starting with /).

If you want to create a new file, use:
    - A new file path, including dir name if needed.
    - An empty old_string.
    - The new file's contents as new_string.

Remember: when making multiple file edits in a row to the same file, you should prefer to send all edits in a single message with multiple calls to this tool, rather than multiple messages with a single call each.
"""

    async def _edit(
        self,
        file_path: Annotated[str, Field(description="Absolute path to the file to edit")],
        old_string: Annotated[str, Field(description="Text to replace (must be unique within the file)")],
        new_string: Annotated[str, Field(description="New text to replace the old text with")],
    ) -> str:
        """Edit a file by replacing a specific string with a new string.

        Args:
            file_path: Absolute path to the file to edit
            old_string: Text to replace (must be unique within the file)
            new_string: New text to replace the old text with

        Returns:
            Success or error message
        """
        try:
            path = Path(file_path).expanduser()

            # Check if we're creating a new file
            if not old_string:
                # Creating a new file
                # Ensure the parent directory exists
                parent_dir = path.parent
                if not parent_dir.exists():
                    parent_dir.mkdir(parents=True, exist_ok=True)

                # Write the new content to the file
                with path.open("w", encoding="utf-8") as f:
                    f.write(new_string)

                return f"Successfully created new file: {file_path}"

            # Editing an existing file
            if not path.exists():
                return f"Error: File not found: {file_path}"

            if path.is_dir():
                return f"Error: Path is a directory, not a file: {file_path}"

            # Read the file content
            with path.open("r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Check if the old string exists in the file
            if old_string not in content:
                return "Error: The specified text was not found in the file. Make sure it matches exactly, including whitespace and indentation."

            # Count occurrences to ensure uniqueness
            occurrences = content.count(old_string)
            if occurrences > 1:
                return f"Error: The specified text appears {occurrences} times in the file. Please provide more context to uniquely identify the instance you want to change."

            # Replace the old string with the new string
            new_content = content.replace(old_string, new_string, 1)

            # Write the modified content back to the file
            with path.open("w", encoding="utf-8") as f:
                f.write(new_content)

        except Exception as e:
            return f"Error editing file: {e!s}"

        else:
            return f"Successfully edited file: {file_path}"

    def init_tool(self) -> Tool:
        return Tool(
            function=self._edit,
            name=self.name,
            description=self.description,
            max_retries=3,
        )


class ReplaceTool(LightBlueTool):
    def __init__(self):
        self.name = "Replace"
        self.scopes = [Scope.write]
        self.description = """This is a tool for writing a file to the local filesystem. It overwrites the existing file if there is one.

Before using this tool:

1. Use the ReadFile tool to understand the file's contents and context.

2. Directory Verification (only applicable when creating new files):
    - Use the LS tool to verify the parent directory exists and is the correct location.
"""

    async def _replace(
        self,
        file_path: Annotated[str, Field(description="Absolute path to the file to write")],
        content: Annotated[str, Field(description="Content to write to the file")],
    ) -> str:
        """Write content to a file, overwriting it if it exists.

        Args:
            file_path: Absolute path to the file to write
            content: Content to write to the file

        Returns:
            Success or error message
        """
        try:
            path = Path(file_path).expanduser()

            # Ensure the parent directory exists
            parent_dir = path.parent
            if not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)

            # Write the content to the file
            with path.open("w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            return f"Error writing to file: {e!s}"
        else:
            return f"Successfully wrote to file: {file_path}"

    def init_tool(self) -> Tool:
        return Tool(
            function=self._replace,
            name=self.name,
            description=self.description,
            max_retries=3,
        )


@hookimpl
def register(manager):
    manager.register(GrepTool())
    manager.register(GlobTool())
    manager.register(ListTool())
    manager.register(ViewTool())
    manager.register(EditTool())
    manager.register(ReplaceTool())
