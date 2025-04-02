from lightblue.settings import Settings
from lightblue.tools.base import LightBlueTool, Scope
from lightblue.tools.extensions import hookimpl


class FluxBflTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.read]


@hookimpl
def register(manager):
    settings = Settings()
    if settings.bfl_api_key:
        manager.register(FluxBflTool())
