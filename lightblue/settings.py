from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    default_model: str

    mcp_config_path: str = (Path.cwd() / "./mcp.json").expanduser().resolve().absolute().as_posix()

    model_config = SettingsConfigDict(env_prefix="LIGHTBLUE_", case_sensitive=False, frozen=True, env_file=".env")
