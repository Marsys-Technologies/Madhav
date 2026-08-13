"""
tests/ka_kshetra/test_optn1_dhara_stage5_wiring.py — OPT-N1 wiring tests (TDD).

Mandatory tests for SM-Δ1 OPT-N1: dhara_compute_null wired into stage-5
analytic path and _RESUME_VERSION bumped 4→5.

Tests are pure-Python; no database, no DB fixture, no real chart data.
"""
from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pytest

import services.ka_kshetra.writer as _writer_module
from services.ka_kshetra import writer as W
from services.ka_kshetra.writer import KaKshetraWriter
from services.ka_kshetra.dhara_null import DEFAULT_REPLICATES as DN_DEFAULT_REPLICATES
from services.ka_kshetra.dhara_null import NullResult
from services.ka_kshetra.stage5_null import DURATION_BUCKETS


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_null_result(replicates: int = DN_DEFAULT_REPLICATES) -> NullResult:
    """Minimal synthetic NullResult for wiring tests."""
    return NullResult(
        replicates=replicates,
        shift_count=replicates - 1,
        horizon_days=36525.0,
        shift_grid_step=36525.0 / replicates,
        q_threshold=0.5,
        max_stats={int(b): [0.1] * (replicates - 1) for b in DURATION_BUCKETS},
        alpha=0.05,
    )


def _make_writer_instance() -> KaKshetraWriter:
    """Return a KaKshetraWriter with plan_substeps NOT called (avoids DB).

    Sets the minimum instance state needed for the tests that inspect
    _RESUME_VERSION and plan-level behaviour.
    """
    # KaKshetraWriter.__init__ is WriterBase.__init__ (no-op besides self._ctx).
    # plan_substeps is where all the real setup happens. We skip it here to
    # avoid needing a real DB connection — each test patches what it needs.
    obj = object.__new__(KaKshetraWriter)
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: plan_substeps emits stage5dhara:{ec} under ENGINE_VERSION=='analytic'
# ─────────────────────────────────────────────────────────────────────────────

class TestPlanSubstepsAnalyticEmitsStage5Dhara:
    """Under ENGINE_VERSION='analytic', plan_substeps must emit stage5dhara:*
    keys and must NOT emit stage5:*:* or stage5finalize:* keys."""

    def _call_plan_substeps(self, engine_version: str, event_classes=None):
        """Call plan_substeps with a minimal mocked context and DB."""
        if event_classes is None:
            event_classes = ['CAREER', 'HEALTH']

        writer = _make_writer_instance()

        # Minimal mock context
        ctx = MagicMock()
        ctx.db_conn = MagicMock()
        ctx.config = MagicMock()
        ctx.config.chart_id = 'test-chart-id'

        # Patch all the helper methods that require real DB data
        with patch.object(KaKshetraWriter, '_load_birth_instant', return_value=('1984-02-05', '10:43:00')), \
             patch.object(KaKshetraWriter, '_corpus_pin', return_value='corpuspin'), \
             patch.object(KaKshetraWriter, '_gochara_corpus_pin', return_value={}), \
             patch('services.ka_kshetra.stage4_field.resolve_weights_pin',
                   return_value=('w-v1', {})), \
             patch.object(KaKshetraWriter, '_discover_event_classes',
                          return_value=event_classes), \
             patch.object(KaKshetraWriter, '_optional_stage_plugins', return_value=[]), \
             patch.object(KaKshetraWriter, '_load_completed_substeps', return_value=None), \
             patch.object(KaKshetraWriter, '_delete_prior_rows'), \
             patch('services.ka_kshetra.engine_config.ENGINE_VERSION', engine_version), \
             patch('services.ka_kshetra.writer.S4.resolve_weights_pin',
                   return_value=('w-v1', {})):
            steps = writer.plan_substeps(ctx)

        return steps

    def test_analytic_emits_stage5dhara_keys(self):
        steps = self._call_plan_substeps('analytic', event_classes=['CAREER'])
        keys = [s.key for s in steps]
        assert any(k == 'stage5dhara:CAREER' for k in keys), (
            f'Expected stage5dhara:CAREER in substep keys, got: {keys}'
        )

    def test_analytic_does_not_emit_stage5_block_keys(self):
        steps = self._call_plan_substeps('analytic', event_classes=['CAREER'])
        keys = [s.key for s in steps]
        block_keys = [k for k in keys if k.startswith('stage5:CAREER:')]
        assert not block_keys, (
            f'stage5:CAREER:* block keys must not appear under analytic, got: {block_keys}'
        )

    def test_analytic_does_not_emit_stage5finalize_keys(self):
        steps = self._call_plan_substeps('analytic', event_classes=['CAREER'])
        keys = [s.key for s in steps]
        finalize_keys = [k for k in keys if k.startswith('stage5finalize:CAREER')]
        assert not finalize_keys, (
            f'stage5finalize:CAREER must not appear under analytic, got: {finalize_keys}'
        )

    def test_analytic_emits_one_dhara_substep_per_event_class(self):
        ecs = ['CAREER', 'HEALTH', 'WEALTH']
        steps = self._call_plan_substeps('analytic', event_classes=ecs)
        keys = [s.key for s in steps]
        for ec in ecs:
            assert f'stage5dhara:{ec}' in keys, (
                f'Expected stage5dhara:{ec} in keys: {keys}'
            )

    def test_analytic_dhara_substep_has_meaningful_label(self):
        steps = self._call_plan_substeps('analytic', event_classes=['CAREER'])
        dhara_steps = [s for s in steps if s.key == 'stage5dhara:CAREER']
        assert len(dhara_steps) == 1
        label = dhara_steps[0].label
        assert 'dhara' in label.lower() or '1024' in label, (
            f'Expected dhara/1024 in label, got: {label!r}'
        )

    def test_analytic_still_emits_stage6_stage65_stage8_snapshot(self):
        """Downstream stages must be present regardless of null engine choice."""
        steps = self._call_plan_substeps('analytic', event_classes=['CAREER'])
        keys = [s.key for s in steps]
        assert 'stage6' in keys
        assert 'stage65' in keys
        assert 'snapshot' in keys
        assert any(k.startswith('stage8:') for k in keys)


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: plan_substeps emits legacy stage5:*:* blocks under 'sampled'
# ─────────────────────────────────────────────────────────────────────────────

class TestPlanSubstepsSampledEmitsStage5Blocks:
    """Under ENGINE_VERSION='sampled', the legacy block+finalize path is used."""

    def _call_plan_substeps_sampled(self, event_classes=None):
        if event_classes is None:
            event_classes = ['CAREER']

        writer = _make_writer_instance()
        ctx = MagicMock()
        ctx.db_conn = MagicMock()
        ctx.config = MagicMock()
        ctx.config.chart_id = 'test-chart-id'

        with patch.object(KaKshetraWriter, '_load_birth_instant', return_value=('1984-02-05', '10:43:00')), \
             patch.object(KaKshetraWriter, '_corpus_pin', return_value='corpuspin'), \
             patch.object(KaKshetraWriter, '_gochara_corpus_pin', return_value={}), \
             patch('services.ka_kshetra.stage4_field.resolve_weights_pin',
                   return_value=('w-v1', {})), \
             patch.object(KaKshetraWriter, '_discover_event_classes',
                          return_value=event_classes), \
             patch.object(KaKshetraWriter, '_optional_stage_plugins', return_value=[]), \
             patch.object(KaKshetraWriter, '_load_completed_substeps', return_value=None), \
             patch.object(KaKshetraWriter, '_delete_prior_rows'), \
             patch('services.ka_kshetra.engine_config.ENGINE_VERSION', 'sampled'), \
             patch('services.ka_kshetra.writer.S4.resolve_weights_pin',
                   return_value=('w-v1', {})):
            steps = writer.plan_substeps(ctx)

        return steps

    def test_sampled_emits_stage5_block_1(self):
        steps = self._call_plan_substeps_sampled(event_classes=['CAREER'])
        keys = [s.key for s in steps]
        assert 'stage5:CAREER:1' in keys, (
            f'Expected stage5:CAREER:1 in sampled keys, got: {keys}'
        )

    def test_sampled_emits_stage5finalize(self):
        steps = self._call_plan_substeps_sampled(event_classes=['CAREER'])
        keys = [s.key for s in steps]
        assert 'stage5finalize:CAREER' in keys, (
            f'Expected stage5finalize:CAREER in sampled keys, got: {keys}'
        )

    def test_sampled_does_not_emit_stage5dhara(self):
        steps = self._call_plan_substeps_sampled(event_classes=['CAREER'])
        keys = [s.key for s in steps]
        dhara_keys = [k for k in keys if k.startswith('stage5dhara:')]
        assert not dhara_keys, (
            f'stage5dhara:* must not appear under sampled, got: {dhara_keys}'
        )


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: _RESUME_VERSION == 5
# ─────────────────────────────────────────────────────────────────────────────

class TestResumeVersionIs5:
    """_RESUME_VERSION must be 5 (FM-17: substep keys changed, fingerprint must change)."""

    def test_resume_version_is_5(self):
        assert W._RESUME_VERSION == 5, (
            f'_RESUME_VERSION must be 5 (FM-17 requirement for OPT-N1), '
            f'got {W._RESUME_VERSION!r}'
        )

    def test_resume_version_is_int(self):
        assert isinstance(W._RESUME_VERSION, int)


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: run_substep routes stage5dhara:{ec} to _run_stage5dhara
# ─────────────────────────────────────────────────────────────────────────────

class TestRunStage5DharaRouting:
    """run_substep must route stage5dhara:* to _run_stage5dhara."""

    def test_run_substep_dispatches_stage5dhara(self):
        """run_substep('stage5dhara:CAREER') calls _run_stage5dhara."""
        writer = _make_writer_instance()
        # Minimal instance state needed by run_substep dispatch
        writer._plugin_stages = []

        ctx = MagicMock()
        ctx.db_conn = MagicMock()

        from pipeline.orchestrator.writers import SubStep
        step = SubStep(key='stage5dhara:CAREER', label='dhara null+windows CAREER')

        called_with = {}

        def fake_run_stage5dhara(conn, ec, step_arg):
            called_with['conn'] = conn
            called_with['ec'] = ec
            called_with['step'] = step_arg
            from pipeline.orchestrator.writers import WriterResult
            return WriterResult(asset_id='ka_kshetra', rows_inserted=7)

        with patch.object(writer, '_run_stage5dhara', side_effect=fake_run_stage5dhara):
            result = writer.run_substep(ctx, step)

        assert called_with.get('ec') == 'CAREER', (
            f"Expected ec='CAREER', got {called_with.get('ec')!r}"
        )
        assert called_with.get('step') is step
        assert result.rows_inserted == 7


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: _run_stage5dhara calls dhara_compute_null with replicates=1024
# ─────────────────────────────────────────────────────────────────────────────

class TestRunStage5DharaCallsDharaComputeNull:
    """_run_stage5dhara must call dhara_compute_null(ev, replicates=1024)."""

    def _make_minimal_writer(self):
        """Return a writer with the minimum instance state for _run_stage5dhara."""
        writer = _make_writer_instance()
        writer._chart_id = 'test-chart-uuid'
        writer._dry_run = True   # skip all DB writes; pure logic test
        writer._weights_version = 'w-v1'
        writer._snapshot_id = 'snap-test'
        writer._skipped = []
        writer._coverage_notes = []
        return writer

    def test_dhara_compute_null_called_with_1024_replicates(self):
        """_run_stage5dhara must call dhara_compute_null(ev, replicates=1024)."""
        writer = self._make_minimal_writer()

        # Build a minimal mock evaluator
        ev = MagicMock()
        ev.horizon_days = 36525.0
        ev.lifetime_count = 100
        ev.promise = MagicMock()
        ev.promise.p = 0.5
        ev.promise.routes = []
        ev.build_segments.return_value = [MagicMock(
            t_start=0.0, t_end=36525.0,
            alpha=-5.0, gamma=0.0,
            refinement_depth=0, refinement_exhausted=False, refinement_residual=None,
        )]

        # Mock class context
        mock_cctx = MagicMock()
        mock_cctx.evaluator = ev
        mock_cctx.temporal_shape = 'periodic'

        # Synthetic NullResult
        null_result = _make_null_result()

        # Minimal window mock
        mock_window = MagicMock()
        mock_window.t_start = 100.0
        mock_window.t_end = 200.0
        mock_window.t_peak = 150.0
        mock_window.lambda_peak = 0.01
        mock_window.expected_count = 0.5
        mock_window.duration_days = 100.0

        from pipeline.orchestrator.writers import SubStep
        step = SubStep(key='stage5dhara:CAREER', label='dhara null+windows CAREER')

        dhara_calls = []

        def fake_dhara_compute_null(ev_arg, replicates):
            dhara_calls.append({'ev': ev_arg, 'replicates': replicates})
            return null_result

        with patch.object(writer, '_require_stage4_committed'), \
             patch.object(writer, '_class_context', return_value=mock_cctx), \
             patch('services.ka_kshetra.writer.DN.dhara_compute_null',
                   side_effect=fake_dhara_compute_null), \
             patch('services.ka_kshetra.integrator.find_windows',
                   return_value=[mock_window]), \
             patch('services.ka_kshetra.stage5_null.adrishta_residual',
                   return_value=0.0), \
             patch.object(writer, '_kinematics_ayanamsha_ids', return_value=set()), \
             patch.object(writer, '_sigma_t_days', return_value=None), \
             patch('services.ka_kshetra.stage4_field.load_legacy_crosscheck',
                   return_value=[]), \
             patch.object(writer, '_write_windows_batch', return_value=3):
            result = writer._run_stage5dhara(MagicMock(), 'CAREER', step)

        assert len(dhara_calls) == 1, (
            f'Expected dhara_compute_null called once, called {len(dhara_calls)} times'
        )
        assert dhara_calls[0]['replicates'] == DN_DEFAULT_REPLICATES, (
            f"Expected replicates={DN_DEFAULT_REPLICATES}, "
            f"got {dhara_calls[0]['replicates']!r}"
        )
        assert dhara_calls[0]['ev'] is ev

    def test_run_stage5dhara_returns_writer_result_with_rows(self):
        """_run_stage5dhara returns WriterResult with rows_inserted > 0
        when _write_windows_batch returns rows."""
        writer = self._make_minimal_writer()

        ev = MagicMock()
        ev.horizon_days = 36525.0
        ev.lifetime_count = 100
        ev.promise = MagicMock()
        ev.promise.p = 0.5
        ev.promise.routes = []
        ev.build_segments.return_value = [MagicMock(
            t_start=0.0, t_end=36525.0, alpha=-5.0, gamma=0.0,
            refinement_depth=0, refinement_exhausted=False, refinement_residual=None,
        )]

        mock_cctx = MagicMock()
        mock_cctx.evaluator = ev
        mock_cctx.temporal_shape = 'periodic'

        null_result = _make_null_result()

        mock_window = MagicMock()
        mock_window.t_start = 100.0
        mock_window.t_end = 200.0
        mock_window.t_peak = 150.0
        mock_window.lambda_peak = 0.01
        mock_window.expected_count = 0.5
        mock_window.duration_days = 100.0

        from pipeline.orchestrator.writers import SubStep
        step = SubStep(key='stage5dhara:CAREER', label='dhara null+windows CAREER')

        with patch.object(writer, '_require_stage4_committed'), \
             patch.object(writer, '_class_context', return_value=mock_cctx), \
             patch('services.ka_kshetra.writer.DN.dhara_compute_null',
                   return_value=null_result), \
             patch('services.ka_kshetra.integrator.find_windows',
                   return_value=[mock_window]), \
             patch('services.ka_kshetra.stage5_null.adrishta_residual',
                   return_value=0.0), \
             patch.object(writer, '_kinematics_ayanamsha_ids', return_value=set()), \
             patch.object(writer, '_sigma_t_days', return_value=None), \
             patch('services.ka_kshetra.stage4_field.load_legacy_crosscheck',
                   return_value=[]), \
             patch.object(writer, '_write_windows_batch', return_value=5):
            result = writer._run_stage5dhara(MagicMock(), 'CAREER', step)

        from pipeline.orchestrator.writers import WriterResult
        assert isinstance(result, WriterResult)
        assert result.rows_inserted == 5   # dry_run=True: _write_windows_batch returns 5

    def test_run_stage5dhara_dry_run_passes_without_db_writes(self):
        """In dry_run=True mode, _run_stage5dhara must not write to DB."""
        writer = self._make_minimal_writer()
        writer._dry_run = True

        ev = MagicMock()
        ev.horizon_days = 36525.0
        ev.lifetime_count = 100
        ev.promise = MagicMock()
        ev.promise.p = 0.5
        ev.promise.routes = []
        ev.build_segments.return_value = []   # no segments (dry_run path)

        mock_cctx = MagicMock()
        mock_cctx.evaluator = ev
        mock_cctx.temporal_shape = 'periodic'

        null_result = _make_null_result()

        from pipeline.orchestrator.writers import SubStep
        step = SubStep(key='stage5dhara:CAREER', label='dhara null+windows CAREER')

        conn = MagicMock()

        # ev.build_segments() returns [] which triggers UpstreamStageIncomplete.
        # Use non-empty segments to ensure we reach the result.
        ev.build_segments.return_value = [MagicMock(
            t_start=0.0, t_end=36525.0, alpha=-5.0, gamma=0.0,
            refinement_depth=0, refinement_exhausted=False, refinement_residual=None,
        )]

        with patch.object(writer, '_require_stage4_committed'), \
             patch.object(writer, '_class_context', return_value=mock_cctx), \
             patch('services.ka_kshetra.writer.DN.dhara_compute_null',
                   return_value=null_result), \
             patch('services.ka_kshetra.integrator.find_windows', return_value=[]), \
             patch('services.ka_kshetra.stage5_null.adrishta_residual', return_value=0.0), \
             patch.object(writer, '_kinematics_ayanamsha_ids', return_value=set()), \
             patch.object(writer, '_sigma_t_days', return_value=None), \
             patch('services.ka_kshetra.stage4_field.load_legacy_crosscheck', return_value=[]), \
             patch.object(writer, '_write_windows_batch', return_value=0):
            result = writer._run_stage5dhara(conn, 'CAREER', step)

        # Must not have called conn.cursor() for DB writes
        conn.cursor.assert_not_called()

        from pipeline.orchestrator.writers import WriterResult
        assert isinstance(result, WriterResult)
        assert result.asset_id == 'ka_kshetra'
