from pydantic import BaseModel

from schemas.enums import NextBestAction, RiskSegmentName


class RuleFired(BaseModel):
    """A single classification rule that matched during risk evaluation."""

    rule: str
    actual: str | int | float


class RiskClassificationResult(BaseModel):
    """Output of the deterministic risk classification engine."""

    matched_segment: RiskSegmentName
    next_best_action: NextBestAction
    engagement_policy: str
    rules_fired: list[RuleFired]

    def format_output(self) -> str:
        """Format classification result for agent consumption."""
        rules_text = "\n".join(
            f"  {rule.rule} - actual: {rule.actual}" for rule in self.rules_fired
        )
        return (
            f"Matched Segment: {self.matched_segment.value}\n"
            f"Next Best Action: {self.next_best_action.value}\n"
            f"Engagement Policy: {self.engagement_policy}\n"
            f"Rules Fired:\n{rules_text}"
        )


class RiskSegment(BaseModel):
    """Risk segment definition loaded from configuration data."""

    id: str
    priority: int
    segment: RiskSegmentName
    definition: str
    decision: NextBestAction
    required_signals: list[str]
    engagement_policy: str
