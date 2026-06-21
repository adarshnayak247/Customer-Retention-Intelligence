from langgraph.prebuilt import create_react_agent

from prompts.agent_prompts import (
    PROFILER_SYSTEM_PROMPT,
    DIAGNOSTICIAN_SYSTEM_PROMPT,
    STRATEGIST_SYSTEM_PROMPT,
)
from tools.agent_tools import (
    fetch_customer_record,
    classify_risk_segment,
    recommend_retention_action,
)


def build_react_agent(llm, tools: list, prompt_text: str):
    """Compatibility wrapper for create_react_agent across LangGraph versions."""
    try:
        return create_react_agent(llm, tools=tools, prompt=prompt_text)
    except TypeError:
        return create_react_agent(llm, tools=tools, state_modifier=prompt_text)


def create_agents(llm) -> tuple:
    """Create the three sub-agents: profiler, diagnostician, strategist.

    Returns:
        Tuple of (profiler_agent, diagnostician_agent, strategist_agent).
    """
    profiler_agent = build_react_agent(
        llm, [fetch_customer_record], PROFILER_SYSTEM_PROMPT
    )
    diagnostician_agent = build_react_agent(
        llm, [classify_risk_segment], DIAGNOSTICIAN_SYSTEM_PROMPT
    )
    strategist_agent = build_react_agent(
        llm, [recommend_retention_action], STRATEGIST_SYSTEM_PROMPT
    )
    return profiler_agent, diagnostician_agent, strategist_agent
