# EXPECT-VIOLATIONS: 1
from dataclasses import dataclass

@dataclass
class Summary:
    two_pass_verified: int = 0

def summarize(row, expected):
    summary = Summary()
    comparison = compare_row(row, expected)
    comparison = ForcedVerdict()
    if comparison.verdict == TWO_PASS_VERIFIED:
        summary.two_pass_verified += 1
    return summary

class ForcedVerdict:
    verdict = TWO_PASS_VERIFIED
