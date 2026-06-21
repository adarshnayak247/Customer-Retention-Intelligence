from langchain_core.tools import tool

from bl.classifier import classify_customer
from schemas.customer import CustomerRecord

# --- Module-level state (set by initialize_tools) ---
_customer_pool: dict[str, CustomerRecord] = {}
_playbook_retriever = None


def initialize_tools(
    customer_pool: dict[str, CustomerRecord],
    playbook_retriever,
) -> None:
    """Initialize module-level state for tool functions.

    Must be called before any agent invocation.

    Args:
        customer_pool: Dict mapping customer_id -> CustomerRecord.
        playbook_retriever: ChromaDB retriever for playbook RAG queries.
    """
    global _customer_pool, _playbook_retriever
    _customer_pool = customer_pool
    _playbook_retriever = playbook_retriever


@tool
def fetch_customer_record(customer_id: str) -> str:
    """Fetch and return a formatted summary of a customer record by customer ID."""
    customer = _customer_pool.get(customer_id)
    if not customer:
        return f"ERROR: Customer ID '{customer_id}' not found in the customer pool."
    return customer.format_summary()


@tool
def classify_risk_segment(customer_id: str) -> str:
    """Classify the churn risk segment for a customer using deterministic rules."""
    customer = _customer_pool.get(customer_id)
    if not customer:
        return f"ERROR: Customer ID '{customer_id}' not found in the customer pool."

    result = classify_customer(customer)
    if not result.rules_fired:
        return (
            "Matched Segment: Unclassified\n"
            "Next Best Action: REVIEW\n"
            "Engagement Policy: Manually review customer profile and assign appropriate segment.\n"
            "Rules Fired: None - no segment thresholds were met."
        )
    return result.format_output()


@tool
def recommend_retention_action(segment_name: str) -> str:
    """Retrieve the retention playbook for the given segment name using RAG."""
    if _playbook_retriever is None:
        return "ERROR: Playbook retriever not initialized."
    results = _playbook_retriever.invoke(segment_name)
    if not results:
        return f"ERROR: No playbook found for segment '{segment_name}'."
    return results[0].page_content


def get_tools() -> list:
    """Return the list of tool functions for agent binding."""
    return [fetch_customer_record, classify_risk_segment, recommend_retention_action]
