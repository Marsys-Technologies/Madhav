"""
test_ba_p25_4_bo_upaya_resonance_wiring.py — BA Phase 2.5 fast-follow #4
=========================================================================
bo_upaya's resonance_score_v1 previously fed 5 hardcoded 0.0 inputs
(cancellation_burden, dispositor_chain_weakness, dasha_proximity_activation_score,
cdlm_weakest_constituent_count, cgm_motifs_weakest_node), which collapsed
resonance_score toward weakness_score for every graha regardless of real
dispositor-chain condition or dasha timing.

This fix wires 3 of the 5 inputs to real already-computed sources:
  - dispositor_chain_weakness      <- chart_facts composite_dispositor_strength (ga_structural)
  - dasha_proximity_activation_score <- chart_dashas (ga_dashas)
  - cgm_motifs_weakest_node         <- bodha_cgm_motifs (bo_cgm_motifs)

The other 2 (cancellation_burden, cdlm_weakest_constituent_count) have no
already-computed source anywhere in the codebase and remain honest 0.0
placeholders (B.10 — no fabricated computation).

All tests are pure unit tests: no real DB connections.
"""
from __future__ import annotations

import collections
import importlib.util
import pathlib
import sys
import types
from datetime import datetime, timezone
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


# ─────────────────────────────────────────────────────────────────────────────
# _fetch_dispositor_terminal_strength — wired real source #1
# ─────────────────────────────────────────────────────────────────────────────

class TestDispositorChainWeaknessWired:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_maps_fact_subject_codes_to_planet_names(self):
        mod = self._load()
        rows = [("SUN", 1.0), ("SAT", 0.25), ("MAR", 0.5)]
        conn = _conn_returning(rows)
        result = mod._fetch_dispositor_terminal_strength(conn, "chart-1", "lahiri_chitrapaksha")
        assert result == {"Sun": 1.0, "Saturn": 0.25, "Mars": 0.5}

    def test_unknown_subject_is_skipped(self):
        mod = self._load()
        conn = _conn_returning([("BOGUS", 0.9)])
        result = mod._fetch_dispositor_terminal_strength(conn, "chart-1", "lahiri_chitrapaksha")
        assert result == {}

    def test_value_clamped_to_0_1_range(self):
        mod = self._load()
        conn = _conn_returning([("SUN", 1.4), ("MOON", -0.3)])
        result = mod._fetch_dispositor_terminal_strength(conn, "chart-1", "lahiri_chitrapaksha")
        assert result["Sun"] == 1.0
        assert result["Moon"] == 0.0

    def test_differs_per_graha_not_constant(self):
        """Core fix assertion: real per-graha dispositor strength varies (not
        the old flat 0.0 that made dispositor_chain_weakness identical for
        every graha)."""
        mod = self._load()
        rows = [("SUN", 1.0), ("MOON", 0.5), ("SAT", 0.25)]
        conn = _conn_returning(rows)
        result = mod._fetch_dispositor_terminal_strength(conn, "chart-1", "lahiri_chitrapaksha")
        weaknesses = {g: round(1.0 - v, 6) for g, v in result.items()}
        assert len(set(weaknesses.values())) > 1, (
            f"dispositor_chain_weakness must vary across grahas, got {weaknesses}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# _fetch_dasha_proximity — wired real source #2
# ─────────────────────────────────────────────────────────────────────────────

class TestDashaProximityWired:
    def _load(self):
        return _load_module("bo_upaya.py")

    def _at(self):
        return datetime(2026, 7, 5, tzinfo=timezone.utc)

    def test_md_and_ad_same_graha_scores_1_0(self):
        mod = self._load()
        rows = [(1, "Saturn"), (2, "Saturn")]
        conn = _conn_returning(rows)
        result = mod._fetch_dasha_proximity(conn, "chart-1", "lahiri_chitrapaksha", self._at())
        assert result["Saturn"] == 1.0

    def test_md_only_scores_0_6(self):
        mod = self._load()
        rows = [(1, "Saturn"), (2, "Mercury")]
        conn = _conn_returning(rows)
        result = mod._fetch_dasha_proximity(conn, "chart-1", "lahiri_chitrapaksha", self._at())
        assert result["Saturn"] == 0.6
        assert result["Mercury"] == 0.6

    def test_neither_scores_0_0(self):
        mod = self._load()
        rows = [(1, "Saturn"), (2, "Mercury")]
        conn = _conn_returning(rows)
        result = mod._fetch_dasha_proximity(conn, "chart-1", "lahiri_chitrapaksha", self._at())
        assert result["Venus"] == 0.0
        assert result["Sun"] == 0.0

    def test_no_active_dasha_rows_all_zero(self):
        mod = self._load()
        conn = _conn_returning([])
        result = mod._fetch_dasha_proximity(conn, "chart-1", "lahiri_chitrapaksha", self._at())
        assert all(v == 0.0 for v in result.values())

    def test_all_nine_grahas_present_in_output(self):
        mod = self._load()
        conn = _conn_returning([(1, "Saturn"), (2, "Mercury")])
        result = mod._fetch_dasha_proximity(conn, "chart-1", "lahiri_chitrapaksha", self._at())
        assert set(result.keys()) == set(mod.KNOWN_GRAHAS)

    def test_scores_differ_per_graha_not_constant(self):
        """Core fix assertion: dasha_proximity_activation_score is no longer a
        flat 0.0 across all grahas — it now distinguishes the running MD/AD
        lords from everyone else."""
        mod = self._load()
        conn = _conn_returning([(1, "Saturn"), (2, "Saturn")])
        result = mod._fetch_dasha_proximity(conn, "chart-1", "lahiri_chitrapaksha", self._at())
        assert len(set(result.values())) > 1, (
            f"dasha_proximity_activation_score must vary across grahas, got {result}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# _fetch_cgm_motif_weakness — wired real source #3
# ─────────────────────────────────────────────────────────────────────────────

class TestCgmMotifWeaknessWired:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_weakness_is_one_minus_min_motif_strength(self):
        mod = self._load()
        conn = _conn_returning([("Saturn", 0.3)])
        result = mod._fetch_cgm_motif_weakness(conn, "chart-1", "lahiri_chitrapaksha")
        assert result["Saturn"] == pytest.approx(0.7)

    def test_non_graha_node_subject_is_skipped(self):
        mod = self._load()
        conn = _conn_returning([("HOUSE_5", 0.2)])
        result = mod._fetch_cgm_motif_weakness(conn, "chart-1", "lahiri_chitrapaksha")
        assert result == {}

    def test_null_strength_is_skipped_not_fabricated(self):
        mod = self._load()
        conn = _conn_returning([("Mars", None)])
        result = mod._fetch_cgm_motif_weakness(conn, "chart-1", "lahiri_chitrapaksha")
        assert "Mars" not in result

    def test_no_motifs_returns_empty_dict(self):
        """Honest: grahas with no motif membership get no entry (caller defaults to 0.0
        'no burden observed', not a fabricated positive value)."""
        mod = self._load()
        conn = _conn_returning([])
        result = mod._fetch_cgm_motif_weakness(conn, "chart-1", "lahiri_chitrapaksha")
        assert result == {}


# ─────────────────────────────────────────────────────────────────────────────
# Degeneracy-gate: resonance_score no longer collapses to weakness_score
# ─────────────────────────────────────────────────────────────────────────────

class TestResonanceDegeneracyGate:
    """Core BA-P2.5 #4 assertion: feeding the 3 newly-wired inputs (dispositor
    chain weakness, dasha proximity, CGM motif weakness) with real, non-zero,
    per-graha-varying values must change resonance_score — proving the old bug
    (all 5 inputs hardcoded to 0.0, collapsing resonance_score toward a flat
    function of weakness_score alone) is fixed. Mirrors the degeneracy-gate
    style used for bo_cgm_paths.path_strength / ph_muhurta composite_quality."""

    def _formulas(self):
        from bodha_writers.formulas import ResonanceInputs, resonance_score_v1
        return ResonanceInputs, resonance_score_v1

    def test_wired_nonzero_inputs_change_resonance_score(self):
        ResonanceInputs, resonance_score_v1 = self._formulas()

        base_kwargs = dict(
            shadbala_normalized=0.5,
            bhava_bala_normalized=0.5,
            combustion_score=0.0,
            debility_score=0.0,
            affliction_count_normalized=0.0,
            cancellation_burden=0.0,        # honest placeholder — unchanged
            vargottama_absence_score=0.5,   # honest placeholder — unchanged
            cdlm_weakest_constituent_count=0.0,  # honest placeholder — unchanged
            msr_signals_in_conflict=0.0,
        )

        old_bug = resonance_score_v1(ResonanceInputs(
            **base_kwargs,
            dispositor_chain_weakness=0.0,
            dasha_proximity_activation_score=0.0,
            cgm_motifs_weakest_node=0.0,
        ))
        wired = resonance_score_v1(ResonanceInputs(
            **base_kwargs,
            dispositor_chain_weakness=0.8,
            dasha_proximity_activation_score=0.6,
            cgm_motifs_weakest_node=0.4,
        ))

        assert wired["resonance_score"] != old_bug["resonance_score"], (
            "Wiring real non-zero dispositor/dasha/motif inputs must change "
            f"resonance_score; old_bug={old_bug['resonance_score']} "
            f"wired={wired['resonance_score']}"
        )
        assert wired["weakness_score"] != old_bug["weakness_score"], (
            "dispositor_chain_weakness and dasha_proximity_activation_score feed "
            "weakness_score directly — must differ once wired to non-zero values"
        )

    def test_two_grahas_with_different_wired_inputs_get_different_resonance(self):
        """Simulates the exact bug scenario: two grahas that are otherwise
        identical (same shadbala/bhava_bala/combustion/debility/afflictions)
        must now get DIFFERENT resonance_score once dispositor-chain and
        dasha-timing data (which naturally differ per graha) are wired in —
        previously they would have been indistinguishable."""
        ResonanceInputs, resonance_score_v1 = self._formulas()

        shared = dict(
            shadbala_normalized=0.6, bhava_bala_normalized=0.6,
            combustion_score=0.0, debility_score=0.0,
            affliction_count_normalized=0.0, cancellation_burden=0.0,
            vargottama_absence_score=0.5, cdlm_weakest_constituent_count=0.0,
            msr_signals_in_conflict=0.0,
        )

        # graha A: strong dispositor terminal, no current dasha
        graha_a = resonance_score_v1(ResonanceInputs(
            **shared, dispositor_chain_weakness=0.0,
            dasha_proximity_activation_score=0.0, cgm_motifs_weakest_node=0.0,
        ))
        # graha B: weak dispositor terminal AND currently running its own MD+AD
        graha_b = resonance_score_v1(ResonanceInputs(
            **shared, dispositor_chain_weakness=0.75,
            dasha_proximity_activation_score=1.0, cgm_motifs_weakest_node=0.0,
        ))

        assert graha_a["resonance_score"] != graha_b["resonance_score"], (
            "Two grahas with identical base weakness inputs but different real "
            "dispositor-chain/dasha-timing data must not collapse to the same "
            f"resonance_score; got {graha_a['resonance_score']} for both"
        )
        assert graha_b["resonance_score"] > graha_a["resonance_score"], (
            "The graha with weaker dispositor terminal + active own-dasha should "
            "rank as MORE resonant (higher remedy priority), not less"
        )


# ─────────────────────────────────────────────────────────────────────────────
# CR-67 (SARVA-SIDDHI W-3): _fetch_graha_cdlm_cells — the previously-missing
# resonance → CDLM cell derivation (associated_cdlm_cells_array was 100% NULL).
# ─────────────────────────────────────────────────────────────────────────────

class TestGrahaCdlmCellsWired:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_groups_cell_ids_by_graha(self):
        mod = self._load()
        # SQL returns one (graha, cell_id) row per material (graha × cell) pair.
        rows = [
            ("Sun", "cell-1"), ("Sun", "cell-2"), ("Saturn", "cell-1"),
            ("Jupiter", "cell-3"),
        ]
        conn = _conn_returning(rows)
        result = mod._fetch_graha_cdlm_cells(conn, "chart-1", "lahiri_chitrapaksha")
        assert result["Sun"] == ["cell-1", "cell-2"]
        assert result["Saturn"] == ["cell-1"]
        assert result["Jupiter"] == ["cell-3"]

    def test_empty_when_no_material_cells(self):
        mod = self._load()
        conn = _conn_returning([])
        result = mod._fetch_graha_cdlm_cells(conn, "chart-1", "lahiri_chitrapaksha")
        assert result == {}

    def test_handles_dict_row_factory(self):
        mod = self._load()
        rows = [{"graha": "Venus", "cell_id": "cell-9"}]
        conn = _conn_returning(rows)
        result = mod._fetch_graha_cdlm_cells(conn, "chart-1", "lahiri_chitrapaksha")
        assert result == {"Venus": ["cell-9"]}

    def test_insert_binds_cdlm_param_not_literal_null(self):
        """The INSERT must bind %(associated_cdlm_cells_array)s — a regression
        to the old literal NULL is what left the column 100% empty DB-wide."""
        mod = self._load()
        assert "%(associated_cdlm_cells_array)s" in mod._RESONANCE_INSERT


# ─────────────────────────────────────────────────────────────────────────────
# CR-69 (SARVA-SIDDHI W-3): the sadhana-milestone date filter must use a
# parameter cast (`%s::date`), not the invalid `DATE %s` that raised a
# SyntaxError and kept bodha_rm_dasha_windowed_prescriptions at 0 rows.
# ─────────────────────────────────────────────────────────────────────────────

class TestSadhanaMilestoneDateCast:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_sadhana_query_uses_param_cast_not_date_keyword(self):
        mod = self._load()
        import inspect
        src = inspect.getsource(mod._fetch_sadhana_milestones)
        assert "%s::date" in src, "sadhana date filter must cast the bound param"
        assert "DATE %s" not in src, "the invalid `DATE %s` parameter form must be gone"
