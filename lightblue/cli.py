from pathlib import Path

import typer

from lightblue.agent import LightBlueAgent
from lightblue.log import logger
from lightblue.mcps import get_mcp_servers

app = typer.Typer()


@app.command()
async def submit(
    prompt: str,
    all_messages_json: Path = typer.Option(
        default="all_messages.json",
        help="The path to store the result",
    ),
    usage_json: Path = typer.Option(
        default="usage.json",
        help="The path to store the usage",
    ),
):
    agent = LightBlueAgent()

    result = await agent.run(prompt)
    print(result.data)

    with all_messages_json.open("w") as f:
        f.write(result.all_messages_json())

    with usage_json.open("w") as f:
        f.write(result.usage())


@app.command()
def status():
    agent = LightBlueAgent()

    logger.info(f"Found {len(agent.tool_manager.get_all_tools())} tools.")
    logger.info(f"Found {len(get_mcp_servers())} MCP servers.")
