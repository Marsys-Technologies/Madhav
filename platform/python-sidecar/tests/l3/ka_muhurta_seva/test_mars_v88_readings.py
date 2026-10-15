"""NB-02: exercise both local v.88 readings, without choosing a translation.

These are synthetic chart-free sky controls, not claims about the native.
Removing the reconstruction companion must turn the disagreement control red.
The entire directory runs in CI's required kala-db-tests job.
"""
import json
from pathlib import Path

import pytest

from services.ka_muhurta_seva.parihara_eval import evaluate_candidate


FIXTURES = Path(__file__).with_name("parihara_predicates.json")


def mars_readings():
    return [row for row in json.loads(FIXTURES.read_text())
            if row["dosha_canonical_id"] == "mars_eighth"]


@pytest.mark.parametrize("mars,sun,lagna,expected,state,reason,observed", [
    # Scorpio is eighth from Aries, neither debilitated nor close to the Sun.
    (220., 0., 0., ["applies", "does_not_apply"],
     "cancellation_unassessed", "readings_disagree",
     [[False, False, True], [True, False, False]]),
    # Cancer is eighth from Sagittarius: the debilitation condition is earned.
    (100., 0., 240., ["applies", "applies"], "cancelled", None,
     [[True, False, True], [True, True, False]]),
    # Scorpio eighth from Aries, ten degrees from the Sun: combust.
    (220., 210., 0., ["applies", "applies"], "cancelled", None,
     [[False, True, True], [True, False, True]]),
])
def test_mars_v88_readings_are_evaluated_and_cited_separately(
        sky, request_data, mars, sun, lagna, expected, state, reason, observed):
    sky(longitudes={"Mars": mars, "Sun": sun}, lagna=lagna)
    request_data["dosas_present"] = ["mars_eighth"]
    out = evaluate_candidate(**request_data, rules=mars_readings())

    assert out["dosas"] == [{"dosha_canonical_id": "mars_eighth",
        "state": state, "reason": reason, "by_rules": [201, 206]}]
    assert [r["result"] for r in out["rules"]] == expected
    assert [(r["extraction_context"], r["source_chunk_id"]) for r in out["rules"]] == [
        ("tika_commentary", "muhurta_chintamani_pg0116_c01"),
        ("mula_reconstructed", "muhurta_chintamani_pg0115_c02"),
    ]
    for row, values in zip(out["rules"], observed):
        assert "v.88" in row["source_citation"]
        assert len(row["terms"]) == len(values)
        for term, value in zip(row["terms"], values):
            assert [o["value"] for o in term["observed"]] == [value] * 3
            for fact in term["facts"]:
                assert fact["positions"]["Mars"]["longitude_deg"] == mars
                assert fact["positions"]["Sun"]["longitude_deg"] == sun
                assert fact["lagna"]["longitude_deg"] == lagna
                assert fact["coverage"]["complete"]


def test_mars_v88_changing_combustion_cannot_become_agreement(sky, request_data):
    sky(longitudes={"Sun": 210.}, sequences={"Mars": [220., 230., 220.]})
    request_data["dosas_present"] = ["mars_eighth"]
    out = evaluate_candidate(**request_data, rules=mars_readings())
    assert out["dosas"] == [{"dosha_canonical_id": "mars_eighth",
        "state": "cancellation_unassessed", "reason": "predicate_changes_within_candidate",
        "by_rules": [201, 206]}]
    assert [r["result"] for r in out["rules"]] == ["unassessable", "unassessable"]


def test_mars_v88_preserves_literal_preparation_reading(sky, request_data):
    """Qualification must not silently replace fixture 201's governed predicate."""
    sky(longitudes={"Mars": 220.})
    request_data["dosas_present"] = ["mars_eighth"]
    out = evaluate_candidate(**request_data, rules=[r for r in mars_readings() if r["id"] == 201])
    assert out["dosas"] == [{"dosha_canonical_id": "mars_eighth", "state": "cancelled",
                             "reason": None, "by_rules": [201]}]
    assert [t["observed"][0]["value"] for t in out["rules"][0]["terms"]] == [False, False, True]
