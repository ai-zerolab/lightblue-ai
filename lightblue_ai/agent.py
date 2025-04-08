from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import TypeVar

from pydantic_ai.agent import Agent, AgentRun, AgentRunResult
from pydantic_ai.mcp import MCPServer
from pydantic_ai.messages import (
    AgentStreamEvent,
    FinalResultEvent,
    HandleResponseEvent,
    ModelMessage,
    UserContent,
)
from pydantic_ai.models import Model
from pydantic_ai.tools import Tool
from pydantic_ai.usage import Usage

from lightblue_ai.log import logger
from lightblue_ai.mcps import get_mcp_servers
from lightblue_ai.models import infer_model
from lightblue_ai.prompts import get_system_prompt
from lightblue_ai.settings import Settings
from lightblue_ai.tools.manager import LightBlueToolManager

T = TypeVar("T")


class LightBlueAgent[T]:
    def __init__(
        self,
        model: str | Model | None = None,
        system_prompt: str | None = None,
        result_type: T = str,
        result_tool_name: str = "final_result",
        result_tool_description: str | None = None,
        tools: list[Tool] | None = None,
        mcp_servers: list[MCPServer] | None = None,
    ):
        self.tool_manager = LightBlueToolManager()
        self.settings = Settings()
        tools = tools or []
        mcp_servers = mcp_servers or []

        if not (model or self.settings.default_model):
            raise ValueError("model or ENV `DEFAULT_MODEL` must be set")

        self.agent = Agent(
            infer_model(model or self.settings.default_model),
            result_type=result_type,
            result_tool_name=result_tool_name,
            result_tool_description=result_tool_description,
            system_prompt=system_prompt or get_system_prompt(),
            tools=[*tools, *self.tool_manager.get_all_tools()],
            mcp_servers=[*mcp_servers, *get_mcp_servers()],
        )

    async def run(
        self,
        user_prompt: str | Sequence[UserContent],
        *,
        message_history: None | list[ModelMessage] = None,
        usage: None | Usage = None,
    ) -> AgentRunResult[T]:
        async with self.agent.run_mcp_servers():
            result = await self.agent.run(user_prompt, message_history=message_history)
        if usage:
            usage.incr(result.usage(), requests=1)

        return result

    @asynccontextmanager
    async def iter(
        self,
        user_prompt: str | Sequence[UserContent],
        *,
        message_history: None | list[ModelMessage] = None,
        usage: None | Usage = None,
    ) -> AsyncIterator[AgentRun]:
        async with (
            self.agent.run_mcp_servers(),
            self.agent.iter(user_prompt, message_history=message_history) as run,
        ):
            yield run

        if usage:
            usage.incr(run.usage(), requests=1)

    async def yield_response_event(self, run: AgentRun) -> AsyncIterator[HandleResponseEvent | AgentStreamEvent]:
        """
        Yield the response event from the node.
        """
        async for node in run:
            if Agent.is_user_prompt_node(node) or Agent.is_end_node(node):
                continue

            elif Agent.is_model_request_node(node) or Agent.is_call_tools_node(node):
                async with node.stream(run.ctx) as request_stream:
                    async for event in request_stream:
                        if not event or isinstance(event, FinalResultEvent):
                            continue
                        yield event
            else:
                logger.warning(f"Unknown node: {node}")
