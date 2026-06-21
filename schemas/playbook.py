from pydantic import BaseModel

from schemas.enums import NextBestAction


class RetentionPlaybook(BaseModel):
    """Retention playbook loaded from configuration data for RAG retrieval."""

    id: str
    segment: str
    decision: NextBestAction
    treatment_steps: list[str]
    escalation_condition: str
    engagement_policy: str

    def to_rag_text(self) -> str:
        """Convert playbook to plain text for vector store embedding."""
        steps_text = "\n".join(
            f"  {i + 1}. {step}" for i, step in enumerate(self.treatment_steps)
        )
        return (
            f"Playbook ID: {self.id}\n"
            f"Segment: {self.segment}\n"
            f"Decision: {self.decision.value}\n"
            f"Treatment Steps:\n{steps_text}\n"
            f"Escalation Condition: {self.escalation_condition}\n"
            f"Engagement Policy: {self.engagement_policy}"
        )
