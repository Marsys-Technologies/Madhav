"""
test_ga_single_tier_emission.py -- Q-L1-16(a) BEHAVIOURAL guard.

`test_verification_tier_literal_guard.py` is a static (AST) check. This file proves the
three L1 writers that used to stamp the deprecated alias `single_pass` now actually EMIT
the canonical `single` from their real row builders, and that their chart_facts insert
choke points refuse an alias / out-of-vocabulary tier BEFORE any delete or insert (so a
tier built by concatenation or a future helper cannot reach the database).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from brahmagyan.verification_tiers import SINGLE, SINGLE_PASS

_CHART = "482012f1-710e-4a25-994a-93821f5871aa"


# ── ga_panchanga ─────────────────────────────────────────────────────────────


def test_panchanga_single_tier_helper_and_derived_rows_emit_single():
    from ga_writers import ga_panchanga_writer as w

    assert w._single_verif() == SINGLE == "single"
    pi = SimpleNamespace(karana=SimpleNamespace(id=7))
    rows = w._emit_bhadra_flag(pi, _CHART, "b1", "2026-10-02T00:00:00+00:00")
    assert rows
    assert {r["verification_pass_status"] for r in rows} == {"single"}


# ── ga_structural ────────────────────────────────────────────────────────────


def test_structural_composite_state_classification_rows_emit_single():
    from ga_writers.ga_structural_writer import _build_structural_relationship_rows

    signs = {
        "Sun": "Capricorn", "Moon": "Aquarius", "Mars": "Libra", "Mercury": "Capricorn",
        "Jupiter": "Sagittarius", "Venus": "Sagittarius", "Saturn": "Libra",
        "Rahu": "Taurus", "Ketu": "Scorpio",
    }
    grahas = [
        {"name": n, "sign": s, "dignity_status": "neutral", "house": 1} for n, s in signs.items()
    ]
    rows = _build_structural_relationship_rows(
        {"grahas": grahas}, "test-chart", "test-build", "lahiri_chitrapaksha",
        "2026-10-02T00:00:00Z", "test-eng",
    )
    cls = [r for r in rows if r["fact_category"] == "graha_composite_state_classification"]
    assert cls, "builder produced no graha_composite_state_classification rows"
    assert {r["verification_pass_status"] for r in cls} == {"single"}
    assert SINGLE_PASS not in {r["verification_pass_status"] for r in rows}


def test_structural_catalog_label_rows_emit_single():
    from tests import test_ga8_writer as t8

    sut = t8.sut
    args = (t8.NULL_CONN, t8.MOCK_CHART_OUTPUT, t8.CHART_ID, t8.BUILD_ID, t8.AY_ID,
            t8.COMPUTED_AT, t8.ENG_VER)
    rows = list(sut._build_yoga_rows(*args)) + list(sut._build_dosha_rows(*args))
    assert rows, "yoga/dosha builders produced no rows offline"
    tiers = {r["verification_pass_status"] for r in rows}
    assert tiers == {"single"}, tiers  # catalog-label rows: single catalog evaluation, no 2nd pass
    assert SINGLE_PASS not in tiers


# ── ga_strength ──────────────────────────────────────────────────────────────


def test_strength_ashtakavarga_verifier_emits_classical_match():
    from ga_writers.ga_strength_writer import _verify_ashtakavarga

    bav = {g: [4] * 12 for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")}
    bav["SARVA"] = [28] * 12  # 12 * 28 = 336, within tolerance of 337
    # Q03 / SS N-62: a passed consistency check over the raw bindus earns `classical_match` (the writer
    # applies it only to the raw-bindu rows it examines; every other ga_strength row is `single`).
    assert _verify_ashtakavarga(bav, tolerance=2) == "classical_match"


# ── chart_facts insert choke points ──────────────────────────────────────────


class _TripWire:
    """Any use of the connection means the choke point let the row through."""

    def __getattr__(self, name):  # pragma: no cover - only reached on failure
        raise AssertionError(f"connection touched ({name}) before the tier was rejected")


def _bad_rows(tier):
    return [{"verification_pass_status": tier, "fact_category": "x", "fact_subject": "y",
             "fact_key": "z", "chart_id": _CHART, "ayanamsha_id": "INVARIANT"}]


@pytest.mark.parametrize("modname", ["ga_panchanga_writer", "ga_strength_writer", "ga_structural_writer"])
@pytest.mark.parametrize("tier", ["single" + "_pass", "single_" + "pass", "made_up_tier", "PASS"])
def test_insert_choke_point_rejects_alias_and_unknown_tiers_before_touching_db(modname, tier):
    import importlib

    w = importlib.import_module(f"ga_writers.{modname}")
    with pytest.raises(ValueError):
        w._insert_chart_facts_rows(_TripWire(), _bad_rows(tier))
