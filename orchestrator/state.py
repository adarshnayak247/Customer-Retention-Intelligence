from typing import TypedDict, Annotated, Sequence
import operator


class AgentState(TypedDict):
    """Shared state passed between agents in the LangGraph workflow."""

    messages: Annotated[Sequence, operator.add]
    next_agent: str
