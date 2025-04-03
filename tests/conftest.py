from pathlib import Path

import pytest

_HERE = Path(__file__).parent


@pytest.fixture(autouse=True)
def auto_patch_env(monkeypatch, tmp_path):
    monkeypatch.setenv("MCP_CONFIG_PATH", (_HERE / "mock_mcp.json").absolute().as_posix())
