from __future__ import annotations

import pluggy

project_name = "lightblue-tools"
"""
The entry-point name of this extension.

Should be used in ``pyproject.toml`` as ``[project.entry-points."{project_name}"]``
"""
hookimpl = pluggy.HookimplMarker(project_name)
"""
Hookimpl marker for this extension, extension module should use this marker

Example:

    .. code-block:: python

        @hookimpl
        def register(manager):
            ...
"""

hookspec = pluggy.HookspecMarker(project_name)


@hookspec
def register(manager):
    """
    Example:

    .. code-block:: python

        class SomeTool(LightBlueTool):
            ...

        from lightblue.tools.extensions import hookimpl

        @hookimpl
        def register(manager):
            manager.register(SomeTool())

    Config ``project.entry-points`` so that we can find it

    .. code-block:: toml

        [project.entry-points."lightblue-tools"]
        {whatever-name} = "{package}.{path}.{to}.{file-with-hookimpl-function}"
    """
