import re

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from bl.tier_resolver import resolve_tier_in_step, lookup_playbook
from orchestrator.state import AgentState
from prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT
from schemas.playbook import RetentionPlaybook


def create_node_functions(llm, agents: tuple, playbooks: list[RetentionPlaybook]):
    """Create node functions with injected dependencies.

    Args:
        llm: The Azure ChatOpenAI LLM instance.
        agents: Tuple of (profiler_agent, diagnostician_agent, strategist_agent).
        playbooks: List of loaded RetentionPlaybook instances.

    Returns:
        Dict mapping node names to their handler functions.
    """
    profiler_agent, diagnostician_agent, strategist_agent = agents

    def supervisor_node(state: AgentState) -> dict:
        """Route to next agent or produce the final 6-field response."""
        messages = state["messages"]

        history_text = " ".join(
            [m.content for m in messages if hasattr(m, "content")]
        )
        profiler_done = "Sub-Agent: Customer Profiler Agent" in history_text
        diagnostician_done = "Sub-Agent: Churn Diagnostician Agent" in history_text
        strategist_done = "Sub-Agent: Retention Strategist Agent" in history_text

        if not profiler_done:
            return {"messages": [], "next_agent": "profiler"}
        if not diagnostician_done:
            return {"messages": [], "next_agent": "diagnostician"}
        if not strategist_done:
            return {"messages": [], "next_agent": "strategist"}

        # All agents done — resolve tier and produce final response
        tier_match = re.search(
            r"CLV Tier:\s*(Bronze|Silver|Gold|Platinum)",
            history_text,
            re.IGNORECASE,
        )
        clv_tier = tier_match.group(1) if tier_match else "Silver"

        segment_match = re.search(
            r"Matched Risk Segment:\s*(.+?)(?:\n|$)",
            history_text,
            re.IGNORECASE,
        )
        playbook = (
            lookup_playbook(segment_match.group(1).strip(), playbooks)
            if segment_match
            else None
        )

        if playbook:
            resolved_steps = [
                resolve_tier_in_step(step, clv_tier)
                for step in playbook.treatment_steps
            ]
            formatted_steps = "\n".join(
                f"  {i + 1}. {step}" for i, step in enumerate(resolved_steps)
            )
            final_prompt = (
                f"All three sub-agents have completed.\n\n"
                f"Pre-resolved Treatment Steps (copy these EXACTLY as written, no changes):\n{formatted_steps}\n\n"
                f"Engagement Policy (copy EXACTLY): {playbook.engagement_policy}\n\n"
                f"Generate the complete six-field FINAL RESPONSE now."
            )
        else:
            final_prompt = (
                "All three sub-agents have completed. "
                "Generate the complete six-field FINAL RESPONSE now."
            )

        supervisor_messages = (
            [SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT)]
            + list(messages)
            + [HumanMessage(content=final_prompt)]
        )

        response = llm.invoke(supervisor_messages)
        return {
            "messages": [AIMessage(content=response.content.strip())],
            "next_agent": "FINISH",
        }

    def profiler_node(state: AgentState) -> dict:
        """Run the Customer Profiler Agent."""
        user_msg = state["messages"][0].content if state["messages"] else ""
        result = profiler_agent.invoke(
            {"messages": [HumanMessage(content=user_msg)]}
        )
        return {
            "messages": [AIMessage(content=result["messages"][-1].content)],
            "next_agent": "supervisor",
        }

    def diagnostician_node(state: AgentState) -> dict:
        """Run the Churn Diagnostician Agent."""
        user_msg = state["messages"][0].content if state["messages"] else ""
        result = diagnostician_agent.invoke(
            {"messages": [HumanMessage(content=user_msg)]}
        )
        return {
            "messages": [AIMessage(content=result["messages"][-1].content)],
            "next_agent": "supervisor",
        }

    def strategist_node(state: AgentState) -> dict:
        """Run the Retention Strategist Agent with full context."""
        context_parts = [
            m.content for m in state["messages"] if hasattr(m, "content")
        ]
        full_context = "\n\n".join(context_parts)
        result = strategist_agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=(
                            "Based on the following analysis, retrieve the retention "
                            f"playbook and confirm the retrieval:\n\n{full_context}"
                        )
                    )
                ]
            }
        )
        return {
            "messages": [AIMessage(content=result["messages"][-1].content)],
            "next_agent": "supervisor",
        }

    return {
        "supervisor": supervisor_node,
        "profiler": profiler_node,
        "diagnostician": diagnostician_node,
        "strategist": strategist_node,
    }
