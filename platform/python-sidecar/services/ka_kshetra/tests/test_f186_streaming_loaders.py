"""
tests/ka_kshetra/test_f186_streaming_loaders.py — F-186 streaming-loader tests.

F-186: `_load_window_provenance` and `_load_segments` used to end in
`S4._rows(cur)` — a single client-side `fetchall()` — the same pattern the
module's own docstring (`stage4_field._rows`) flags as wrong for a per-chart
fact table, and the confirmed root cause of the F-141 OOM incident once
already (F-149, on the content-hash walk over the same tables). These tests
assert, structurally, that:

  1. `_load_window_provenance` and `_load_segments` now fetch via a NAMED
     (server-side) cursor + batched `fetchmany()` — never a single unbounded
     `fetchall()` — for a large synthetic fixture, so a real chart's
     ~1.8M-row `kala_field_provenance` / ~8.6M-row `kala_field` table is never
     buffered client-side in one shot.
  2. `_load_window_provenance`'s result is memoized on the writer instance:
     calling it twice (directly, and via `_load_window_fact_ids`, which is
     how stage 6 and stage 6.5 each used to trigger an independent full-table
     read) issues exactly ONE query, not two.
  3. Both loaders' output is byte-identical to the pre-F-186 eager-fetch
     shape — this is a materialization-strategy change only, never a
     behavior change.

Pure-Python; no real DB, no real chart data (CLAUDE.md hard constraint on this
finding — code fix only, no execution against real chart data). The fake
cursor stands in for a psycopg named cursor.
"""
from __future__ import annotations

from services.ka_kshetra.writer import KaKshetraWriter
from services.ka_kshetra.contracts import Segment


# ─────────────────────────────────────────────────────────────────────────────
# Fakes
# ─────────────────────────────────────────────────────────────────────────────

class _FakeCursor:
    """Stands in for a psycopg named (server-side) cursor.

    Serves rows out of an in-memory list via batched `fetchmany()` only — no
    `fetchall()` is implemented, so any loader that regresses to the eager
    `S4._rows` pattern fails LOUDLY (AttributeError) rather than silently
    passing this test.
    """

    def __init__(self, rows: list[dict]):
        self._rows = rows
        self._offset = 0
        self.description = None  # rows are already dicts; _normalize_batch doesn't need this
        self.fetchmany_calls = 0
        self.executed: list[tuple] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchmany(self, size):
        self.fetchmany_calls += 1
        batch = self._rows[self._offset:self._offset + size]
        self._offset += size
        return batch

    def close(self):
        pass


class _FakeConn:
    """Records whether `cursor()` was asked for a NAMED (server-side) cursor,
    and how many cursors were opened in total — the memoization detector."""

    def __init__(self, rows: list[dict]):
        self._rows = rows
        self.cursor_calls: list[dict] = []

    def cursor(self, name=None):
        self.cursor_calls.append({'name': name})
        return _FakeCursor(list(self._rows))


def _make_writer(chart_id='test-chart-id', snapshot_id='snap-1') -> KaKshetraWriter:
    """A KaKshetraWriter with only the F-186-relevant instance state set,
    mirroring `test_optn1_dhara_stage5_wiring.py`'s `_make_writer_instance`
    (skips `plan_substeps` entirely to avoid needing a DB)."""
    obj = object.__new__(KaKshetraWriter)
    obj._chart_id = chart_id
    obj._snapshot_id = snapshot_id
    obj._window_provenance_cache = None
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# _load_window_provenance
# ─────────────────────────────────────────────────────────────────────────────

_N_WINDOWS = 500
_TERMS_PER_WINDOW = 100  # 50,000 provenance rows — several FETCH_BATCH_ROWS batches


def _make_provenance_rows(n_windows=_N_WINDOWS, terms_per_window=_TERMS_PER_WINDOW):
    rows = []
    for w in range(n_windows):
        wid = f'w{w:05d}'
        for t in range(terms_per_window):
            rows.append({
                'target_id': wid,
                'term_key': f'term:{t}',
                'log_contribution': float(t) * 0.001,
                'source_fact_id': f'fact-{w}-{t}',
            })
    return rows


class TestLoadWindowProvenanceStreams:
    def test_uses_named_server_side_cursor(self):
        """Never a plain client-side `conn.cursor()` — the streaming fix's
        whole point is a server-side (named) cursor so the driver bounds what
        it buffers."""
        rows = _make_provenance_rows(n_windows=5, terms_per_window=3)
        conn = _FakeConn(rows)
        writer = _make_writer()

        writer._load_window_provenance(conn)

        assert len(conn.cursor_calls) == 1
        assert conn.cursor_calls[0]['name'] is not None

    def test_batches_via_fetchmany_never_fetchall(self):
        """50,000 synthetic rows — several FETCH_BATCH_ROWS (20,000-default)
        batches — served purely through `fetchmany()`. `_FakeCursor` has no
        `fetchall`, so a regression to eager fetch fails this test with an
        AttributeError, not a silent pass."""
        rows = _make_provenance_rows()
        conn = _FakeConn(rows)
        writer = _make_writer()

        out = writer._load_window_provenance(conn)

        cur = conn.cursor_calls  # sanity: exactly one cursor opened
        assert len(cur) == 1
        assert len(out) == _N_WINDOWS
        assert len(out['w00000']) == _TERMS_PER_WINDOW

    def test_second_call_is_memoized_not_requeried(self):
        """The F-186 highest-priority sub-fix: `_load_window_fact_ids` used to
        call `_load_window_provenance` a SECOND time rather than reuse the
        first call's result, doubling a full-table read of a ~1.8M-row table
        every build. Assert exactly ONE query fires across both call paths.
        """
        rows = _make_provenance_rows(n_windows=10, terms_per_window=4)
        conn = _FakeConn(rows)
        writer = _make_writer()

        first = writer._load_window_provenance(conn)
        second = writer._load_window_provenance(conn)  # direct second call
        fact_ids = writer._load_window_fact_ids(conn)   # indirect (real trigger)

        assert len(conn.cursor_calls) == 1, (
            f'expected exactly 1 query across 3 call sites, got '
            f'{len(conn.cursor_calls)} — memoization regressed'
        )
        assert first is second  # same cached dict object, not a re-fetch
        assert len(fact_ids) == 10
        assert fact_ids['w00000'] == sorted(f'fact-0-{t}' for t in range(4))

    def test_output_shape_matches_pre_f186_eager_semantics(self):
        """The refactor is a materialization-strategy change only: output must
        be identical dict[window_id, list[row-dict]] with the same rows."""
        rows = _make_provenance_rows(n_windows=3, terms_per_window=2)
        conn = _FakeConn(rows)
        writer = _make_writer()

        out = writer._load_window_provenance(conn)

        assert set(out.keys()) == {'w00000', 'w00001', 'w00002'}
        for wid, terms in out.items():
            assert len(terms) == 2
            assert {t['term_key'] for t in terms} == {'term:0', 'term:1'}


# ─────────────────────────────────────────────────────────────────────────────
# _load_segments
# ─────────────────────────────────────────────────────────────────────────────

def _make_segment_rows(n=50_000):
    return [
        {
            'segment_index': i,
            't_start': float(i),
            't_end': float(i + 1),
            'alpha': -1.0,
            'gamma': 0.01,
            'refinement_depth': 0,
            'refinement_exhausted': False,
            'refinement_residual': None,
        }
        for i in range(n)
    ]


class TestLoadSegmentsStreams:
    def test_uses_named_server_side_cursor(self):
        rows = _make_segment_rows(n=5)
        conn = _FakeConn(rows)
        writer = _make_writer()

        writer._load_segments(conn, 'CAREER')

        assert len(conn.cursor_calls) == 1
        assert conn.cursor_calls[0]['name'] is not None

    def test_batches_via_fetchmany_and_preserves_output(self):
        """50,000 synthetic segment rows — several FETCH_BATCH_ROWS batches —
        served only through `fetchmany()` (no `fetchall` on the fake cursor),
        and the returned `list[Segment]` is unchanged in shape/values."""
        rows = _make_segment_rows()
        conn = _FakeConn(rows)
        writer = _make_writer()

        out = writer._load_segments(conn, 'CAREER')

        assert len(out) == len(rows)
        assert all(isinstance(s, Segment) for s in out)
        assert out[0].index == 0
        assert out[0].t_start == 0.0
        assert out[-1].index == len(rows) - 1

    def test_each_event_class_call_reissues_its_own_query(self):
        """Unlike window provenance, `_load_segments` is legitimately called
        once per event class (§D.2 Hub H) — no cross-call memoization is
        expected or correct here (each class's segments differ)."""
        rows = _make_segment_rows(n=3)
        conn = _FakeConn(rows)
        writer = _make_writer()

        writer._load_segments(conn, 'CAREER')
        writer._load_segments(conn, 'HEALTH')

        assert len(conn.cursor_calls) == 2
