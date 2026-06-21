import re

from schemas.playbook import RetentionPlaybook


def resolve_tier_in_step(step: str, clv_tier: str) -> str:
    """Resolve all tier-conditional language in a playbook step.

    Handles four regex patterns for Gold/Platinum vs Silver/Bronze branching.
    """
    is_premium = clv_tier.lower() in ("gold", "platinum")

    # Pattern 1: trailing "- Gold/Platinum: X; Silver/Bronze: Y"
    step = re.sub(
        r'\s*-\s*Gold/Platinum:\s*(.+?);\s*Silver/Bronze:\s*(.+?)$',
        lambda m: f" - {m.group(1).strip()}" if is_premium else f" - {m.group(2).strip()}",
        step, flags=re.IGNORECASE,
    )

    # Pattern 2: "... - A or B (Gold/Platinum: X; Silver/Bronze: Y)"
    step = re.sub(
        r'\s*-\s*[^-(]+\s+or\s+[^(]+\(Gold/Platinum:\s*([^;)]+);\s*Silver/Bronze:\s*([^)]+)\)',
        lambda m: f" - {m.group(1).strip()}" if is_premium else f" - {m.group(2).strip()}",
        step, flags=re.IGNORECASE,
    )

    # Pattern 3: "escalate to CRM specialist for Gold/Platinum customers; move Silver/Bronze to X"
    step = re.sub(
        r'escalate to CRM specialist for Gold/Platinum customers;\s*move Silver/Bronze to (.+?)$',
        lambda m: "escalate to CRM specialist" if is_premium else f"move to {m.group(1).strip()}",
        step, flags=re.IGNORECASE,
    )

    # Pattern 4: "X (Gold/Platinum tier) or Y (Silver/Bronze tier) - trailing"
    step = re.sub(
        r'(.+?)\s*\(Gold/Platinum tier\)\s*or\s*(.+?)\s*\(Silver/Bronze tier\)(.*?)$',
        lambda m: f"{m.group(1).strip()}{m.group(3)}" if is_premium else f"{m.group(2).strip()}{m.group(3)}",
        step, flags=re.IGNORECASE,
    )

    return step.strip()


def lookup_playbook(
    segment_name: str,
    playbooks: list[RetentionPlaybook],
) -> RetentionPlaybook | None:
    """Find the retention playbook matching the given segment name."""
    segment_name_clean = segment_name.strip().lstrip("-").strip()
    return next(
        (pb for pb in playbooks if pb.segment.lower() == segment_name_clean.lower()),
        None,
    )
