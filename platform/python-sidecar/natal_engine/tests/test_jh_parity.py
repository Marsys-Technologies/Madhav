"""
test_jh_parity.py — Unit 1.2 JH parity harness (G1 hard gate).

Asserts the natal_engine output matches the pinned Jagannatha Hora oracle
(`fixtures/jh_oracle.json`) field-by-field under `ayanamsha_id='jh_true_chitra'`:

HARD parity (test_*_hard):
  - ascendant longitude within `tolerances.longitude_arcseconds` (60") of oracle
  - each of 9 grahas: longitude ≤ 60" delta; nakshatra exact; pada exact
  - vimshottari MD sequence: lords exact, start_iso within `tolerances.dasha_seconds` (1 day)
  - panchanga tithi/vara/nakshatra/yoga/karana exact (with case+whitespace normalization,
    plus the documented karana alias Garija≡Garaja and Sunday→Ravivara)

SOFT/advisory (test_*_soft): emit warnings but do NOT fail:
  - dignity match (oracle uses temporal-friendship dignities, engine's 1.1
    scaffold only computes exaltation/own/debility — the brief calls dignity
    SOFT in the _provenance.soft_fields note)
  - sign-name match (name-normalized)
  - sensitive_points longitudes (not in the anchor set per brief §Scope)

INVARIANTS (test_*_invariant):
  - Constant-offset across the 3 ayanamsha sets: sidereal-longitude differences
    across (A,B) equal ayanamsha(B)-ayanamsha(A) within 1".
  - Vimshottari contiguous + total span ≈ 120 years.
  - Navamsa-lagna consistency: D9 derived from D1 ascendant with valid sign.

DETERMINISM (test_*_determinism):
  - Two compute_chart calls with identical inputs + pinned `computed_at_iso`
    produce byte-identical JSON output.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import pytest

from natal_engine import (
    AYANAMSHA_REGISTRY,
    apply_ayanamsha,
    compute_chart,
    list_ayanamsha_ids,
)
from natal_engine.fixtures.jh_oracle_loader import (
    JH_ORACLE_PATH,
    jh_oracle_present,
    load_jh_oracle,
)

# JH oracle has been pinned (unit 1.1.2). Hard-skip if the fixture vanishes —
# that means the G1 prereq gate has flipped red and the conductor should halt.
pytestmark = pytest.mark.skipif(
    not jh_oracle_present(),
    reason=f"jh_oracle_pinned RED — fixture missing at {JH_ORACLE_PATH}",
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def oracle() -> dict[str, Any]:
    return load_jh_oracle()


@pytest.fixture(scope="module")
def oracle_inputs(oracle: dict[str, Any]) -> dict[str, Any]:
    meta = oracle["meta"]
    return {
        "datetime_iso": meta["datetime_iso"],
        "tz_offset_hours": meta["tz_offset_hours"],
        "latitude_deg": meta["latitude_deg"],
        "longitude_deg": meta["longitude_deg"],
        "place_name": meta["place_name"],
        "subject_label": meta.get("subject_label", ""),
    }


@pytest.fixture(scope="module")
def chart(oracle_inputs: dict[str, Any]) -> dict[str, Any]:
    return compute_chart(
        oracle_inputs,
        ayanamsha_id="jh_true_chitra",
        computed_at_iso="1984-02-05T05:13:00+00:00",
    )


def _arcsec_delta(deg_a: float, deg_b: float) -> float:
    """Smallest-arc absolute delta in arcseconds (handles 360° wrap)."""
    d = abs(deg_a - deg_b) % 360.0
    if d > 180.0:
        d = 360.0 - d
    return d * 3600.0


def _norm_panchanga(s: str) -> str:
    """Case + whitespace tolerant comparison for panchanga strings."""
    return " ".join(s.casefold().strip().split())


def _normalize_karana(s: str) -> str:
    """Garija ≡ Garaja (oracle uses 'Garija', engine emits 'Garaja') — known alias."""
    return _norm_panchanga(s).replace("garija", "garaja")


def _normalize_vara(s: str) -> str:
    """Map English weekday names to Vedic vara names (oracle uses 'Sunday')."""
    s_norm = _norm_panchanga(s)
    return {
        "sunday": "ravivara",
        "monday": "somavara",
        "tuesday": "mangalavara",
        "wednesday": "budhavara",
        "thursday": "guruvara",
        "friday": "shukravara",
        "saturday": "shanivara",
    }.get(s_norm, s_norm)


def _oracle_jd_ut(oracle: dict[str, Any]) -> float:
    """Birth JD(UT) from oracle meta."""
    import swisseph as swe
    meta = oracle["meta"]
    dt = datetime.fromisoformat(meta["datetime_iso"])
    if dt.tzinfo is not None:
        utc = dt.astimezone(tz=None).replace(tzinfo=None) - timedelta(
            hours=meta["tz_offset_hours"]
        )
    else:
        utc = dt - timedelta(hours=meta["tz_offset_hours"])
    return swe.julday(
        utc.year, utc.month, utc.day,
        utc.hour + utc.minute / 60.0 + utc.second / 3600.0,
        swe.GREG_CAL,
    )


# ---------------------------------------------------------------------------
# Phase 0 — ayanamsha gate
# ---------------------------------------------------------------------------

def test_jh_true_chitra_ayanamsha_residual_within_tolerance(oracle: dict[str, Any]) -> None:
    """The engine's jh_true_chitra ayanamsha must reproduce JH's pinned value
    to within the oracle's longitude tolerance (60") at the native birth JD.
    """
    jd_ut = _oracle_jd_ut(oracle)
    engine_ayan = apply_ayanamsha(jd_ut, "jh_true_chitra")
    jh_pinned = oracle["ayanamsha"]["value_deg_at_birth"]
    residual_arcsec = abs(engine_ayan - jh_pinned) * 3600.0
    tol = oracle["tolerances"]["longitude_arcseconds"]
    assert residual_arcsec <= tol, (
        f"jh_true_chitra ayanamsha residual {residual_arcsec:.3f}\" exceeds "
        f"tolerance {tol}\" (engine={engine_ayan:.7f}°, JH={jh_pinned:.7f}°)"
    )


# ---------------------------------------------------------------------------
# HARD parity — ascendant + 9 grahas + nakshatra + pada + retrograde
# ---------------------------------------------------------------------------

def test_ascendant_longitude_within_tolerance_hard(
    chart: dict[str, Any], oracle: dict[str, Any]
) -> None:
    tol = oracle["tolerances"]["longitude_arcseconds"]
    engine_lon = chart["ascendant"]["longitude_deg"]
    oracle_lon = oracle["ascendant"]["longitude_deg"]
    delta = _arcsec_delta(engine_lon, oracle_lon)
    assert delta <= tol, (
        f"Ascendant longitude delta {delta:.3f}\" > tolerance {tol}\" "
        f"(engine={engine_lon:.6f}°, JH={oracle_lon:.6f}°)"
    )


def test_ascendant_nakshatra_pada_match_hard(
    chart: dict[str, Any], oracle: dict[str, Any]
) -> None:
    assert chart["ascendant"]["nakshatra"] == oracle["ascendant"]["nakshatra"], (
        f"Ascendant nakshatra: engine={chart['ascendant']['nakshatra']!r}, "
        f"JH={oracle['ascendant']['nakshatra']!r}"
    )
    assert chart["ascendant"]["pada"] == oracle["ascendant"]["pada"], (
        f"Ascendant pada: engine={chart['ascendant']['pada']}, "
        f"JH={oracle['ascendant']['pada']}"
    )


def test_graha_longitudes_within_tolerance_hard(
    chart: dict[str, Any], oracle: dict[str, Any]
) -> None:
    tol = oracle["tolerances"]["longitude_arcseconds"]
    engine_by_name = {g["name"]: g for g in chart["grahas"]}
    failures: list[str] = []
    for og in oracle["grahas"]:
        eg = engine_by_name[og["name"]]
        delta = _arcsec_delta(eg["longitude_deg"], og["longitude_deg"])
        if delta > tol:
            failures.append(
                f"{og['name']}: delta {delta:.3f}\" > tolerance {tol}\" "
                f"(engine={eg['longitude_deg']:.6f}°, JH={og['longitude_deg']:.6f}°)"
            )
    assert not failures, "Graha longitude parity FAILED:\n  " + "\n  ".join(failures)


def test_graha_nakshatra_pada_match_hard(
    chart: dict[str, Any], oracle: dict[str, Any]
) -> None:
    engine_by_name = {g["name"]: g for g in chart["grahas"]}
    failures: list[str] = []
    for og in oracle["grahas"]:
        eg = engine_by_name[og["name"]]
        if eg["nakshatra"] != og["nakshatra"]:
            failures.append(
                f"{og['name']} nakshatra: engine={eg['nakshatra']!r} JH={og['nakshatra']!r}"
            )
        if eg["pada"] != og["pada"]:
            failures.append(
                f"{og['name']} pada: engine={eg['pada']} JH={og['pada']}"
            )
    assert not failures, "Graha nak/pada parity FAILED:\n  " + "\n  ".join(failures)


def test_graha_retrograde_flag_matches_hard(
    chart: dict[str, Any], oracle: dict[str, Any]
) -> None:
    """Retrograde is ayanamsha-independent (computed via pyswisseph speed)."""
    engine_by_name = {g["name"]: g for g in chart["grahas"]}
    failures: list[str] = []
    for og in oracle["grahas"]:
        eg = engine_by_name[og["name"]]
        if bool(eg["retrograde"]) != bool(og["retrograde"]):
            failures.append(
                f"{og['name']} retrograde: engine={eg['retrograde']} JH={og['retrograde']}"
            )
    assert not failures, "Retrograde parity FAILED:\n  " + "\n  ".join(failures)


# ---------------------------------------------------------------------------
# HARD parity — Vimshottari mahadasha sequence
# ---------------------------------------------------------------------------

def test_vimshottari_sequence_lords_and_starts_hard(
    chart: dict[str, Any], oracle: dict[str, Any]
) -> None:
    tol_sec = oracle["tolerances"]["dasha_seconds"]
    engine_seq = chart["dashas"]["mahadasha_sequence"]
    oracle_seq = oracle["vimshottari"]["sequence"]

    assert len(engine_seq) >= len(oracle_seq), (
        f"Engine emitted {len(engine_seq)} MDs, oracle has {len(oracle_seq)}"
    )

    failures: list[str] = []
    for i, og in enumerate(oracle_seq):
        eg = engine_seq[i]
        if eg["lord"] != og["lord"]:
            failures.append(f"MD[{i}] lord: engine={eg['lord']} JH={og['lord']}")
            continue
        e_start = datetime.fromisoformat(eg["start_iso"])
        o_start = datetime.fromisoformat(og["start_iso"])
        # Normalize: oracle dates are naive midnight; engine carries tz.
        if e_start.tzinfo is not None:
            e_start = e_start.astimezone(tz=None).replace(tzinfo=None)
        if o_start.tzinfo is not None:
            o_start = o_start.replace(tzinfo=None)
        delta_sec = abs((e_start - o_start).total_seconds())
        if delta_sec > tol_sec:
            failures.append(
                f"MD[{i}] {eg['lord']} start delta {delta_sec:.0f}s > tol {tol_sec}s "
                f"(engine={eg['start_iso']}, JH={og['start_iso']})"
            )
    assert not failures, "Vimshottari MD parity FAILED:\n  " + "\n  ".join(failures)


# ---------------------------------------------------------------------------
# HARD parity — panchanga
# ---------------------------------------------------------------------------

def test_panchanga_matches_hard(chart: dict[str, Any], oracle: dict[str, Any]) -> None:
    e = chart["panchanga"]
    o = oracle["panchanga"]
    failures: list[str] = []

    if _norm_panchanga(e["tithi"]) != _norm_panchanga(o["tithi"]):
        failures.append(f"tithi: engine={e['tithi']!r} JH={o['tithi']!r}")
    if _normalize_vara(e["vara"]) != _normalize_vara(o["vara"]):
        failures.append(f"vara: engine={e['vara']!r} JH={o['vara']!r}")
    if _norm_panchanga(e["nakshatra"]) != _norm_panchanga(o["nakshatra"]):
        failures.append(f"nakshatra: engine={e['nakshatra']!r} JH={o['nakshatra']!r}")
    if _norm_panchanga(e["yoga"]) != _norm_panchanga(o["yoga"]):
        failures.append(f"yoga: engine={e['yoga']!r} JH={o['yoga']!r}")
    if _normalize_karana(e["karana"]) != _normalize_karana(o["karana"]):
        failures.append(f"karana: engine={e['karana']!r} JH={o['karana']!r}")

    assert not failures, "Panchanga parity FAILED:\n  " + "\n  ".join(failures)


# ---------------------------------------------------------------------------
# SOFT / advisory
# ---------------------------------------------------------------------------

def test_dignity_match_soft(chart: dict[str, Any], oracle: dict[str, Any]) -> None:
    """Oracle dignity is temporal-friendship rule-derived; engine scaffold
    only does exaltation/own/debility. Mismatches are advisory (brief
    §_provenance.soft_fields)."""
    import warnings
    engine_by_name = {g["name"]: g for g in chart["grahas"]}
    for og in oracle["grahas"]:
        eg = engine_by_name[og["name"]]
        if eg["dignity_status"] != og["dignity"]:
            warnings.warn(
                f"SOFT dignity mismatch {og['name']}: engine={eg['dignity_status']!r} "
                f"JH={og['dignity']!r} (advisory — pancha-dha-maitri pending)",
                stacklevel=1,
            )


def test_sign_name_match_soft(chart: dict[str, Any], oracle: dict[str, Any]) -> None:
    import warnings
    engine_by_name = {g["name"]: g for g in chart["grahas"]}
    for og in oracle["grahas"]:
        eg = engine_by_name[og["name"]]
        if eg["sign"].casefold() != og["sign"].casefold():
            warnings.warn(
                f"SOFT sign mismatch {og['name']}: engine={eg['sign']!r} JH={og['sign']!r}",
                stacklevel=1,
            )


def test_sensitive_points_structurally_present_soft(chart: dict[str, Any]) -> None:
    """Sensitive points (Maandi/Gulika) are NOT in the anchor set per brief §Scope.
    Assert structural presence; longitude check is advisory (still stubbed)."""
    assert "sensitive_points" in chart
    sp = chart["sensitive_points"]
    assert "maandi" in sp or "gulika" in sp


# ---------------------------------------------------------------------------
# INVARIANTS
# ---------------------------------------------------------------------------

def test_constant_offset_across_three_ayanamshas_invariant(
    oracle_inputs: dict[str, Any],
) -> None:
    """For each graha, sidereal-longitude differences across (A,B) ayanamshas
    must equal ayanamsha(B)-ayanamsha(A) within 1\" — i.e. the engine truly
    isolates per-ayanamsha state (cross-contamination tripwire)."""
    ids = list_ayanamsha_ids()
    assert set(ids) >= {"jh_true_chitra", "kp", "lahiri_standard"}, (
        f"Registry missing required ids; got {ids}"
    )

    charts = {
        aid: compute_chart(
            oracle_inputs,
            ayanamsha_id=aid,
            computed_at_iso="1984-02-05T05:13:00+00:00",
        )
        for aid in ("jh_true_chitra", "kp", "lahiri_standard")
    }
    ayans = {aid: charts[aid]["ayanamsha"]["value_deg"] for aid in charts}

    tol_arcsec = 1.0
    pairs = [
        ("jh_true_chitra", "kp"),
        ("jh_true_chitra", "lahiri_standard"),
        ("kp", "lahiri_standard"),
    ]
    failures: list[str] = []
    for a, b in pairs:
        # sidereal = tropical - ayanamsha, so sid(a)-sid(b) = ayan(b)-ayan(a)
        expected_diff_arcsec = (ayans[b] - ayans[a]) * 3600.0
        for ge, gb in zip(charts[a]["grahas"], charts[b]["grahas"]):
            assert ge["name"] == gb["name"]
            actual_diff_arcsec = (ge["longitude_deg"] - gb["longitude_deg"]) * 3600.0
            # wrap-correct
            if actual_diff_arcsec > 180 * 3600:
                actual_diff_arcsec -= 360 * 3600
            elif actual_diff_arcsec < -180 * 3600:
                actual_diff_arcsec += 360 * 3600
            residual = abs(actual_diff_arcsec - expected_diff_arcsec)
            if residual > tol_arcsec:
                failures.append(
                    f"{ge['name']} ({a} vs {b}): diff {actual_diff_arcsec:.3f}\" "
                    f"expected {expected_diff_arcsec:.3f}\" residual {residual:.3f}\" > 1\""
                )
    assert not failures, "Constant-offset invariant FAILED:\n  " + "\n  ".join(failures)


def test_vimshottari_contiguous_and_120_years_invariant(chart: dict[str, Any]) -> None:
    seq = chart["dashas"]["mahadasha_sequence"]
    # Contiguity
    for i in range(len(seq) - 1):
        end_i = datetime.fromisoformat(seq[i]["end_iso"])
        start_next = datetime.fromisoformat(seq[i + 1]["start_iso"])
        gap_sec = abs((end_i - start_next).total_seconds())
        assert gap_sec < 1.0, (
            f"Vimshottari non-contiguous at MD[{i}]→MD[{i+1}]: gap {gap_sec:.3f}s"
        )
    # Total span ≈ 120 years (43830 days at 365.25 d/y)
    total_days = (
        datetime.fromisoformat(seq[-1]["end_iso"])
        - datetime.fromisoformat(seq[0]["start_iso"])
    ).total_seconds() / 86400.0
    expected_days = 120 * 365.25
    assert abs(total_days - expected_days) < 1.0, (
        f"Vimshottari total span {total_days:.3f}d != 120y ({expected_days}d)"
    )


def test_navamsa_lagna_structurally_consistent_invariant(chart: dict[str, Any]) -> None:
    """D9 lagna derivable from D1 ascendant; sign id must be valid (1..12)."""
    from natal_engine.vargas import _d9_sign
    from natal_engine.schema import GrahaState

    asc = chart["ascendant"]
    fake = GrahaState(
        name="Lagna",
        longitude_deg=asc["longitude_deg"],
        sign=asc["sign"], sign_id=asc["sign_id"],
        nakshatra=asc["nakshatra"], nakshatra_id=asc["nakshatra_id"], pada=asc["pada"],
        retrograde=False, speed_deg_per_day=0.0, dignity_status="unknown",
    )
    d9_id, d9_name = _d9_sign(fake)
    assert 1 <= d9_id <= 12, f"D9 lagna sign_id {d9_id} out of range"
    assert d9_name, "D9 lagna sign name empty"


# ---------------------------------------------------------------------------
# DETERMINISM
# ---------------------------------------------------------------------------

def test_byte_identical_jsonl_determinism(oracle_inputs: dict[str, Any]) -> None:
    """Same inputs + same engine_version + same ayanamsha_id + pinned
    computed_at_iso ⇒ byte-identical canonical-JSON output."""
    a = compute_chart(
        oracle_inputs, ayanamsha_id="jh_true_chitra",
        computed_at_iso="1984-02-05T05:13:00+00:00",
    )
    b = compute_chart(
        oracle_inputs, ayanamsha_id="jh_true_chitra",
        computed_at_iso="1984-02-05T05:13:00+00:00",
    )
    a_json = json.dumps(a, sort_keys=True, separators=(",", ":"))
    b_json = json.dumps(b, sort_keys=True, separators=(",", ":"))
    assert a_json == b_json, "compute_chart non-deterministic across runs"
