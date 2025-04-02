import os

USER_DEFINED_LOG_LEVEL = os.getenv("LIGHTBLUE_LOG_LEVEL", "DEBUG")

os.environ["LOGURU_LEVEL"] = USER_DEFINED_LOG_LEVEL

from loguru import logger  # noqa: E402

__all__ = ["logger"]
