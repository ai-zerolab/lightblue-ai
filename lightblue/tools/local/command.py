# Bash tool
import asyncio
import contextlib
import os
from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_ai.tools import Tool

from lightblue.tools.base import LightBlueTool, Scope
from lightblue.tools.extensions import hookimpl


class BashTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.exec]
        self.description = """Executes the given Bash command in a persistent shell session with optional timeout, ensuring appropriate security measures.
#### **Pre-Execution Checks**

1. **Directory Validation**
   - Before creating new directories or files, use the `LS` tool to verify that the parent directory exists and is correctly located.
   - For example, before running `mkdir foo/bar`, first check that `foo` exists as the intended parent directory.

2. **Security Restrictions**
   - To prevent command injection and potential security issues, certain commands are **restricted** or **disabled**.
   - The following commands are **blocked**:
     `alias`, `curl`, `curlie`, `wget`, `axel`, `aria2c`, `nc`, `telnet`, `lynx`, `w3m`, `links`, `httpie`, `xh`, `http-prompt`, `chrome`, `firefox`, `safari`.
   - If a blocked command is used, an error message will be returned explaining the reason.

#### **Execution Process**

1. **Command Execution**
   - Ensures correct quoting before executing the command.
   - Captures command output.

2. **Output Handling**
   - If output exceeds 30,000 characters, it will be truncated.
   - Prepares the output for user review.

3. **Result Return**
   - Returns the command execution output.
   - If execution fails, includes error details.

#### **Usage Guidelines**

- `command` is a **required** parameter.
- Optional timeout (in milliseconds) can be set, with a **maximum of 600,000 ms (10 minutes)**. Default is **30 minutes**.
- **DO NOT** use `find` and `grep` for searching—use `GrepTool`, `GlobTool`, or `dispatch_agent` instead.
- **DO NOT** use `cat`, `head`, `tail`, or `ls` to read files—use `View` and `LS`.
- Multiple commands should be connected using `;` or `&&` **instead of** line breaks (line breaks can be used in strings).
- **Persistent Shell Session**: Environment variables, virtual environments, and current directories persist across sessions.
- **Avoid using `cd`**, unless explicitly required by the user.
- **Examples**:
  - ✅ **Preferred**: `pytest /foo/bar/tests`
  - ❌ **Avoid**: `cd /foo/bar && pytest tests`
"""

    async def _bash(
        self,
        command: Annotated[list[str], Field(description="The command to execute as a list of strings")],
        timeout_seconds: Annotated[int, Field(default=30, description="Maximum execution time in seconds")] = 30,
        working_dir: Annotated[
            str | None,
            Field(default=None, description="Directory to execute the command in"),
        ] = None,
    ) -> dict[str, str]:
        if not command:
            return {
                "error": "Command cannot be empty",
                "stdout": "",
                "stderr": "",
                "return_code": 1,
            }
        if isinstance(command, str):
            return {
                "error": "Command must be a list of strings",
                "stdout": "",
                "stderr": "",
                "return_code": 1,
            }

        try:
            # Expand user home directory in working_dir if provided
            expanded_working_dir = Path(working_dir).expanduser() if working_dir else working_dir

            # Create subprocess with current environment
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ,
                cwd=expanded_working_dir,
            )

            try:
                # Wait for the process with timeout
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)

                # Decode output
                stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
                stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

            except asyncio.TimeoutError:
                # Kill the process if it times out
                with contextlib.suppress(ProcessLookupError):
                    process.kill()

                return {
                    "error": f"Command execution timed out after {timeout_seconds} seconds",
                    "stdout": "",
                    "stderr": "",
                    "return_code": 124,  # Standard timeout return code
                }
            else:
                return {
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "return_code": process.returncode,
                }

        except Exception as e:
            return {
                "error": f"Failed to execute command: {e!s}",
                "stdout": "",
                "stderr": "",
                "return_code": 1,
            }

    def init_tool(self) -> Tool:
        return Tool(
            function=self._bash,
            name="BASH",
            description=self.description,
        )


@hookimpl
def register(manager):
    manager.register(BashTool())
