from pydantic import BaseModel
from pydantic_ai import BinaryContent
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


class PendingMessage(BaseModel):
    multi_turn: bool
    tool_return_data: bool
    messages: list[BinaryContent] = []

    def add(self, message: BinaryContent):
        self.messages.append(message)

    def clear(self):
        self.messages = []

    def has_messages(self):
        return bool(len(self.messages))

    def use_tool_return(self, data: BinaryContent) -> BinaryContent | str:
        if self.multi_turn:
            self.add(data)
            return "File content added to context, will provided in next user prompt"
        if self.tool_return_data:
            return data
        else:
            return "Use `context_agent` tool to read binary files. Place the file in `attatchments` field of `context_agent` tool."
