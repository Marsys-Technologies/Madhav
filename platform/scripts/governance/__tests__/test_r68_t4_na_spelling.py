"""test_r68_t4_na_spelling.py — R68 (T4 half only; NIKASHA_CHANGE_REGISTER_v2_0.md).

Verdict spelling drift: T3 :359/:520 use "NO DETECTOR" (space) while T4 :278 used a bare "NA" —
both diverge from the closed verdict set (`PASS` / `FAIL` / `PARTIAL` / `NO_DETECTOR` / `N/A`) that
ledgers, tracker and census already use. Per D2 ruling 2026-09-27 only the T4 half proceeds now
(the T3 :359/:520 half is D2 reopen work on the sealed tier-3 document, out of scope here). This
test covers the T4 half: the "history" check's "if never run" branch must read the closed-set
`N/A`, never a bare `NA`.
"""
from __future__ import annotations

import re
import pathlib

T4 = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md"


def test_history_check_uses_closed_set_na_spelling():
    text = T4.read_text(encoding="utf-8")
    # Isolate check 8 ("history")'s row so a match elsewhere in the doc (e.g. the verdict-vocabulary
    # sentence itself, which correctly spells N/A already) cannot mask a regression here.
    m = re.search(r"\*\*history\*\*.*?\n", text)
    assert m, "could not locate the history check row"
    row = m.group(0)
    assert re.search(r"(?<![A-Za-z/])NA(?![A-Za-z/])", row) is None, (
        f"history check row still uses a bare 'NA': {row!r}"
    )
    assert "N/A if never run" in row
