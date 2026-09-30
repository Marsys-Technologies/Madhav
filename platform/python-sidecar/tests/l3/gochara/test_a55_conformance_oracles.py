"""Frozen A5.5 test oracles — annual identity + conformance (spec §9, §10).

Oracle set (GOCHARA_TEST_ORACLES_v1_4, given/when/then normative):
O-AO-1, O-AO-2, O-AO-3 (§9 annual_object_identity);
O-CF-N5, O-CF-N6, O-CF-N7 (§10 conformance).

REAL tests where the merged code exposes the seam (O-CF-N5 producer trim
policy, O-CF-N6 birth_anchor exclusion, O-CF-N7 testimony A/B, O-AO-3
pre-D-T2 empty set); strict=False xfail naming the exact missing symbol
where the target belongs to the unbuilt A5.x writer (never a faked pass).

L1 pins: chart 482012f1-710e-4a25-994a-93821f5871aa, ayanamsha
lahiri_chitrapaksha, natal build 1c092ffb-72eb-4614-8422-552ca6eae985.
All operands printed literals — no database is queried.
"""
from __future__ import annotations

import pytest

from services.gochara_rules.predicates import ADMITTED
from services.gochara_rules.records import RelationshipRecord
from services.gochara_rules.registry import RULE_PATHS, signature_houses
from services.gochara_rules.score import (
    path_channel_scores, record_channel_value,
)
from services.gochara_v3.resolution_hierarchy import (
    MIN_PEAK_SEPARATION_DAYS, PeakCandidate, retain_candidates,
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _record(**kw) -> RelationshipRecord:
    base = dict(
        chart_id=CHART_ID, generation="5.0", event_class="marriage",
        affected_person="native", frame="lagna", agent="Jupiter",
        relation="residence", object_id="obj:sign:Libra",
        object_kind="sign_span", object_role="occupant",
        contact_id="sha256:contact-x", path_id="P3", rule_version="1.0.0",
        prerequisites=[], provenance="verse_cited", operator_role="scored",
    )
    return RelationshipRecord(**{**base, **kw})


# ── O-CF-N5 (§10; defects N5, RQ-6) — 90-day filter is serve-time only ──────
def test_o_cf_n5_producer_keeps_both_peaks_60d_apart():
    # given: a producer fixture containing TWO eligible peaks 60 days apart
    # (< 90) — literal jds and λ.
    admitted = [PeakCandidate(jd=1000.0, lam=0.90),
                PeakCandidate(jd=1060.0, lam=0.85)]  # 60 days apart
    assert MIN_PEAK_SEPARATION_DAYS == 90.0

    # then: BOTH peaks survive in the producer output — the producer default
    # applies NO MIN_PEAK_SEPARATION_DAYS filter (N-17/H-5).
    produced = retain_candidates(admitted)
    assert [c.jd for c in produced] == [1000.0, 1060.0]
    assert len(produced) == 2

    # the 90-day filter, where applied, exists only at serve time — the
    # caller must pass min_separation_days explicitly; the lower-λ follower
    # trims, the higher-λ peak never re-ranks away.
    served = retain_candidates(admitted, min_separation_days=90.0)
    assert [c.jd for c in served] == [1000.0]
    # mutation guard: a producer-side 90-day suppression drops one peak and
    # fails the count.
    assert len(produced) != len(served)


# ── O-CF-N6 (§10; defect N6) — birth_anchor: zero rows, control non-empty ───
def test_o_cf_n6_birth_anchor_excluded_control_present():
    # ZERO rows for birth_anchor at any resolution: the registry excludes it
    # from enumeration entirely — the seam raises rather than fabricate.
    with pytest.raises(ValueError, match="birth_anchor"):
        signature_houses("birth_anchor", {"lagna_deg": 12.43, "natal": {}})
    # the class has no rule path either (no enumeration entry point).
    assert ("birth_anchor", "1.0.0") not in RULE_PATHS
    # POSITIVE CONTROL: a non-empty control class resolves its known rows
    # (an empty or no-op build fails the control, not just the assertion).
    chart = {"lagna_deg": 12.43,
             "natal": {"Sun": 291.96, "Moon": 327.06, "Mars": 198.52,
                       "Mercury": 270.84, "Jupiter": 249.79, "Venus": 259.19,
                       "Saturn": 202.43, "Rahu": 49.03, "Ketu": 229.03},
             "day_birth": True, "paksha": "Shukla"}
    control = signature_houses("marriage", chart)
    assert control and isinstance(control, frozenset)


# ── O-CF-N7 (§10; defects N7, RQ-4) — mūrti rows testimony, zero effect ─────
def test_o_cf_n7_moorti_testimony_bit_identical_score():
    # given: synthetic mūrti rows per the oracle's shape — operator_role =
    # testimony, provenance uncited_extension (never verse_cited by
    # computation alone), attached beside a scored row.
    scored = _record(agent="Jupiter", relation="residence",
                     object_id="obj:sign:Libra")
    moorti = _record(agent="Jupiter", relation="association",
                     object_id="obj:sign:Libra", contact_id=None,
                     object_role="karaka",
                     provenance="uncited_extension",
                     operator_role="testimony", ruling_ref="D-T2-pending")
    assert moorti.operator_role == "testimony"
    assert moorti.provenance != "verse_cited"

    ev_scored = record_channel_value(
        scored, "marriage", "favourable", [{"value": 0.5, "null_state": "omit"}])
    ev_moorti = record_channel_value(
        moorti, "marriage", "favourable", [{"value": 0.9, "null_state": "omit"}])
    # the mūrti annotation is present in BOTH content fields, both zero.
    assert ev_moorti == {"evidence_for_occurrence": 0.0,
                         "evidence_against_occurrence": 0.0}
    # a window scored WITH vs WITHOUT the mūrti rows is BIT-IDENTICAL.
    without = path_channel_scores([scored], "marriage",
                                  {scored.record_id: ev_scored})
    with_ = path_channel_scores(
        [scored, moorti], "marriage",
        {scored.record_id: ev_scored, moorti.record_id: ev_moorti})
    assert with_ == without
    # positive control: the scored row moves its channel (no vacuous pass).
    assert without["evidence_for_occurrence"] > 0.0


@pytest.mark.xfail(
    reason="A5.5: the production mūrti row audit (actual build rows carry no "
           "computed verse_cited) requires the A5.x build; the A/B scoring "
           "leg above is real",
    strict=False)
def test_o_cf_n7_production_moorti_row_audit():
    # the row-audit leg against actual build rows (oracle's 'given').
    from services.ka_moorti_nirnaya.writer import audit_moorti_rows  # expected
    report = audit_moorti_rows(CHART_ID)
    assert report["verse_cited_by_computation"] == 0
    assert all(r["operator_role"] == "testimony" for r in report["rows"])


# ── O-AO-3 (§9; defects D-T2-gate, S-04) — pre-D-T2 P9: testimony or empty ──
def test_o_ao_3_no_scored_p9_before_d_t2():
    # the empty set, asserted AS SUCH (the oracle admits it): no P9 rule
    # path exists in the frozen registry before D-T2.
    assert not any(path_id == "P9" for (path_id, _v) in RULE_PATHS), (
        "a P9 rule path exists before D-T2 — it must be testimony-only, "
        "never scored")
    # a synthetic scored-P9-row fixture demonstrates the audit shape the
    # gate requires: a scored P9 row is the defect on test.
    scored_p9 = _record(path_id="P9", operator_role="scored")
    assert scored_p9.operator_role == "scored"  # fixture built…
    testimony_p9 = _record(path_id="P9", operator_role="testimony",
                           provenance="uncited_extension",
                           ruling_ref="D-T2-pending")
    ev = record_channel_value(
        testimony_p9, "marriage", "favourable",
        [{"value": 0.9, "null_state": "omit"}])
    # …and a testimony P9 row carries zero in both channels, no activation
    # factor present.
    assert ev == {"evidence_for_occurrence": 0.0,
                  "evidence_against_occurrence": 0.0}
    assert not hasattr(testimony_p9, "activation_factor")


# ── O-AO-1 (§9; defects saham-year-mixing, S-07) — year-qualified join ──────
@pytest.mark.xfail(
    reason="A5.3 not built: annual object store (expected symbol "
           "services.gochara_rules.annual.join_annual_objects); the broken "
           "kind-only join is the defect on test",
    strict=False)
def test_o_ao_1_year_qualified_join_no_cross_year_match():
    # given: Vivāha saham for two consecutive varṣa years (two rows,
    # different longitudes; values derive from the varṣa-praveśa charts at
    # build time — literals substituted when the annual store exists).
    from services.gochara_rules.annual import join_annual_objects  # expected
    rows = [
        {"chart_id": CHART_ID, "year": 2025, "kind": "vivaha_saham",
         "longitude": None},  # varṣa-praveśa-derived at build
        {"chart_id": CHART_ID, "year": 2026, "kind": "vivaha_saham",
         "longitude": None},
    ]
    hit = join_annual_objects(rows, chart_id=CHART_ID, year=2025,
                              kind="vivaha_saham")
    assert hit["year"] == 2025
    # the broken join (kind alone) returns cross-year rows — demonstrated:
    cross = join_annual_objects(rows, chart_id=CHART_ID, year=None,
                                kind="vivaha_saham")
    assert len(cross) == 2  # the defect, shown, never silently matched


# ── O-AO-2 (§9; defects saham-provenance, R2-S06) — saham source register ───
@pytest.mark.xfail(
    reason="A5.3 not built: no saham rows exist yet; the positive control "
           "(≥1 saham row whose source_ref resolves to a B3.3-register "
           "Tājaka chunk locator) may not vacuously pass on an empty set",
    strict=False)
def test_o_ao_2_saham_source_ref_resolves_in_b33_register():
    from services.gochara_rules.annual import saham_rows  # expected
    rows = saham_rows(CHART_ID)
    assert rows, "positive control: at least one saham row must exist"
    for row in rows:
        assert row["source_ref"].startswith("TN"), (
            "saham source_ref must resolve to a Tājaka Nīlakaṇṭhī chunk "
            "locator from the B3.3 register")
