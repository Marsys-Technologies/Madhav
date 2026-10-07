"""ga_structural aspect sentences use proper ordinals ('Saturn 3rd aspect', not '3th').

These L1 sentences are copied verbatim into bodha_msr_signals.citation_human by bo_laksana, so the
L2 rows only read correctly after ga_structural is rebuilt with this fix.
"""
from __future__ import annotations

import pytest

from brahmagyan.ordinal_text import ordinal

def test_ga_structural_aspect_sentences_use_proper_ordinals():
    import re
    from tests.test_ga8_writer import MOCK_CHART_OUTPUT
    import ga_writers.ga_structural_writer as sut

    args = ("c", "b", "lahiri_chitrapaksha", "2026-10-07T00:00:00+00:00", "e")
    rows = sut._build_aspect_rows(MOCK_CHART_OUTPUT, *args)
    saturn = [r for r in rows if r["fact_category"] == "aspect_parashari_given" and r["fact_subject"] == "SAT"]
    assert len(saturn) == 3
    for r in saturn:
        m = re.search(r" (\d+)(st|nd|rd|th) aspect on house", r["citation_human"])
        assert m, r["citation_human"]
        assert m.group(0).strip().split(" ")[0] == ordinal(int(m.group(1)))
    assert sorted(re.search(r" (\w+) aspect on house", r["citation_human"]).group(1) for r in saturn) == ["10th", "3rd", "7th"]
    received = [r for r in rows if r["fact_category"] == "aspect_parashari_received" and "Saturn 3" in r["citation_human"]]
    assert received and all("Saturn 3rd aspect" in r["citation_human"] for r in received)

    vrows = sut._build_virupa_drishti_rows({"Saturn": {"house": 1}}, "D1", *args)
    assert sorted(r["citation_human"].split(" ")[3] for r in vrows) == ["10th", "3rd", "7th"]
    assert not any(re.search(r"(^|[^0-9])[123]th\b", r["citation_human"]) for r in rows + vrows)


def test_ga_structural_has_no_hardcoded_th_suffix_after_an_interpolation():
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parents[2] / "ga_writers/ga_structural_writer.py").read_text(encoding="utf-8")
    assert not re.findall(r"\}(?:th|st|nd|rd)\b", src)
