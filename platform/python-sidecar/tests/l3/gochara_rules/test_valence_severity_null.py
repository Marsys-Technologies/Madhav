"""C8 — severity is None, never an invented 0.0 (Pravāha C8, 2026-10-02).

No rule in the spec or registry computes severity, so a default of 0.0 was an
invented value. compute_valence and RelationshipRecord now default severity to
None (migration 1156's kgew severity column allows NULL); these tests pin the
None contract on the real code paths.
"""
from __future__ import annotations

from dataclasses import asdict

import pytest

from services.gochara_rules.records import RelationshipRecord
from services.gochara_rules.valence import compute_valence


@pytest.mark.parametrize(
    "event_class,evidence_for,evidence_against,unresolved_operand",
    [
        # for-only: evidence for occurrence, none against
        ("career_advancement", 0.6, 0.0, None),
        # against-only: evidence against occurrence, none for
        ("career_setback", 0.0, 0.5, None),
        # unresolved operand: unqualified window
        ("career_entry", 0.4, 0.0, "P5c donor matrix"),
    ],
)
def test_compute_valence_severity_is_none(
    event_class, evidence_for, evidence_against, unresolved_operand
):
    v = compute_valence(
        event_class,
        evidence_for=evidence_for,
        evidence_against=evidence_against,
        unresolved_operand=unresolved_operand,
    )
    assert v.severity is None
    # mutation guard: the invented 0.0 default must never come back
    assert not isinstance(v.severity, (int, float))


def test_no_caller_converts_none_to_a_number():
    """The real valence/record paths pass None through unchanged.

    Calls the real compute_valence and the real RelationshipRecord
    constructor exactly as services/gochara_rules/permission.py invokes it
    (severity never passed), then serializes both with the dataclass idiom —
    nothing may coerce None to a number on the way out.
    """
    v = compute_valence("career_advancement", evidence_for=0.6,
                        evidence_against=0.0)
    assert asdict(v)["severity"] is None

    rec = RelationshipRecord(
        chart_id="chart:test", generation="5.0",
        event_class="career_advancement", affected_person="native",
        frame="lagna", agent="Jupiter", relation="occupancy",
        object_id="obj:sign:9", object_kind="sign_span",
        object_role="signature_house",
        contact_id=None, path_id="P1", rule_version="v1",
        prerequisites=[], provenance="verse_cited",
        operator_role="scored")
    assert rec.severity is None
    assert asdict(rec)["severity"] is None
    assert not isinstance(rec.severity, (int, float))
