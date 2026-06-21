from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

from orchestrator.agents import create_agents
from orchestrator.nodes import create_node_functions
from orchestrator.state import AgentState
from schemas.playbook import RetentionPlaybook


def build_graph(llm, playbooks: list[RetentionPlaybook]):
    """Build and compile the multi-agent LangGraph workflow.

    Args:
        llm: Azure ChatOpenAI LLM instance.
        playbooks: List of loaded RetentionPlaybook instances.

    Returns:
        Compiled LangGraph ready for invocation.
    """
    agents = create_agents(llm)
    nodes = create_node_functions(llm, agents, playbooks)

    def route_next(state: AgentState):
        next_agent = state.get("next_agent", "FINISH")
        if next_agent == "FINISH":
            return END
        return next_agent

    workflow = StateGraph(AgentState)
    workflow.add_node("supervisor", nodes["supervisor"])
    workflow.add_node("profiler", nodes["profiler"])
    workflow.add_node("diagnostician", nodes["diagnostician"])
    workflow.add_node("strategist", nodes["strategist"])
    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        route_next,
        {
            "profiler": "profiler",
            "diagnostician": "diagnostician",
            "strategist": "strategist",
            END: END,
        },
    )

    workflow.add_edge("profiler", "supervisor")
    workflow.add_edge("diagnostician", "supervisor")
    workflow.add_edge("strategist", "supervisor")

    return workflow.compile()


def run_retention_review(graph, customer_id: str) -> str:
    """Execute a full retention review for a single customer.

    Args:
        graph: Compiled LangGraph workflow.
        customer_id: The customer ID to review (e.g., 'V001').

    Returns:
        The final agent response as a string.
    """
    input_message = f"Perform a full retention review for customer {customer_id}."
    result = graph.invoke(
        {"messages": [HumanMessage(content=input_message)], "next_agent": ""}
    )
    return result["messages"][-1].content
