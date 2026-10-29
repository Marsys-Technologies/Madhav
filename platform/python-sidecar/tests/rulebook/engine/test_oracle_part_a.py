"""E3a: the independently authored, hand-derived oracle set (Part A: synthetic cards, synthetic fixtures).

The expected values in data/oracle_partA_synthetic.json were derived by an author who never saw
the evaluator (explicit arithmetic on the fixtures). Part B (real rules) is private; its counts
are reported in the PR, not here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.rulebook.engine import chart as chart_mod
from services.rulebook.engine import oracle_check, resolve

DATA = Path(__file__).parent / "data" / "oracle_partA_synthetic.json"


@pytest.fixture(scope="module")
def doc():
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_oracle_part_a_has_no_mismatch(doc):
    res = oracle_check.run(doc)
    assert res["cases"] >= 60
    assert res["values"] >= 350
    assert res["mismatches"] == []


def test_oracle_part_a_is_synthetic_only(doc):
    for c in doc["cases"]:
        assert c["card"]["field1_citation"]["text_id"] == "synthtext"
    assert doc["oracle_schema"] == "rulebook-oracle-v1"


def test_oracle_can_fail(doc, monkeypatch):
    """Not vacuous: break the house count and the oracle must object."""
    real = chart_mod.house_from

    def off_by_one(ref, sign):
        h = real(ref, sign)
        return None if h is None else (h % 12) + 1

    monkeypatch.setattr(resolve, "house_from", off_by_one)
    assert oracle_check.run(doc)["mismatches"]
