"""test_r64_t4_nine_checks_heading.py — R64 (NIKASHA_CHANGE_REGISTER_v2_0.md).

T4's §4.2 heading said "the six checks" while the body under it already enumerates nine checks
(1 registered .. 9 dependency liveness, "All nine checks run read-only, and all nine can return
false"). Also fixes the Build gate row in §4 which cross-referenced §4.2 with the same stale
count ("the six checks of §4.2"). Fails against the pre-fix text.
"""
from __future__ import annotations

import pathlib
import re

T4 = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md"


def test_no_stale_six_checks_phrase():
    text = T4.read_text(encoding="utf-8")
    assert "the six checks" not in text


def test_section_4_2_heading_says_nine_checks():
    text = T4.read_text(encoding="utf-8")
    assert re.search(r"^### 4\.2 .*the nine checks", text, re.MULTILINE), (
        "§4.2 heading must read 'the nine checks'"
    )


def test_body_actually_enumerates_nine_numbered_checks():
    text = T4.read_text(encoding="utf-8")
    section = text.split("### 4.2", 1)[1].split("\n## ", 1)[0]
    numbered = re.findall(r"^\| (\d+) \| \*\*", section, re.MULTILINE)
    assert numbered == [str(i) for i in range(1, 10)], numbered
