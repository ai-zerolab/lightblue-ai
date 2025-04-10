from __future__ import annotations

import functools
import importlib
from pathlib import Path

import pluggy
from pydantic_ai.tools import Tool

import lightblue_ai.tools as tools_package
from lightblue_ai.log import logger
from lightblue_ai.tools import extensions
from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import project_name as PROJECT_NAME


class QueryTool(LightBlueTool):
    """
    Inspired by https://docs.llamaindex.ai/en/stable/examples/agent/openai_agent_lengthy_tools/,
    but using tool to get the model to fetch the info instead of prompt.
    """

    def __init__(self, manager: LightBlueToolManager):
        self.name = "query_tool"
        self.scopes = [Scope.read]
        self._manager = manager
        self.description = "For tool's description is truncated, before calling the tool you need to use this tool to get the full description of the tool."

    def query_tool_desciption(self, tool_name: str) -> str:
        tool = self._manager.get_lightblue_tool(tool_name)
        if tool is None:
            return "No tool found"
        return tool.description

    def init_tool(self) -> Tool:
        return Tool(
            function=self.query_tool_desciption,
            name=self.name,
            description=self.description,
        )


def might_truncate(func):
    @functools.wraps(func)
    def wrapper(self: LightBlueToolManager):
        r = func(self)
        self._truncate_tool_description(r)
        return r

    return wrapper


class LightBlueToolManager:
    max_description_length: int | None

    def __init__(
        self,
        enable_query_tools: bool = False,
        max_description_length: int | None = None,
    ):
        self.pm = pluggy.PluginManager(PROJECT_NAME)
        self.pm.add_hookspecs(extensions)
        self._registed_instance: list[LightBlueTool] = []

        self._load_all_local_model()
        self.pm.load_setuptools_entrypoints(PROJECT_NAME)

        self._init_tools()

        logger.info(f"Found {len(self._registed_instance)} tools.")

        if enable_query_tools or max_description_length:
            logger.info(f"Enabling query tools, max description length: {max_description_length}")
            self._registed_instance.append(QueryTool(self))
        self.max_description_length = max_description_length

    def _truncate_tool_description(self, tools: list[Tool]) -> None:
        if not self.max_description_length:
            return

        truncated_reminder = "... (truncated)"
        for tool in tools:
            if len(tool.description) > self.max_description_length:
                tool.description = (
                    tool.description[: self.max_description_length - len(truncated_reminder)] + truncated_reminder
                )

    def get_lightblue_tool(self, tool_name: str) -> None | LightBlueTool:
        for tool in self._registed_instance:
            if tool.name == tool_name:
                return tool
        return None

    def _init_tools(self):
        for f in self.pm.hook.register(manager=self):
            try:
                f()
            except Exception as e:
                logger.exception(f"Cannot register tool {f}: {e}")

    def _load_all_local_model(self):
        """
        loads all local models by automatically discovering all subdirectories in the tools directory
        """

        # Get the path of the tools directory
        tools_path = Path(tools_package.__path__[0])

        # Find all subdirectories in the tools directory
        for item in tools_path.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                # Import the module and load it
                module_name = f"lightblue_ai.tools.{item.name}"
                try:
                    module = importlib.import_module(module_name)
                    logger.debug(f"Auto-loading module: {module_name}")
                    self._load_dir(module)
                except ImportError as e:
                    logger.warning(f"Failed to import module {module_name}: {e}")

    def _load_dir(self, module):
        """
        Import all python files in a submodule.
        """
        modules = list(Path(module.__path__[0]).glob("*.py"))
        sub_packages = (p.stem for p in modules if p.is_file() and p.name != "__init__.py")
        packages = (str(module.__package__) + "." + i for i in sub_packages)
        for p in packages:
            logger.debug(f"loading {p}")
            self.pm.register(importlib.import_module(p))

    def register(self, instance: LightBlueTool):
        """
        Register a new model, if the model is already registed, skip it.
        """
        if instance in self._registed_instance:
            return
        logger.debug(f"Registering tool: {instance}")
        self._registed_instance.append(instance)

    @might_truncate
    def get_sub_agent_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance if i.is_read_tool() or i.is_web_tool()]

    @might_truncate
    def get_read_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance if i.is_read_tool()]

    @might_truncate
    def get_write_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance if i.is_write_tool()]

    @might_truncate
    def get_exec_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance if i.is_exec_tool()]

    @might_truncate
    def get_generation_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance if i.is_generation_tool()]

    @might_truncate
    def get_all_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance]
