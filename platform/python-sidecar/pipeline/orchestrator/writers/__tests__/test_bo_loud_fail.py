"""
G3 loud-fail guards — RED→GREEN tests for bo_* writers.

RED state (before each guard): writer returned WriterResult(rows_inserted=0) silently
  on broken/empty upstream data — build showed green while producing nothing.
GREEN state (after each guard): writer raises RuntimeError with a diagnostic message
  on the same broken/empty upstream state.

Every test proves the GREEN behavior: RuntimeError is raised.
Comments annotate what the RED (pre-guard) behavior was.

Run: python -m pytest platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_bo_loud_fail.py -v
"""
from __future__ import annotations

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from pipeline.orchestrator.writers import ContextSpec, SubStep


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_ctx(chart_id: str = "test-chart-001", dry_run: bool = False) -> ContextSpec:
    conn = MagicMock()
    # Support conn.cursor() as context manager
    cur = MagicMock()
    cur.fetchall.return_value = []
    cur.fetchone.return_value = None
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value = cur
    return ContextSpec(
        asset_id="test",
        build_id="build-001",
        db_conn=conn,
        config={"chart_id": chart_id},
        dry_run=dry_run,
    )


# ── §G3-1 bo_laksana: empty chart_facts → RuntimeError ───────────────────────
# RED: returned WriterResult(rows_inserted=0, notes="no facts for ayanamsha=...")
# GREEN: raises RuntimeError with L1-not-built diagnostic

class TestBoLaksanaLoudFail:
    def test_empty_chart_facts_raises(self):
        """
        GREEN: if chart_facts is empty for this ayanamsha, run_substep raises
        RuntimeError instead of silently returning 0 rows.
        """
        from pipeline.orchestrator.writers.bo_laksana import BoLaksanaWriter

        writer = BoLaksanaWriter()
        ctx    = _make_ctx()
        step   = SubStep(key="aya_lahiri", label="bo_laksana — lahiri")

        with patch("pipeline.orchestrator.writers.bo_laksana._fetch_all_facts", return_value=[]):
            with patch("pipeline.orchestrator.writers.bo_laksana._build_strength_lookup", return_value={}):
                with patch("pipeline.orchestrator.writers.bo_laksana._build_dignity_lookup", return_value={}):
                    with patch("pipeline.orchestrator.writers.bo_laksana._build_av_lookup", return_value={}):
                        with pytest.raises(RuntimeError, match="chart_facts is empty"):
                            writer.run_substep(ctx, step)

    def test_all_facts_skipped_raises(self):
        """
        GREEN: if all fact rows throw during _build_signal_row, all-skipped raises
        RuntimeError instead of silently returning 0 rows.
        """
        from pipeline.orchestrator.writers.bo_laksana import BoLaksanaWriter

        writer = BoLaksanaWriter()
        ctx    = _make_ctx()
        step   = SubStep(key="aya_lahiri", label="bo_laksana — lahiri")

        fake_fact = {"fact_id": "f1", "fact_category": "graha_position", "fact_key": "Sun", "fact_value_text": "bad"}

        with patch("pipeline.orchestrator.writers.bo_laksana._fetch_all_facts", return_value=[fake_fact]):
            with patch("pipeline.orchestrator.writers.bo_laksana._build_strength_lookup", return_value={}):
                with patch("pipeline.orchestrator.writers.bo_laksana._build_dignity_lookup", return_value={}):
                    with patch("pipeline.orchestrator.writers.bo_laksana._build_av_lookup", return_value={}):
                        with patch("pipeline.orchestrator.writers.bo_laksana._build_signal_row",
                                   side_effect=ValueError("bad row")):
                            with pytest.raises(RuntimeError, match="all .* facts were skipped"):
                                writer.run_substep(ctx, step)

    def test_dry_run_does_not_raise(self):
        """Dry run must still return silently even with 0 facts (no real insert)."""
        from pipeline.orchestrator.writers.bo_laksana import BoLaksanaWriter

        writer = BoLaksanaWriter()
        ctx    = _make_ctx(dry_run=True)
        step   = SubStep(key="aya_lahiri", label="bo_laksana — lahiri")

        with patch("pipeline.orchestrator.writers.bo_laksana._fetch_all_facts", return_value=[]):
            result = writer.run_substep(ctx, step)
        assert result.rows_inserted == 0


# ── §G3-2 bo_bimba: empty MSR signals → RuntimeError ─────────────────────────
# RED: returned WriterResult(rows_inserted=28, all at default strength 0.5) silently
# GREEN: raises RuntimeError — 0 MSR signals means bo_laksana failed upstream

class TestBoBimbaLoudFail:
    def test_empty_msr_signals_raises(self):
        """
        GREEN: bodha_msr_signals returns 0 rows for this ayanamsha →
        RuntimeError instead of silently building nodes with all-default strength.
        """
        from pipeline.orchestrator.writers.bo_bimba import BoBimbaWriter

        writer = BoBimbaWriter()
        ctx    = _make_ctx()

        with patch("pipeline.orchestrator.writers.bo_bimba._fetch_msr_signals", return_value=[]):
            with pytest.raises(RuntimeError, match="bodha_msr_signals is empty"):
                writer.run(ctx)

    def test_dry_run_does_not_raise(self):
        """Dry run with 0 signals logs and returns without raising."""
        from pipeline.orchestrator.writers.bo_bimba import BoBimbaWriter

        writer = BoBimbaWriter()
        ctx    = _make_ctx(dry_run=True)

        with patch("pipeline.orchestrator.writers.bo_bimba._fetch_msr_signals", return_value=[]):
            result = writer.run(ctx)
        assert result.rows_inserted == 0


# ── §G3-3 bo_karanajala: empty node_map → RuntimeError ───────────────────────
# RED: returned WriterResult(edges=0, contradictions=0) silently when node_map={}
# GREEN: raises RuntimeError — node_map empty means bo_bimba produced 0 CGM nodes

class TestBoKaranajalaLoudFail:
    def test_empty_node_map_raises(self):
        """
        GREEN: bodha_cgm_nodes returns 0 nodes for this chart/aya →
        RuntimeError before trying to build 0 edges.
        """
        from pipeline.orchestrator.writers.bo_karanajala import BoKaranajalaWriter

        writer = BoKaranajalaWriter()
        ctx    = _make_ctx()

        with patch("pipeline.orchestrator.writers.bo_karanajala._fetch_signals", return_value=[{"signal_id": "s1"}]):
            with patch("pipeline.orchestrator.writers.bo_karanajala._fetch_node_map", return_value={}):
                with pytest.raises(RuntimeError, match="node_map is empty"):
                    writer.run(ctx)

    def test_dry_run_with_empty_node_map_does_not_raise(self):
        """Dry run skips the guard (it just logs the counts)."""
        from pipeline.orchestrator.writers.bo_karanajala import BoKaranajalaWriter

        writer = BoKaranajalaWriter()
        ctx    = _make_ctx(dry_run=True)

        with patch("pipeline.orchestrator.writers.bo_karanajala._fetch_signals", return_value=[]):
            with patch("pipeline.orchestrator.writers.bo_karanajala._fetch_node_map", return_value={}):
                result = writer.run(ctx)
        assert result.rows_inserted == 0


# ── §G3-4 bo_upaya: 0 prescriptions → RuntimeError ──────────────────────────
# RED: returned WriterResult(rows_inserted=resonances_only) silently with 0 prescriptions
# GREEN: raises RuntimeError — 0 prescriptions means brahma_remedy_corpus is empty

class TestBoUpayaLoudFail:
    def test_zero_prescriptions_raises(self):
        """
        GREEN: _build_resonances_and_prescriptions returns (resonances, []) for all
        ayanamshas → RuntimeError after the loop instead of silent 0-prescription success.
        """
        from pipeline.orchestrator.writers.bo_upaya import BoUpayaWriter

        writer = BoUpayaWriter()
        ctx    = _make_ctx()

        fake_resonance = {"resonance_id": "r1", "chart_id": "test-chart-001"}

        def _realistic_batch_insert(conn, rows, sql):
            return len(rows)  # 0 prescriptions → 0 inserted

        with patch("pipeline.orchestrator.writers.bo_upaya._build_resonances_and_prescriptions",
                   return_value=([fake_resonance], [])):  # prescriptions=[] → 0
            with patch("pipeline.orchestrator.writers.bo_upaya._batch_insert",
                       side_effect=_realistic_batch_insert):
                with patch("pipeline.orchestrator.writers.bo_upaya._strip_private_keys",
                           return_value=[fake_resonance]):
                    with patch("bodha_writers._idempotency.replace_prior_rm_resonances", return_value=0):
                        with patch("bodha_writers._idempotency.replace_prior_rm_prescriptions", return_value=0):
                            with pytest.raises(RuntimeError, match="0 remedy prescriptions written"):
                                writer.run(ctx)

    def test_dry_run_does_not_raise(self):
        """Dry run skips all body execution and does not raise."""
        from pipeline.orchestrator.writers.bo_upaya import BoUpayaWriter

        writer = BoUpayaWriter()
        ctx    = _make_ctx(dry_run=True)

        result = writer.run(ctx)
        assert result.rows_inserted == 0


# ── §G3-5 bo_samskara: signals > 0 but 0 embeddings → RuntimeError ──────────
# RED: _batch_insert returned 0 on all-Vertex-fail; writer silently returned 0
# GREEN: raises RuntimeError — signals seen but 0 embeddings = Vertex total failure

class TestBoSamskaraLoudFail:
    def test_signals_present_but_zero_embeddings_raises(self):
        """
        GREEN: signals > 0 but _batch_insert writes 0 embeddings →
        RuntimeError instead of silently succeeding with empty embeddings table.
        """
        from pipeline.orchestrator.writers.bo_samskara import BoSamskaraWriter

        writer = BoSamskaraWriter()
        ctx    = _make_ctx()

        fake_signal = {
            "signal_id": "s1", "signal_type_id": "graha_position",
            "primary_graha": "Sun", "signal_tier": "A",
            "signal_domain": "career", "signal_polarity": "positive",
            "signal_strength_normalized": 0.8, "signal_label": "Sun strong",
        }

        with patch("pipeline.orchestrator.writers.bo_samskara._fetch_signals",
                   return_value=[fake_signal]):
            with patch("pipeline.orchestrator.writers.bo_samskara._embed_batch",
                       return_value=[[0.1] * 768]):
                with patch("pipeline.orchestrator.writers.bo_samskara._batch_insert", return_value=0):
                    with patch("bodha_writers._idempotency.replace_prior_signal_embeddings", return_value=0):
                        with pytest.raises(RuntimeError, match="0 embeddings written"):
                            writer.run(ctx)

    def test_zero_signals_does_not_raise(self):
        """0 signals → 0 embeddings is fine (upstream just produced nothing yet)."""
        from pipeline.orchestrator.writers.bo_samskara import BoSamskaraWriter

        writer = BoSamskaraWriter()
        ctx    = _make_ctx()

        with patch("pipeline.orchestrator.writers.bo_samskara._fetch_signals", return_value=[]):
            result = writer.run(ctx)
        assert result.rows_inserted == 0

    def test_dry_run_does_not_raise(self):
        from pipeline.orchestrator.writers.bo_samskara import BoSamskaraWriter

        writer = BoSamskaraWriter()
        ctx    = _make_ctx(dry_run=True)

        with patch("pipeline.orchestrator.writers.bo_samskara._fetch_signals", return_value=[{"signal_id": "s1"}]):
            result = writer.run(ctx)
        assert result.rows_inserted == 0


# ── §G3-6 bo_drishti: all lenses fail → RuntimeError ────────────────────────
# RED: per-lens exception logged as warning; total=0; WriterResult returned silently
# GREEN: raises RuntimeError when 0 lenses produced across all ayanamshas

class TestBoDrishtiLoudFail:
    def test_all_lenses_fail_raises(self):
        """
        GREEN: every _build_lens call raises, total=0 across all ayanamshas →
        RuntimeError instead of silent 0-lens success.
        """
        from pipeline.orchestrator.writers.bo_drishti import BoDrishtiWriter

        writer = BoDrishtiWriter()
        ctx    = _make_ctx()

        with patch("pipeline.orchestrator.writers.bo_drishti._build_lens",
                   side_effect=RuntimeError("db empty")):
            with pytest.raises(RuntimeError, match="0 question-lenses produced"):
                writer.run(ctx)

    def test_partial_failure_does_not_raise(self):
        """If at least one lens succeeds, do not raise (partial coverage allowed)."""
        from pipeline.orchestrator.writers.bo_drishti import BoDrishtiWriter, QUESTION_TYPE_CONFIG

        writer = BoDrishtiWriter()
        ctx    = _make_ctx()

        call_count = [0]
        def _flaky_build(conn, chart_id, aya, build_id, now, qt, cfg):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                raise RuntimeError("flaky")
            return {"lens_id": "l1", "chart_id": chart_id, "ayanamsha_id": aya,
                    "build_id": build_id, "question_type": qt,
                    "lens_formula_version": "1.0", "lens_template_version": "1.0",
                    "points_only_assertion": True, "created_at": "2026-01-01"}

        with patch("pipeline.orchestrator.writers.bo_drishti._build_lens", side_effect=_flaky_build):
            with patch("pipeline.orchestrator.writers.bo_drishti._batch_insert", return_value=3):
                result = writer.run(ctx)
        assert result.rows_inserted > 0


# ── §G3-7 bo_pramana_mapa: msr_count=0 → RuntimeError ───────────────────────
# RED: proceeded to build scorecard with 0/None pct fields; MV refresh ran on empty tables
# GREEN: raises RuntimeError immediately after detecting 0 MSR signals

class TestBoPramanaMapaLoudFail:
    def test_zero_msr_signals_raises(self):
        """
        GREEN: bodha_msr_signals count = 0 for this chart →
        RuntimeError before writing a meaningless scorecard.
        """
        from pipeline.orchestrator.writers.bo_pramana_mapa import BoPramanaMapa

        writer = BoPramanaMapa()
        ctx    = _make_ctx()

        def _count_router(conn, sql, params):
            if "bodha_msr_signals" in sql and "verification_pass_status" not in sql and "constituent_facts_array" not in sql:
                return 0  # msr_count = 0 → triggers the guard
            return 10

        with patch("pipeline.orchestrator.writers.bo_pramana_mapa._count_one", side_effect=_count_router):
            with pytest.raises(RuntimeError, match="bodha_msr_signals is empty"):
                writer.run(ctx)

    def test_nonzero_msr_does_not_raise_at_guard(self):
        """When msr_count > 0, the guard does not fire (writer may still fail later)."""
        from pipeline.orchestrator.writers.bo_pramana_mapa import BoPramanaMapa

        writer = BoPramanaMapa()
        ctx    = _make_ctx()

        with patch("pipeline.orchestrator.writers.bo_pramana_mapa._count_one", return_value=100):
            with patch("pipeline.orchestrator.writers.bo_pramana_mapa._formula_version", return_value=None):
                with patch("bodha_writers._idempotency.replace_prior_scorecard", return_value=None):
                    with patch("pipeline.orchestrator.writers.bo_pramana_mapa._refresh_mv", return_value=None):
                        ctx.db_conn.execute.return_value = None
                        # Should not raise at the msr_count guard — may raise later on scorecard insert
                        # which is fine; we only test the guard itself
                        try:
                            writer.run(ctx)
                        except RuntimeError as e:
                            assert "bodha_msr_signals is empty" not in str(e), \
                                "guard fired on non-zero msr_count — unexpected"
                        except Exception:
                            pass  # Other failures (e.g. mock DB insert) are expected

    def test_dry_run_does_not_reach_guard(self):
        """Dry run returns before the guard is checked."""
        from pipeline.orchestrator.writers.bo_pramana_mapa import BoPramanaMapa

        writer = BoPramanaMapa()
        ctx    = _make_ctx(dry_run=True)

        result = writer.run(ctx)
        assert result.rows_inserted == 0


# ── §G5 bo_pramana_mapa: all 8 MVs refreshed ─────────────────────────────────
# Before G5: only 3 MVs were refreshed (mv_msr_*); 5 CDLM MVs were never refreshed.
# After G5: all 8 MVs are refreshed every time pramana_mapa runs.

EXPECTED_MVS = [
    "mv_msr_top_signals_per_chart",
    "mv_msr_recurring_patterns_per_chart",
    "mv_msr_domain_summary",
    "mv_cdlm_static_summary",
    "mv_cdlm_top_K_links_per_chart",
    "mv_cdlm_per_tradition_summary",
    "mv_cdlm_dasha_window_lookup",
    "mv_cdlm_pattern_summary",
]


class TestG5AllMVsRefreshed:
    def test_all_8_mvs_are_refreshed_after_rebuild(self):
        """
        GREEN: after a successful pramana_mapa run, _refresh_mv is called exactly
        once for each of the 8 expected MV names — no CDLM MVs silently skipped.
        """
        from pipeline.orchestrator.writers.bo_pramana_mapa import BoPramanaMapa

        writer = BoPramanaMapa()
        ctx    = _make_ctx()

        refreshed: list[str] = []

        def _capture_refresh(conn, mv_name):
            refreshed.append(mv_name)

        with patch("pipeline.orchestrator.writers.bo_pramana_mapa._count_one", return_value=100):
            with patch("pipeline.orchestrator.writers.bo_pramana_mapa._formula_version", return_value=None):
                with patch("bodha_writers._idempotency.replace_prior_scorecard", return_value=None):
                    with patch("pipeline.orchestrator.writers.bo_pramana_mapa._refresh_mv",
                               side_effect=_capture_refresh):
                        try:
                            writer.run(ctx)
                        except Exception:
                            pass  # scorecard insert may fail on mock conn — we only test MV refreshes

        assert len(refreshed) == 8, f"Expected 8 MV refreshes, got {len(refreshed)}: {refreshed}"
        for mv in EXPECTED_MVS:
            assert mv in refreshed, f"MV not refreshed: {mv}"

    def test_cdlm_mvs_included_in_refresh_list(self):
        """Verify the 5 CDLM MVs appear in the refresh loop (static inspection)."""
        import pipeline.orchestrator.writers.bo_pramana_mapa as module
        import inspect

        source = inspect.getsource(module)
        for mv in EXPECTED_MVS:
            assert mv in source, f"MV name missing from bo_pramana_mapa source: {mv}"
