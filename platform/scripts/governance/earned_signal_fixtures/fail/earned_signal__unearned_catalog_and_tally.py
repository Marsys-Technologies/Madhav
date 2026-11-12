# EXPECT-VIOLATIONS: 2
from dataclasses import dataclass

UPAPADA_RULES: list[dict] = [{
    "slug": "unearned",
    "rule_id": _rule_id("text", "verse", "unearned"),
    "condition": "no_chart_condition",
    "verdict": "PASS",
    "citation_human": "Example citation",
}]


@dataclass
class FrozenSummary:
    two_pass_verified: int = 0


def compare():
    return FrozenSummary()
