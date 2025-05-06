from collections.abc import AsyncIterator

from inline_snapshot import snapshot
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import AgentInfo, DeltaToolCalls, FunctionModel

from lightblue_ai.agent import LightBlueAgent


def return_tools(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    return ModelResponse(
        parts=[
            TextPart(f"{tool.name}, {tool.description}, {tool.parameters_json_schema}") for tool in info.function_tools
        ]
    )


async def stream_function(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str | DeltaToolCalls]:
    yield "hello"


async def test_agent():
    agent = LightBlueAgent(model=FunctionModel(function=return_tools, stream_function=stream_function))

    (await agent.run("Hello, world!")).output == snapshot(
        """\
thinking, Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed., {'additionalProperties': False, 'properties': {'thought': {'description': 'A thought to think about.', 'type': 'string'}}, 'required': ['thought'], 'type': 'object'}

sequentialthinking, A detailed tool for dynamic and reflective problem-solving through thoughts.
This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
Each thought can build on, question, or revise previous insights as understanding deepens.

When to use this tool:
- Breaking down complex problems into steps
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where the full scope might not be clear initially
- Problems that require a multi-step solution
- Tasks that need to maintain context over multiple steps
- Situations where irrelevant information needs to be filtered out

Key features:
- You can adjust total_thoughts up or down as you progress
- You can question or revise previous thoughts
- You can add more thoughts even after reaching what seemed like the end
- You can express uncertainty and explore alternative approaches
- Not every thought needs to build linearly - you can branch or backtrack
- Generates a solution hypothesis
- Verifies the hypothesis based on the Chain of Thought steps
- Repeats the process until satisfied
- Provides a correct answer

Parameters explained:
- thought: Your current thinking step, which can include:
* Regular analytical steps
* Revisions of previous thoughts
* Questions about previous decisions
* Realizations about needing more analysis
* Changes in approach
* Hypothesis generation
* Hypothesis verification
- next_thought_needed: True if you need more thinking, even if at what seemed like the end
- thought_number: Current number in sequence (can go beyond initial total if needed)
- total_thoughts: Current estimate of thoughts needed (can be adjusted up/down)
- is_revision: A boolean indicating if this thought revises previous thinking
- revises_thought: If is_revision is true, which thought number is being reconsidered
- branch_from_thought: If branching, which thought number is the branching point
- branch_id: Identifier for the current branch (if any)
- needs_more_thoughts: If reaching end but realizing more thoughts needed

You should:
1. Start with an initial estimate of needed thoughts, but be ready to adjust
2. Feel free to question or revise previous thoughts
3. Don't hesitate to add more thoughts if needed, even at the "end"
4. Express uncertainty when present
5. Mark thoughts that revise previous thinking or branch into new paths
6. Ignore information that is irrelevant to the current step
7. Generate a solution hypothesis when appropriate
8. Verify the hypothesis based on the Chain of Thought steps
9. Repeat the process until satisfied with the solution
10. Provide a single, ideally correct answer as the final output
11. Only set next_thought_needed to false when truly done and a satisfactory answer is reached
, {'additionalProperties': False, 'properties': {'thought': {'description': 'Your current thinking step', 'type': 'string'}, 'thought_number': {'description': 'Current thought number', 'type': 'integer'}, 'total_thoughts': {'description': 'Estimated total thoughts needed', 'type': 'integer'}, 'next_thought_needed': {'description': 'Whether another thought step is needed', 'type': 'boolean'}, 'is_revision': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}], 'description': 'Whether this revises previous thinking'}, 'revises_thought': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'description': 'Which thought is being reconsidered'}, 'branch_from_thought': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'description': 'Branching point thought number'}, 'branch_id': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'description': 'Branch identifier'}, 'needs_more_thoughts': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}], 'description': 'If more thoughts are needed'}}, 'required': ['thought', 'thought_number', 'total_thoughts', 'next_thought_needed'], 'type': 'object'}

Plan, Use the tool to draw a plan in markdown. It will not obtain new information or change the database, but just append the plan to the log. Use it when complex tasks like search or planning are needed. Use it multiple times to complete a complex task if necessary., {'additionalProperties': False, 'properties': {'plan': {'description': 'A plan for the task.', 'type': 'string'}}, 'required': ['plan'], 'type': 'object'}

html_edit, This is a specialized tool for editing HTML files using XPath expressions to target specific elements.

Before using this tool:

1. Use the View tool to understand the HTML file's structure.
2. Verify that the file is a valid HTML document.

This tool allows you to replace the content of HTML elements by:
- Targeting elements with XPath expressions
- Replacing their entire content with new HTML

To make an HTML edit, provide:
1. file_path: The absolute path to the HTML file to modify (must be absolute, not relative).
2. xpath: The XPath expression that identifies the element(s) to modify.
   For example: "//div[@id='header']", "//h1[1]", or "//section[@class='about']".
3. new_content: The new HTML content to replace the inner content of the targeted element(s).
4. match_index: (Optional) The index of the element to modify if multiple elements match the XPath (0-based, default: 0).

Common XPath expressions:
- "//tagname": Selects all elements with the given tag name
- "//tagname[@attr='value']": Selects elements with a specific attribute value
- "//tagname[contains(@attr, 'partial')]": Selects elements with attribute containing a string
- "//tagname[1]": Selects the first element with the given tag name
- "//div[@id='main']//p": Selects all paragraphs inside the div with id="main"
- "//h1 | //h2": Selects all h1 and h2 elements

Examples:
- To replace the main heading and subtitle: xpath="//header", new_content="<h1>New Heading</h1><p>New subtitle text</p>"
- To replace the about section content: xpath="//section[@id='about']", new_content="<h2>About Us</h2><p>New about text...</p>"
- To replace a specific navigation item: xpath="//nav//li[3]", new_content="<li><a href='contact.html'>Contact Us</a></li>"

Best Practices:
- This tool works best for replacing entire chunks of HTML rather than making small edits
- Make comprehensive changes in a single operation instead of multiple small edits
- Use highly specific XPath queries to ensure you target the exact element you want to modify
- Test your XPath queries first to make sure they match exactly what you intend to replace
- Create complete, well-formed HTML fragments for your replacement content
, {'additionalProperties': False, 'properties': {'file_path': {'description': 'Absolute path to the HTML file to edit', 'type': 'string'}, 'xpath': {'description': 'XPath expression to target elements', 'type': 'string'}, 'new_content': {'description': 'New HTML content to replace the targeted elements', 'type': 'string'}, 'match_index': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'default': None, 'description': 'Index of the element to modify if multiple elements match the XPath (0-based)'}}, 'required': ['file_path', 'xpath', 'new_content'], 'type': 'object'}

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
- **DO NOT** use `find` and `grep` for searching—use `GrepTool`, `GlobTool`, or `context_agent` instead.
- **DO NOT** use `cat`, `head`, `tail`, or `ls` to read files—use `View` and `LS`.
- Multiple commands should be connected using `;` or `&&` **instead of** line breaks (line breaks can be used in strings).
- **Persistent Shell Session**: Environment variables, virtual environments, and current directories persist across sessions.
- **Avoid using `cd`**, unless explicitly required by the user.
- **Examples**:
  - ✅ **Preferred**: `["pytest", "/foo/bar/tests"]`
  - ❌ **Avoid**: `["cd /foo/bar", "&&", "pytest tests"]`
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

View, Reads a file from the local filesystem. The file_path parameter must be an absolute path, not a relative path. By default, it reads up to 2000 lines starting from the beginning of the file. You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters. Any lines longer than 2000 characters will be truncated. For image files, the tool will display the image for you. If you cannot read image via tool, just call the tool and it will display in next user prompt, you can wait for the next prompt.For very large PDF files, you need to use the PDF2Images tool to convert them into multiple images and read the images to understand the PDF., {'additionalProperties': False, 'properties': {'file_path': {'description': 'Absolute path to the file to read', 'type': 'string'}, 'line_offset': {'anyOf': [{'type': 'integer'}, {'type': 'null'}], 'default': None, 'description': 'Line number to start reading from (0-indexed)'}, 'line_limit': {'default': 2000, 'description': 'Maximum number of lines to read', 'type': 'integer'}}, 'required': ['file_path'], 'type': 'object'}

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

convert_to_markdown, MarkItDown is a lightweight Python utility for converting various files to Markdown.
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
- ... and more!

Use this tool when the file cannot be read with View tool
, {'additionalProperties': False, 'properties': {'source': {'description': 'source with following schema:local file: `file:///path/to/file` or just path of the file: `/path/to/file`url: `https://example.com/file.pdf` or `http://example.com/file.pdf`data: `data;base64,<base64-encoded-data>`', 'type': 'string'}}, 'required': ['source'], 'type': 'object'}

convert_pdf_to_images, Converts a PDF file to multiple PNG image files. The file_path parameter must be an absolute path to a PDF file. The output_path parameter is optional and will default to the same directory as the input file if not provided.For PDF file, try convert_to_markdown tool first. For using this tool, you should to use View tool to view the images., {'additionalProperties': False, 'properties': {'file_path': {'description': 'Absolute path to the PDF file to convert', 'type': 'string'}, 'output_path': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'description': 'Optional. Absolute path to the directory to save the images. If not provided, the images will be saved in the same directory as the PDF file.'}}, 'required': ['file_path', 'output_path'], 'type': 'object'}

convert_pdf_to_markdown, Converts a PDF file to markdown format via pymupdf4llm. This is the best tool to use for PDF file. You should always use this tool first. This tool will also convert the PDF to images and save them in the `image_path` directory. You can View the images using the `view` tool. , {'additionalProperties': False, 'properties': {'file_path': {'description': 'Absolute path to the PDF file to convert', 'type': 'string'}, 'image_path': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'description': 'Optional. Absolute path to the directory to save the images. If not provided, the images will be saved in the same directory as the PDF file.'}}, 'required': ['file_path'], 'type': 'object'}

view_web_file, Reads a file or image from the web.
For image files, the tool will display the image for you. If you cannot read image via tool, just call the tool and it will display in next user prompt, you can wait for the next prompt.
Use this tool to read files and images from the web.
Use `read_web` related tools if you need to read web pages. Only use this tool if you need to view it directly.
, {'additionalProperties': False, 'properties': {'url': {'description': 'URL of the web resource to view', 'type': 'string'}}, 'required': ['url'], 'type': 'object'}

screenshot_playwright, Take screenshot of a web page. For images, you should use the `save_web` tool to download the image then use `view` to view it. For local html, use this tool to take screenshot for reference or review., {'additionalProperties': False, 'properties': {'path': {'description': 'URL of the web page or local html to take a screenshot of.\\n- For local html: `file:///path/to/file.html`\\n- For web page: `https://example.com`\\n', 'type': 'string'}}, 'required': ['path'], 'type': 'object'}

http_request_tool, Makes an HTTP request to a URL and get the response., {'additionalProperties': False, 'properties': {'url': {'description': 'URL to make the request to', 'type': 'string'}, 'method': {'description': 'HTTP method', 'type': 'string'}, 'headers': {'anyOf': [{'additionalProperties': True, 'type': 'object'}, {'type': 'null'}], 'description': 'Request headers'}, 'data': {'anyOf': [{'additionalProperties': True, 'type': 'object'}, {'type': 'null'}], 'description': 'Request data'}, 'authrization': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'description': 'Authorization header to use for the request. If not provided, the tool will not include an authorization header. e.g. Bearer <token>'}}, 'required': ['url', 'method'], 'type': 'object'}

save_web_to_file, Downloads files from the web (HTML, images, documents, etc.) and saves them to the specified path. Supports various file types including HTML, PNG, JPEG, PDF, and more. Use `read_web` related tools if you need to read web pages. Only use this tool if you need to download files from the internet.Use `view_web_file` if you want to view files from the internet directly., {'additionalProperties': False, 'properties': {'urls': {'description': 'List of URLs to download', 'items': {'type': 'string'}, 'type': 'array'}, 'save_dir': {'description': 'Dir where the file should be saved', 'type': 'string'}}, 'required': ['urls', 'save_dir'], 'type': 'object'}

context_agent, Launch a new agent that has access to the following tools: GlobTool, GrepTool, LS, View and others for searching information.

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
, {'additionalProperties': False, 'properties': {'system_prompt': {'description': 'System prompt for the agent.', 'type': 'string'}, 'objective': {'description': 'The objective to achieve.', 'type': 'string'}, 'attatchments': {'anyOf': [{'items': {'type': 'string'}, 'type': 'array'}, {'type': 'null'}], 'default': None, 'description': 'A list of file paths to attach to the agent.'}}, 'required': ['system_prompt', 'objective'], 'type': 'object'}

reflaction_agent, Launch a reflection agent that evaluates completed tasks and provides improvement feedback.

When you have completed a task and want to verify its correctness, quality, or identify potential improvements, use this tool to perform an objective assessment. The reflection agent will:

- Analyze the completed task against the original requirements
- Identify any errors, omissions, or potential issues
- Evaluate the quality and effectiveness of the solution
- Suggest specific improvements or alternative approaches
- Provide a confidence score regarding the correctness of the solution

Usage notes:

1. Provide the reflection agent with: (a) the original task requirements, (b) the completed solution, and (c) any specific evaluation criteria you want addressed.
2. The agent will return a single comprehensive evaluation message containing its analysis and recommendations.
3. The evaluation result is not visible to the user automatically. To share insights with the user, you should send a text message summarizing the key findings.
4. Each reflection agent invocation is stateless. Your prompt should contain all the context needed for a thorough evaluation, including the complete task description and solution.
5. The reflection agent excels at identifying logical errors, edge cases, optimizations, and alignment with requirements that might have been overlooked during initial implementation.
6. If multiple evaluation perspectives are needed, launch multiple reflection agents concurrently with different evaluation criteria.
7. The reflection agent can evaluate code, writing, plans, decisions, and other outputs, but cannot execute code or make changes to files.
8. For maximum value, include specific questions or concerns you want the reflection agent to address in its evaluation.
, {'additionalProperties': False, 'properties': {'system_prompt': {'description': 'System prompt for the agent.', 'type': 'string'}, 'objective': {'description': 'The objective to achieve.', 'type': 'string'}, 'attatchments': {'anyOf': [{'items': {'type': 'string'}, 'type': 'array'}, {'type': 'null'}], 'default': None, 'description': 'A list of file paths to attach to the agent.'}}, 'required': ['system_prompt', 'objective'], 'type': 'object'}

celsius_to_fahrenheit, Convert Celsius to Fahrenheit.

    Args:
        celsius: Temperature in Celsius

    Returns:
        Temperature in Fahrenheit
    , {'properties': {'celsius': {'title': 'Celsius', 'type': 'number'}}, 'required': ['celsius'], 'title': 'celsius_to_fahrenheitArguments', 'type': 'object'}\
"""
    )

    async with agent.iter("Hello, world!") as run:
        async for event in agent.yield_response_event(run):
            assert event
