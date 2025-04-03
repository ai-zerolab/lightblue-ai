from inline_snapshot import snapshot

from lightblue_ai.tools.manager import LightBlueToolManager


def test_manager():
    manager = LightBlueToolManager()

    assert sorted([i.name for i in manager.get_all_tools()]) == snapshot([
        "BASH",
        "Edit",
        "GlobTool",
        "GrepTool",
        "LS",
        "PDF2Image",
        "Replace",
        "View",
        "dispatch_agent",
        "save_web",
        "screenshot",
        "thinking",
    ])

    assert sorted([i.name for i in manager.get_sub_agent_tools()]) == snapshot([
        "GlobTool",
        "GrepTool",
        "LS",
        "PDF2Image",
        "View",
        "save_web",
        "screenshot",
        "thinking",
    ])

    assert sorted([i.name for i in manager.get_read_tools()]) == snapshot([
        "GlobTool",
        "GrepTool",
        "LS",
        "PDF2Image",
        "View",
        "thinking",
    ])

    assert sorted([i.name for i in manager.get_write_tools()]) == snapshot(["Edit", "Replace"])

    assert sorted([i.name for i in manager.get_exec_tools()]) == snapshot(["BASH", "dispatch_agent"])

    assert sorted([i.name for i in manager.get_generation_tools()]) == snapshot([])
