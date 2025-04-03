from inline_snapshot import snapshot
from pydantic_ai.mcp import MCPServerStdio

from lightblue_ai.mcps import get_mcp_servers


def test_get_mcp():
    mcp_server, *_ = get_mcp_servers()
    assert isinstance(mcp_server, MCPServerStdio)
    assert mcp_server.command == snapshot("python")
    assert mcp_server.args == snapshot(["tests/mcp_server.py"])
