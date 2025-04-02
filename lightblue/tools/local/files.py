# GrepTool
# GlobTool
# LS
# View
# Edit
# Replace


from lightblue.tools.base import LightBlueTool, Scope
from lightblue.tools.extensions import hookimpl


class GrepTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.read]


class GlobTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.read]


class ListTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.read]


class ViewTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.read]


class EditTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.write]


class ReplaceTool(LightBlueTool):
    def __init__(self):
        self.scopes = [Scope.write]


@hookimpl
def register(manager):
    manager.register(GrepTool())
    manager.register(GlobTool())
    manager.register(ListTool())
    manager.register(ViewTool())
    manager.register(EditTool())
    manager.register(ReplaceTool())
