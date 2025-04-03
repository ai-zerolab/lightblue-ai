import asyncio
import functools
from pathlib import Path

import typer
from pydantic_ai import Agent

from lightblue_ai.agent import LightBlueAgent
from lightblue_ai.log import logger
from lightblue_ai.mcps import get_mcp_servers
from lightblue_ai.utils import format_part

app = typer.Typer()


def make_sync(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@app.command()
@make_sync
async def submit(
    prompt: str = typer.Argument("prompt.md", help="The prompt to send to the agent, text or file"),
    all_messages_json: Path = typer.Option(
        default="all_messages.json",
        help="The path to store the result",
    ),
):
    if Path(prompt).exists():
        with open(prompt) as f:
            prompt = f.read()

    agent = LightBlueAgent()

    result = await agent.run(prompt)
    print(result.data)

    with all_messages_json.open("wb") as f:
        f.write(result.all_messages_json())

    print(f"Usage: {result.usage()}")
    print(f"Saved all messages to {all_messages_json}")


@app.command()
@make_sync
async def stream(  # noqa: C901
    prompt: str = typer.Argument("prompt.md", help="The prompt to send to the agent, text or file"),
):
    if Path(prompt).exists():
        with open(prompt) as f:
            prompt = f.read()
    agent = LightBlueAgent()
    async for node in agent.iter(prompt):
        if Agent.is_user_prompt_node(node):
            # A user prompt node => The user has provided input
            if node.system_prompts:
                print(f"System: {node.system_prompts}")
            if node.user_prompt:
                print(f"User: {node.user_prompt}")
        elif Agent.is_model_request_node(node):
            for part in node.request.parts:
                print(f"->[{part.part_kind}]: {format_part(part)}")
        elif Agent.is_call_tools_node(node):
            for part in node.model_response.parts:
                print(f"Assistant[{part.part_kind}]: {format_part(part)}")
        elif Agent.is_end_node(node):
            result = node.data
            print(f"Final Result: {result.data}")


@app.command()
def status():
    agent = LightBlueAgent()

    logger.info(f"Found {len(agent.tool_manager.get_all_tools())} tools.")
    logger.info(f"Found {len(get_mcp_servers())} MCP servers.")
