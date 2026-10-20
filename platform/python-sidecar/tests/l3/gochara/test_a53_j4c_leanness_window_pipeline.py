"""J-4c F-LEANNESS — the window store sends a grain's window and membership inserts as ONE write group.

CLAIM C6: `replace_grain_windows` (a) stores byte-identical windows and memberships whether its inserts travel as one pipelined group or
one statement each, and (b) really sends them as ONE group — a grain's per-record membership insert is the loop that cost ~800 round trips
per tiny class. The oracle for (a) is the sequential path; for (b) a counting connection (no INSERT of the grain travels alone)."""
from __future__ import annotations

import contextlib

from services.gochara_kernel import record_store as rs
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.window_store import WindowStore

from .test_a53_record_store import CHART_ID  # noqa: F401
from .test_a53_window_sweep_pg import (CLS, GEN, PATH, VERSION, _geometry_probe_for_every_read,  # noqa: F401  (fixtures)
                                       _p3_probe, _window_rows, grain, pg)


class _Counting:
    def __init__(self, conn):
        self._conn = conn
        self.log: list[tuple[str, bool]] = []
        self.groups = 0
        self._depth = 0

    def execute(self, query, params=None, **kwargs):
        self.log.append((" ".join(str(query).split()), self._depth > 0))
        return self._conn.execute(query, params, **kwargs)

    @contextlib.contextmanager
    def pipeline(self):
        self.groups += 1
        self._depth += 1
        try:
            with self._conn.pipeline():
                yield
        finally:
            self._depth -= 1

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _write(raw, via=None):
    """Sweep the grain on the raw connection, then replace its windows through `via` (the raw connection or a counting wrapper of it)."""
    conn = via if via is not None else raw
    store = WindowStore(conn)
    recs = WindowStore(raw).read_grain(
        chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=PATH, rule_version=VERSION, position_at=_p3_probe)
    drafts, _excluded = ws.draft_windows(CLS, recs, ws.registry_factor_rows)
    with raw.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = store.replace_grain_windows(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=PATH,
                                             rule_version=VERSION, drafts=drafts)
        store.verify_grain(chart_id=CHART_ID, generation=GEN, event_class=CLS, path_id=PATH, rule_version=VERSION)
    return counts


def _stored(conn):
    return (_window_rows(conn),
            conn.execute("SELECT window_id::text, record_id::text, event_class, path_id, rule_version"
                         " FROM public.ka_gochara_eval_window_record ORDER BY 1, 2").fetchall())


def test_c6_the_windows_and_memberships_travel_as_one_group_and_equal_the_sequential_rows(grain, monkeypatch):
    monkeypatch.setattr(rs, "PIPELINE_ENABLED", False)
    sequential_counts = _write(grain)
    sequential = _stored(grain)
    assert sequential[0] and sequential[1], "no window and membership rows: the comparison is vacuous"

    monkeypatch.setattr(rs, "PIPELINE_ENABLED", True)
    counting = _Counting(grain)
    counts = _write(grain, via=counting)                          # replace_grain_windows deletes and re-inserts the grain
    assert counts["windows"] == sequential_counts["windows"] and counts["memberships"] == sequential_counts["memberships"]
    assert _stored(grain) == sequential, "the pipelined window grain stored different rows"

    inserts = [(sql, grouped) for sql, grouped in counting.log if sql.startswith("INSERT INTO public.ka_gochara_eval_window")]
    assert len(inserts) == counts["windows"] + counts["memberships"] >= 2
    alone = [sql[:70] for sql, grouped in inserts if not grouped]
    assert not alone, f"window/membership insert(s) sent as their own round trip: {alone}"
    assert counting.groups == 1, f"the grain's inserts must be ONE group, got {counting.groups}"
