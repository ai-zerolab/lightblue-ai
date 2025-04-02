from lightblue.settings import Settings
from lightblue.tools.base import LightBlueTool, Scope
from lightblue.tools.extensions import hookimpl


class TavilyTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.read]


class DuckDuckGoTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.read]


@hookimpl
def register(manager):
    settings = Settings()
    if settings.tavily_api_key:
        manager.register(TavilyTool())
    if settings.duckduckgo_api_key:
        manager.register(DuckDuckGoTool())
