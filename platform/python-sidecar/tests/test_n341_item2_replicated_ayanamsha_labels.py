"""
test_n341_item2_replicated_ayanamsha_labels.py -- SS N-341 item 2 / finding F15 (CLAUDE.md section N.8),
SS rulings N-389 (label only, keep the original tier) and N-389b (sade_sati depends on the Moon sign).

The false green: `ga_panchanga` computes `panchanga_instant` ONCE (Lahiri-only; the engine pins the Lahiri
sidereal mode and takes no ayanamsha argument) and stores the dependent categories under all five
ayanamsha ids; `ga_sade_sati` scans Saturn's transits ONCE with the Lahiri mode and applies them to each
ayanamsha's own natal Moon sign. A cross-ayanamsha reader counting "n of 5 agree" over those rows would
read one computation copied as independent agreement.

The honest option (rows are still emitted for every id), tiers NEVER change (no row uses
`computed_extension`):
  * ga_panchanga: the values are identical under every ayanamsha, so a non-Lahiri replica keeps the
    tier of the Lahiri row and only `source_calculation` says "copied from the lahiri computation; not an
    independent check".
  * ga_sade_sati (SS N-410, withdrawing the N-389b Moon-sign comparison): every non-Lahiri id keeps ALL its rows
    (they are computed with that id's OWN natal Moon sign; on production surya_siddhanta_classical is Pisces, the
    other four Aquarius) and `source_calculation` says the Saturn ingress dates are in the Lahiri frame. No validity
    claim, no deletion, no marker.

This file drives the REAL row builders (build_ga_panchanga with its DB edges stubbed, the same way
test_q03_tiers_panchanga_structural.py does; build_ga_sade_sati with its reads / scans / insert stubbed on
fixture data only; _emit_cycle_rows and _emit_dhaiya_rows). Every labelling assertion goes through a
detector helper that a mutant (label removed / comparison removed) makes fail.
"""
from __future__ import annotations

import os
import pathlib
import sys
from datetime import datetime, timezone

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))
sys.path.insert(0, os.path.dirname(__file__))

from brahmagyan import verification_tiers as T
from ga_writers.gates import FORBIDDEN_PATTERNS
import ga_writers.ga_panchanga_writer as P
import ga_writers.ga_sade_sati_writer as S
from test_ga4_writer import _make_forensic_pi

REF = "lahiri_chitrapaksha"
OTHERS = ["true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
ALL_FIVE = [REF] + OTHERS

PAN_PHRASE = "copied from the lahiri computation; not an independent check"
SADE_PHRASE = ("Saturn ingress dates in the Lahiri frame (not recomputed in this ayanamsha's frame; "
               "Raman/Surya Siddhanta ingresses differ by days); Moon sign is this ayanamsha's own")


def _no_computed_extension(rows: list[dict]) -> None:
    bad = [(r["ayanamsha_id"], r["fact_category"], r["fact_key"]) for r in rows
           if r["verification_pass_status"] == T.COMPUTED_EXTENSION]
    assert not bad, f"no row may use computed_extension (SS N-389): {bad[:3]}"


# ── ga_panchanga ──────────────────────────────────────────────────────────────

# Categories built from the single Lahiri `pi` (replicated under the other four ids).
PAN_REPLICATED = {
    "panchanga_nakshatra_moon",
    "panchanga_special_yoga_combinations",
    "panchanga_panchaka_classification",
    "panchaka_flag",
    "eclipse_proximity_natal",
    "bhadra_flag",
    "tara_bala_natal_baseline",
}
# Read from that ayanamsha's OWN ga_positions Moon-sign fact: genuinely per-ayanamsha, never labelled.
PAN_PER_AYANAMSHA = {"chandra_bala_natal_baseline"}


@pytest.fixture()
def panchanga_rows(monkeypatch) -> list[dict]:
    captured: list[dict] = []
    import panchang_engine

    monkeypatch.setattr(panchang_engine, "panchanga_instant", lambda *a, **k: _make_forensic_pi())
    monkeypatch.setattr(P, "_insert_chart_facts_rows", lambda conn, rows: captured.extend(rows) or len(rows))
    monkeypatch.setattr(P, "_read_birth_moon_signs",
                        lambda conn, chart_id: {ay: "Aquarius" for ay in P.CANONICAL_AYANAMSHAS})
    bp = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.27, "longitude_deg": 85.84,
          "tz_offset_hours": 5.5}
    summary = P.build_ga_panchanga("chart-n341-not-canonical", "build-n341", conn=object(), birth_params=bp)
    assert summary["status"] == "PASS"
    return captured


def _pan_key(r: dict) -> tuple:
    return (r["fact_category"], r["fact_subject"], r["fact_key"])


def _assert_pan_replica_labelled(rows: list[dict]) -> None:
    """Detector: every row passed in carries the exact replica phrase and keeps the engine string."""
    assert rows, "detector needs rows to examine"
    for r in rows:
        where = (r["ayanamsha_id"], r["fact_category"], r["fact_key"])
        assert PAN_PHRASE in r["source_calculation"], where
        assert r["source_calculation"].startswith(P.ENGINE_STRING), where


def test_panchanga_all_five_ids_still_emit_every_replicated_category(panchanga_rows):
    by = {(r["ayanamsha_id"], r["fact_category"]) for r in panchanga_rows}
    for ay in ALL_FIVE:
        for cat in PAN_REPLICATED | PAN_PER_AYANAMSHA:
            assert (ay, cat) in by, f"rows for {cat} under {ay} must still be emitted"


def test_panchanga_lahiri_rows_are_unchanged(panchanga_rows):
    lahiri = [r for r in panchanga_rows if r["ayanamsha_id"] == REF]
    assert {r["fact_category"] for r in lahiri} == PAN_REPLICATED | PAN_PER_AYANAMSHA
    for r in lahiri:
        assert r["verification_pass_status"] == T.SINGLE, (r["fact_category"], r["fact_key"])
        assert r["source_calculation"] == P.ENGINE_STRING, (r["fact_category"], r["fact_key"])


def test_panchanga_replicas_carry_the_phrase_and_keep_the_lahiri_tier(panchanga_rows):
    lahiri_tier = {_pan_key(r): r["verification_pass_status"]
                   for r in panchanga_rows if r["ayanamsha_id"] == REF and r["fact_category"] in PAN_REPLICATED}
    for ay in OTHERS:
        rep = [r for r in panchanga_rows if r["ayanamsha_id"] == ay and r["fact_category"] in PAN_REPLICATED]
        assert {r["fact_category"] for r in rep} == PAN_REPLICATED, ay
        _assert_pan_replica_labelled(rep)
        for r in rep:  # (b) SAME tier the Lahiri row has for the same category/subject/key
            assert r["verification_pass_status"] == lahiri_tier[_pan_key(r)], (ay, _pan_key(r))


def test_panchanga_per_ayanamsha_and_invariant_rows_are_not_labelled(panchanga_rows):
    for r in panchanga_rows:
        if r["fact_category"] in PAN_PER_AYANAMSHA or r["ayanamsha_id"] == "INVARIANT":
            assert r["source_calculation"] == P.ENGINE_STRING, (r["ayanamsha_id"], r["fact_category"])
            assert PAN_PHRASE not in r["source_calculation"]


def test_panchanga_labelling_changes_no_value_no_tier_and_no_identity(panchanga_rows):
    def shape(r):
        return (r["fact_category"], r["fact_subject"], r["fact_key"], r["fact_value_text"],
                r["fact_value_num"], r["fact_value_jsonb"], r["unit"], r["verification_pass_status"])

    ref = sorted(shape(r) for r in panchanga_rows if r["ayanamsha_id"] == REF and r["fact_category"] in PAN_REPLICATED)
    for ay in OTHERS:
        got = sorted(shape(r) for r in panchanga_rows if r["ayanamsha_id"] == ay and r["fact_category"] in PAN_REPLICATED)
        assert got == ref, ay
    ids = [r["fact_id"] for r in panchanga_rows]
    assert len(ids) == len(set(ids)), "fact_id identity must not collide"


def test_panchanga_every_row_is_single_and_no_row_uses_computed_extension(panchanga_rows):
    assert {r["verification_pass_status"] for r in panchanga_rows} == {T.SINGLE}
    _no_computed_extension(panchanga_rows)
    for r in panchanga_rows:
        T.emit_tier(r["verification_pass_status"], table="chart_facts")


def test_panchanga_label_removed_is_caught(panchanga_rows, monkeypatch):
    """MUTANT: the labelling helper becomes the identity. The detector must fail on the rows."""
    rows = [r for r in panchanga_rows if r["ayanamsha_id"] == "raman" and r["fact_category"] in PAN_REPLICATED]
    _assert_pan_replica_labelled(rows)  # the real build is labelled

    unlabelled = [dict(r, source_calculation=P.ENGINE_STRING) for r in rows]
    with pytest.raises(AssertionError):
        _assert_pan_replica_labelled(unlabelled)

    monkeypatch.setattr(P, "_mark_replicated_rows", lambda rows, ayanamsha_id: rows)
    mutant_rows = P._mark_replicated_rows(P._emit_nakshatra_moon(_make_forensic_pi(), "c", "b", "t", "raman"), "raman")
    with pytest.raises(AssertionError):
        _assert_pan_replica_labelled(mutant_rows)


def test_panchanga_reference_constants():
    assert P.REFERENCE_AYANAMSHA == REF == P.CANONICAL_AYANAMSHAS[0]
    assert P.REPLICATED_SOURCE_NOTE == PAN_PHRASE


# ── ga_sade_sati ──────────────────────────────────────────────────────────────

CHART = S.CANONICAL_CHART_ID
BUILD = "n341-build"
AT = "2026-10-10T00:00:00+00:00"


def _dt(y, m=1, d=1):
    return datetime(y, m, d, tzinfo=timezone.utc)


# One full Sade Sati for an Aquarius Moon, plus a 4H (Taurus) and an 8H (Virgo) window for the dhaiya rows.
_SIGN_CHANGES = [
    {"date_utc": _dt(2009, 9, 9), "sign_from": "Leo", "sign_to": "Virgo"},
    {"date_utc": _dt(2011, 11, 15), "sign_from": "Virgo", "sign_to": "Libra"},
    {"date_utc": _dt(2017, 10, 26), "sign_from": "Sagittarius", "sign_to": "Capricorn"},
    {"date_utc": _dt(2020, 1, 23), "sign_from": "Capricorn", "sign_to": "Aquarius"},
    {"date_utc": _dt(2022, 4, 28), "sign_from": "Aquarius", "sign_to": "Pisces"},
    {"date_utc": _dt(2025, 3, 29), "sign_from": "Pisces", "sign_to": "Aries"},
    {"date_utc": _dt(2028, 6, 1), "sign_from": "Aries", "sign_to": "Taurus"},
    {"date_utc": _dt(2030, 6, 1), "sign_from": "Taurus", "sign_to": "Gemini"},
]
_RETROS = [{"start_utc": _dt(2021, 6, 5), "end_utc": _dt(2021, 10, 23)}]
_NATAL = {
    "moon_pada": 4, "saturn_yoga_karaka": False, "natal_saturn_aspects_natal_moon": False,
    "saturn_moon_parivartana": False, "moon_sign_lord_strong": False,
    "jupiter_aspects_saturn_during_cycle": False, "d10_karya_bhava_activation_flag": False,
    "d10_karya_activation_facts": [], "argala_during_period": [],
    "tara_bala_at_janma_peak": "PENDING_GA4_LOOKUP", "mars_aspect_during_period": False,
    "jupiter_aspect_during_period": False, "saturn_rahu_axis_flag": False,
    "eclipse_during_period": False, "concurrent_saturn_return": False,
    "saturn_vargottama_natal": False,
    "concurrent_vimshottari_maha_lord_at_cycle_start": "Venus",
}


def _sade_rows(ay: str, sign: str = "Aquarius") -> list[dict]:
    cycles = S.build_sade_sati_cycles(sign, _SIGN_CHANGES)
    rows = []
    for c in cycles:
        rows += S._emit_cycle_rows(CHART, ay, BUILD, c, _RETROS, dict(_NATAL), AT)
    rows += S._emit_dhaiya_rows(CHART, ay, BUILD, sign, _SIGN_CHANGES, AT)
    return rows


def _is_natal_read(r: dict) -> bool:
    return (r["fact_category"], r["fact_key"]) in S.PER_AYANAMSHA_NATAL_READS


def _skey(r: dict) -> tuple:
    return (r["fact_category"], r["fact_subject"], r["fact_key"])


def _assert_sade_labelled(rows: list[dict]) -> None:
    """Detector: every Lahiri-frame (non natal-read) row passed in carries the exact Lahiri-frame phrase."""
    assert rows, "detector needs rows to examine"
    for r in rows:
        where = (r["ayanamsha_id"], r["fact_category"], r["fact_key"])
        assert SADE_PHRASE in r["source_calculation"], where
        assert r["source_calculation"].startswith(f"ga_sade_sati_writer/{S.ENGINE_VERSION}"), where


# -- row-builder level (same Moon sign: what a non-Lahiri id emits) --

@pytest.mark.parametrize("ay", ALL_FIVE)
def test_sade_sati_rows_are_emitted_for_every_id(ay):
    cats = {r["fact_category"] for r in _sade_rows(ay)}
    assert {"sade_sati_cycle", "sade_sati_phase", "sade_sati_phase_quarter", "dhaiya_period",
            "kantaka_shani_period", "ashtama_shani_period", "sade_sati_saturn_retrograde_subset",
            "sade_sati_concurrent_dasha_overlay"} <= cats


def test_sade_sati_lahiri_rows_are_unchanged():
    rows = _sade_rows(REF)
    assert len(rows) > 100
    for r in rows:
        assert r["source_calculation"] == f"ga_sade_sati_writer/{S.ENGINE_VERSION}", (r["fact_category"], r["fact_key"])
        assert r["verification_pass_status"] in {T.SINGLE, T.DOCUMENTED_APPROXIMATION}, (r["fact_category"], r["fact_key"])


@pytest.mark.parametrize("ay", OTHERS)
def test_sade_sati_copied_rows_carry_the_phrase_and_keep_the_lahiri_tier(ay):
    lahiri = {_skey(r): r["verification_pass_status"] for r in _sade_rows(REF)}
    rows = _sade_rows(ay)
    labelled = [r for r in rows if not _is_natal_read(r)]
    assert len(labelled) > 100
    _assert_sade_labelled(labelled)
    for r in rows:  # tier identical to the Lahiri row for the same category/subject/key
        assert r["verification_pass_status"] == lahiri[_skey(r)], (ay, _skey(r))
    _no_computed_extension(rows)


@pytest.mark.parametrize("ay", OTHERS)
def test_sade_sati_pure_natal_reads_are_not_labelled(ay):
    rows = [r for r in _sade_rows(ay) if _is_natal_read(r)]
    assert {(r["fact_category"], r["fact_key"]) for r in rows} == set(S.PER_AYANAMSHA_NATAL_READS)
    for r in rows:
        assert r["source_calculation"] == f"ga_sade_sati_writer/{S.ENGINE_VERSION}", (r["fact_category"], r["fact_key"])


@pytest.mark.parametrize("ay", OTHERS)
def test_sade_sati_labelling_changes_no_value(ay):
    def shape(r):
        return (r["fact_category"], r["fact_subject"], r["fact_key"], r["fact_value_text"],
                r["fact_value_num"], r["fact_value_jsonb"], r["unit"], r["verification_pass_status"])

    assert sorted(shape(r) for r in _sade_rows(ay)) == sorted(shape(r) for r in _sade_rows(REF))


def test_sade_sati_documented_approximation_tier_is_preserved():
    rows = [r for r in _sade_rows("raman") if r["fact_category"] == "sade_sati_phase_quarter"
            and r["fact_key"] in {"quarter_start_iso", "quarter_end_iso", "duration_days"}]
    assert rows and {r["verification_pass_status"] for r in rows} == {T.DOCUMENTED_APPROXIMATION}


# -- build level: same-sign case (1) and boundary case (2) --

@pytest.fixture()
def run_build(monkeypatch):
    """Drive the REAL build_ga_sade_sati loop on fixture data only (no database, no ephemeris)."""
    def _run(moon_signs: dict[str, str]):
        inserted: list[list[dict]] = []
        cleared: list[list[dict]] = []
        monkeypatch.setattr(S, "_verify_upstream_rows", lambda conn, chart_id: {"ga_positions": True})
        monkeypatch.setattr(S, "_read_moon_sign_per_ayanamsha", lambda conn, chart_id: dict(moon_signs))
        monkeypatch.setattr(S, "_read_moon_pada_per_ayanamsha", lambda conn, chart_id: {a: 4 for a in moon_signs})
        monkeypatch.setattr(S, "_detect_saturn_sign_changes", lambda ws, we: list(_SIGN_CHANGES))
        monkeypatch.setattr(S, "_detect_saturn_retrogrades", lambda ws, we: list(_RETROS))
        monkeypatch.setattr(S, "_build_static_natal_facts",
                            lambda conn, chart_id, ay, moon_sign, moon_pada: dict(_NATAL, lagna_sign="Aries"))
        monkeypatch.setattr(S, "_lookup_dasha_lord_at", lambda *a, **k: "Venus")
        monkeypatch.setattr(S, "_lookup_tara_bala_for_saturn_at", lambda *a, **k: None)
        monkeypatch.setattr(S, "_lookup_argala_for_sign", lambda *a, **k: [])
        monkeypatch.setattr(S, "_insert_rows", lambda conn, rows: inserted.append(list(rows)) or len(rows))
        monkeypatch.setattr(S, "replace_prior_chart_facts", lambda conn, rows: cleared.append(list(rows)) or 0)
        monkeypatch.setattr(S, "_refresh_mv", lambda conn: "SKIP")
        summary = S.build_ga_sade_sati(CHART, BUILD, conn=object(), birth_params=None)
        by_ay: dict[str, list[dict]] = {}
        for batch in inserted:
            for r in batch:
                by_ay.setdefault(r["ayanamsha_id"], []).append(r)
        return summary, by_ay, cleared
    return _run


def _expected_keys(sign: str) -> set:
    return {_skey(r) for r in _sade_rows(REF, sign)}


def _assert_every_row_kept_and_labelled(by_ay: dict[str, list[dict]], signs: dict[str, str]) -> None:
    """Detector (SS N-410): each id emitted exactly the rows computed with ITS OWN Moon sign (nothing deleted, nothing
    replaced by a marker); non-Lahiri rows built from the Lahiri-frame Saturn scan say so; Lahiri rows are unlabelled;
    tiers equal those of the same rows built directly."""
    assert set(by_ay) == set(signs)
    for ay, rows in by_ay.items():
        assert {_skey(r) for r in rows} == _expected_keys(signs[ay]), ay
        assert not any(r["fact_subject"] == "NOT_COMPUTED" for r in rows), ay
        direct = {_skey(r): r["verification_pass_status"] for r in _sade_rows(REF, signs[ay])}
        for r in rows:
            assert r["verification_pass_status"] == direct[_skey(r)], (ay, _skey(r))
        if ay == REF:
            assert all(r["source_calculation"] == f"ga_sade_sati_writer/{S.ENGINE_VERSION}" for r in rows)
        else:
            _assert_sade_labelled([r for r in rows if not _is_natal_read(r)])
            assert all(r["source_calculation"] == f"ga_sade_sati_writer/{S.ENGINE_VERSION}" for r in rows if _is_natal_read(r))
        _no_computed_extension(rows)


def test_sade_sati_all_five_share_one_moon_sign(run_build):
    signs = {ay: "Aquarius" for ay in ALL_FIVE}
    summary, by_ay, cleared = run_build(signs)
    _assert_every_row_kept_and_labelled(by_ay, signs)
    assert not cleared, "nothing is ever cleared: no id is dropped"
    assert summary["total_chart_facts_rows"] == sum(len(v) for v in by_ay.values())


def test_sade_sati_production_shape_surya_siddhanta_is_pisces_and_keeps_its_own_rows(run_build):
    """Kāla's finding on #3400: on production the surya_siddhanta_classical natal Moon is in PISCES, the other four in Aquarius.
    Its rows were computed with ITS sign, so they are kept (and differ from the Aquarius set), labelled as Lahiri-frame."""
    signs = {ay: "Aquarius" for ay in ALL_FIVE}
    signs["surya_siddhanta_classical"] = "Pisces"
    summary, by_ay, cleared = run_build(signs)
    _assert_every_row_kept_and_labelled(by_ay, signs)
    assert _expected_keys("Pisces") != _expected_keys("Aquarius"), "the fixture would prove nothing if both signs gave the same rows"
    assert len(by_ay["surya_siddhanta_classical"]) > 50
    assert not cleared and summary["total_chart_facts_rows"] == sum(len(v) for v in by_ay.values())


def test_sade_sati_a_missing_lahiri_moon_sign_still_emits_the_other_ids_labelled(run_build):
    signs = {ay: "Aquarius" for ay in OTHERS}
    _, by_ay, _ = run_build(signs)
    assert REF not in by_ay
    _assert_every_row_kept_and_labelled(by_ay, signs)


def test_sade_sati_the_withdrawn_marker_branch_stays_withdrawn():
    """SS N-410 withdrew the Moon-sign comparison / not_computed marker / clearing: no trace of it may return."""
    for name in ("NOT_COMPUTED_CATEGORY", "NOT_COMPUTED_SUBJECT", "NOT_COMPUTED_KEY", "NOT_COMPUTED_TIER", "OWNED_CATEGORIES",
                 "COPIED_SAME_MOON_SIGN_NOTE", "_not_computed_marker_row"):
        assert not hasattr(S, name), name


# -- mutation detection: the detectors fail when the label is gone or a row set is dropped / replaced --

def test_sade_sati_detectors_catch_a_removed_label_a_dropped_id_and_a_replaced_row_set(run_build):
    signs = {ay: "Aquarius" for ay in ALL_FIVE}
    signs["surya_siddhanta_classical"] = "Pisces"
    _, by_ay, _ = run_build(signs)
    _assert_every_row_kept_and_labelled(by_ay, signs)                       # the real build satisfies it

    unlabelled = {ay: [dict(r, source_calculation=f"ga_sade_sati_writer/{S.ENGINE_VERSION}") for r in rows] for ay, rows in by_ay.items()}
    with pytest.raises(AssertionError):
        _assert_every_row_kept_and_labelled(unlabelled, signs)
    dropped = {ay: rows for ay, rows in by_ay.items() if ay != "surya_siddhanta_classical"}
    with pytest.raises(AssertionError):
        _assert_every_row_kept_and_labelled(dropped, {a: s_ for a, s_ in signs.items() if a in dropped} | {"surya_siddhanta_classical": "Pisces"})
    replaced = dict(by_ay)
    replaced["surya_siddhanta_classical"] = _sade_rows("surya_siddhanta_classical", "Aquarius")      # the Aquarius periods copied onto a Pisces Moon
    with pytest.raises(AssertionError):
        _assert_every_row_kept_and_labelled(replaced, signs)


def test_sade_sati_constants():
    assert S.REFERENCE_AYANAMSHA == REF == S.CANONICAL_AYANAMSHAS[0]
    assert S.LAHIRI_FRAME_SATURN_NOTE == SADE_PHRASE
