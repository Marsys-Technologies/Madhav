"""
tests/ka_kshetra/test_dhara_term_matrix.py — TDD suite for dhara_term_matrix.py

Tests are written against the DHARA DESIGN v1.1 spec (section 4, Appendix C.3,
F-06 + F-14 amendments).  They are deliberately independent of any running DB or
evaluator — every input is synthetic, constructed here from first principles.

Test plan:
  1. TermMatrixRow construction + field access
  2. build_term_matrix — shape, column order, dtype
  3. build_term_matrix — column_ids follow spec conventions
  4. save_term_matrix — .npz round-trip (all fields present + correct)
  5. F-06/F-14 — raw_u_matrix and rho_values present and correct dtype/shape
  6. refit_from_term_matrix — beta refit (mod:* columns)
  7. refit_from_term_matrix — rho refit (sup:* columns via raw_u_matrix)
  8. refit_from_term_matrix — output Segment alpha/gamma values correct
  9. refit_from_term_matrix — no-op refit (same weights) reproduces original segments
  10. rho refit correctness: ln(1-rho_new*u) computed from raw_u, not from stored log term
"""
from __future__ import annotations

import math
import os
import tempfile

import numpy as np
import pytest

from services.ka_kshetra.dhara_term_matrix import (
    TermMatrixRow,
    build_term_matrix,
    build_term_matrix_row,
    refit_from_term_matrix,
    save_term_matrix,
)
from services.ka_kshetra.hazard import COVARIATE_KEYS


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_row(
    *,
    baseline: float = -6.0,
    promise: float = -1.0,
    clock_terms: list[float] | None = None,
    clock_ids: list[str] | None = None,
    modifier_terms: list[float] | None = None,
    modifier_ids: list[str] | None = None,
    suppression_log_terms: list[float] | None = None,
    suppression_ids: list[str] | None = None,
    raw_u_values: list[float] | None = None,
    rho_values: list[float] | None = None,
) -> TermMatrixRow:
    """Build a synthetic TermMatrixRow for testing."""
    # Defaults: 2 clock systems, 12 covariates (zeroed), 2 vighnas
    if clock_terms is None:
        clock_terms = [0.10, -0.05]
    if clock_ids is None:
        clock_ids = ['clock:vimshottari', 'clock:chara']
    if modifier_terms is None:
        modifier_terms = [0.0] * 12
    if modifier_ids is None:
        modifier_ids = [f'mod:x{i+1}_{key}' for i, key in enumerate(COVARIATE_KEYS)]
    if suppression_log_terms is None:
        suppression_log_terms = [math.log1p(-0.5 * 0.3), math.log1p(-0.4 * 0.2)]
    if suppression_ids is None:
        suppression_ids = ['sup:vedha:Sa->10', 'sup:ashtakavarga_deficit:Ju->7']
    if raw_u_values is None:
        raw_u_values = [0.3, 0.2]
    if rho_values is None:
        rho_values = [0.5, 0.4]
    return TermMatrixRow(
        baseline=baseline,
        promise=promise,
        clock_terms=clock_terms,
        clock_ids=clock_ids,
        modifier_terms=modifier_terms,
        modifier_ids=modifier_ids,
        suppression_log_terms=suppression_log_terms,
        suppression_ids=suppression_ids,
        raw_u_values=raw_u_values,
        rho_values=rho_values,
    )


def _make_rows(K: int = 5, **kwargs) -> list[TermMatrixRow]:
    """Build K identical synthetic rows."""
    return [_make_row(**kwargs) for _ in range(K)]


# ── 1. TermMatrixRow construction ────────────────────────────────────────────

class TestTermMatrixRow:
    def test_fields_accessible(self):
        row = _make_row(baseline=-7.0, promise=-2.0)
        assert row.baseline == pytest.approx(-7.0)
        assert row.promise == pytest.approx(-2.0)
        assert len(row.clock_terms) == 2
        assert len(row.modifier_terms) == 12
        assert len(row.suppression_log_terms) == 2
        assert len(row.raw_u_values) == 2
        assert len(row.rho_values) == 2

    def test_clock_ids_follow_convention(self):
        row = _make_row()
        for cid in row.clock_ids:
            assert cid.startswith('clock:'), f"Expected 'clock:' prefix, got {cid!r}"

    def test_modifier_ids_follow_convention(self):
        row = _make_row()
        for mid in row.modifier_ids:
            assert mid.startswith('mod:'), f"Expected 'mod:' prefix, got {mid!r}"

    def test_suppression_ids_follow_convention(self):
        row = _make_row()
        for sid in row.suppression_ids:
            assert sid.startswith('sup:'), f"Expected 'sup:' prefix, got {sid!r}"

    def test_lengths_consistent(self):
        row = _make_row()
        assert len(row.clock_terms) == len(row.clock_ids)
        assert len(row.modifier_terms) == len(row.modifier_ids)
        assert len(row.suppression_log_terms) == len(row.suppression_ids)
        assert len(row.raw_u_values) == len(row.suppression_ids)
        assert len(row.rho_values) == len(row.suppression_ids)


# ── 2. build_term_matrix — shape ─────────────────────────────────────────────

class TestBuildTermMatrixShape:
    def test_shape(self):
        K = 7
        rows = _make_rows(K)
        knot_times = np.linspace(0.0, 100.0, K, dtype=np.float64)
        term_matrix, column_ids, raw_u_matrix, rho_values_arr = build_term_matrix(
            knot_times, rows
        )
        S = 2   # clock systems
        V = 2   # vighnas
        T = 2 + S + 12 + V
        assert term_matrix.shape == (K, T), (
            f"Expected [{K}, {T}], got {term_matrix.shape}"
        )
        assert term_matrix.dtype == np.float64
        assert len(column_ids) == T
        assert raw_u_matrix.shape == (K, V)
        assert raw_u_matrix.dtype == np.float32
        assert rho_values_arr.shape == (V,)
        assert rho_values_arr.dtype == np.float32

    def test_column_count_formula(self):
        """T = 2 + S + 12 + V, for varying S and V."""
        for S, V in [(3, 4), (5, 2), (1, 8)]:
            clock_terms = [0.1] * S
            clock_ids = [f'clock:sys{i}' for i in range(S)]
            sup_terms = [math.log1p(-0.3 * 0.2)] * V
            sup_ids = [f'sup:vighna{i}:X->Y' for i in range(V)]
            raw_u = [0.2] * V
            rho = [0.3] * V
            rows = [
                _make_row(
                    clock_terms=clock_terms,
                    clock_ids=clock_ids,
                    suppression_log_terms=sup_terms,
                    suppression_ids=sup_ids,
                    raw_u_values=raw_u,
                    rho_values=rho,
                )
                for _ in range(3)
            ]
            knot_times = np.array([0.0, 1.0, 2.0], dtype=np.float64)
            term_matrix, column_ids, raw_u_matrix, rho_values_arr = build_term_matrix(
                knot_times, rows
            )
            expected_T = 2 + S + 12 + V
            assert term_matrix.shape[1] == expected_T, (
                f"S={S},V={V}: expected T={expected_T}, got {term_matrix.shape[1]}"
            )
            assert raw_u_matrix.shape == (3, V)
            assert rho_values_arr.shape == (V,)

    def test_zero_vighnas(self):
        """V=0 is valid — no suppression active."""
        rows = [
            _make_row(
                suppression_log_terms=[],
                suppression_ids=[],
                raw_u_values=[],
                rho_values=[],
            )
            for _ in range(4)
        ]
        knot_times = np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float64)
        term_matrix, column_ids, raw_u_matrix, rho_values_arr = build_term_matrix(
            knot_times, rows
        )
        T = 2 + 2 + 12 + 0
        assert term_matrix.shape == (4, T)
        assert raw_u_matrix.shape == (4, 0)
        assert rho_values_arr.shape == (0,)


# ── 3. build_term_matrix — column_ids ────────────────────────────────────────

class TestBuildTermMatrixColumnIds:
    def test_first_two_ids(self):
        rows = _make_rows(3)
        knot_times = np.array([0.0, 1.0, 2.0], dtype=np.float64)
        _, column_ids, _, _ = build_term_matrix(knot_times, rows)
        assert column_ids[0] == 'baseline'
        assert column_ids[1] == 'promise'

    def test_clock_ids_position(self):
        rows = _make_rows(3)
        knot_times = np.array([0.0, 1.0, 2.0], dtype=np.float64)
        _, column_ids, _, _ = build_term_matrix(knot_times, rows)
        # columns 2, 3 are the two clock systems
        assert column_ids[2] == 'clock:vimshottari'
        assert column_ids[3] == 'clock:chara'

    def test_modifier_ids_position(self):
        S = 2
        rows = _make_rows(3)
        knot_times = np.array([0.0, 1.0, 2.0], dtype=np.float64)
        _, column_ids, _, _ = build_term_matrix(knot_times, rows)
        # columns 4..15 are the 12 modifiers (2+S=4, 2+S+12=16)
        for i, key in enumerate(COVARIATE_KEYS):
            expected = f'mod:x{i+1}_{key}'
            assert column_ids[2 + S + i] == expected, (
                f"col {2+S+i}: expected {expected!r}, got {column_ids[2+S+i]!r}"
            )

    def test_suppression_ids_position(self):
        S = 2
        rows = _make_rows(3)
        knot_times = np.array([0.0, 1.0, 2.0], dtype=np.float64)
        _, column_ids, _, _ = build_term_matrix(knot_times, rows)
        # columns 16, 17 are the two suppression terms
        assert column_ids[2 + S + 12] == 'sup:vedha:Sa->10'
        assert column_ids[2 + S + 12 + 1] == 'sup:ashtakavarga_deficit:Ju->7'

    def test_column_ids_dtype(self):
        rows = _make_rows(3)
        knot_times = np.array([0.0, 1.0, 2.0], dtype=np.float64)
        _, column_ids, _, _ = build_term_matrix(knot_times, rows)
        assert isinstance(column_ids, np.ndarray), "column_ids must be np.ndarray"
        # numpy unicode array
        assert np.issubdtype(column_ids.dtype, np.str_), (
            f"column_ids dtype should be str, got {column_ids.dtype}"
        )


# ── 4. save_term_matrix — .npz round-trip ───────────────────────────────────

class TestSaveTermMatrix:
    def test_round_trip_fields_present(self, tmp_path):
        K = 5
        rows = _make_rows(K)
        knot_times = np.linspace(0.0, 100.0, K, dtype=np.float64)
        path = str(tmp_path / 'tm.npz')

        result_path = save_term_matrix(
            path=path,
            chart_id='test-chart-id',
            event_class='marriage',
            knot_times=knot_times,
            rows=rows,
            weights_version='v0_classical',
            x_schema_version='x12_v0',
        )

        assert os.path.isfile(result_path)
        data = np.load(result_path, allow_pickle=False)

        required_keys = {
            'knot_times', 'term_matrix', 'column_ids',
            'weights_version', 'x_schema_version',
            'raw_u_matrix', 'rho_values',
        }
        for key in required_keys:
            assert key in data, f"Missing key {key!r} in .npz"

    def test_round_trip_knot_times(self, tmp_path):
        K = 6
        rows = _make_rows(K)
        knot_times = np.linspace(0.0, 50.0, K, dtype=np.float64)
        path = str(tmp_path / 'tm2.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        data = np.load(path, allow_pickle=False)
        np.testing.assert_array_almost_equal(data['knot_times'], knot_times)

    def test_round_trip_term_matrix_shape(self, tmp_path):
        K, S, V = 4, 2, 2
        rows = _make_rows(K)
        knot_times = np.linspace(0.0, 40.0, K, dtype=np.float64)
        path = str(tmp_path / 'tm3.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        data = np.load(path, allow_pickle=False)
        T = 2 + S + 12 + V
        assert data['term_matrix'].shape == (K, T)

    def test_round_trip_metadata(self, tmp_path):
        rows = _make_rows(3)
        knot_times = np.array([0.0, 1.0, 2.0])
        path = str(tmp_path / 'tm4.npz')
        save_term_matrix(
            path=path, chart_id='x', event_class='childbirth',
            knot_times=knot_times, rows=rows,
            weights_version='v1_test', x_schema_version='x12_v0',
        )
        data = np.load(path, allow_pickle=False)
        assert str(data['weights_version']) == 'v1_test'
        assert str(data['x_schema_version']) == 'x12_v0'

    def test_returns_path(self, tmp_path):
        rows = _make_rows(3)
        knot_times = np.array([0.0, 1.0, 2.0])
        path = str(tmp_path / 'ret.npz')
        result = save_term_matrix(
            path=path, chart_id='x', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        assert result == path


# ── 5. F-06/F-14 — raw_u_matrix and rho_values ───────────────────────────────

class TestF06F14:
    def test_raw_u_matrix_shape_and_dtype(self, tmp_path):
        K, V = 6, 2
        rows = _make_rows(K)
        knot_times = np.linspace(0.0, 60.0, K, dtype=np.float64)
        path = str(tmp_path / 'f06.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        data = np.load(path, allow_pickle=False)
        assert data['raw_u_matrix'].shape == (K, V), (
            f"raw_u_matrix shape: expected ({K},{V}), got {data['raw_u_matrix'].shape}"
        )
        assert data['raw_u_matrix'].dtype == np.float32

    def test_rho_values_shape_and_dtype(self, tmp_path):
        K, V = 5, 2
        rows = _make_rows(K)
        knot_times = np.linspace(0.0, 50.0, K, dtype=np.float64)
        path = str(tmp_path / 'f14.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        data = np.load(path, allow_pickle=False)
        assert data['rho_values'].shape == (V,)
        assert data['rho_values'].dtype == np.float32

    def test_raw_u_values_match_input(self, tmp_path):
        """raw_u_matrix[k, m] == row[k].raw_u_values[m] for all k, m."""
        K = 4
        # Two distinct rows so we can verify per-knot variation
        u_per_row = [[0.3, 0.2], [0.5, 0.1], [0.0, 0.7], [0.9, 0.4]]
        rho_per_row = [[0.5, 0.4]] * K
        rows = [
            _make_row(
                raw_u_values=u_per_row[i],
                rho_values=rho_per_row[i],
                suppression_log_terms=[
                    math.log1p(-rho_per_row[i][j] * u_per_row[i][j])
                    for j in range(2)
                ],
            )
            for i in range(K)
        ]
        knot_times = np.linspace(0.0, 30.0, K, dtype=np.float64)
        path = str(tmp_path / 'u_vals.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        data = np.load(path, allow_pickle=False)
        for k in range(K):
            for m in range(2):
                assert data['raw_u_matrix'][k, m] == pytest.approx(u_per_row[k][m], abs=1e-6)

    def test_rho_values_match_first_row(self, tmp_path):
        """rho_values[m] == rows[0].rho_values[m]."""
        K = 3
        rho = [0.7, 0.3]
        rows = [
            _make_row(
                rho_values=rho,
                raw_u_values=[0.2, 0.1],
                suppression_log_terms=[math.log1p(-rho[j] * 0.2) for j in range(2)],
            )
            for _ in range(K)
        ]
        knot_times = np.array([0.0, 1.0, 2.0])
        path = str(tmp_path / 'rho.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        data = np.load(path, allow_pickle=False)
        np.testing.assert_allclose(data['rho_values'], np.array(rho, dtype=np.float32), atol=1e-6)


# ── 6. refit_from_term_matrix — beta refit ───────────────────────────────────

class TestRefitBeta:
    """Verify that mod:* (covariate) columns are correctly re-weighted."""

    def _setup_npz(self, tmp_path, x_vals: list[float], beta_old: float) -> str:
        """Build a matrix with one non-zero modifier column, save, return path."""
        K = 5
        mod_terms = [0.0] * 12
        mod_terms[0] = beta_old * x_vals[0]  # x1 column only
        rows = [
            _make_row(
                baseline=-5.0,
                promise=-1.0,
                clock_terms=[0.0, 0.0],
                modifier_terms=mod_terms,
                suppression_log_terms=[],
                suppression_ids=[],
                raw_u_values=[],
                rho_values=[],
            )
            for _ in range(K)
        ]
        # Override modifier_terms per row to have varying x1
        varied_rows = []
        for i in range(K):
            mt = [0.0] * 12
            mt[0] = beta_old * x_vals[i % len(x_vals)]
            varied_rows.append(
                _make_row(
                    baseline=-5.0,
                    promise=-1.0,
                    clock_terms=[0.0, 0.0],
                    modifier_terms=mt,
                    suppression_log_terms=[],
                    suppression_ids=[],
                    raw_u_values=[],
                    rho_values=[],
                )
            )
        knot_times = np.linspace(0.0, 40.0, K, dtype=np.float64)
        path = str(tmp_path / 'beta_refit.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=varied_rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        return path, knot_times, varied_rows

    def test_beta_refit_segment_count(self, tmp_path):
        x_vals = [0.1, 0.2, 0.3, 0.4, 0.5]
        path, knot_times, rows = self._setup_npz(tmp_path, x_vals, beta_old=1.0)
        new_weights = {'beta_x1': 2.0}
        old_weights = {'beta_x1': 1.0}
        segments = refit_from_term_matrix(path, new_weights, old_weights)
        assert len(segments) == len(knot_times) - 1

    def test_beta_refit_alpha_correct(self, tmp_path):
        """With beta_new=2.0, beta_old=1.0, the new alpha is baseline + promise + 2*x1."""
        x1 = 0.5
        beta_old = 1.0
        beta_new = 2.0
        K = 3
        rows = [
            _make_row(
                baseline=-5.0,
                promise=-1.0,
                clock_terms=[0.0],
                clock_ids=['clock:vimshottari'],
                modifier_terms=[beta_old * x1] + [0.0] * 11,
                suppression_log_terms=[],
                suppression_ids=[],
                raw_u_values=[],
                rho_values=[],
            )
            for _ in range(K)
        ]
        knot_times = np.array([0.0, 10.0, 20.0], dtype=np.float64)
        path = str(tmp_path / 'br2.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        new_weights = {'mod:x1_contact_moon_ref': beta_new}
        old_weights = {'mod:x1_contact_moon_ref': beta_old}
        segments = refit_from_term_matrix(path, new_weights, old_weights)
        # Expected ln_lambda at each knot: -5 + -1 + 0 + beta_new * x1 + 0
        expected_alpha = -5.0 + (-1.0) + 0.0 + beta_new * x1 + 0.0
        for seg in segments:
            assert seg.alpha == pytest.approx(expected_alpha, abs=1e-9)


# ── 7. refit_from_term_matrix — rho refit ────────────────────────────────────

class TestRefitRho:
    """Verify rho refit uses raw_u_matrix + new rho, not stored ln(1-rho*u)."""

    def _build_suppression_npz(self, tmp_path, u_val: float, rho_old: float) -> str:
        K = 4
        sup_log = math.log1p(-rho_old * u_val)
        rows = [
            _make_row(
                baseline=-5.0,
                promise=-1.0,
                clock_terms=[],
                clock_ids=[],
                modifier_terms=[0.0] * 12,
                suppression_log_terms=[sup_log],
                suppression_ids=['sup:vedha:Sa->10'],
                raw_u_values=[u_val],
                rho_values=[rho_old],
            )
            for _ in range(K)
        ]
        knot_times = np.linspace(0.0, 30.0, K, dtype=np.float64)
        path = str(tmp_path / 'rho_refit.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        return path

    def test_rho_refit_alpha_correct(self, tmp_path):
        """ln(1 - rho_new * u) is recomputed from raw_u, not from stored log term.

        raw_u_matrix is stored as float32 (spec §4.3 F-06), so the recovered u
        value carries float32 precision.  The expected alpha is computed from the
        float32-truncated u to match what the implementation reads from the .npz.
        """
        u_val = 0.4
        rho_old = 0.5
        rho_new = 0.7

        path = self._build_suppression_npz(tmp_path, u_val=u_val, rho_old=rho_old)

        new_weights = {'rho:vedha': rho_new}
        old_weights = {'rho:vedha': rho_old}
        segments = refit_from_term_matrix(path, new_weights, old_weights)

        # raw_u_matrix is stored as float32; use float32 u to match implementation.
        u_f32 = float(np.float32(u_val))
        expected_sup = math.log1p(-rho_new * u_f32)
        # Expected alpha = baseline + promise + modifiers(0) + new_sup
        expected_alpha = -5.0 + (-1.0) + 0.0 + expected_sup
        for seg in segments:
            assert seg.alpha == pytest.approx(expected_alpha, abs=1e-6)

    def test_rho_refit_differs_from_beta_refit_on_stored_log(self, tmp_path):
        """Confirm rho refit is NOT just scaling the stored ln(1-rho*u) column.

        raw_u_matrix is stored as float32 (spec §4.3 F-06), so expected values
        are computed from float32-truncated u to match the implementation.
        """
        # If a naive refit just scales the stored column by rho_new/rho_old,
        # it would produce a WRONG result because ln(1-rho*u) is nonlinear in rho.
        u_val = 0.6
        rho_old = 0.3
        rho_new = 0.8
        path = self._build_suppression_npz(tmp_path, u_val=u_val, rho_old=rho_old)

        new_weights = {'rho:vedha': rho_new}
        old_weights = {'rho:vedha': rho_old}
        segments = refit_from_term_matrix(path, new_weights, old_weights)

        # raw_u_matrix stored as float32; use float32 u in expected calculation.
        u_f32 = float(np.float32(u_val))
        # Correct new suppression term (using float32 u)
        correct_sup = math.log1p(-rho_new * u_f32)
        # Wrong naive-scaling result (would use stored ln(1-rho_old*u) directly)
        stored_sup = math.log1p(-rho_old * u_f32)
        naive_wrong_sup = stored_sup * (rho_new / rho_old)

        expected_correct = -5.0 + (-1.0) + correct_sup
        expected_naive_wrong = -5.0 + (-1.0) + naive_wrong_sup

        # They must differ (otherwise the test is vacuous)
        assert expected_correct != pytest.approx(expected_naive_wrong, abs=1e-9)

        # Segments must use the CORRECT formula
        for seg in segments:
            assert seg.alpha == pytest.approx(expected_correct, abs=1e-6)
            assert seg.alpha != pytest.approx(expected_naive_wrong, abs=1e-3)


# ── 8. refit_from_term_matrix — Segment alpha/gamma values ───────────────────

class TestRefitSegmentFields:
    def test_segment_gamma_from_consecutive_knots(self, tmp_path):
        """gamma_i = (ln_lambda_{i+1} - ln_lambda_i) / (t_{i+1} - t_i)."""
        K = 5
        # Make rows with varying modifier_terms to create non-zero gamma
        beta_old = 1.0
        beta_new = 2.0
        x_vals = [0.0, 0.1, 0.3, 0.6, 1.0]
        rows = [
            _make_row(
                baseline=-4.0,
                promise=-0.5,
                clock_terms=[],
                clock_ids=[],
                modifier_terms=[beta_old * x_vals[i]] + [0.0] * 11,
                suppression_log_terms=[],
                suppression_ids=[],
                raw_u_values=[],
                rho_values=[],
            )
            for i in range(K)
        ]
        knot_times = np.array([0.0, 10.0, 25.0, 45.0, 70.0], dtype=np.float64)
        path = str(tmp_path / 'gamma_test.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        mod_col_id = f'mod:x1_{COVARIATE_KEYS[0]}'
        new_weights = {mod_col_id: beta_new}
        old_weights = {mod_col_id: beta_old}
        segments = refit_from_term_matrix(path, new_weights, old_weights)

        # Compute expected ln_lambdas
        expected_ln = [
            -4.0 + (-0.5) + beta_new * x_vals[i]
            for i in range(K)
        ]
        for i, seg in enumerate(segments):
            expected_alpha = expected_ln[i]
            expected_gamma = (
                (expected_ln[i + 1] - expected_ln[i])
                / (knot_times[i + 1] - knot_times[i])
            )
            assert seg.alpha == pytest.approx(expected_alpha, abs=1e-9)
            assert seg.gamma == pytest.approx(expected_gamma, abs=1e-9)
            assert seg.t_start == pytest.approx(knot_times[i])
            assert seg.t_end == pytest.approx(knot_times[i + 1])
            assert seg.index == i

    def test_no_op_refit_reproduces_original_segments(self, tmp_path):
        """Refit with same weights must produce the same alpha/gamma as the build."""
        K = 6
        beta = 1.5
        x_vals = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        rows = [
            _make_row(
                baseline=-3.0,
                promise=-0.7,
                clock_terms=[0.1],
                clock_ids=['clock:vimshottari'],
                modifier_terms=[beta * x_vals[i]] + [0.0] * 11,
                suppression_log_terms=[],
                suppression_ids=[],
                raw_u_values=[],
                rho_values=[],
            )
            for i in range(K)
        ]
        knot_times = np.linspace(0.0, 50.0, K, dtype=np.float64)
        path = str(tmp_path / 'noop.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        mod_col_id = f'mod:x1_{COVARIATE_KEYS[0]}'
        same_weights = {mod_col_id: beta}
        segments = refit_from_term_matrix(path, same_weights, same_weights)

        expected_ln = [
            -3.0 + (-0.7) + 0.1 + beta * x_vals[i]
            for i in range(K)
        ]
        for i, seg in enumerate(segments):
            assert seg.alpha == pytest.approx(expected_ln[i], abs=1e-9)

    def test_segment_index_assigned(self, tmp_path):
        K = 5
        rows = _make_rows(K)
        knot_times = np.linspace(0.0, 40.0, K, dtype=np.float64)
        path = str(tmp_path / 'idx.npz')
        save_term_matrix(
            path=path, chart_id='c', event_class='e',
            knot_times=knot_times, rows=rows,
            weights_version='v0', x_schema_version='x12_v0',
        )
        segments = refit_from_term_matrix(path, {}, {})
        for i, seg in enumerate(segments):
            assert seg.index == i


# ── 9. build_term_matrix_row from HazardTerms ─────────────────────────────────

class TestBuildTermMatrixRow:
    """Verify build_term_matrix_row extracts the correct values from HazardTerms."""

    def test_baseline_and_promise_extracted(self):
        """build_term_matrix_row must use HazardTerms.baseline and .promise_term."""
        import math
        from services.ka_kshetra.hazard import (
            HazardTerms,
            COVARIATE_KEYS,
        )
        from services.ka_kshetra.contracts import ProvenanceEdge

        # Build a minimal HazardTerms with known values
        lam0 = 0.01
        p_tilde = 0.6
        ln_lambda = math.log(lam0) + math.log(p_tilde)
        terms = HazardTerms(
            ln_lambda=ln_lambda,
            baseline=lam0,
            promise_term=p_tilde,
            clock_term=1.0,
            modifier_term=1.0,
            suppression_term=1.0,
            signed_obstruction=0.0,
            edges=(),
        )
        row = build_term_matrix_row(terms, evaluator=None)
        assert row.baseline == pytest.approx(math.log(lam0), abs=1e-12)
        assert row.promise == pytest.approx(math.log(p_tilde), abs=1e-12)

    def test_modifier_terms_from_edges(self):
        """Modifier terms extracted from clock edges, not recomputed."""
        import math
        from services.ka_kshetra.hazard import HazardTerms
        from services.ka_kshetra.contracts import ProvenanceEdge

        # Craft edges with known modifier contributions
        edges = []
        for i, key in enumerate(COVARIATE_KEYS):
            contribution = float(i) * 0.01
            edges.append(ProvenanceEdge(
                term_role='modifier',
                term_key=f'modifier:x{i+1}_{key}',
                term_value=math.exp(contribution),
                log_contribution=contribution,
                source_kind='derived',
            ))

        lam0 = 0.005
        p_tilde = 0.5
        modifier_log = sum(float(i) * 0.01 for i in range(12))
        ln_lambda = math.log(lam0) + math.log(p_tilde) + modifier_log
        terms = HazardTerms(
            ln_lambda=ln_lambda,
            baseline=lam0,
            promise_term=p_tilde,
            clock_term=1.0,
            modifier_term=math.exp(modifier_log),
            suppression_term=1.0,
            signed_obstruction=0.0,
            edges=tuple(edges),
        )
        row = build_term_matrix_row(terms, evaluator=None)
        assert len(row.modifier_terms) == 12
        for i, key in enumerate(COVARIATE_KEYS):
            expected = float(i) * 0.01
            assert row.modifier_terms[i] == pytest.approx(expected, abs=1e-12), (
                f"modifier term {i} ({key}): expected {expected}, got {row.modifier_terms[i]}"
            )

    def test_suppression_terms_from_edges(self):
        """Suppression log_contributions, raw u_values, and rho extracted from edges."""
        import math
        from services.ka_kshetra.hazard import HazardTerms
        from services.ka_kshetra.contracts import ProvenanceEdge

        rho_v = 0.5
        u_v = 0.4
        sup_log = math.log1p(-rho_v * u_v)
        sup_edge = ProvenanceEdge(
            term_role='suppression',
            term_key='suppression:vedha:Sa->10',
            term_value=math.exp(sup_log),
            log_contribution=sup_log,
            weight_id='rho:vedha',
            weight_value=rho_v,
            source_kind='l3_row',
        )
        lam0 = 0.01
        p_tilde = 0.6
        ln_lambda = math.log(lam0) + math.log(p_tilde) + sup_log
        terms = HazardTerms(
            ln_lambda=ln_lambda,
            baseline=lam0,
            promise_term=p_tilde,
            clock_term=1.0,
            modifier_term=1.0,
            suppression_term=math.exp(sup_log),
            signed_obstruction=-(1.0 - math.exp(sup_log)),
            edges=(sup_edge,),
        )
        row = build_term_matrix_row(terms, evaluator=None)
        assert len(row.suppression_log_terms) == 1
        assert row.suppression_log_terms[0] == pytest.approx(sup_log, abs=1e-12)
        # raw u is recovered: u = (1 - exp(log_contribution)) / rho
        expected_u = (1.0 - math.exp(sup_log)) / rho_v
        assert row.raw_u_values[0] == pytest.approx(expected_u, abs=1e-9)
        assert row.rho_values[0] == pytest.approx(rho_v, abs=1e-12)


# ── 10. Rho refit uses raw_u_matrix not stored column ─────────────────────────

class TestRhoRefitFormula:
    """
    Mathematical correctness test: storing ln(1-rho_old*u) and naively scaling
    it by rho_new/rho_old is WRONG; the correct formula is ln(1-rho_new*u).
    This test makes the difference numerically concrete.
    """
    def test_nonlinearity_of_rho_refit(self):
        """ln(1-rho_new*u) != ln(1-rho_old*u) * (rho_new/rho_old) in general."""
        u = 0.5
        rho_old = 0.3
        rho_new = 0.9
        stored = math.log1p(-rho_old * u)      # ln(1 - 0.3 * 0.5) = ln(0.85)
        naive_scale = stored * (rho_new / rho_old)
        correct = math.log1p(-rho_new * u)     # ln(1 - 0.9 * 0.5) = ln(0.55)
        # These differ significantly
        assert abs(naive_scale - correct) > 0.1, (
            f"Expected significant difference; got naive={naive_scale:.6f}, "
            f"correct={correct:.6f}"
        )
