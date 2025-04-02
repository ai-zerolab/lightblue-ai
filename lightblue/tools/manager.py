import importlib
import threading
from pathlib import Path

import pluggy
from pydantic_ai.tools import Tool

import lightblue.tools as tools_package
from lightblue.log import logger
from lightblue.tools import extensions
from lightblue.tools.base import LightBlueTool
from lightblue.tools.extensions import project_name as PROJECT_NAME


class Singleton(type):
    """
    metaclass for singleton, thread-safe.
    """

    _instances = {}  # noqa: RUF012
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)  # noqa: UP008
        return cls._instances[cls]


class LightBlueToolManager(metaclass=Singleton):
    def __init__(self):
        self.pm = pluggy.PluginManager(PROJECT_NAME)
        self.pm.add_hookspecs(extensions)
        self._registed_instance: list[LightBlueTool] = []

        self.load_all_local_model()
        self.pm.load_setuptools_entrypoints(PROJECT_NAME)

        self._init_tools()

    def _init_tools(self):
        for f in self.pm.hook.register(manager=self):
            try:
                f()
            except Exception as e:
                logger.exception(f"Cannot register tool {f}: {e}")

    def load_all_local_model(self):
        """
        loads all local models by automatically discovering all subdirectories in the tools directory
        """

        # Get the path of the tools directory
        tools_path = Path(tools_package.__path__[0])

        # Find all subdirectories in the tools directory
        for item in tools_path.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                # Import the module and load it
                module_name = f"lightblue.tools.{item.name}"
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
        self._registed_instance.append(instance)

    def get_sub_agent_tools(self) -> list[Tool]:
        """read&web tools"""
        return [i.init_tool() for i in self._registed_instance if i.is_read_tool() or i.is_web_tool()]

    def get_read_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance if i.is_read_tool()]

    def get_write_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance if i.is_write_tool()]

    def get_exec_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance if i.is_exec_tool()]

    def get_generation_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance if i.is_generation_tool()]

    def get_all_tools(self) -> list[Tool]:
        return [i.init_tool() for i in self._registed_instance]


if __name__ == "__main__":
    LightBlueToolManager()
