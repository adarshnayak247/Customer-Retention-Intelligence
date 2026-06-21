from schemas.customer import CustomerRecord
from schemas.enums import NextBestAction, RiskSegmentName
from schemas.risk import RiskClassificationResult, RuleFired


def classify_customer(customer: CustomerRecord) -> RiskClassificationResult:
    """Classify a customer into a risk segment using deterministic rules.

    Rules are evaluated in priority order (highest urgency first):
      P1: Support-Fatigued → ESCALATE
      P2: Competitor-Switched → NURTURE
      P3: Disengaged → NURTURE
      P4: Healthy → HOLD
      Fallback: Unclassified → REVIEW
    """

    # P1: Support-Fatigued
    if (
        customer.support_tickets >= 3
        and customer.nps_score <= 4
        and customer.email_open_rate < 0.20
    ):
        return RiskClassificationResult(
            matched_segment=RiskSegmentName.SUPPORT_FATIGUED,
            next_best_action=NextBestAction.ESCALATE,
            engagement_policy="No promotional content until the service issue is confirmed resolved",
            rules_fired=[
                RuleFired(rule="support_tickets >= 3", actual=customer.support_tickets),
                RuleFired(rule="nps_score <= 4", actual=customer.nps_score),
                RuleFired(rule="email_open_rate < 0.20", actual=customer.email_open_rate),
            ],
        )

    # P2: Competitor-Switched
    if (
        customer.recency_days > 90
        and customer.app_sessions_mo == 0
        and customer.email_open_rate < 0.10
    ):
        return RiskClassificationResult(
            matched_segment=RiskSegmentName.COMPETITOR_SWITCHED,
            next_best_action=NextBestAction.NURTURE,
            engagement_policy="Win-back window closes after 180 days - do not invest beyond this threshold",
            rules_fired=[
                RuleFired(rule="recency_days > 90", actual=customer.recency_days),
                RuleFired(rule="app_sessions_mo == 0", actual=customer.app_sessions_mo),
                RuleFired(rule="email_open_rate < 0.10", actual=customer.email_open_rate),
            ],
        )

    # P3: Disengaged
    if (
        customer.recency_days > 60
        and customer.app_sessions_mo < 2
        and customer.email_open_rate < 0.15
    ):
        return RiskClassificationResult(
            matched_segment=RiskSegmentName.DISENGAGED,
            next_best_action=NextBestAction.NURTURE,
            engagement_policy="Do not send generic campaigns - personalise outreach to the customer's top product category",
            rules_fired=[
                RuleFired(rule="recency_days > 60", actual=customer.recency_days),
                RuleFired(rule="app_sessions_mo < 2", actual=customer.app_sessions_mo),
                RuleFired(rule="email_open_rate < 0.15", actual=customer.email_open_rate),
            ],
        )

    # P4: Healthy
    if customer.recency_days <= 30 and customer.nps_score >= 7:
        return RiskClassificationResult(
            matched_segment=RiskSegmentName.HEALTHY,
            next_best_action=NextBestAction.HOLD,
            engagement_policy="No retention spend - route to referral or advocacy programme instead",
            rules_fired=[
                RuleFired(rule="recency_days <= 30", actual=customer.recency_days),
                RuleFired(rule="nps_score >= 7", actual=customer.nps_score),
            ],
        )

    # Fallback: Unclassified
    return RiskClassificationResult(
        matched_segment=RiskSegmentName.UNCLASSIFIED,
        next_best_action=NextBestAction.REVIEW,
        engagement_policy="Manually review customer profile and assign appropriate segment.",
        rules_fired=[],
    )
