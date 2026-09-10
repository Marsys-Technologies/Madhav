#!/usr/bin/env python3
"""
ekv_terminal_check.py — robust terminal-marker detection for CAMPAIGN_COORDINATION.md.
Bash regex got this wrong TWICE tonight (missed the banner-style close, and earlier
false-positived on a prose mention). This checks: does the marker text appear, and is
it NOT an inline-quoted mention inside a sentence (the actual false-positive pattern
observed: "posts `RUN-TERMINAL: ...`" mid-sentence)? Prints COMPLETE, PARTIAL, or NONE.
"""
import re, sys

content = sys.stdin.read()

COMPLETE_MARKERS = [
    r"RUN-TERMINAL:\s*SESSION-EKAVAKYATA-NIGHT1-COMPLETE",
    r"\bEKAVAKYATA-CLOSED\b(?!-PARTIAL)",
]
PARTIAL_MARKERS = [
    r"EKV-NIGHT1-PARTIAL",
    r"EKAVAKYATA-CLOSED-PARTIAL",
]

def real_hit(patterns):
    for pat in patterns:
        for m in re.finditer(pat, content):
            before = content[:m.start()].rstrip()
            if before.endswith("`"):
                continue  # inline code-quoted mention inside prose — the known false-positive shape
            return True
    return False

if real_hit(COMPLETE_MARKERS):
    print("COMPLETE")
elif real_hit(PARTIAL_MARKERS):
    print("PARTIAL")
else:
    print("NONE")
