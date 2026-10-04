"""ga_sensitive orchestrator-path SHAPE guard (TI-l1-hora-lagna-001).

Why this file exists
--------------------
A rebuild rehearsal logged, on every ayanamsha of the orchestrator path::

    [EXTERNAL_COMPUTATION_REQUIRED] Hora Lagna requires sunrise_jd + birth_jd ...
    Trisphuta/Chatushphuta/Panchasphuta rows SKIPPED

and raised the fear that the S-L1 rebuild would DROP stored ``HORA_LAGNA`` rows (the
wealth reading leg ``fetchWealthSpecialLagnas`` needs INDU/SREE/HORA_LAGNA x 7 atoms).
Investigation result (see the lane report): that warning is emitted by
``_build_trisphuta_family_rows``, which feeds ONLY the three ``esoteric_point_trisphuta`` /
``chatushphuta`` / ``panchasphuta`` categories. Those categories are not stored for any chart
(migration 874 documents the honest B.10 gap: "34 of 37 present"), and no call path -- legacy
``build_ga_sensitive`` or the orchestrator adapter -- has supplied ``sunrise_jd``/``birth_jd``
since Wave 3 (88f10a80d, 2026-06-29). ``special_lagna`` (incl. ``HORA_LAGNA``) is a different
builder (``_build_special_lagnas_rows``) that delegates to PyJHora through the adapter, which
computes sunrise itself; it needs neither argument.

These tests pin that conclusion so the rebuild cannot silently lose stored rows:

* the exact function the orchestrator adapter calls (``build_ga_sensitive_for_ayanamsha``)
  is driven on a SYNTHETIC chart with the real PyJHora adapter and real Swiss ephemeris;
  only the DB insert is captured;
* every stored ga_sensitive category is still emitted, at >= its stored per-ayanamsha row
  count (the stored shape numbers below are counts read from the canonical chart's stored
  ``chart_facts`` -- no birth data, no values);
* the wealth leg's INDU/SREE/HORA_LAGNA x 7-atom contract (parsed from reading_checklist.ts
  so it cannot drift from the reader) is met, with a value in the right column and a tier the
  leg serves.

No tier is pinned (the tier of these rows is owned by the S-L1 tier-honesty lane).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

SYNTHETIC_CHART_ID = "aaaaaaaa-1111-4222-8333-000000000002"
# Anchor-matched synthetic birth (Sun Capricorn). NOT the native's data.
SYNTHETIC_BIRTH = {
    "datetime_iso": "2011-02-06T11:00:00",
    "latitude_deg": 23.26,
    "longitude_deg": 77.41,
    "tz_offset_hours": 5.5,
    "place_name": "synthetic",
    "subject_label": "syn",
}

# category -> (rows per ayanamsha, distinct subjects, distinct keys), read from the stored
# canonical chart_facts (counts only). sensitive_point_gulika_mandi: the current writer emits
# a superset (one extra subject); everything else is exactly equal today.
STORED_SHAPE: dict[str, tuple[int, int, int]] = {
    "aprakasha_position": (35, 5, 7),
    "arudha_pada": (57, 19, 3),
    "bhava_arudha": (42, 14, 3),
    "bhrigu_nadi_point": (56, 8, 7),
    "esoteric_point_avayogi": (14, 1, 7),
    "esoteric_point_bhrigu_bindu": (7, 1, 7),
    "esoteric_point_brahma": (16, 1, 8),
    "esoteric_point_mrityu": (21, 1, 7),
    "esoteric_point_pranapada_sphuta": (7, 1, 7),
    "esoteric_point_shiva": (14, 1, 7),
    "esoteric_point_sphuta_fertility": (14, 2, 7),
    "esoteric_point_sri_yantra_position": (3, 3, 1),
    "esoteric_point_trikona_dasha_sphuta": (1, 1, 1),
    "esoteric_point_vishnu": (14, 1, 7),
    "esoteric_point_yogi": (14, 1, 7),
    "esoteric_point_yogi_system": (5, 3, 4),
    "karaka_chara_position": (105, 8, 7),
    "karakamsa_position": (3, 1, 3),
    "kp_cuspal_significators": (60, 12, 5),
    "kp_ruling_planets_natal": (10, 5, 2),
    "lal_kitab_special_point": (20, 10, 2),
    "maharsi_specific_point": (14, 7, 2),
    "midpoint": (216, 54, 4),
    "nakshatra_pada_sensitive": (16, 4, 4),
    "saham_position": (560, 70, 8),
    "saturn_derived_point": (29, 5, 7),
    "sensitive_point_gulika_mandi": (14, 2, 7),
    "special_lagna": (49, 7, 7),
    "sun_derived_upagraha": (28, 4, 7),
    "swamsa_position": (24, 12, 2),
    "tajik_hadda_lord": (240, 60, 4),
    "tajik_triraashipathi": (2, 1, 2),
    "tajik_vargottama_specific": (3, 1, 3),
    "upagraha_position": (42, 6, 7),
}

STORED_SPECIAL_LAGNA_SUBJECTS = {
    "BHAVA_LAGNA", "GHATI_LAGNA", "HORA_LAGNA", "INDU_LAGNA",
    "SREE_LAGNA", "VARNADA_LAGNA", "VIGHATI_LAGNA",
}
STORED_SPECIAL_LAGNA_KEYS = {
    "house_d1", "longitude_sidereal", "nakshatra", "nakshatra_lord", "pada", "sign", "sign_lord",
}
# Declared in the registry partition (migration 874) but never emitted: honest B.10 gap.
KNOWN_ABSENT_CATEGORIES = {
    "esoteric_point_trisphuta", "esoteric_point_chatushphuta", "esoteric_point_panchasphuta",
}

_REPO_ROOT = Path(__file__).resolve().parents[3]
_READING_CHECKLIST = (
    _REPO_ROOT / "platform/src/lib/retrieval/registry/layers/reading_checklist.ts"
)


def _ts_string_list(src: str, const_name: str) -> list[str]:
    m = re.search(rf"export const {const_name}\s*=\s*\[(.*?)\]\s*as const", src, re.S)
    assert m, f"{const_name} not found in reading_checklist.ts"
    return re.findall(r"'([^']+)'", m.group(1))


def _ts_servable_tiers(src: str) -> set[str]:
    m = re.search(
        r"export const WEALTH_LEG_SERVABLE_TIERS[^=]*=\s*new Set<VerificationPassStatus>\(\[(.*?)\]\)",
        src, re.S,
    )
    assert m, "WEALTH_LEG_SERVABLE_TIERS not found in reading_checklist.ts"
    body = re.sub(r"//[^\n]*", "", m.group(1))
    return set(re.findall(r"'([^']+)'", body))


@pytest.fixture(scope="module")
def rows_by_ayanamsha() -> dict[str, list[dict[str, Any]]]:
    """Run the adapter's own entry point per ayanamsha, capturing what it would insert."""
    from ga_writers import ga_sensitive_writer as w

    captured: list[dict[str, Any]] = []
    mp = pytest.MonkeyPatch()
    mp.setattr(
        w, "_insert_rows",
        lambda conn, rows, *, commit=True: captured.extend(rows) or len(rows),
    )
    out: dict[str, list[dict[str, Any]]] = {}
    try:
        prereqs, eng_ver = w.get_ga_sensitive_context(SYNTHETIC_BIRTH, conn=None)
        for aya_key, aya_id in w.CANONICAL_AYANAMSHAS.items():
            captured.clear()
            n = w.build_ga_sensitive_for_ayanamsha(
                ayanamsha_key=aya_key, ayanamsha_id=aya_id,
                chart_id=SYNTHETIC_CHART_ID, build_id="bbbbbbbb-0000-4000-8000-000000000001",
                conn=None, birth_params=SYNTHETIC_BIRTH, prereqs=prereqs, eng_ver=eng_ver,
            )
            assert n == len(captured) > 0
            out[aya_key] = list(captured)
    finally:
        mp.undo()
    return out


def _by_category(rows: list[dict[str, Any]], category: str) -> list[dict[str, Any]]:
    return [r for r in rows if r["fact_category"] == category]


def test_all_five_ayanamshas_built(rows_by_ayanamsha):
    assert len(rows_by_ayanamsha) == 5


def test_every_stored_category_is_still_emitted_without_row_loss(rows_by_ayanamsha):
    """The rebuild must not ship a loss of stored rows (SS rule), category by category."""
    for aya, rows in rows_by_ayanamsha.items():
        emitted_categories = {r["fact_category"] for r in rows}
        assert set(STORED_SHAPE) <= emitted_categories, (
            f"{aya}: stored categories no longer emitted: {sorted(set(STORED_SHAPE) - emitted_categories)}"
        )
        for cat, (n_rows, n_subjects, n_keys) in STORED_SHAPE.items():
            cat_rows = _by_category(rows, cat)
            assert len(cat_rows) >= n_rows, f"{aya}/{cat}: {len(cat_rows)} < stored {n_rows}"
            assert len({r["fact_subject"] for r in cat_rows}) >= n_subjects, f"{aya}/{cat}: subjects lost"
            assert len({r["fact_key"] for r in cat_rows}) >= n_keys, f"{aya}/{cat}: keys lost"


def test_trisphuta_family_is_the_documented_absent_gap_not_a_loss(rows_by_ayanamsha):
    """The EXTERNAL_COMPUTATION_REQUIRED warning concerns exactly these categories, which are
    not stored for any chart (migration 874). If a later change starts emitting them, the
    Trisphuta formula must be re-verified first: the dormant builder derives Hora Lagna as
    Lagna + 12 deg/hr x elapsed (not the classical Sun-at-sunrise + 30 deg/hr), and its
    Panchasphuta uses Saturn. Update STORED_SHAPE + this test deliberately in that change."""
    for aya, rows in rows_by_ayanamsha.items():
        assert KNOWN_ABSENT_CATEGORIES.isdisjoint({r["fact_category"] for r in rows}), aya


def test_special_lagna_exact_stored_shape(rows_by_ayanamsha):
    for aya, rows in rows_by_ayanamsha.items():
        sl = _by_category(rows, "special_lagna")
        assert len(sl) == 49, aya
        pairs = {(r["fact_subject"], r["fact_key"]) for r in sl}
        assert len(pairs) == 49, f"{aya}: duplicate (subject,key) atoms"
        assert {s for s, _ in pairs} == STORED_SPECIAL_LAGNA_SUBJECTS, aya
        for subj in STORED_SPECIAL_LAGNA_SUBJECTS:
            assert {k for s, k in pairs if s == subj} == STORED_SPECIAL_LAGNA_KEYS, (aya, subj)


def test_special_lagna_none_floored_all_values_present(rows_by_ayanamsha):
    numeric_keys = {"longitude_sidereal", "pada", "house_d1"}
    for aya, rows in rows_by_ayanamsha.items():
        for r in _by_category(rows, "special_lagna"):
            assert r["verification_pass_status"] != "floored", (aya, r["fact_subject"])
            if r["fact_key"] in numeric_keys:
                assert r["fact_value_num"] is not None, (aya, r["fact_subject"], r["fact_key"])
            else:
                assert r["fact_value_text"], (aya, r["fact_subject"], r["fact_key"])
            if r["fact_key"] == "longitude_sidereal":
                assert 0.0 <= r["fact_value_num"] < 360.0


def test_wealth_leg_expected_atoms_are_emitted_and_servable(rows_by_ayanamsha):
    """Bind the writer to fetchWealthSpecialLagnas: INDU/SREE/HORA x 7 keys, exactly one atom
    each, right value column, and a tier the leg serves (tier value itself is not pinned)."""
    src = _READING_CHECKLIST.read_text(encoding="utf-8")
    lagnas = _ts_string_list(src, "WEALTH_SPECIAL_LAGNAS")
    keys = _ts_string_list(src, "WEALTH_SPECIAL_LAGNA_KEYS")
    servable = _ts_servable_tiers(src)
    assert lagnas == ["INDU_LAGNA", "SREE_LAGNA", "HORA_LAGNA"] and len(keys) == 7
    for aya, rows in rows_by_ayanamsha.items():
        sl = _by_category(rows, "special_lagna")
        for lagna in lagnas:
            for key in keys:
                atoms = [r for r in sl if r["fact_subject"] == lagna and r["fact_key"] == key]
                assert len(atoms) == 1, (aya, lagna, key, len(atoms))
                r = atoms[0]
                assert r["verification_pass_status"] in servable, (aya, lagna, key, r["verification_pass_status"])
                col = "fact_value_num" if key in ("longitude_sidereal", "pada", "house_d1") else "fact_value_text"
                assert r[col] is not None, (aya, lagna, key)
