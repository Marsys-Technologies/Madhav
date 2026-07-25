"""
test_beta_g_el51_maraka_verdict.py — Elevation Campaign v2.1, Stream β, Lane G (EL-51)
=========================================================================================
Tests the deterministic gemstone maraka-contraindication verdict added to bo_upaya.py:
  - _fetch_maraka_facts            <- chart_facts (ayurdaya.CHART.maraka_grahas, L1-authoritative)
  - _compute_gemstone_maraka_verdict  (pure function, BPHS Ch.44/47-grounded)
  - _fetch_active_doshas_by_graha  <- chart_facts (dosha_label, fires=true, traced via
                                       constituent_facts_array — never inferred from a dosha's name)

Covers the safety-bearing discipline this lane is built on: never a fabricated verdict, never a
silent False when the L1 fact is absent, always a citation on a "contraindicated" result.

All tests are pure unit tests: no real DB connections (same _conn_returning / _load_module /
_ensure_writers_stub pattern as test_ba_p25_4_bo_upaya_resonance_wiring.py).
"""
from __future__ import annotations

import collections
import importlib.util
import json
import pathlib
import sys
import types
from unittest.mock import MagicMock

import pytest

_WRITERS_DIR = str(
    pathlib.Path(__file__).parent.parent / "pipeline" / "orchestrator" / "writers"
)
_WORKTREE = _WRITERS_DIR + "/"
_PKG = "pipeline.orchestrator.writers"

FakeWriterResult = collections.namedtuple(
    "WriterResult", ["asset_id", "rows_inserted", "notes", "duration_seconds"],
    defaults=[None, 0, None, 0.0],
)


def _ensure_writers_stub():
    existing = sys.modules.get(_PKG)
    if existing is not None and hasattr(existing, "__file__"):
        return existing
    stub = types.ModuleType(_PKG)
    stub.WriterBase = object
    stub.ContextSpec = object
    stub.WriterResult = FakeWriterResult
    stub.SubStep = MagicMock
    stub.register = lambda x: (lambda cls: cls)
    stub.__path__ = [_WRITERS_DIR]
    stub.__package__ = _PKG
    sys.modules[_PKG] = stub
    return stub


def _load_module(filename: str) -> types.ModuleType:
    stub = _ensure_writers_stub()
    key = f"{_PKG}.{filename.replace('.py', '')}"
    prev_mod = sys.modules.pop(key, None)

    path = _WORKTREE + filename
    spec = importlib.util.spec_from_file_location(key, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _PKG
    sys.modules[key] = mod

    _noop_register = lambda asset_id: (lambda cls: cls)
    original_register = getattr(stub, "register", _noop_register)
    stub.register = _noop_register
    try:
        spec.loader.exec_module(mod)
    finally:
        stub.register = original_register
        if prev_mod is not None:
            sys.modules[key] = prev_mod
        else:
            sys.modules.pop(key, None)

    return mod


def _conn_returning(rows):
    conn = MagicMock()
    result = MagicMock()
    result.fetchall.return_value = rows
    conn.execute.return_value = result
    return conn


@pytest.fixture(scope="module")
def bo_upaya():
    return _load_module("bo_upaya.py")


# ── _compute_gemstone_maraka_verdict (pure function) ───────────────────────────────────────

def test_verdict_unavailable_when_no_l1_fact(bo_upaya):
    """Never a silent False — absence of the L1 fact must be a distinct, disclosed state."""
    v = bo_upaya._compute_gemstone_maraka_verdict("Venus", None)
    assert v["verdict"] == "unavailable"
    assert v["is_maraka_lord"] is None
    assert "citation" in v and "BPHS" in v["citation"]


def test_verdict_contraindicated_when_2nd_lord(bo_upaya):
    facts = {"second_lord": "Venus", "seventh_lord": "Mars", "_source_fact_id": "abc123"}
    v = bo_upaya._compute_gemstone_maraka_verdict("Venus", facts)
    assert v["verdict"] == "contraindicated"
    assert v["is_maraka_lord"] is True
    assert "2nd house" in v["reason"]
    assert v["citation"] == bo_upaya.MARAKA_CITATION
    assert v["source_fact_id"] == "abc123"


def test_verdict_contraindicated_when_7th_lord(bo_upaya):
    facts = {"second_lord": "Mars", "seventh_lord": "Venus"}
    v = bo_upaya._compute_gemstone_maraka_verdict("Venus", facts)
    assert v["verdict"] == "contraindicated"
    assert v["is_maraka_lord"] is True
    assert "7th house" in v["reason"]


def test_verdict_both_lords(bo_upaya):
    """Same graha rules both 2nd and 7th (can happen for certain lagnas) — must not
    silently pick one and drop the other from the reason text."""
    facts = {"second_lord": "Venus", "seventh_lord": "Venus"}
    v = bo_upaya._compute_gemstone_maraka_verdict("Venus", facts)
    assert v["verdict"] == "contraindicated"
    assert "both" in v["reason"].lower()


def test_verdict_no_contraindication(bo_upaya):
    facts = {"second_lord": "Mars", "seventh_lord": "Jupiter"}
    v = bo_upaya._compute_gemstone_maraka_verdict("Venus", facts)
    assert v["verdict"] == "no_contraindication_found"
    assert v["is_maraka_lord"] is False
    assert "Mars" in v["reason"] and "Jupiter" in v["reason"]


def test_verdict_always_carries_citation_and_rule_scope(bo_upaya):
    """Every verdict shape (available or not, contraindicated or not) must carry a citation
    and an explicit rule_scope — the safety-bearing discipline this lane is built on."""
    for facts in (None, {"second_lord": "Sun", "seventh_lord": "Moon"}, {"second_lord": "Venus", "seventh_lord": "Mars"}):
        v = bo_upaya._compute_gemstone_maraka_verdict("Venus", facts)
        assert v.get("citation")
        assert v.get("rule_scope")


def test_verdict_matches_canonical_chart_live_facts(bo_upaya):
    """Regression pin: live G0 probe (2026-07-25) confirmed BOTH second_lord and
    seventh_lord = Venus for the canonical chart (482012f1…, lahiri_chitrapaksha) —
    occupants_2_7 = [Mars, Saturn]. If ga_ayurdaya_writer's computation ever changes this,
    this test should be revisited, not silently left stale."""
    facts = {"second_lord": "Venus", "seventh_lord": "Venus",
             "occupants_2_7": ["Mars", "Saturn"], "natural_maraka": "Saturn"}
    v = bo_upaya._compute_gemstone_maraka_verdict("Venus", facts)
    assert v["verdict"] == "contraindicated"
    v_mars = bo_upaya._compute_gemstone_maraka_verdict("Mars", facts)
    assert v_mars["verdict"] == "no_contraindication_found"


# ── _fetch_maraka_facts (mocked DB) ─────────────────────────────────────────────────────────

def test_fetch_maraka_facts_parses_jsonb_dict_row(bo_upaya):
    conn = _conn_returning([
        ({"second_lord": "Venus", "seventh_lord": "Venus"}, "fact-id-1"),
    ])
    facts = bo_upaya._fetch_maraka_facts(conn, "chart-1", "lahiri_chitrapaksha")
    assert facts["second_lord"] == "Venus"
    assert facts["_source_fact_id"] == "fact-id-1"


def test_fetch_maraka_facts_parses_jsonb_string_row(bo_upaya):
    """Some drivers return jsonb as a raw string — must not crash, must parse."""
    conn = _conn_returning([
        (json.dumps({"second_lord": "Mars", "seventh_lord": "Jupiter"}), "fact-id-2"),
    ])
    facts = bo_upaya._fetch_maraka_facts(conn, "chart-1", "lahiri_chitrapaksha")
    assert facts["second_lord"] == "Mars"


def test_fetch_maraka_facts_returns_none_when_absent(bo_upaya):
    """No row — never a silent default (e.g. never invent second_lord=None-that-reads-as-real)."""
    conn = _conn_returning([])
    facts = bo_upaya._fetch_maraka_facts(conn, "chart-1", "lahiri_chitrapaksha")
    assert facts is None


# ── _fetch_active_doshas_by_graha (mocked DB, two-query join) ──────────────────────────────

def test_fetch_active_doshas_traces_graha_via_constituent_facts(bo_upaya):
    """The dosha_label row's constituent_facts_array resolves to a chart_facts row whose
    fact_subject IS a graha name — a real, traceable association, not a name-based guess."""
    conn = MagicMock()

    dosha_result = MagicMock()
    dosha_result.fetchall.return_value = [
        ("manglik", "Mangal Dosha", {"fires": "true", "constituent_facts_array": ["f1", "f2"]}),
    ]
    constituent_result = MagicMock()
    constituent_result.fetchall.return_value = [("MARS",), ("HOUSE_7",)]

    conn.execute.side_effect = [dosha_result, constituent_result]

    out = bo_upaya._fetch_active_doshas_by_graha(conn, "chart-1", "lahiri_chitrapaksha")
    assert out.get("Mars") == ["Mangal Dosha"]


def test_fetch_active_doshas_no_constituents_no_crash(bo_upaya):
    conn = MagicMock()
    dosha_result = MagicMock()
    dosha_result.fetchall.return_value = [
        ("kemadruma", "Kemadruma Yoga", {"fires": "true", "constituent_facts_array": []}),
    ]
    conn.execute.return_value = dosha_result
    out = bo_upaya._fetch_active_doshas_by_graha(conn, "chart-1", "lahiri_chitrapaksha")
    assert out == {}
