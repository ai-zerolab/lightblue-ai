import os
from functools import cache
from pathlib import Path
from typing import TypeVar

from mcp import StdioServerParameters
from pydantic import BaseModel, Field
from pydantic_ai.mcp import MCPServer, MCPServerHTTP, MCPServerStdio

from lightblue_ai.settings import Settings


class SSEServerParameters(BaseModel):
    url: str
    headers: dict | None = None
    timeout: float = 5
    sse_read_timeout: float = 60 * 5


ServerParams = TypeVar("ServerParams", StdioServerParameters, SSEServerParameters)


class MCPConfig(BaseModel):
    mcp_servers: dict[str, ServerParams] = Field({}, alias="mcpServers")


@cache
def get_mcp_servers() -> list[MCPServer]:
    settings = Settings()

    config_path = Path(settings.mcp_config_path)
    mcp_config = MCPConfig.model_validate_json(config_path.read_text())

    mcp_servers: list[MCPServer] = []
    for _, server_params in mcp_config.mcp_servers.items():
        if isinstance(server_params, StdioServerParameters):
            server_params = server_params.model_copy(update={"env": {**os.environ, **(server_params.env or {})}})
            mcp_servers.append(
                MCPServerStdio(
                    command=server_params.command,
                    args=server_params.args,
                    env=server_params.env,
                )
            )
        elif isinstance(server_params, SSEServerParameters):
            mcp_servers.append(
                MCPServerHTTP(
                    url=server_params.url,
                    headers=server_params.headers,
                    timeout=server_params.timeout,
                    sse_read_timeout=server_params.sse_read_timeout,
                )
            )
    return mcp_servers
