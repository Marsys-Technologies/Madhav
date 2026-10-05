"""
test_q03_tiers_panchanga_structural.py -- Q03 / SS N-62 honest tiers for ga_panchanga and
ga_structural (TS-PAN / TS-STRUCT).

  * ga_panchanga: no check of any kind runs on any panchanga row -> every row is `single`
    (UNVERIFIED_DEFAULT), including the 11 `_emit_*` derived-anga emitters.
  * ga_structural: yoga_label, dosha_label and graha_composite_state_classification are catalog-rule
    evaluations with no second path -> `single`.
  * No ga_writers / orchestrator-writer source carries a bare `single_pass` literal (the deprecated
    alias); grep-level guard, in addition to the AST guard in test_verification_tier_literal_guard.

Spec: AUDIT_L1_TIERS_PER_EMITTER_v1_0.md v1.1 §5 (TS-PAN / TS-STRUCT) and §6.
"""
from __future__ import annotations

import os
import pathlib
import re
import sys
from unittest.mock import patch

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))
sys.path.insert(0, os.path.dirname(__file__))

from brahmagyan import verification_tiers as T
import ga_writers.ga_panchanga_writer as P
import ga_writers.ga_structural_writer as S
from test_ga4_writer import _make_forensic_pi
from test_ga8_writer import (
    AY_ID, BUILD_ID, CHART_ID, COMPUTED_AT, ENG_VER, MOCK_CHART_OUTPUT, NULL_CONN,
)

AYA = "lahiri_chitrapaksha"


# ── ga_panchanga ──────────────────────────────────────────────────────────────


def _derived_emitter_rows() -> dict[str, list[dict]]:
    pi = _make_forensic_pi()
    c, b, t = "chart-q03", "build-q03", "2026-10-02T00:00:00+00:00"
    out = {
        "_emit_disha_shul": P._emit_disha_shul(pi, c, b, t),
        "_emit_tithi_shoonya": P._emit_tithi_shoonya(pi, c, b, t),
        "_emit_nakshatra_shoonya": P._emit_nakshatra_shoonya(pi, c, b, t),
        "_emit_agni_vasa": P._emit_agni_vasa(pi, c, b, t),
        "_emit_inauspicious_window": P._emit_inauspicious_window(pi, "rahu_kalam", "RAHU_KALAM_BIRTH_DAY", c, b, t),
        "_emit_auspicious_window": P._emit_auspicious_window(pi, "abhijit_muhurta", "ABHIJIT_MUHURTA_BIRTH_DAY", c, b, t),
        "_emit_bhadra_flag": P._emit_bhadra_flag(pi, c, b, t, "INVARIANT"),
        "_emit_special_yoga_combinations": P._emit_special_yoga_combinations(pi, c, b, t, AYA),
        "_emit_panchaka_classification": P._emit_panchaka_classification(pi, c, b, t, AYA),
        "_emit_panchaka_flag": P._emit_panchaka_flag(pi, c, b, t, AYA),
        "_emit_eclipse_proximity": P._emit_eclipse_proximity(pi, c, b, t, AYA),
    }
    return out


def test_the_eleven_derived_emitters_stamp_only_single():
    by = _derived_emitter_rows()
    assert len(by) == 11
    produced = {name: rows for name, rows in by.items() if rows}
    assert len(produced) >= 8, f"fixture should exercise most emitters; got {sorted(produced)}"
    for name, rows in by.items():
        for r in rows:
            assert r["verification_pass_status"] == T.SINGLE, (name, r["fact_category"], r["fact_key"])


def test_single_verif_helper_is_the_canonical_single():
    assert P._single_verif() == T.UNVERIFIED_DEFAULT == "single"


def test_build_ga_panchanga_every_row_is_single(monkeypatch):
    captured: list[dict] = []
    import panchang_engine
    monkeypatch.setattr(panchang_engine, "panchanga_instant", lambda *a, **k: _make_forensic_pi())
    monkeypatch.setattr(P, "_insert_chart_facts_rows", lambda conn, rows: captured.extend(rows) or len(rows))
    # #2969: the birth Moon sign is READ from the ga_positions fact through the connection; this test
    # drives the writer on an opaque connection, so serve the read (one sign per canonical ayanamsha).
    monkeypatch.setattr(P, "_read_birth_moon_signs",
                        lambda conn, chart_id: {ay: "Aquarius" for ay in P.CANONICAL_AYANAMSHAS})
    bp = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.27, "longitude_deg": 85.84,
          "tz_offset_hours": 5.5}
    summary = P.build_ga_panchanga("chart-q03-not-canonical", "build-q03", conn=object(), birth_params=bp)
    assert summary["status"] == "PASS" and len(captured) > 100
    assert {r["verification_pass_status"] for r in captured} == {T.SINGLE}
    for r in captured:
        T.emit_tier(r["verification_pass_status"], table="chart_facts")


def test_panchanga_tier_mutant_is_caught(monkeypatch):
    """MUTANT: stamping a verified tier on a derived emitter (the pre-M-22 defect) fails the
    all-single assertion above."""
    monkeypatch.setattr(P, "_single_verif", lambda: T.TWO_PASS_VERIFIED)
    rows = P._emit_disha_shul(_make_forensic_pi(), "c", "b", "t")
    assert rows and {r["verification_pass_status"] for r in rows} == {T.TWO_PASS_VERIFIED}


# ── ga_structural ─────────────────────────────────────────────────────────────

_YOGA_ENTRY = {
    "canonical_id": "q03_probe_yoga", "name_en": "Q03 probe yoga",
    "formation_rule_jsonb": {"distinct_signs_occupied": 5},
    "classical_citations": {}, "source_chunk_ids": [], "category": "yoga",
}


def _dosha_entry():
    return {"canonical_id": "kemadruma", "name_en": "Kemadruma",
            "formation_rule_jsonb": {"requires": "no planet in 2nd or 12th from Moon"},
            "classical_citations": {}, "source_chunk_ids": [], "category": "dosha"}


def test_yoga_label_rows_are_single():
    rows = S._build_yoga_rows(NULL_CONN, MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT,
                              ENG_VER, yoga_catalog=[_YOGA_ENTRY])
    labels = [r for r in rows if r["fact_category"] == "yoga_label"]
    assert labels, "the probe rule must fire on the fixture chart"
    assert {r["verification_pass_status"] for r in labels} == {T.SINGLE}


def test_dosha_label_rows_are_single():
    chart = {
        "ascendant": {"sign": "Aries", "sign_id": 1, "longitude": 15.0},
        "grahas": [
            {"name": "Sun", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 295.0, "retrograde": False},
            {"name": "Moon", "sign": "Gemini", "sign_id": 3, "house": 3, "longitude": 70.0, "retrograde": False},
            {"name": "Mars", "sign": "Leo", "sign_id": 5, "house": 5, "longitude": 130.0, "retrograde": False},
            {"name": "Mercury", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 300.0, "retrograde": False},
            {"name": "Jupiter", "sign": "Sagittarius", "sign_id": 9, "house": 9, "longitude": 265.0, "retrograde": False},
            {"name": "Venus", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 308.0, "retrograde": False},
            {"name": "Saturn", "sign": "Libra", "sign_id": 7, "house": 7, "longitude": 195.0, "retrograde": False},
            {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude": 48.0, "retrograde": True},
            {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 8, "longitude": 228.0, "retrograde": True},
        ],
    }
    rows = S._build_dosha_rows(NULL_CONN, chart, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
                               dosha_catalog=[_dosha_entry()])
    labels = [r for r in rows if r["fact_category"] == "dosha_label"]
    assert labels, "a formed-but-cancelled Kemadruma still emits an auditable dosha_label row"
    assert {r["verification_pass_status"] for r in labels} == {T.SINGLE}


def test_composite_state_classification_rows_are_single():
    rows = S._build_structural_relationship_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
    cls = [r for r in rows if r["fact_category"] == "graha_composite_state_classification"]
    assert cls and {r["verification_pass_status"] for r in cls} == {T.SINGLE}


def test_structural_tier_mutant_is_caught(monkeypatch):
    """MUTANT: a catalog label stamped with a verified tier would fail the assertions above."""
    monkeypatch.setattr(S, "UNVERIFIED_DEFAULT", T.TWO_PASS_VERIFIED)
    rows = S._build_structural_relationship_rows(MOCK_CHART_OUTPUT, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER)
    cls = [r for r in rows if r["fact_category"] == "graha_composite_state_classification"]
    assert {r["verification_pass_status"] for r in cls} == {T.TWO_PASS_VERIFIED}


# ── grep guard: no new bare `single_pass` literal in L1 / orchestrator writers ─

#: L2 (bo_*) writers whose switch rides the S-L2 batch (same allowlist as the AST guard) and the
#: one declared READER of stored rows.
_GREP_ALLOW = {
    "pipeline/orchestrator/writers/bo_bimba.py",
    "pipeline/orchestrator/writers/bo_karanajala.py",
    "pipeline/orchestrator/writers/bo_pramana_mapa.py",
}
_STRING_LITERAL = re.compile(r"""["']single_pass["']""")


def _scan_for_single_pass(roots: list[pathlib.Path]) -> list[str]:
    hits: list[str] = []
    for root in roots:
        for p in sorted(root.rglob("*.py")):
            rel = p.relative_to(_SIDECAR).as_posix()
            if "__tests__" in p.parts or "tests" in p.parts or rel in _GREP_ALLOW:
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                code = line.split("#", 1)[0]
                if _STRING_LITERAL.search(code):
                    hits.append(f"{rel}:{i}")
    return hits


def test_no_bare_single_pass_literal_in_ga_writers_or_orchestrator_writers():
    hits = _scan_for_single_pass([_SIDECAR / "ga_writers", _SIDECAR / "pipeline" / "orchestrator" / "writers"])
    # docstring prose that merely names the deprecated alias is filtered by requiring a quoted
    # literal on a non-comment line; a real emission (`"single_pass"`) is what this guard finds.
    docstring_only = [h for h in hits if _is_docstring_line(h)]
    assert [h for h in hits if h not in docstring_only] == [], hits


def _is_docstring_line(hit: str) -> bool:
    rel, line = hit.rsplit(":", 1)
    import ast
    tree = ast.parse((_SIDECAR / rel).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value and \
                hasattr(node, "lineno") and node.lineno <= int(line) <= getattr(node, "end_lineno", node.lineno) \
                and "\n" in node.value:
            return True  # inside a multi-line string (docstring / prose), not an emitted value
    return False


def test_grep_guard_detects_a_synthetic_emission(tmp_path):
    f = tmp_path / "w.py"
    f.write_text('row = {"verification_pass_status": "single_pass"}\n')
    hits = []
    for i, line in enumerate(f.read_text().splitlines(), 1):
        if _STRING_LITERAL.search(line.split("#", 1)[0]):
            hits.append(i)
    assert hits == [1]
