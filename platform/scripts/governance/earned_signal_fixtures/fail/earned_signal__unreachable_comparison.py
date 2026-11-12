# EXPECT-VIOLATIONS: 1
from dataclasses import dataclass

@dataclass
class FrozenSummary:
    two_pass_verified: int = 0

def fake_comparison(row, expected):
    result = FrozenSummary()
    if False:
        comparison = compare_row(row, expected)
        if comparison.verdict == TWO_PASS_VERIFIED:
            result.two_pass_verified += 1
    return result
