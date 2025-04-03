from inline_snapshot import snapshot

from lightblue_ai.tools.manager import LightBlueToolManager


def test_manager():
    manager = LightBlueToolManager()

    assert [i.name for i in manager.get_all_tools()] == snapshot([
        "thinking",
        "BASH",
        "GrepTool",
        "GlobTool",
        "LS",
        "View",
        "Edit",
        "Replace",
        "PDF2Image",
        "search_with_tavily",
        "screenshot",
        "search_image",
        "save_web",
        "generate_image_with_flux",
        "dispatch_agent",
    ])

    assert [i.name for i in manager.get_sub_agent_tools()] == snapshot([
        "thinking",
        "GrepTool",
        "GlobTool",
        "LS",
        "View",
        "PDF2Image",
        "search_with_tavily",
        "screenshot",
        "search_image",
        "save_web",
    ])

    assert [i.name for i in manager.get_read_tools()] == snapshot([
        "thinking",
        "GrepTool",
        "GlobTool",
        "LS",
        "View",
        "PDF2Image",
    ])

    assert [i.name for i in manager.get_write_tools()] == snapshot(["Edit", "Replace"])

    assert [i.name for i in manager.get_exec_tools()] == snapshot(["BASH", "dispatch_agent"])

    assert [i.name for i in manager.get_generation_tools()] == snapshot(["generate_image_with_flux"])
