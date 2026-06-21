from pydantic import BaseModel

from schemas.enums import NextBestAction


class FinalRetentionResponse(BaseModel):
    """The structured 6-field final output produced by the supervisor agent."""

    customer_id: str
    risk_segment: str
    next_best_action: NextBestAction
    action_rationale: str
    treatment_steps: list[str]
    engagement_policy: str

    def format_output(self) -> str:
        """Format the final response for display."""
        steps_text = "\n".join(
            f"    {i + 1}. {step}" for i, step in enumerate(self.treatment_steps)
        )
        return (
            f"- Customer ID: {self.customer_id}\n"
            f"- Risk Segment: {self.risk_segment}\n"
            f"- Next Best Action: {self.next_best_action.value}\n"
            f"- Action Rationale: {self.action_rationale}\n"
            f"- Treatment Steps:\n{steps_text}\n"
            f"- Engagement Policy: {self.engagement_policy}"
        )


class AgentResponseRecord(BaseModel):
    """A single customer's agent response for batch result tracking."""

    customer_id: str
    agent_response: str
