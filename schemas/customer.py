from pydantic import BaseModel, Field

from schemas.enums import CLVTier


class CustomerRecord(BaseModel):
    """Validated customer record with behavioural signals."""

    customer_id: str
    name: str
    clv_tier: CLVTier
    recency_days: int = Field(ge=0)
    app_sessions_mo: int = Field(ge=0)
    email_open_rate: float = Field(ge=0, le=1)
    nps_score: int = Field(ge=0, le=10)
    support_tickets: int = Field(ge=0)

    def format_summary(self) -> str:
        """Format customer data into a human-readable summary for agent consumption."""
        return (
            f"Customer Summary\n"
            f"- Customer ID: {self.customer_id}\n"
            f"- Name: {self.name}\n"
            f"- CLV Tier: {self.clv_tier.value}\n"
            f"- Recency (days since last purchase): {self.recency_days}\n"
            f"- App Sessions / Month: {self.app_sessions_mo}\n"
            f"- Email Open Rate: {int(self.email_open_rate * 100)}%\n"
            f"- NPS Score (out of 10): {self.nps_score}\n"
            f"- Support Tickets (last 30 days): {self.support_tickets}"
        )
