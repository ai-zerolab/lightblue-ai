from pydantic_ai.messages import (
    ModelRequestPart,
    ModelResponsePart,
    ToolCallPart,
    ToolReturnPart,
)


def format_part(part: ModelResponsePart | ModelRequestPart) -> str:
    if isinstance(part, ToolReturnPart):
        return f"{part.tool_name}({part.tool_call_id}): {part.content!s}"
    elif isinstance(part, ToolCallPart):
        return f"{part.tool_name}({part.tool_call_id}): {part.args!s}"
    else:
        return f"{part.content!s}"
