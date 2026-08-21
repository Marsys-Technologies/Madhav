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
# _fetch_cgm_motif_weakest_node_burden — wired real source #3
#
# F-117 SUPERSEDES the BA-P2.5 #4 shape of this fetcher. It previously computed
# 1 - MIN(motif_strength); those assertions are replaced (not merely relaxed)
# because that quantity was structurally incapable of varying — bo_cgm_motifs
# writes motif_strength as a per-motif-CLASS constant, so the term evaluated to
# exactly 0.4 for all nine grahas of the native chart. The fetcher now computes
# A13 §3's own definition: the share of a graha's motif memberships in which it
# is the weakest participating node by L1 shadbala.
# ─────────────────────────────────────────────────────────────────────────────

class TestCgmMotifWeakestNodeBurden:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_weakest_member_by_l1_shadbala_carries_the_burden(self):
        mod = self._load()
        conn = _conn_returning([("m1", ["Saturn", "Jupiter"])])
        result = mod._fetch_cgm_motif_weakest_node_burden(
            conn, "chart-1", "lahiri", {"Saturn": 0.5, "Jupiter": 1.4}
        )
        assert result["Saturn"] == pytest.approx(1.0)
        assert result["Jupiter"] == pytest.approx(0.0)

    def test_normalized_by_the_grahas_own_membership_count(self):
        mod = self._load()
        conn = _conn_returning([
            ("m1", ["Saturn", "Jupiter"]),
            ("m2", ["Saturn", "Mars"]),
        ])
        # Saturn is weakest in m1 only; Mars is weakest in m2. Saturn: 1 of 2.
        result = mod._fetch_cgm_motif_weakest_node_burden(
            conn, "chart-1", "lahiri",
            {"Saturn": 0.9, "Jupiter": 1.4, "Mars": 0.4},
        )
        assert result["Saturn"] == pytest.approx(0.5)
        assert result["Mars"] == pytest.approx(1.0)
        assert result["Jupiter"] == pytest.approx(0.0)

    def test_is_not_degenerate_when_upstream_motif_strength_is_constant(self):
        """The exact F-117 regression: identical motif_strength for every motif must
        no longer produce an identical burden for every graha. motif_strength is not
        read at all now — L1 shadbala decides the weak member."""
        mod = self._load()
        conn = _conn_returning([
            ("m1", ["Sun", "Venus"]),
            ("m2", ["Venus", "Mars"]),
            ("m3", ["Sun", "Mars"]),
        ])
        result = mod._fetch_cgm_motif_weakest_node_burden(
            conn, "chart-1", "lahiri", {"Sun": 1.7, "Venus": 0.8, "Mars": 1.1},
        )
        assert len(set(result.values())) > 1, (
            f"motif_burden must discriminate between grahas, got {result}"
        )

    def test_non_graha_node_subject_is_skipped(self):
        mod = self._load()
        conn = _conn_returning([("m1", ["HOUSE_5", "ASC"])])
        result = mod._fetch_cgm_motif_weakest_node_burden(
            conn, "chart-1", "lahiri", {"Saturn": 0.5}
        )
        assert result == {}

    def test_node_with_no_l1_shadbala_is_never_credited_as_weakest(self):
        """§N.5 / B.10: classical shadbala defines no requirement for Rahu/Ketu, so
        they cannot be adjudged the weak member. They still count as members (the
        denominator), but the burden goes to the weakest graha that HAS an L1 row."""
        mod = self._load()
        conn = _conn_returning([("m1", ["Rahu", "Jupiter"])])
        result = mod._fetch_cgm_motif_weakest_node_burden(
            conn, "chart-1", "lahiri", {"Jupiter": 1.4}
        )
        assert result["Rahu"] == pytest.approx(0.0)
        assert result["Jupiter"] == pytest.approx(1.0)

    def test_motif_of_only_nodes_credits_nobody(self):
        mod = self._load()
        conn = _conn_returning([("m1", ["Rahu", "Ketu"])])
        result = mod._fetch_cgm_motif_weakest_node_burden(
            conn, "chart-1", "lahiri", {"Jupiter": 1.4}
        )
        assert result == {"Rahu": 0.0, "Ketu": 0.0}

    def test_no_motifs_returns_empty_dict(self):
        """Honest: grahas with no motif membership get no entry (caller defaults to 0.0
        'no structural motif to be the weak point of', not a fabricated value)."""
        mod = self._load()
        conn = _conn_returning([])
        result = mod._fetch_cgm_motif_weakest_node_burden(
            conn, "chart-1", "lahiri", {"Saturn": 0.5}
        )
        assert result == {}


# ─────────────────────────────────────────────────────────────────────────────
# F-117 — _cdlm_weakest_constituent_burden (domain_burden; was hardcoded 0.0)
# ─────────────────────────────────────────────────────────────────────────────

class TestCdlmWeakestConstituentBurden:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_weakest_material_constituent_of_a_cell_carries_it(self):
        mod = self._load()
        cells = {"Venus": ["c1"], "Jupiter": ["c1"]}
        result = mod._cdlm_weakest_constituent_burden(
            cells, {"Venus": 0.84, "Jupiter": 1.4}
        )
        assert result["Venus"] == pytest.approx(1.0)
        assert result["Jupiter"] == pytest.approx(0.0)

    def test_normalized_by_the_grahas_own_cell_count(self):
        mod = self._load()
        cells = {"Venus": ["c1", "c2"], "Jupiter": ["c1"], "Mars": ["c2"]}
        result = mod._cdlm_weakest_constituent_burden(
            cells, {"Venus": 0.84, "Jupiter": 1.4, "Mars": 0.4}
        )
        assert result["Venus"] == pytest.approx(0.5)   # weakest in c1, not c2
        assert result["Mars"] == pytest.approx(1.0)

    def test_no_longer_hardcoded_zero_for_every_graha(self):
        """The exact F-117 regression: domain_burden was 0 for all nine grahas."""
        mod = self._load()
        cells = {"Venus": ["c1"], "Jupiter": ["c1"], "Mars": ["c2"], "Sun": ["c2"]}
        result = mod._cdlm_weakest_constituent_burden(
            cells, {"Venus": 0.84, "Jupiter": 1.4, "Mars": 1.1, "Sun": 1.7}
        )
        assert any(v > 0 for v in result.values()), result
        assert len(set(result.values())) > 1, result

    def test_graha_bridging_no_cell_is_absent_not_fabricated(self):
        mod = self._load()
        assert mod._cdlm_weakest_constituent_burden({}, {"Venus": 0.84}) == {}

    def test_node_without_shadbala_is_not_credited_as_weakest(self):
        mod = self._load()
        cells = {"Ketu": ["c1"], "Jupiter": ["c1"]}
        result = mod._cdlm_weakest_constituent_burden(cells, {"Jupiter": 1.4})
        assert result["Ketu"] == pytest.approx(0.0)
        assert result["Jupiter"] == pytest.approx(1.0)


# ─────────────────────────────────────────────────────────────────────────────
# F-117 — _fetch_msr_contradiction_burden (honest NULL, no substitution)
# ─────────────────────────────────────────────────────────────────────────────

class TestMsrContradictionBurden:
    def _load(self):
        return _load_module("bo_upaya.py")

    def test_reports_source_unavailable_when_upstream_column_is_empty(self):
        """§N.7 item 4 / §N.8: the availability flag must have a real detector behind
        it. With zero populated contradicts_signals_array rows it reads False, and the
        caller stores NULL rather than a 0.0 indistinguishable from a measurement."""
        mod = self._load()
        conn = _conn_returning([(0,)])
        burden, available = mod._fetch_msr_contradiction_burden(conn, "chart-1", "lahiri")
        assert available is False
        assert burden == {}

    def test_reads_the_source_when_it_is_populated(self):
        mod = self._load()
        conn = MagicMock()
        conn.execute.return_value.fetchall.side_effect = [
            [(3,)],                              # probe: source populated
            [("Mars", 2.0), ("Venus", 1.0)],     # per-graha conflict salience
        ]
        burden, available = mod._fetch_msr_contradiction_burden(conn, "chart-1", "lahiri")
        assert available is True
        assert burden["Mars"] == pytest.approx(1.0)   # chart-relative peak
        assert burden["Venus"] == pytest.approx(0.5)

    def test_does_not_substitute_dosha_counts(self):
        """The pre-F-117 defect: contradiction_factor was fed dosha counts, the same
        fact affliction_count_normalized already carries. This fetcher touches only
        contradicts_signals_array — no dosha table appears in its SQL."""
        mod = self._load()
        conn = _conn_returning([(0,)])
        mod._fetch_msr_contradiction_burden(conn, "chart-1", "lahiri")
        sql = " ".join(str(c) for c in conn.execute.call_args_list).lower()
        assert "contradicts_signals_array" in sql
        assert "dosha" not in sql


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
