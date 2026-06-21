import pandas as pd
from bl.similarity import semantic_similarity_pct
from prompts.judge_prompt import JUDGE_SYSTEM_PROMPT
from schemas.evaluation import JudgeEvaluation


def judge_response(
    agent_response: str,
    reference_response: str,
    llm,
    embeddings,
) -> JudgeEvaluation:
    """Evaluate an agent response against a reference using LLM-as-Judge.

    Args:
        agent_response: The agent's output for a customer.
        reference_response: The human-authored reference response.
        llm: Azure ChatOpenAI LLM instance.
        embeddings: Azure Embeddings instance for similarity computation.

    Returns:
        A structured JudgeEvaluation with quality ratings and similarity score.
    """
    prompt = f"""{JUDGE_SYSTEM_PROMPT}

---
AGENT RESPONSE:
{agent_response}

REFERENCE RESPONSE:
{reference_response}
---

Evaluate all four dimensions and respond in exact JSON and nothing else:
{{
  "agent_risk_segment": "<Support-Fatigued | Disengaged | Competitor-Switched | Healthy | MISSING>",
  "agent_next_best_action": "<ESCALATE | NURTURE | HOLD | MISSING>",
  "reference_risk_segment": "<Support-Fatigued | Disengaged | Competitor-Switched | Healthy>",
  "reference_next_best_action": "<ESCALATE | NURTURE | HOLD>",
  "risk_segment_match": true or false,
  "next_best_action_match": true or false,
  "action_rationale_quality": "<GOOD or BAD>",
  "action_rationale_justification": "<one sentence>",
  "treatment_steps_quality": "<GOOD or BAD>",
  "treatment_steps_justification": "<one sentence>"
}}"""

    response = llm.invoke(prompt)
    evaluation = JudgeEvaluation.from_llm_json(response.content)
    evaluation.semantic_similarity_pct = semantic_similarity_pct(
        agent_response, reference_response, embeddings
    )
    return evaluation


def run_batch_evaluation(
    eval_df: pd.DataFrame,
    llm,
    embeddings,
) -> pd.DataFrame:
    """Run LLM-as-Judge evaluation for a batch of agent responses.

    Args:
        eval_df: DataFrame with columns ['customer_id', 'agent_response', 'reference_agent_response'].
        llm: Azure ChatOpenAI LLM instance.
        embeddings: Azure Embeddings instance.

    Returns:
        DataFrame with evaluation results for each customer.
    """
    eval_results: list[JudgeEvaluation] = []

    for _, row in eval_df.iterrows():
        cid = row["customer_id"]
        print(f"Judging {cid}...", end=" ")

        result = judge_response(
            row["agent_response"],
            row["reference_agent_response"],
            llm,
            embeddings,
        )
        result.customer_id = cid
        eval_results.append(result)

        seg_ok = "✓" if result.risk_segment_match else "✗"
        nba_ok = "✓" if result.next_best_action_match else "✗"
        print(
            f"Segment {seg_ok}  NBA {nba_ok}  "
            f"Rationale {result.action_rationale_quality.value}  "
            f"Steps {result.treatment_steps_quality.value}  "
            f"Similarity {result.semantic_similarity_pct}%"
        )

    eval_results_df = pd.DataFrame(
        [result.model_dump() for result in eval_results]
    )

    # Print summary
    print(f"\n{'=' * 55}")
    print(f"Risk Segment Accuracy : {eval_results_df['risk_segment_match'].mean():.0%}")
    print(f"NBA Accuracy          : {eval_results_df['next_best_action_match'].mean():.0%}")
    print(
        f"Action Rationale GOOD : "
        f"{(eval_results_df['action_rationale_quality'] == 'GOOD').sum()}"
        f"/{len(eval_results_df)}"
    )
    print(
        f"Treatment Steps GOOD  : "
        f"{(eval_results_df['treatment_steps_quality'] == 'GOOD').sum()}"
        f"/{len(eval_results_df)}"
    )
    print(f"Avg Semantic Similarity: {eval_results_df['semantic_similarity_pct'].mean():.1f}%")
    print(f"{'=' * 55}")

    return eval_results_df
