from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(Path.cwd() / ".env")


class Settings(BaseSettings):
    default_model: str | None = None
    sub_agent_model: str | None = None
    reflection_agent_model: str | None = None
    enable_multi_turn: bool = True
    enable_bash_tool: bool = True
    auto_resize_images: bool = False

    jina_api_key: str | None = None
    tavily_api_key: str | None = None
    bfl_api_key: str | None = None
    urlbox_api_key: str | None = None
    pixabay_api_key: str | None = None

    mcp_config_path: str = (Path.cwd() / "./mcp.json").expanduser().resolve().absolute().as_posix()

    model_config = SettingsConfigDict(case_sensitive=False, frozen=True, env_file=".env", extra="allow")
