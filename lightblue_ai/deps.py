from dataclasses import dataclass


@dataclass
class AgentContext:
    next_prompt: str | None = None
