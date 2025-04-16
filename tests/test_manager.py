from lightblue_ai.tools.manager import LightBlueToolManager


def test_manager():
    manager = LightBlueToolManager()

    all_tools = {
        "BASH",
        "Edit",
        "GlobTool",
        "GrepTool",
        "LS",
        "convert_pdf_to_images",
        "Replace",
        "View",
        "context_agent",
        "save_web_to_file",
        "thinking",
        "convert_to_markdown",
    }
    sub_agent_tools = {
        "GlobTool",
        "GrepTool",
        "LS",
        "convert_pdf_to_images",
        "View",
        "save_web_to_file",
        "thinking",
        "convert_to_markdown",
    }
    read_tools = {
        "GlobTool",
        "GrepTool",
        "LS",
        "convert_pdf_to_images",
        "View",
        "thinking",
        "convert_to_markdown",
    }
    write_tools = {"Edit", "Replace"}
    exec_tools = {"BASH", "context_agent"}
    generation_tools = set()

    assert all_tools.issubset({i.name for i in manager.get_all_tools()})
    assert sub_agent_tools.issubset({i.name for i in manager.get_sub_agent_tools()})
    assert read_tools.issubset({i.name for i in manager.get_read_tools()})
    assert write_tools.issubset({i.name for i in manager.get_write_tools()})
    assert exec_tools.issubset({i.name for i in manager.get_exec_tools()})
    assert generation_tools.issubset({i.name for i in manager.get_generation_tools()})

    # Ensure all tools have name, description
    for tool in manager.get_all_tools():
        assert tool.name is not None
        assert tool.description is not None


def test_strict_manager():
    manager = LightBlueToolManager(strict=True)

    all_tools = {
        "BASH",
        "Edit",
        "GlobTool",
        "GrepTool",
        "LS",
        "convert_pdf_to_images",
        "Replace",
        "View",
        "context_agent",
        "save_web_to_file",
        "thinking",
        "convert_to_markdown",
    }
    sub_agent_tools = {
        "GlobTool",
        "GrepTool",
        "LS",
        "convert_pdf_to_images",
        "View",
        "save_web_to_file",
        "thinking",
        "convert_to_markdown",
    }
    read_tools = {
        "GlobTool",
        "GrepTool",
        "LS",
        "convert_pdf_to_images",
        "View",
        "thinking",
        "convert_to_markdown",
    }
    write_tools = {"Edit", "Replace"}
    exec_tools = {"BASH", "context_agent"}
    generation_tools = set()

    assert all_tools.issubset({i.name for i in manager.get_all_tools()})
    assert sub_agent_tools.issubset({i.name for i in manager.get_sub_agent_tools()})
    assert read_tools.issubset({i.name for i in manager.get_read_tools()})
    assert write_tools.issubset({i.name for i in manager.get_write_tools()})
    assert exec_tools.issubset({i.name for i in manager.get_exec_tools()})
    assert generation_tools.issubset({i.name for i in manager.get_generation_tools()})

    # Ensure all tools have name, description
    for tool in manager.get_all_tools():
        assert tool.name is not None
        assert tool.description is not None
        assert tool.strict is True
