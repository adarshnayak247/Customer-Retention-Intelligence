import json
import re
from typing import Optional

from pydantic import BaseModel

from schemas.enums import QualityRating


class JudgeEvaluation(BaseModel):
    """Structured evaluation result from the LLM-as-Judge."""

    agent_risk_segment: str
    agent_next_best_action: str
    reference_risk_segment: str
    reference_next_best_action: str
    risk_segment_match: bool
    next_best_action_match: bool
    action_rationale_quality: QualityRating
    action_rationale_justification: str
    treatment_steps_quality: QualityRating
    treatment_steps_justification: str
    semantic_similarity_pct: Optional[float] = None
    customer_id: Optional[str] = None

    @classmethod
    def from_llm_json(cls, content: str) -> "JudgeEvaluation":
        """Parse LLM output (potentially wrapped in markdown code fences) into a JudgeEvaluation."""
        content = content.strip()
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        return cls.model_validate(json.loads(content.strip()))
