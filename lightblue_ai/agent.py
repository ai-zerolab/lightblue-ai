from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Generic, TypeVar

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
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.result import ToolOutput
from pydantic_ai.tools import Tool
from pydantic_ai.usage import Usage

from lightblue_ai.log import logger
from lightblue_ai.mcps import get_mcp_servers
from lightblue_ai.models import infer_model
from lightblue_ai.prompts import get_system_prompt
from lightblue_ai.settings import Settings
from lightblue_ai.tools.manager import LightBlueToolManager

OutputDataT = TypeVar("T")


class LightBlueAgent(Generic[OutputDataT]):
    def __init__(
        self,
        model: str | Model | None = None,
        system_prompt: str | None = None,
        result_type: type[OutputDataT] = str,
        result_tool_name: str = "final_result",
        result_tool_description: str | None = None,
        tools: list[Tool] | None = None,
        mcp_servers: list[MCPServer] | None = None,
        retries: int = 3,
        max_description_length: int | None = None,
        strict: bool | None = None,
    ):
        self.settings = Settings()
        model = model or self.settings.default_model
        tools = tools or []
        mcp_servers = mcp_servers or []

        if not model:
            raise ValueError("model or ENV `DEFAULT_MODEL` must be set")
        model_name = model.model_name if isinstance(model, Model) else model
        system_prompt = system_prompt or get_system_prompt()
        if (
            "openrouter" in model_name
            or "openai" in model_name
            or ("anthropic" not in model_name and "gemini-2.5" not in model_name)
        ) and not isinstance(model, FunctionModel):
            # OpenAI Compatible OR not anthropic/gemini-2.5
            max_description_length = max_description_length or 1000
        else:
            max_description_length = max_description_length
        logger.info(f"Using model: {model_name}, description length: {max_description_length}")

        self.tool_manager = LightBlueToolManager(max_description_length=max_description_length, strict=strict)
        if max_description_length and self.settings.append_tools_to_prompt:
            system_prompt = "\n".join([
                system_prompt,
                "## The following tools are available to you:",
                self.tool_manager.describe_all_tools(),
            ])
        self.agent = Agent[result_type](
            infer_model(model),
            output_type=(
                ToolOutput(
                    type_=result_type,
                    name=result_tool_name,
                    description=result_tool_description,
                    strict=strict,
                )
                if result_type is not str
                else str
            ),
            system_prompt=system_prompt,
            tools=[*tools, *self.tool_manager.get_all_tools()],
            mcp_servers=[*mcp_servers, *get_mcp_servers()],
            retries=retries,
        )

    async def run(
        self,
        user_prompt: str | Sequence[UserContent],
        *,
        message_history: None | list[ModelMessage] = None,
        usage: None | Usage = None,
    ) -> AgentRunResult[OutputDataT]:
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
            self.agent.iter(
                user_prompt,
                message_history=message_history,
            ) as run,
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
