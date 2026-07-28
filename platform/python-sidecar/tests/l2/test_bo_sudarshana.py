"""
Tests for bo_sudarshana / bodha_writers.sudarshana_emitter (D-1.5b Lane B-3, CR-100).

Covers:
  - house_from() sign-count arithmetic (pure math, no DB)
  - classify_house() classical quadrant priority
  - compute_tri_frame() agreement classification
  - the TYPE SPECIMEN independently reproduced against chart 482012f1's real
    lahiri_chitrapaksha graha_position sign facts (Sun+Mercury both Capricorn,
    Lagna Aries, Moon Aquarius): 10th-from-Lagna vs 12th-from-Moon — verified
    live via mcp__postgres__query against chart_facts before writing this test
    (the brief's own specimen for this lane; confirmed to hold, unlike some
    other D-1.5b lane specimens which needed replacement).
  - build_signal_row() emits the DIS.016/DR-3 ratified class_prior=1.15,
    subsystem='structural' constants, and all bodha_msr_signals NOT NULL
    columns are populated.
"""
from __future__ import annotations

import json

import pytest

from bodha_writers.sudarshana_emitter import (
    SIGNS,
    SIGN_INDEX,
    GRAHAS,
    SUDARSHANA_CLASS_PRIOR,
    SUDARSHANA_SUBSYSTEM,
    SIGNAL_TYPE_CLASS,
    house_from,
    classify_house,
    sign_index,
    compute_tri_frame,
    build_signal_row,
)


# ── house_from() ──────────────────────────────────────────────────────────

def test_house_from_self_is_always_first():
    for s in range(12):
        assert house_from(s, s) == 1


def test_house_from_wraps_correctly():
    # Aries(0) reference, graha in Pisces(11) -> 12th house
    assert house_from(0, 11) == 12
    # Aries(0) reference, graha in Taurus(1) -> 2nd house
    assert house_from(0, 1) == 2
    # Aquarius(10) reference, graha in Capricorn(9) -> ((9-10)%12)+1 = 12
    assert house_from(10, 9) == 12
    # Capricorn(9) reference, graha in Aries(0) -> ((0-9)%12)+1 = 4
    assert house_from(9, 0) == 4


def test_house_from_range_always_1_to_12():
    for ref in range(12):
        for tgt in range(12):
            h = house_from(ref, tgt)
            assert 1 <= h <= 12


# ── classify_house() priority order ─────────────────────────────────────

def test_classify_house_trikona_priority_over_kendra():
    # H1 is both kendra and trikona -> trikona wins (highest priority)
    assert classify_house(1) == "trikona"


def test_classify_house_kendra_priority_over_upachaya():
    # H10 is both kendra and upachaya -> kendra wins
    assert classify_house(10) == "kendra"


def test_classify_house_dusthana_priority_over_upachaya():
    # H6 is both dusthana and upachaya -> dusthana wins
    assert classify_house(6) == "dusthana"


def test_classify_house_pure_categories():
    assert classify_house(5) == "trikona"
    assert classify_house(9) == "trikona"
    assert classify_house(4) == "kendra"
    assert classify_house(7) == "kendra"
    assert classify_house(3) == "upachaya"
    assert classify_house(11) == "upachaya"
    assert classify_house(8) == "dusthana"
    assert classify_house(12) == "dusthana"
    assert classify_house(2) == "maraka"


def test_classify_house_covers_all_12():
    for h in range(1, 13):
        cls = classify_house(h)
        assert cls in ("trikona", "kendra", "dusthana", "upachaya", "maraka", "neutral")


# ── sign_index() ──────────────────────────────────────────────────────────

def test_sign_index_known_signs():
    assert sign_index("Aries") == 0
    assert sign_index("Capricorn") == 9
    assert sign_index("Aquarius") == 10
    assert sign_index("Pisces") == 11


def test_sign_index_unknown_or_none():
    assert sign_index(None) is None
    assert sign_index("") is None
    assert sign_index("NotASign") is None


def test_signs_list_is_12_and_matches_index():
    assert len(SIGNS) == 12
    for i, s in enumerate(SIGNS):
        assert SIGN_INDEX[s] == i


# ── compute_tri_frame() agreement classification ─────────────────────────

def test_compute_tri_frame_confirmed_when_all_three_match():
    # Contrived: reference points chosen so the graha lands in trikona from
    # all three frames (Lagna=0, Moon=4, Sun=8; graha=4 -> houses 5,1,9, all trikona)
    tri = compute_tri_frame(graha_sign0=4, lagna_sign0=0, moon_sign0=4, sun_sign0=8)
    assert tri["house_from_lagna"] == 5
    assert tri["house_from_moon"] == 1
    assert tri["house_from_sun"] == 9
    assert tri["class_from_lagna"] == tri["class_from_moon"] == tri["class_from_sun"] == "trikona"
    assert tri["agreement"] == "confirmed_3frame"
    assert tri["matching_class"] == "trikona"


def test_compute_tri_frame_partial_when_two_match():
    tri = compute_tri_frame(graha_sign0=6, lagna_sign0=0, moon_sign0=10, sun_sign0=9)
    # Mars/Saturn-equivalent specimen (see below): houses 7(kendra), 9(trikona), 10(kendra)
    assert tri["house_from_lagna"] == 7
    assert tri["house_from_moon"] == 9
    assert tri["house_from_sun"] == 10
    assert tri["class_from_lagna"] == "kendra"
    assert tri["class_from_moon"] == "trikona"
    assert tri["class_from_sun"] == "kendra"
    assert tri["agreement"] == "partial_2frame"
    assert tri["matching_class"] == "kendra"


def test_compute_tri_frame_contradicted_when_all_differ():
    tri = compute_tri_frame(graha_sign0=9, lagna_sign0=0, moon_sign0=10, sun_sign0=9)
    assert tri["agreement"] == "contradicted"
    assert tri["matching_class"] is None


# ── TYPE SPECIMEN: Sun+Mercury on chart 482012f1 (lahiri_chitrapaksha) ────
# Independently verified live against chart_facts before writing this test:
#   LAGNA=Aries, MOON=Aquarius, SUN=Capricorn, MER=Capricorn (Sun+Mercury conjunct)
# The brief's own specimen ("Sun+Mercury 12th-from-Moon vs 10th-from-Lagna")
# holds EXACTLY as stated for this real chart — no replacement needed.

def test_type_specimen_sun_mercury_10th_lagna_12th_moon():
    lagna_i = sign_index("Aries")      # 0
    moon_i = sign_index("Aquarius")    # 10
    sun_i = sign_index("Capricorn")    # 9
    # Sun and Mercury are both in Capricorn on 482012f1/lahiri_chitrapaksha.
    sun_sign_i = sign_index("Capricorn")
    mercury_sign_i = sign_index("Capricorn")
    assert sun_sign_i == mercury_sign_i  # conjunction confirmed

    tri_sun = compute_tri_frame(sun_sign_i, lagna_i, moon_i, sun_i)
    tri_mercury = compute_tri_frame(mercury_sign_i, lagna_i, moon_i, sun_i)

    # The exact specimen the brief mandates must fire:
    assert tri_sun["house_from_lagna"] == 10
    assert tri_sun["house_from_moon"] == 12
    assert tri_mercury["house_from_lagna"] == 10
    assert tri_mercury["house_from_moon"] == 12

    # 10th (kendra/career) vs 12th (dusthana/loss) are classically opposed
    # categories -> this specimen is CONTRADICTED, not confirmed.
    assert tri_sun["class_from_lagna"] == "kendra"
    assert tri_sun["class_from_moon"] == "dusthana"
    assert tri_sun["agreement"] == "contradicted"
    assert tri_mercury["agreement"] == "contradicted"


# ── build_signal_row() ────────────────────────────────────────────────────

def test_build_signal_row_uses_ratified_class_prior():
    tri = compute_tri_frame(graha_sign0=9, lagna_sign0=0, moon_sign0=10, sun_sign0=9)
    row = build_signal_row(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        ayanamsha_id="lahiri_chitrapaksha",
        build_id="00000000-0000-0000-0000-000000000000",
        graha_code="SUN",
        tri_frame=tri,
        fact_ids={"graha": "f1", "lagna": "f2", "moon": "f3", "sun": "f4"},
        now="2026-07-15T00:00:00+00:00",
    )
    cfg = json.loads(row["configuration_jsonb"])
    assert cfg["agreement"] == "contradicted"
    assert row["signal_type_class"] == SIGNAL_TYPE_CLASS == "sudarshana_agreement"
    assert row["source_subsystem"] == SUDARSHANA_SUBSYSTEM == "structural"
    assert SUDARSHANA_CLASS_PRIOR == 1.15
    assert row["computed_salience"] > 0
    assert row["constituent_facts_array"] == ["f1", "f2", "f3", "f4"]
    assert row["signal_type_id"] == "sudarshana_agreement:SUN"


def test_build_signal_row_not_null_columns_populated():
    """Every NOT NULL bodha_msr_signals column (migration 325) must be non-None."""
    tri = compute_tri_frame(graha_sign0=4, lagna_sign0=0, moon_sign0=4, sun_sign0=8)
    row = build_signal_row(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        ayanamsha_id="lahiri_chitrapaksha",
        build_id="00000000-0000-0000-0000-000000000000",
        graha_code="JUP",
        tri_frame=tri,
        fact_ids={"graha": "f1", "lagna": "f2", "moon": "f3", "sun": "f4"},
        now="2026-07-15T00:00:00+00:00",
    )
    not_null_cols = [
        "signal_id", "chart_id", "ayanamsha_id", "build_id",
        "signal_type_id", "signal_type_class", "signal_tradition",
        "fact_kind", "source_l1_asset", "source_subsystem", "lel_origin",
        "configuration_jsonb", "constituent_facts_array",
        "deterministic_strength", "verification_certainty",
        "computed_salience", "salience_formula_version",
        "domains_affected_array", "domain_salience_jsonb",
        "active_duration_class", "verification_pass_status",
        "citation_ref", "citation_human", "computed_at", "engine_version",
    ]
    for col in not_null_cols:
        assert row[col] is not None, f"{col} must not be None (NOT NULL column)"


def test_build_signal_row_specificity_reflects_agreement_grade():
    """confirmed > partial > contradicted salience, all else equal (same graha/frames shape)."""
    confirmed = compute_tri_frame(graha_sign0=4, lagna_sign0=0, moon_sign0=4, sun_sign0=8)
    contradicted = compute_tri_frame(graha_sign0=9, lagna_sign0=0, moon_sign0=10, sun_sign0=9)

    row_confirmed = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="JUP", tri_frame=confirmed,
        fact_ids={"graha": "f1", "lagna": "f2", "moon": "f3", "sun": "f4"},
        now="2026-07-15T00:00:00+00:00",
    )
    row_contradicted = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="SUN", tri_frame=contradicted,
        fact_ids={"graha": "f1", "lagna": "f2", "moon": "f3", "sun": "f4"},
        now="2026-07-15T00:00:00+00:00",
    )
    assert row_confirmed["computed_salience"] > row_contradicted["computed_salience"]


# ── P0-7 D4_GRADE_INVERSION: valence must come from matching_class (the
# classical quadrant), never from agreement (the tri-frame corroboration
# tier). Pre-fix, ALL confirmed_3frame rows were hardcoded "benefic"
# regardless of quadrant — including a confirmed DUSTHANA placement, which
# is classically inauspicious. Agreement answers "how sure are we this
# fired"; matching_class answers "is this auspicious or not" — they are
# orthogonal and must not be conflated. ──────────────────────────────────

def test_confirmed_3frame_dusthana_must_not_be_labeled_benefic():
    """Contrived: Lagna=0, Moon=6, Sun=10; graha=5 -> house_from(0,5)=6,
    house_from(6,5)=12, house_from(10,5)=8 — all three land in DUSTHANA
    (6/8/12), i.e. maximal corroboration (confirmed_3frame) of an
    INAUSPICIOUS quadrant."""
    tri = compute_tri_frame(graha_sign0=5, lagna_sign0=0, moon_sign0=6, sun_sign0=10)
    assert tri["house_from_lagna"] == 6
    assert tri["house_from_moon"] == 12
    assert tri["house_from_sun"] == 8
    assert tri["class_from_lagna"] == tri["class_from_moon"] == tri["class_from_sun"] == "dusthana"
    assert tri["agreement"] == "confirmed_3frame"
    assert tri["matching_class"] == "dusthana"

    row = build_signal_row(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        ayanamsha_id="lahiri_chitrapaksha",
        build_id="00000000-0000-0000-0000-000000000000",
        graha_code="SAT",
        tri_frame=tri,
        fact_ids={"graha": "f1", "lagna": "f2", "moon": "f3", "sun": "f4"},
        now="2026-07-15T00:00:00+00:00",
    )
    # The defect: valence was keyed on `agreement` alone, so confirmed_3frame
    # always produced "benefic" — even here, a confirmed DUSTHANA placement.
    assert row["valence"] != "benefic", (
        "confirmed_3frame agreement must not force 'benefic' valence when "
        "matching_class is dusthana (classically inauspicious) — valence "
        "must be derived from matching_class, not agreement"
    )
    # Positive assertion of the correct behavior: dusthana quadrant -> malefic.
    assert row["valence"] == "malefic"


def test_confirmed_3frame_trikona_is_benefic():
    """Sanity check the other direction: confirmed_3frame + trikona (the
    classically auspicious pillar) should still read benefic — the fix must
    not flip valence to something worse than agreement-only did for the
    genuinely auspicious case."""
    tri = compute_tri_frame(graha_sign0=4, lagna_sign0=0, moon_sign0=4, sun_sign0=8)
    assert tri["agreement"] == "confirmed_3frame"
    assert tri["matching_class"] == "trikona"
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="JUP", tri_frame=tri,
        fact_ids={"graha": "f1", "lagna": "f2", "moon": "f3", "sun": "f4"},
        now="2026-07-15T00:00:00+00:00",
    )
    assert row["valence"] == "benefic"


def test_contradicted_matching_class_none_is_honest_neutral():
    """agreement='contradicted' has matching_class=None (no single quadrant
    to restate) — valence must be an honest neutral, not a fabricated
    judgment call (§1.2: narration may only restate computed facts)."""
    tri = compute_tri_frame(graha_sign0=9, lagna_sign0=0, moon_sign0=10, sun_sign0=9)
    assert tri["agreement"] == "contradicted"
    assert tri["matching_class"] is None
    row = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="SUN", tri_frame=tri,
        fact_ids={"graha": "f1", "lagna": "f2", "moon": "f3", "sun": "f4"},
        now="2026-07-15T00:00:00+00:00",
    )
    assert row["valence"] == "neutral"


def test_valence_keyed_off_matching_class_not_agreement():
    """Direct regression guard for D4_GRADE_INVERSION: two rows with the SAME
    agreement tier (partial_2frame) but DIFFERENT matching_class (kendra vs
    dusthana) must get DIFFERENT valence. If valence were still keyed off
    agreement alone, these would be identical."""
    tri_kendra = compute_tri_frame(graha_sign0=6, lagna_sign0=0, moon_sign0=10, sun_sign0=9)
    assert tri_kendra["agreement"] == "partial_2frame"
    assert tri_kendra["matching_class"] == "kendra"

    tri_dusthana = compute_tri_frame(graha_sign0=5, lagna_sign0=0, moon_sign0=10, sun_sign0=2)
    assert tri_dusthana["house_from_lagna"] == 6
    assert tri_dusthana["house_from_moon"] == 8
    assert tri_dusthana["house_from_sun"] == 4
    assert tri_dusthana["class_from_lagna"] == "dusthana"
    assert tri_dusthana["class_from_moon"] == "dusthana"
    assert tri_dusthana["class_from_sun"] == "kendra"
    assert tri_dusthana["agreement"] == "partial_2frame"
    assert tri_dusthana["matching_class"] == "dusthana"

    row_kendra = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="VEN", tri_frame=tri_kendra,
        fact_ids={"graha": "f1", "lagna": "f2", "moon": "f3", "sun": "f4"},
        now="2026-07-15T00:00:00+00:00",
    )
    row_dusthana_maraka_kendra = build_signal_row(
        chart_id="c", ayanamsha_id="lahiri_chitrapaksha", build_id="b",
        graha_code="MAR", tri_frame=tri_dusthana,
        fact_ids={"graha": "f1", "lagna": "f2", "moon": "f3", "sun": "f4"},
        now="2026-07-15T00:00:00+00:00",
    )
    assert row_kendra["valence"] == "benefic"
    assert row_dusthana_maraka_kendra["valence"] != row_kendra["valence"]


def test_all_9_grahas_covered():
    assert len(GRAHAS) == 9
    assert set(GRAHAS) == {"SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN"}


# ── L0 class_priors seed: sudarshana_agreement row (append-only, DIS.016) ──

def test_l0_class_priors_has_sudarshana_agreement_row():
    from brahmagyan.l0_class_priors import CLASS_ROWS

    matches = [r for r in CLASS_ROWS if r[0] == "sudarshana_agreement"]
    assert len(matches) == 1, "exactly one sudarshana_agreement row expected (append-only)"
    _, prior, _ = matches[0]
    assert prior == 1.15  # DIS.016/DR-3 ratified value


def test_bo_sudarshana_writer_is_registered():
    from pipeline.orchestrator.writers.bo_sudarshana import BoSudarshanaWriter
    from pipeline.orchestrator.writers import get_writer

    assert BoSudarshanaWriter.asset_id == "bo_sudarshana"
    assert get_writer("bo_sudarshana") is BoSudarshanaWriter
