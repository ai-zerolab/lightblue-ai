import asyncio
import functools
from pathlib import Path

import typer

from lightblue.agent import LightBlueAgent
from lightblue.log import logger
from lightblue.mcps import get_mcp_servers

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
def status():
    agent = LightBlueAgent()

    logger.info(f"Found {len(agent.tool_manager.get_all_tools())} tools.")
    logger.info(f"Found {len(get_mcp_servers())} MCP servers.")
