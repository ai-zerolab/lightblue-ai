from lightblue_ai.tools.manager import LightBlueToolManager


def test_manager():
    manager = LightBlueToolManager()

    all_tools = {
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
    }
    sub_agent_tools = {
        "GlobTool",
        "GrepTool",
        "LS",
        "PDF2Image",
        "View",
        "save_web",
        "screenshot",
        "thinking",
    }
    read_tools = {
        "GlobTool",
        "GrepTool",
        "LS",
        "PDF2Image",
        "View",
        "thinking",
    }
    write_tools = {"Edit", "Replace"}
    exec_tools = {"BASH", "dispatch_agent"}
    generation_tools = set()

    assert all_tools.issubset(manager.get_all_tools())
    assert sub_agent_tools.issubset(manager.get_sub_agent_tools())
    assert read_tools.issubset(manager.get_read_tools())
    assert write_tools.issubset(manager.get_write_tools())
    assert exec_tools.issubset(manager.get_exec_tools())
    assert generation_tools.issubset(manager.get_generation_tools())
