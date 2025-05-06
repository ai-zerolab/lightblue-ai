from typing import Annotated, Any

from pydantic import Field

from lightblue_ai.tools.base import LightBlueTool, Scope
from lightblue_ai.tools.extensions import hookimpl


class ThinkingTool(LightBlueTool):
    """https://www.anthropic.com/engineering/claude-think-tool"""

    def __init__(self):
        self.name = "thinking"
        self.scopes = [Scope.read]
        self.description = "Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed."

    async def call(
        self,
        thought: Annotated[str, Field(description="A thought to think about.")],
    ) -> dict[str, str]:
        return {
            "thought": thought,
        }


class SequentialThinking(LightBlueTool):
    """https://github.com/modelcontextprotocol/servers/blob/main/src/sequentialthinking"""

    def __init__(self):
        self.name = "sequentialthinking"
        self.scopes = [Scope.read]
        self.thought_history = []
        self.branches = {}
        self.description = """A detailed tool for dynamic and reflective problem-solving through thoughts.
This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
Each thought can build on, question, or revise previous insights as understanding deepens.

When to use this tool:
- Breaking down complex problems into steps
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where the full scope might not be clear initially
- Problems that require a multi-step solution
- Tasks that need to maintain context over multiple steps
- Situations where irrelevant information needs to be filtered out

Key features:
- You can adjust total_thoughts up or down as you progress
- You can question or revise previous thoughts
- You can add more thoughts even after reaching what seemed like the end
- You can express uncertainty and explore alternative approaches
- Not every thought needs to build linearly - you can branch or backtrack
- Generates a solution hypothesis
- Verifies the hypothesis based on the Chain of Thought steps
- Repeats the process until satisfied
- Provides a correct answer

Parameters explained:
- thought: Your current thinking step, which can include:
* Regular analytical steps
* Revisions of previous thoughts
* Questions about previous decisions
* Realizations about needing more analysis
* Changes in approach
* Hypothesis generation
* Hypothesis verification
- next_thought_needed: True if you need more thinking, even if at what seemed like the end
- thought_number: Current number in sequence (can go beyond initial total if needed)
- total_thoughts: Current estimate of thoughts needed (can be adjusted up/down)
- is_revision: A boolean indicating if this thought revises previous thinking
- revises_thought: If is_revision is true, which thought number is being reconsidered
- branch_from_thought: If branching, which thought number is the branching point
- branch_id: Identifier for the current branch (if any)
- needs_more_thoughts: If reaching end but realizing more thoughts needed

You should:
1. Start with an initial estimate of needed thoughts, but be ready to adjust
2. Feel free to question or revise previous thoughts
3. Don't hesitate to add more thoughts if needed, even at the "end"
4. Express uncertainty when present
5. Mark thoughts that revise previous thinking or branch into new paths
6. Ignore information that is irrelevant to the current step
7. Generate a solution hypothesis when appropriate
8. Verify the hypothesis based on the Chain of Thought steps
9. Repeat the process until satisfied with the solution
10. Provide a single, ideally correct answer as the final output
11. Only set next_thought_needed to false when truly done and a satisfactory answer is reached
"""

    async def call(
        self,
        thought: Annotated[str, Field(description="Your current thinking step")],
        thought_number: Annotated[int, Field(description="Current thought number")],
        total_thoughts: Annotated[int, Field(description="Estimated total thoughts needed")],
        next_thought_needed: Annotated[bool, Field(description="Whether another thought step is needed")],
        is_revision: Annotated[bool | None, Field(description="Whether this revises previous thinking")] = None,
        revises_thought: Annotated[int | None, Field(description="Which thought is being reconsidered")] = None,
        branch_from_thought: Annotated[int | None, Field(description="Branching point thought number")] = None,
        branch_id: Annotated[str | None, Field(description="Branch identifier")] = None,
        needs_more_thoughts: Annotated[bool | None, Field(description="If more thoughts are needed")] = None,
    ) -> dict[str, Any]:
        # Adjust total_thoughts if thought_number is greater
        if thought_number > total_thoughts:
            total_thoughts = thought_number

        # Create thought data
        thought_data = {
            "thought": thought,
            "thoughtNumber": thought_number,
            "totalThoughts": total_thoughts,
            "nextThoughtNeeded": next_thought_needed,
            "isRevision": is_revision,
            "revisesThought": revises_thought,
            "branchFromThought": branch_from_thought,
            "branchId": branch_id,
            "needsMoreThoughts": needs_more_thoughts,
        }

        # Add to thought history
        self.thought_history.append(thought_data)

        # Handle branches
        if branch_from_thought and branch_id:
            if branch_id not in self.branches:
                self.branches[branch_id] = []
            self.branches[branch_id].append(thought_data)

        # Return response
        return {
            "thoughtNumber": thought_number,
            "totalThoughts": total_thoughts,
            "nextThoughtNeeded": next_thought_needed,
            "branches": list(self.branches.keys()),
            "thoughtHistoryLength": len(self.thought_history),
        }


@hookimpl
def register(manager):
    manager.register(ThinkingTool())
    manager.register(SequentialThinking())
