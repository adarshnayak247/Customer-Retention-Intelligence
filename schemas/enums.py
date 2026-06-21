from enum import Enum


class CLVTier(str, Enum):
    """Customer Lifetime Value tier classification."""

    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"


class NextBestAction(str, Enum):
    """Recommended next best action for a customer."""

    ESCALATE = "ESCALATE"
    NURTURE = "NURTURE"
    HOLD = "HOLD"
    REVIEW = "REVIEW"


class RiskSegmentName(str, Enum):
    """Risk segment classification labels."""

    SUPPORT_FATIGUED = "Support-Fatigued"
    COMPETITOR_SWITCHED = "Competitor-Switched"
    DISENGAGED = "Disengaged"
    HEALTHY = "Healthy"
    UNCLASSIFIED = "Unclassified"


class QualityRating(str, Enum):
    """LLM-as-Judge quality rating for evaluation."""

    GOOD = "GOOD"
    BAD = "BAD"
