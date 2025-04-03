from inline_snapshot import snapshot
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from lightblue_ai.agent import LightBlueAgent


def return_tools(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    return ModelResponse(
        parts=[
            TextPart(f"{tool.name}, {tool.description}, {tool.parameters_json_schema}") for tool in info.function_tools
        ]
    )


async def test_agent():
    agent = LightBlueAgent(model=FunctionModel(return_tools))

    (await agent.run("Hello, world!")).data == snapshot(
        """\
thinking, Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed., {'additionalProperties': False, 'properties': {'thought': {'description': 'A thought to think about.', 'type': 'string'}}, 'required': ['thought'], 'type': 'object'}

BASH, Executes the given Bash command in a persistent shell session with optional timeout, ensuring appropriate security measures.
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
, {'additionalProperties': False, 'properties': {'command': {'description': 'The command to execute as a list of strings', 'items': {'type': 'string'}, 'type': 'array'}, 'timeout_seconds': {'default': 30, 'description': 'Maximum execution time in seconds', 'type': 'integer'}, 'working_dir': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None, 'description': 'Directory to execute the command in'}}, 'required': ['command'], 'type': 'object'}

GrepTool, - Fast content search tool that works with any codebase size
- Searches file contents using regular expressions
- Supports full regex syntax (eg. "log.*Error", "function\\s+\\w+", etc.)
- Filter files by pattern with the include parameter (eg. "*.js", "*.{ts,tsx}")
- Returns matching file paths sorted by modification time
- Use this tool when you need to find files containing specific patterns
- When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead
, {'additionalProperties': False, 'properties': {'pattern': {'description': 'Regular expression pattern to search for', 'type': 'string'}, 'include': {'default': '**/*', 'description': 'Optional glob pattern to filter files', 'type': 'string'}, 'context_lines': {'default': 2, 'description': 'Number of context lines to include before and after matches', 'type': 'integer'}}, 'required': ['pattern'], 'type': 'object'}

GlobTool, - Fast file pattern matching tool that works with any codebase size
- Supports glob patterns like "**/*.js" or "src/**/*.ts"
- Returns matching file paths sorted by modification time
- Use this tool when you need to find files by name patterns
- When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the Agent tool instead
, {'additionalProperties': False, 'properties': {'pattern': {'description': "Glob pattern to match files (e.g. '**/*.py')", 'type': 'string'}}, 'required': ['pattern'], 'type': 'object'}

LS, Lists files and directories in a given path. The path parameter must be an absolute path, not a relative path. You should generally prefer the Glob and Grep tools, if you know which directories to search, {'additionalProperties': False, 'properties': {'path': {'description': 'Directory path', 'type': 'string'}, 'recursive': {'default': False, 'description': 'Whether to list recursively', 'type': 'boolean'}, 'max_depth': {'default': -1, 'description': 'Maximum recursion depth', 'type': 'integer'}, 'include_hidden': {'default': False, 'description': 'Whether to include hidden files', 'type': 'boolean'}, 'ignore_patterns': {'anyOf': [{'items': {'type': 'string'}, 'type': 'array'}, {'type': 'null'}], 'default': ['node_modules', 'dist', 'build', 'public', 'static', '.next', '.git', '.vscode', '.idea', '.DS_Store', '.env', '.venv'], 'description': "Glob patterns to ignore (e.g. ['node_modules', '*.tmp'])"}}, 'required': ['path'], 'type': 'object'}

View, Reads a file from the local filesystem. The file_path parameter must be an absolute path, not a relative path. By default, it reads up to 2000 lines starting from the beginning of the file. You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters. Any lines longer than 2000 characters will be truncated. For image files, the tool will display the image for you. For very large PDF files, you need to use the PDF2Images tool to convert them into multiple images and read the images to understand the PDF., {'additionalProperties': False, 'properties': {'file_path': {'description': 'Absolute path to the file to read', 'type': 'string'}, 'line_offset': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'default': None, 'description': 'Line number to start reading from (0-indexed)'}, 'line_limit': {'default': 2000, 'description': 'Maximum number of lines to read', 'type': 'integer'}}, 'required': ['file_path'], 'type': 'object'}

Edit, This is a tool for editing files. For moving or renaming files, you should generally use the Bash tool with the 'mv' command instead. For larger edits, use the Write tool to overwrite files. For Jupyter notebooks (.ipynb files), use the NotebookEditCell instead.

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
, {'additionalProperties': False, 'properties': {'file_path': {'description': 'Absolute path to the file to edit', 'type': 'string'}, 'old_string': {'description': 'Text to replace (must be unique within the file)', 'type': 'string'}, 'new_string': {'description': 'New text to replace the old text with', 'type': 'string'}}, 'required': ['file_path', 'old_string', 'new_string'], 'type': 'object'}

Replace, This is a tool for writing a file to the local filesystem. It overwrites the existing file if there is one.

Before using this tool:

1. Use the ReadFile tool to understand the file's contents and context.

2. Directory Verification (only applicable when creating new files):
    - Use the LS tool to verify the parent directory exists and is the correct location.
, {'additionalProperties': False, 'properties': {'file_path': {'description': 'Absolute path to the file to write', 'type': 'string'}, 'content': {'description': 'Content to write to the file', 'type': 'string'}}, 'required': ['file_path', 'content'], 'type': 'object'}

PDF2Image, Converts a PDF file to a PNG image file. The file_path parameter must be an absolute path to a PDF file. The output_path parameter is optional and will default to the same directory as the input file if not provided. , {'additionalProperties': False, 'properties': {'file_path': {'description': 'Absolute path to the PDF file to convert', 'type': 'string'}, 'output_path': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'description': 'Optional. Absolute path to the directory to save the images. If not provided, the images will be saved in the same directory as the PDF file.'}}, 'required': ['file_path', 'output_path'], 'type': 'object'}

search_with_tavily, Performs web searches using Tavily.
If the initial query is too broad or results are not ideal, the LLM can refine the search by progressively reducing keywords to improve accuracy.
Useful for retrieving up-to-date information, specific data, or detailed background research.
, {'additionalProperties': False, 'properties': {'query': {'description': 'The search query', 'type': 'string'}, 'search_deep': {'default': 'basic', 'description': 'The search depth', 'enum': ['basic', 'advanced'], 'type': 'string'}, 'topic': {'default': 'general', 'description': 'The topic', 'enum': ['general', 'news'], 'type': 'string'}, 'time_range': {'anyOf': [{'enum': ['day', 'week', 'month', 'year', 'd', 'w', 'm', 'y'], 'type': 'string'}, {'type': 'null'}], 'default': None, 'description': 'The time range'}}, 'required': ['query'], 'type': 'object'}

screenshot, Take screenshot of a web page. For images, you should use the `save_web` tool to download the image then use `view` to view it., {'additionalProperties': False, 'properties': {'url': {'description': 'URL of the web page to take a screenshot of', 'type': 'string'}}, 'required': ['url'], 'type': 'object'}

search_image, Search images from internet via Pixabay. Use this tool if you need to find images from the internet.

query: A Search term. If omitted, all images are returned. This value may not exceed 100 characters. Example: "yellow+flower"
, {'additionalProperties': False, 'properties': {'query': {'description': 'The search query', 'type': 'string'}}, 'required': ['query'], 'type': 'object'}

save_web, Downloads files from the web (HTML, images, documents, etc.) and saves them to the specified path. Supports various file types including HTML, PNG, JPEG, PDF, and more., {'additionalProperties': False, 'properties': {'url': {'description': 'URL of the web resource to download', 'type': 'string'}, 'save_path': {'description': 'Path where the file should be saved', 'type': 'string'}}, 'required': ['url', 'save_path'], 'type': 'object'}

generate_image_with_flux, Generate an image using the Flux API and save it to a local file., {'additionalProperties': False, 'properties': {'prompt': {'description': 'The text prompt for image generation', 'type': 'string'}, 'output_dir': {'description': 'The directory to save the image', 'type': 'string'}, 'model_name': {'default': 'flux.1.1-pro', 'description': 'The model version to use', 'type': 'string'}, 'width': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'default': None, 'description': 'Width of the image in pixels'}, 'height': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'default': None, 'description': 'Height of the image in pixels'}, 'seed': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'default': None, 'description': 'Seed for reproducibility'}}, 'required': ['prompt', 'output_dir'], 'type': 'object'}

dispatch_agent, Launch a new agent that has access to the following tools: GlobTool, GrepTool, LS, View.

When you are searching for a keyword or file and are not confident that you will find the right match on the first try, use this tool to perform the search for you. For example:

- If you are searching for a keyword like "config" or "logger", this tool is appropriate.
- If you want to read a specific file path, use the View or GlobTool tool instead to find the match more quickly.
- If you are searching for a specific class definition like "class Foo", use the GlobTool tool instead to find the match more quickly.

Usage notes:

1. Launch multiple agents concurrently whenever possible to maximize performance; to do that, use a single message with multiple tool uses.
2. When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result.
3. Each agent invocation is stateless. You will not be able to send additional messages to the agent, nor will the agent be able to communicate with you outside of its final report. Therefore, your prompt should contain a highly detailed task description for the agent to perform autonomously, and you should specify exactly what information the agent should return in its final and only message to you.
4. The agent's outputs should generally be trusted.
5. IMPORTANT: The agent cannot use Bash, Replace, Edit, so it cannot modify files. If you need to use these tools, use them directly instead of going through the agent.
, {'additionalProperties': False, 'properties': {'system_prompt': {'type': 'string'}, 'objective': {'type': 'string'}}, 'required': ['system_prompt', 'objective'], 'type': 'object'}

celsius_to_fahrenheit, Convert Celsius to Fahrenheit.

    Args:
        celsius: Temperature in Celsius

    Returns:
        Temperature in Fahrenheit
    , {'properties': {'celsius': {'title': 'Celsius', 'type': 'number'}}, 'required': ['celsius'], 'title': 'celsius_to_fahrenheitArguments', 'type': 'object'}\
"""
    )
