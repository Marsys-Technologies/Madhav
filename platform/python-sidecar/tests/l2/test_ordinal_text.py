"""The shared English ordinal helper (brahmagyan.ordinal_text.ordinal) and the L2 sentences that use it.

The bug this pins: bo_karanajala printed 'Argala: Venus in 2th from Sun' and bo_pratijna_v4_engine printed
'(1th) from lagna' because the suffix was a fixed 'th'. Only 4th..10th, and 11th-13th, were right by accident.
"""
from __future__ import annotations

import pytest

from brahmagyan.ordinal_text import ordinal
from pipeline.orchestrator.writers.bo_karanajala import _build_argala_edges
from pipeline.orchestrator.writers import bo_pratijna_v4_engine as E


@pytest.mark.parametrize(
    "n, expected",
    [
        (1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"), (5, "5th"), (9, "9th"), (10, "10th"),
        (11, "11th"), (12, "12th"), (13, "13th"), (14, "14th"),
        (20, "20th"), (21, "21st"), (22, "22nd"), (23, "23rd"), (24, "24th"),
        (101, "101st"), (102, "102nd"), (103, "103rd"), (111, "111th"), (112, "112th"), (113, "113th"),
        (121, "121st"), (0, "0th"),
    ],
)
def test_ordinal_suffix_table(n, expected):
    assert ordinal(n) == expected


def test_ordinal_covers_every_house_number_exactly():
    assert [ordinal(h) for h in range(1, 13)] == [
        "1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th",
    ]


@pytest.mark.parametrize("bad", [2.0, "2", None, True])
def test_ordinal_refuses_a_non_integer_instead_of_inventing_a_suffix(bad):
    with pytest.raises(TypeError):
        ordinal(bad)


def test_ordinal_is_pure_and_deterministic():
    assert [ordinal(i) for i in range(1, 200)] == [ordinal(i) for i in range(1, 200)]


def _argala_sentence(offset: int, direction: str = "forward") -> str:
    node_map = {("graha", "Sun"): "node-sun", ("graha", "Venus"): "node-ven"}
    facts = [{
        "fact_id": "f1", "target": "Sun", "source": "Venus", "offset": offset,
        "obstruction_offset": 12, "obstructors": [], "direction": direction,
    }]
    (edge,) = _build_argala_edges("chart-1", "lahiri_chitrapaksha", "build-1", facts, node_map, "2026-10-07T00:00:00+00:00")
    return edge["citation_human"]


def test_bo_karanajala_argala_sentence_second_house_reads_2nd_not_2th():
    assert _argala_sentence(2) == "Argala: Venus in 2nd from Sun (argala)"


@pytest.mark.parametrize("offset, word", [(2, "2nd"), (4, "4th"), (5, "5th"), (11, "11th")])
def test_bo_karanajala_argala_sentence_for_every_argala_house(offset, word):
    assert f"Venus in {word} from Sun" in _argala_sentence(offset)


def test_bo_karanajala_argala_sentence_keeps_reverse_marker():
    assert _argala_sentence(2, "reverse") == "Argala: Venus in 2nd from Sun (counted in reverse) (argala)"


def test_bo_pratijna_neecha_bhanga_reason_uses_proper_ordinals():
    # graha in sign 7 (Libra) -> dispositor Venus; the sentence builder only reads the house maps and the sign number.
    ok, reason = E._neecha_bhanga("Sun", 7, 1, 1, {"Venus": 1})
    assert ok and reason == "dispositor Venus is kendra (1st) from lagna"
    ok, reason = E._neecha_bhanga("Sun", 7, 1, 4, {"Venus": 7})
    assert ok and reason == "dispositor Venus is kendra (7th) from lagna"
    ok, reason = E._neecha_bhanga("Sun", 7, 1, 10, {"Venus": 3})
    assert not ok and reason == "dispositor Venus not kendra from lagna (3rd) or Moon (6th)"
    ok, reason = E._neecha_bhanga("Sun", 7, 2, 3, {"Venus": 3})
    assert ok and reason == "dispositor Venus is kendra (1st) from Moon"


@pytest.mark.parametrize("rel", [
    "pipeline/orchestrator/writers/bo_karanajala.py",
    "pipeline/orchestrator/writers/bo_pratijna_v4_engine.py",
])
def test_no_hardcoded_th_suffix_after_an_interpolation(rel):
    """A '{x}th' f-string is the defect itself; these writers must route every ordinal through ordinal()."""
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parents[2] / rel).read_text(encoding="utf-8")
    assert not re.findall(r"\}(?:th|st|nd|rd)\b", src)
