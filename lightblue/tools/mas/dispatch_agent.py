from pydantic_ai import Agent, Tool

from lightblue.models import infer_model
from lightblue.settings import Settings
from lightblue.tools.base import LightBlueTool, Scope
from lightblue.tools.extensions import hookimpl
from lightblue.tools.manager import LightBlueToolManager


class DispatchAgentTool(LightBlueTool):
    def __init__(self):
        self.settings = Settings()
        self.scopes = [Scope.exec]
        self.description = """Launch a new agent that has access to the following tools: GlobTool, GrepTool, LS, View.

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
"""

    async def _dispatch_agent(self, system_prompt: str, objective: str) -> str:
        tools = LightBlueToolManager().get_read_tools()

        self.agent = Agent(
            infer_model(self.settings.sub_agent_model or self.settings.default_model),
            system_prompt=system_prompt,
            tools=tools,
        )

        return await self.agent.run(objective)

    def init_tool(self) -> Tool:
        return Tool(
            name="dispatch_agent",
            function=self._dispatch_agent,
            description=self.description,
        )


@hookimpl
def register(manager):
    manager.register(DispatchAgentTool())
